"""Multi-Camera Management and REST API Server"""

import cv2, threading, logging, queue, asyncio
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


class MultiCameraManager:
    """Manage multiple camera streams"""
    
    def __init__(self, max_cameras=4):
        self.max_cameras = max_cameras
        self.cameras = {}
        self.lock = threading.Lock()
        self.frame_buffers = {}
        self.stats = defaultdict(dict)
    
    def add_camera(self, camera_id, source, source_type="rtsp"):
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
        with self.lock:
            if camera_id in self.cameras:
                del self.cameras[camera_id]
                del self.frame_buffers[camera_id]
                logger.info(f"Camera {camera_id} removed")
    
    def get_camera_list(self):
        with self.lock:
            return {cid: {k: v for k, v in cam.items() if k != 'source'} 
                   for cid, cam in self.cameras.items()}
    
    def put_frame(self, camera_id, frame):
        if camera_id in self.frame_buffers:
            try:
                self.frame_buffers[camera_id].put_nowait(frame)
            except queue.Full:
                pass


class DetectionAPIServer:
    """FastAPI server for remote monitoring"""
    
    def __init__(self, camera_manager, model, db, port=8000):
        self.app = FastAPI(title="AI Detection API v4.0")
        self.camera_manager = camera_manager
        self.model = model
        self.db = db
        self.port = port
        
        self._setup_cors()
        self._setup_routes()
    
    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        @self.app.get("/api/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/cameras")
        async def get_cameras():
            return self.camera_manager.get_camera_list()
        
        @self.app.post("/api/cameras/add")
        async def add_camera(camera_id: str, source: str, source_type: str = "rtsp"):
            try:
                self.camera_manager.add_camera(camera_id, source, source_type)
                return {"status": "success", "camera_id": camera_id}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/cameras/{camera_id}")
        async def remove_camera(camera_id: str):
            self.camera_manager.remove_camera(camera_id)
            return {"status": "success", "camera_id": camera_id}
        
        @self.app.get("/api/detections/summary")
        async def get_detection_summary():
            df = self.db.read_all()
            if df.empty:
                return {"total": 0, "by_class": {}, "avg_confidence": 0}
            
            return {
                "total": len(df),
                "by_class": df['class_name'].value_counts().to_dict(),
                "avg_confidence": float(df['confidence'].mean())
            }
        
        @self.app.get("/api/model/info")
        async def get_model_info():
            return {
                "model": self.model.model_name,
                "classes": len(self.model.classes),
                "confidence_threshold": self.model.conf
            }
    
    def run(self):
        logger.info(f"Starting API server on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, log_level="info")


if __name__ == "__main__":
    print("Multi-Camera API Server - Use with app.py")
