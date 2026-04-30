"""Phase 4: Multi-Camera, RTSP Streams, REST API Server"""

import cv2, numpy as np, threading, time, logging, json, queue
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

logger = logging.getLogger(__name__)


class MultiCameraManager:
    """Manage multiple camera streams simultaneously"""
    
    def __init__(self, max_cameras=4):
        self.max_cameras = max_cameras
        self.cameras = {}
        self.lock = threading.Lock()
        self.frame_buffers = {}
        self.stats = defaultdict(dict)
    
    def add_camera(self, camera_id, source, source_type="rtsp"):
        """Add camera stream (webcam, file, RTSP)"""
        if len(self.cameras) >= self.max_cameras:
            raise ValueError(f"Max {self.max_cameras} cameras reached")
        
        with self.lock:
            self.cameras[camera_id] = {
                'source': source,
                'type': source_type,
                'status': 'CONNECTING',
                'frame_count': 0,
                'detections': 0,
                'fps': 0,
                'connected_at': datetime.now()
            }
            self.frame_buffers[camera_id] = queue.Queue(maxsize=5)
        
        logger.info(f"Camera {camera_id} added: {source}")
        return camera_id
    
    def remove_camera(self, camera_id):
        """Remove camera stream"""
        with self.lock:
            if camera_id in self.cameras:
                del self.cameras[camera_id]
                del self.frame_buffers[camera_id]
                logger.info(f"Camera {camera_id} removed")
    
    def get_camera_list(self):
        """Get all active cameras"""
        with self.lock:
            return {cid: {k: v for k, v in cam.items() if k != 'source'} 
                   for cid, cam in self.cameras.items()}
    
    def update_stats(self, camera_id, frame_count, detections, fps):
        """Update camera statistics"""
        with self.lock:
            if camera_id in self.cameras:
                self.cameras[camera_id]['frame_count'] = frame_count
                self.cameras[camera_id]['detections'] = detections
                self.cameras[camera_id]['fps'] = fps
                self.cameras[camera_id]['status'] = 'ACTIVE'
    
    def put_frame(self, camera_id, frame):
        """Add frame to buffer"""
        if camera_id in self.frame_buffers:
            try:
                self.frame_buffers[camera_id].put_nowait(frame)
            except queue.Full:
                pass
    
    def get_frame(self, camera_id):
        """Get latest frame"""
        if camera_id in self.frame_buffers:
            try:
                return self.frame_buffers[camera_id].get(timeout=0.1)
            except queue.Empty:
                return None
        return None


class RTSPStreamHandler:
    """Handle RTSP/HTTP streams"""
    
    @staticmethod
    def validate_rtsp_url(url):
        """Validate RTSP URL format"""
        valid_protocols = ['rtsp://', 'rtsps://', 'http://', 'https://', 'rtmp://']
        return any(url.startswith(proto) for proto in valid_protocols)
    
    @staticmethod
    def connect_stream(source):
        """Connect to RTSP/HTTP stream"""
        try:
            cap = cv2.VideoCapture(source)
            if not cap.isOpened():
                raise ConnectionError(f"Failed to connect to {source}")
            
            # Set buffer size to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        except Exception as e:
            logger.error(f"RTSP connection error: {e}")
            return None
    
    @staticmethod
    def generate_mjpeg_stream(frame_buffer):
        """Generate MJPEG stream from frame buffer"""
        while True:
            try:
                frame = frame_buffer.get(timeout=1)
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(buffer)).encode() + b'\r\n\r\n' 
                       + buffer.tobytes() + b'\r\n')
            except queue.Empty:
                continue


