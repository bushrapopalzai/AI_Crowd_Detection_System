"""AI Detection System v2.0 - SQLite + YOLOv8s + Async"""

import cv2, numpy as np, tkinter as tk, threading, time, sqlite3, logging
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from collections import deque
from datetime import datetime
import pandas as pd

try:
    import customtkinter as ctk
    USE_CTK = True
except:
    USE_CTK = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteDB:
    def __init__(self, db_path="detection_records.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.buffer = []
        self.buffer_size = 50
        self.last_flush = time.time()
        self._init_db()
        threading.Thread(target=self._bg_flush, daemon=True).start()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY, timestamp DATETIME, date TEXT, time TEXT,
                session_id INTEGER, frame_number INTEGER, class_name TEXT, confidence REAL,
                bbox_x1 INTEGER, bbox_y1 INTEGER, bbox_x2 INTEGER, bbox_y2 INTEGER,
                fps REAL, source_type TEXT, source_path TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY, start_time DATETIME, end_time DATETIME,
                date TEXT, source_type TEXT, source_path TEXT, total_frames INTEGER,
                total_detections INTEGER, unique_classes INTEGER, avg_confidence REAL,
                duration_seconds REAL, status TEXT)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON detections(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON detections(session_id)')
            conn.commit()
    
    def _bg_flush(self):
        while True:
            time.sleep(1)
            if len(self.buffer) >= self.buffer_size or (time.time() - self.last_flush >= 5 and self.buffer):
                self._flush()
    
    def _flush(self):
        if not self.buffer:
            return
        with self.lock:
            buf = self.buffer.copy()
            self.buffer = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany('''INSERT INTO detections 
                    (timestamp, date, time, session_id, frame_number, class_name, confidence,
                     bbox_x1, bbox_y1, bbox_x2, bbox_y2, fps, source_type, source_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', buf)
                conn.commit()
            self.last_flush = time.time()
        except Exception as e:
            logger.error(f"Flush error: {e}")
            with self.lock:
                self.buffer = buf + self.buffer
    
    def insert(self, session_id, frame_num, det, fps, src_type, src_path):
        now = datetime.now()
        with self.lock:
            self.buffer.append((now, now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S.%f')[:-3],
                session_id, frame_num, det['class'], round(det['confidence'], 4),
                det['bbox'][0], det['bbox'][1], det['bbox'][2], det['bbox'][3],
                round(fps, 2), src_type, src_path))
        if len(self.buffer) >= self.buffer_size:
            threading.Thread(target=self._flush, daemon=True).start()
    
    def end_session(self, sid, frames, dets, classes, conf):
        self._flush()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''INSERT INTO sessions 
                    (session_id, start_time, end_time, date, source_type, source_path,
                     total_frames, total_detections, unique_classes, avg_confidence, duration_seconds, status)
                    SELECT ?, ?, ?, date, source_type, source_path, ?, ?, ?, ?, ?, 'COMPLETED'
                    FROM detections WHERE session_id = ? LIMIT 1''',
                    (sid, datetime.now(), datetime.now(), frames, dets, classes, conf, 0, sid))
                conn.commit()
        except Exception as e:
            logger.error(f"Session error: {e}")
    
    def read_all(self):
        self._flush()
        try:
            return pd.read_sql_query('SELECT * FROM detections', sqlite3.connect(self.db_path))
        except:
            return pd.DataFrame()


class DetectionModel:
    def __init__(self, model='yolov8s.pt'):
        self.model_name = model
        self.model = None
        self.classes = {}
        self.colors = {}
        self.conf = 0.5
        self._load()
    
    def _load(self):
        try:
            from ultralytics import YOLO
            logger.info(f"Loading {self.model_name}...")
            self.model = YOLO(self.model_name)
            self.classes = self.model.names
            np.random.seed(42)
            for cls_name in self.classes.values():
                self.colors[cls_name] = tuple(map(int, np.random.randint(0, 255, 3)))
            logger.info(f"Model loaded: {len(self.classes)} classes")
        except Exception as e:
            logger.error(f"Load error: {e}")
    
    def detect(self, frame):
        if not self.model:
            return frame, []
        try:
            results = self.model(frame, conf=self.conf, verbose=False)
            dets = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.classes[cls_id]
                dets.append({'class': cls_name, 'confidence': conf, 'bbox': (x1, y1, x2, y2)})
            
            frame = frame.copy()
            for det in dets:
                x1, y1, x2, y2 = det['bbox']
                color = self.colors.get(det['class'], (0, 255, 0))
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{det['class']} {det['confidence']:.2f}"
                cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            return frame, dets
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return frame, []


class VideoProcessor(threading.Thread):
    def __init__(self, model, buffer, stop_event, db, sid, src_type, src_path):
        super().__init__(daemon=True)
        self.model = model
        self.buffer = buffer
        self.stop_event = stop_event
        self.db = db
        self.sid = sid
        self.src_type = src_type
        self.src_path = src_path
        self.frame_count = 0
        self.total_dets = 0
        self.confs = []
        self.classes = set()
    
    def run(self):
        cap = cv2.VideoCapture(self.src_path)
        if not cap.isOpened():
            logger.error("Failed to open video")
            self.stop_event.set()
            return
        
        prev_time = time.time()
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0
            prev_time = current_time
            
            self.frame_count += 1
            frame, dets = self.model.detect(frame)
            
            self.total_dets += len(dets)
            for det in dets:
                self.confs.append(det['confidence'])
                self.classes.add(det['class'])
                self.db.insert(self.sid, self.frame_count, det, fps, self.src_type, str(self.src_path))
            
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Frame: {self.frame_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            try:
                self.buffer.put_nowait((frame, dets, fps, datetime.now()))
            except:
                pass
        
        cap.release()
        avg_conf = sum(self.confs) / len(self.confs) if self.confs else 0
        self.db.end_session(self.sid, self.frame_count, self.total_dets, len(self.classes), avg_conf)


class GUI:
    def __init__(self):
        self.root = ctk.CTk() if USE_CTK else tk.Tk()
        self.root.title("AI Detection v2.0 - SQLite + YOLOv8s")
        self.root.geometry("1600x1000")
        
        self.model = DetectionModel('yolov8s.pt')
        self.db = SQLiteDB()
        self.buffer = __import__('queue').Queue(maxsize=5)
        
        self.sid = int(time.time())
        self.current_sid = None
        self.is_processing = False
        self.stop_event = threading.Event()
        self.video_thread = None
        self.photo_image = None
        self.after_id = None
        
        self._setup_ui()
        self._start_loop()
    
    def _setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        if USE_CTK:
            self.tabview = ctk.CTkTabview(self.root)
        else:
            self.tabview = ttk.Notebook(self.root)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        if USE_CTK:
            self.tab_live = self.tabview.add("Live Detection")
            self.tab_data = self.tabview.add("Database")
        else:
            self.tab_live = tk.Frame(self.tabview)
            self.tab_data = tk.Frame(self.tabview)
            self.tabview.add(self.tab_live, text="Live")
            self.tabview.add(self.tab_data, text="Data")
        
        # Live tab
        main = ctk.CTkFrame(self.tab_live) if USE_CTK else tk.Frame(self.tab_live)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        video_frame = ctk.CTkFrame(main) if USE_CTK else tk.LabelFrame(main, text="Video")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.video_canvas = tk.Canvas(video_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        self.video_canvas.create_text(400, 300, text="Start Camera or Upload Video", fill="white", font=("Arial", 16))
        
        ctrl = ctk.CTkFrame(main, width=300) if USE_CTK else tk.LabelFrame(main, text="Controls", width=300)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ctrl.pack_propagate(False)
        
        self.btn_cam = ctk.CTkButton(ctrl, text="Start Camera", command=self._start_cam) if USE_CTK else tk.Button(ctrl, text="Start Camera", command=self._start_cam)
        self.btn_cam.pack(fill=tk.X, pady=5)
        
        self.btn_vid = ctk.CTkButton(ctrl, text="Upload Video", command=self._upload_vid) if USE_CTK else tk.Button(ctrl, text="Upload Video", command=self._upload_vid)
        self.btn_vid.pack(fill=tk.X, pady=5)
        
        self.btn_stop = ctk.CTkButton(ctrl, text="Stop", command=self._stop, state="disabled") if USE_CTK else tk.Button(ctrl, text="Stop", command=self._stop, state="disabled")
        self.btn_stop.pack(fill=tk.X, pady=5)
        
        self.stat_labels = {}
        for name in ["Status", "Frames", "Detections", "FPS"]:
            row = ctk.CTkFrame(ctrl) if USE_CTK else tk.Frame(ctrl)
            row.pack(fill=tk.X, pady=2)
            if USE_CTK:
                ctk.CTkLabel(row, text=f"{name}:").pack(side=tk.LEFT)
                lbl = ctk.CTkLabel(row, text="-")
            else:
                tk.Label(row, text=f"{name}:").pack(side=tk.LEFT)
                lbl = tk.Label(row, text="-")
            lbl.pack(side=tk.LEFT)
            self.stat_labels[name] = lbl
        
        # Data tab
        self.text_data = tk.Text(self.tab_data, font=("Courier", 9))
        self.text_data.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _start_cam(self):
        self._start(0, "camera")
    
    def _upload_vid(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv")])
        if f:
            self._start(f, "file")
    
    def _start(self, src, src_type):
        if self.is_processing:
            return
        self.sid += 1
        self.current_sid = self.sid
        self.is_processing = True
        self.stop_event.clear()
        self.btn_cam.configure(state="disabled")
        self.btn_vid.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.stat_labels["Status"].configure(text="Running")
        
        self.video_thread = VideoProcessor(self.model, self.buffer, self.stop_event, self.db, self.current_sid, src_type, src)
        self.video_thread.start()
    
    def _stop(self):
        if not self.is_processing:
            return
        self.stop_event.set()
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=3)
        self.is_processing = False
        self.btn_cam.configure(state="normal")
        self.btn_vid.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.stat_labels["Status"].configure(text="Stopped")
    
    def _start_loop(self):
        self._update_frame()
        self._update_stats()
    
    def _update_frame(self):
        if self.is_processing:
            try:
                frame, dets, fps, ts = self.buffer.get(timeout=0.001)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                self.photo_image = __import__('PIL.ImageTk', fromlist=['PhotoImage']).PhotoImage(image=img)
                self.video_canvas.delete("all")
                self.video_canvas.create_image(500, 350, image=self.photo_image)
            except:
                pass
        self.after_id = self.root.after(33, self._update_frame)
    
    def _update_stats(self):
        if self.is_processing and self.video_thread:
            self.stat_labels["Frames"].configure(text=str(self.video_thread.frame_count))
            self.stat_labels["Detections"].configure(text=str(self.video_thread.total_dets))
        self.root.after(1000, self._update_stats)
    
    def _on_close(self):
        if self.is_processing:
            self._stop()
        self.db._flush()
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()


if __name__ == "__main__":
    print("="*50)
    print("AI Detection v2.0 - SQLite + YOLOv8s")
    print("="*50)
    GUI().run()
