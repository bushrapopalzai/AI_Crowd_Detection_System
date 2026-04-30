"""AI Detection System v4.0 - Main Application"""

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
    
    def export_csv(self, filepath):
        df = self.read_all()
        df.to_csv(filepath, index=False)
        return len(df)


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
        self.root.title("AI Detection System v4.0")
        self.root.geometry("1800x1000")
        
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
        self.stats_history = deque(maxlen=500)
        
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
            self.tab_analytics = self.tabview.add("Analytics & Charts")
            self.tab_export = self.tabview.add("Export & Reports")
        else:
            self.tab_live = tk.Frame(self.tabview)
            self.tab_analytics = tk.Frame(self.tabview)
            self.tab_export = tk.Frame(self.tabview)
            self.tabview.add(self.tab_live, text="Live")
            self.tabview.add(self.tab_analytics, text="Analytics")
            self.tabview.add(self.tab_export, text="Export")
        
        self._setup_live_tab()
        self._setup_analytics_tab()
        self._setup_export_tab()
    
    def _setup_live_tab(self):
        main = ctk.CTkFrame(self.tab_live) if USE_CTK else tk.Frame(self.tab_live)
        main.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        video_frame = ctk.CTkFrame(main) if USE_CTK else tk.LabelFrame(main, text="Video")
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.video_canvas = tk.Canvas(video_frame, bg="black")
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        self.video_canvas.create_text(400, 300, text="Start Camera or Upload Video", fill="white", font=("Arial", 16))
        
        ctrl = ctk.CTkFrame(main, width=350) if USE_CTK else tk.LabelFrame(main, text="Controls", width=350)
        ctrl.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        ctrl.pack_propagate(False)
        
        self.btn_cam = ctk.CTkButton(ctrl, text="📷 Start Camera", command=self._start_cam) if USE_CTK else tk.Button(ctrl, text="Start Camera", command=self._start_cam)
        self.btn_cam.pack(fill=tk.X, pady=5)
        
        self.btn_vid = ctk.CTkButton(ctrl, text="📁 Upload Video", command=self._upload_vid) if USE_CTK else tk.Button(ctrl, text="Upload Video", command=self._upload_vid)
        self.btn_vid.pack(fill=tk.X, pady=5)
        
        self.btn_stop = ctk.CTkButton(ctrl, text="⏹ Stop", command=self._stop, state="disabled") if USE_CTK else tk.Button(ctrl, text="Stop", command=self._stop, state="disabled")
        self.btn_stop.pack(fill=tk.X, pady=5)
        
        self.stat_labels = {}
        for name in ["Status", "Frames", "Detections", "FPS", "Avg Conf"]:
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
    
    def _setup_analytics_tab(self):
        frame = ctk.CTkFrame(self.tab_analytics) if USE_CTK else tk.Frame(self.tab_analytics)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(14, 8))
        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _setup_export_tab(self):
        frame = ctk.CTkFrame(self.tab_export) if USE_CTK else tk.Frame(self.tab_export)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_csv = ctk.CTkButton(frame, text="📊 Export to CSV", command=self._export_csv) if USE_CTK else tk.Button(frame, text="Export CSV", command=self._export_csv)
        btn_csv.pack(pady=10)
        
        btn_pdf = ctk.CTkButton(frame, text="📄 Export to PDF", command=self._export_pdf) if USE_CTK else tk.Button(frame, text="Export PDF", command=self._export_pdf)
        btn_pdf.pack(pady=10)
        
        self.export_status = tk.Label(frame, text="Ready to export", font=("Arial", 10))
        self.export_status.pack(pady=10)
    
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
        self.stats_history.clear()
        
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
        self._update_charts()
    
    def _update_frame(self):
        if self.is_processing:
            try:
                frame, dets, fps, ts = self.buffer.get(timeout=0.001)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                self.photo_image = __import__('PIL.ImageTk', fromlist=['PhotoImage']).PhotoImage(image=img)
                self.video_canvas.delete("all")
                self.video_canvas.create_image(500, 350, image=self.photo_image)
                self.stats_history.append({'time': ts, 'dets': len(dets), 'fps': fps})
            except:
                pass
        self.after_id = self.root.after(33, self._update_frame)
    
    def _update_stats(self):
        if self.is_processing and self.video_thread:
            self.stat_labels["Frames"].configure(text=str(self.video_thread.frame_count))
            self.stat_labels["Detections"].configure(text=str(self.video_thread.total_dets))
            if self.video_thread.confs:
                self.stat_labels["Avg Conf"].configure(text=f"{sum(self.video_thread.confs)/len(self.video_thread.confs):.2f}")
            if self.stats_history:
                self.stat_labels["FPS"].configure(text=f"{self.stats_history[-1]['fps']:.1f}")
        self.root.after(1000, self._update_stats)
    
    def _update_charts(self):
        try:
            self.ax1.clear()
            self.ax2.clear()
            self.ax3.clear()
            self.ax4.clear()
            
            if len(self.stats_history) > 1:
                times = list(range(len(self.stats_history)))
                dets = [s['dets'] for s in self.stats_history]
                fps_vals = [s['fps'] for s in self.stats_history]
                
                # Chart 1: Detections per frame
                self.ax1.plot(times, dets, color='#3498db', linewidth=2, marker='o')
                self.ax1.fill_between(times, dets, alpha=0.3, color='#3498db')
                self.ax1.set_title("Detections per Frame", fontsize=12, fontweight='bold')
                self.ax1.set_xlabel("Frame")
                self.ax1.grid(True, alpha=0.3)
                
                # Chart 2: FPS Timeline
                self.ax2.plot(times, fps_vals, color='#2ecc71', linewidth=2, marker='s')
                self.ax2.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='Target 30 FPS')
                self.ax2.set_title("Processing FPS", fontsize=12, fontweight='bold')
                self.ax2.set_xlabel("Frame")
                self.ax2.legend()
                self.ax2.grid(True, alpha=0.3)
                
                # Chart 3: Detection distribution
                if self.video_thread and self.video_thread.classes:
                    df = self.db.read_all()
                    if not df.empty:
                        class_counts = df['class_name'].value_counts().head(10)
                        self.ax3.barh(list(class_counts.index), list(class_counts.values), color='#e74c3c')
                        self.ax3.set_title("Top 10 Detected Classes", fontsize=12, fontweight='bold')
                        self.ax3.set_xlabel("Count")
                        self.ax3.grid(True, alpha=0.3, axis='x')
                
                # Chart 4: Confidence distribution
                if self.video_thread and self.video_thread.confs:
                    self.ax4.hist(self.video_thread.confs, bins=20, color='#9b59b6', alpha=0.7, edgecolor='black')
                    self.ax4.set_title("Confidence Score Distribution", fontsize=12, fontweight='bold')
                    self.ax4.set_xlabel("Confidence")
                    self.ax4.set_ylabel("Frequency")
                    self.ax4.grid(True, alpha=0.3, axis='y')
            
            self.fig.tight_layout()
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Chart error: {e}")
        
        self.root.after(2000, self._update_charts)
    
    def _export_csv(self):
        f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f:
            try:
                count = self.db.export_csv(f)
                self.export_status.configure(text=f"✅ Exported {count} records to {f}")
                messagebox.showinfo("Success", f"Exported {count} records to CSV")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {e}")
    
    def _export_pdf(self):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            
            f = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not f:
                return
            
            doc = SimpleDocTemplate(f, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph("AI Detection Report", styles['Heading1']))
            elements.append(Spacer(1, 12))
            
            df = self.db.read_all()
            if not df.empty:
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Detections', str(len(df))],
                    ['Unique Classes', str(df['class_name'].nunique())],
                    ['Avg Confidence', f"{df['confidence'].mean():.2f}"],
                    ['Date Range', f"{df['date'].min()} to {df['date'].max()}"]
                ]
                table = Table(summary_data)
                elements.append(table)
            
            doc.build(elements)
            self.export_status.configure(text=f"✅ PDF exported to {f}")
            messagebox.showinfo("Success", "PDF exported successfully")
        except Exception as e:
            messagebox.showerror("Error", f"PDF export failed: {e}")
    
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
    print("AI Detection System v4.0")
    print("="*50)
    GUI().run()