class MultiCameraProcessor(threading.Thread):
    """Process multiple camera streams in parallel"""
    
    def __init__(self, camera_id, source, model, db, camera_manager, stop_event):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.source = source
        self.model = model
        self.db = db
        self.camera_manager = camera_manager
        self.stop_event = stop_event
        
        self.frame_count = 0
        self.total_detections = 0
        self.confidences = []
        self.classes = set()
    
    def run(self):
        """Process camera stream"""
        cap = RTSPStreamHandler.connect_stream(self.source)
        if not cap:
            self.camera_manager.cameras[self.camera_id]['status'] = 'FAILED'
            return
        
        prev_time = time.time()
        session_id = int(time.time() * 1000) + hash(self.camera_id) % 1000
        
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Camera {self.camera_id} stream ended")
                break
            
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0
            prev_time = current_time
            
            self.frame_count += 1
            
            # Resize for faster processing
            frame_small = cv2.resize(frame, (640, 480))
            annotated, detections, _ = self.model.detect(frame_small)
            
            self.total_detections += len(detections)
            for det in detections:
                self.confidences.append(det['confidence'])
                self.classes.add(det['class'])
                self.db.insert(session_id, self.frame_count, det, fps, 
                             'rtsp' if 'rtsp' in self.source.lower() else 'http', 
                             self.source)
            
            # Add camera ID overlay
            cv2.putText(annotated, f"Camera: {self.camera_id}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            self.camera_manager.put_frame(self.camera_id, annotated)
            self.camera_manager.update_stats(self.camera_id, self.frame_count, 
                                            self.total_detections, fps)
        
        cap.release()
        logger.info(f"Camera {self.camera_id} processor stopped")


class DetectionAPIServer:
    """FastAPI server for remote monitoring and control"""
    
    def __init__(self, camera_manager, model, db, port=8000):
        self.app = FastAPI(title="AI Detection API v4.0")
        self.camera_manager = camera_manager
        self.model = model
        self.db = db
        self.port = port
        self.active_streams = {}
        
        self._setup_cors()
        self._setup_routes()
    
    def _setup_cors(self):
        """Setup CORS for cross-origin requests"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/api/health")
        async def health():
            """Health check"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/cameras")
        async def get_cameras():
            """Get all active cameras"""
            return self.camera_manager.get_camera_list()
        
        @self.app.post("/api/cameras/add")
        async def add_camera(camera_id: str, source: str, source_type: str = "rtsp"):
            """Add new camera stream"""
            try:
                if source_type == "rtsp" and not RTSPStreamHandler.validate_rtsp_url(source):
                    raise HTTPException(status_code=400, detail="Invalid RTSP URL")
                
                self.camera_manager.add_camera(camera_id, source, source_type)
                return {"status": "success", "camera_id": camera_id}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/cameras/{camera_id}")
        async def remove_camera(camera_id: str):
            """Remove camera stream"""
            self.camera_manager.remove_camera(camera_id)
            return {"status": "success", "camera_id": camera_id}
        
        @self.app.get("/api/cameras/{camera_id}/stats")
        async def get_camera_stats(camera_id: str):
            """Get camera statistics"""
            cameras = self.camera_manager.get_camera_list()
            if camera_id not in cameras:
                raise HTTPException(status_code=404, detail="Camera not found")
            return cameras[camera_id]
        
        @self.app.get("/api/cameras/{camera_id}/stream")
        async def stream_camera(camera_id: str):
            """Stream camera as MJPEG"""
            if camera_id not in self.camera_manager.frame_buffers:
                raise HTTPException(status_code=404, detail="Camera not found")
            
            return StreamingResponse(
                RTSPStreamHandler.generate_mjpeg_stream(
                    self.camera_manager.frame_buffers[camera_id]
                ),
                media_type="multipart/x-mixed-replace; boundary=frame"
            )
        
        @self.app.get("/api/detections/summary")
        async def get_detection_summary():
            """Get detection summary across all cameras"""
            df = self.db.read_all()
            if df.empty:
                return {"total": 0, "by_class": {}, "by_camera": {}}
            
            return {
                "total": len(df),
                "by_class": df['class_name'].value_counts().to_dict(),
                "by_camera": df['source_path'].value_counts().to_dict(),
                "avg_confidence": float(df['confidence'].mean())
            }
        
        @self.app.get("/api/detections/date-range")
        async def get_detections_by_date(start_date: str, end_date: str):
            """Get detections for date range"""
            df = self.db.get_date_range_data(start_date, end_date)
            return {
                "count": len(df),
                "by_class": df['class_name'].value_counts().to_dict() if not df.empty else {},
                "data": df.to_dict(orient='records')[:100]  # Limit to 100 records
            }
        
        @self.app.post("/api/model/update")
        async def update_model(model_name: str):
            """Update detection model"""
            try:
                self.model.model_name = f"{model_name}.pt"
                self.model._load()
                return {"status": "success", "model": model_name}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/model/info")
        async def get_model_info():
            """Get current model info"""
            return {
                "model": self.model.model_name,
                "classes": len(self.model.classes),
                "confidence_threshold": self.model.conf
            }
        
        @self.app.websocket("/ws/live")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            try:
                while True:
                    cameras = self.camera_manager.get_camera_list()
                    await websocket.send_json({
                        "timestamp": datetime.now().isoformat(),
                        "cameras": cameras
                    })
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
    
    def run(self):
        """Start API server"""
        logger.info(f"Starting API server on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")


class GridViewGUI:
    """Multi-camera grid view GUI"""
    
    def __init__(self, camera_manager, max_cameras=4):
        import tkinter as tk
        from tkinter import ttk
        
        self.root = tk.Tk()
        self.root.title("Multi-Camera Grid View")
        self.root.geometry("1600x1000")
        
        self.camera_manager = camera_manager
        self.max_cameras = max_cameras
        self.canvas_widgets = {}
        
        self._setup_grid()
        self._start_update()
    
    def _setup_grid(self):
        """Setup grid layout for cameras"""
        import tkinter as tk
        
        grid_size = int(np.ceil(np.sqrt(self.max_cameras)))
        
        for i in range(self.max_cameras):
            row = i // grid_size
            col = i % grid_size
            
            frame = tk.Frame(self.root, bg="black", relief=tk.SUNKEN, bd=2)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            canvas = tk.Canvas(frame, bg="black", highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.create_text(200, 150, text=f"Camera {i+1}", fill="white", font=("Arial", 14))
            
            self.canvas_widgets[f"camera_{i}"] = canvas
            
            self.root.grid_rowconfigure(row, weight=1)
            self.root.grid_columnconfigure(col, weight=1)
    
    def _start_update(self):
        """Start updating grid"""
        def update():
            for cam_id, canvas in self.canvas_widgets.items():
                frame = self.camera_manager.get_frame(cam_id)
                if frame is not None:
                    from PIL import Image, ImageTk
                    import cv2
                    
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb)
                    img.thumbnail((400, 300))
                    photo = ImageTk.PhotoImage(image=img)
                    
                    canvas.delete("all")
                    canvas.create_image(200, 150, image=photo)
                    canvas.image = photo
            
            self.root.after(100, update)
        
        update()
    
    def run(self):
        """Run GUI"""
        self.root.mainloop()


# Example usage
if __name__ == "__main__":
    from main_v2 import DetectionModel, SQLiteDB
    
    # Initialize
    model = DetectionModel('yolov8s.pt')
    db = SQLiteDB()
    camera_manager = MultiCameraManager(max_cameras=4)
    
    # Start API server
    api = DetectionAPIServer(camera_manager, model, db, port=8000)
    api_thread = threading.Thread(target=api.run, daemon=True)
    api_thread.start()
    
    print("API Server running on http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    
    # Add cameras
    camera_manager.add_camera("cam1", 0, "webcam")
    camera_manager.add_camera("cam2", "rtsp://example.com/stream1", "rtsp")
    
    # Start processors
    stop_event = threading.Event()
    for cam_id, cam_info in camera_manager.cameras.items():
        processor = MultiCameraProcessor(cam_id, cam_info['source'], model, db, 
                                        camera_manager, stop_event)
        processor.start()
    
    # Start grid view
    grid = GridViewGUI(camera_manager)
    grid.run()
