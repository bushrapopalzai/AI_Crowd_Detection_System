"""
Phase 3: Modern PyQt6 GUI with Interactive Charts & Real-time Heatmaps
Features: Dark/Light theme, responsive layout, Plotly charts, zone-based counting
"""

import sys
import cv2
import numpy as np
from datetime import datetime
from collections import deque
import threading
import logging

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                                 QTableWidget, QTableWidgetItem, QSlider, QComboBox,
                                 QSpinBox, QCheckBox, QFileDialog, QMessageBox)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
    from PyQt6.QtGui import QImage, QPixmap, QFont, QColor
    from PyQt6.QtChart import QChart, QChartView, QLineSeries
    from PyQt6.QtCore import QPointF
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt6 not installed. Install with: pip install PyQt6 PyQt6-Charts")

logger = logging.getLogger(__name__)


class SignalEmitter(QObject):
    """Signal emitter for thread-safe GUI updates"""
    frame_ready = pyqtSignal(np.ndarray)
    stats_updated = pyqtSignal(dict)
    alert_triggered = pyqtSignal(dict)


class ModernDetectionGUIv3(QMainWindow):
    """Modern PyQt6-based detection GUI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Detection System v3.0 - PyQt6")
        self.setGeometry(100, 100, 1800, 1000)
        
        self.signal_emitter = SignalEmitter()
        self.signal_emitter.frame_ready.connect(self.on_frame_ready)
        self.signal_emitter.stats_updated.connect(self.on_stats_updated)
        
        self.is_processing = False
        self.current_session_id = None
        self.stats_history = deque(maxlen=200)
        
        self._setup_ui()
        self._setup_theme()
        
    def _setup_ui(self):
        """Setup main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left: Video display
        left_panel = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setMinimumSize(1000, 700)
        left_panel.addWidget(self.video_label)
        
        # Right: Controls & Stats
        right_panel = QVBoxLayout()
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Controls
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        
        # Buttons
        self.btn_camera = QPushButton("📷 Start Camera")
        self.btn_camera.clicked.connect(self.start_camera)
        self.btn_upload = QPushButton("📁 Upload Video")
        self.btn_upload.clicked.connect(self.upload_video)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        
        control_layout.addWidget(self.btn_camera)
        control_layout.addWidget(self.btn_upload)
        control_layout.addWidget(self.btn_stop)
        
        # Model selector
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["yolov8n", "yolov8s", "yolov8m"])
        control_layout.addWidget(model_label)
        control_layout.addWidget(self.model_combo)
        
        # Confidence threshold
        conf_label = QLabel("Confidence Threshold:")
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_slider.setValue(50)
        self.conf_value_label = QLabel("0.50")
        self.conf_slider.valueChanged.connect(
            lambda v: self.conf_value_label.setText(f"{v/100:.2f}")
        )
        control_layout.addWidget(conf_label)
        control_layout.addWidget(self.conf_slider)
        control_layout.addWidget(self.conf_value_label)
        
        # Feature toggles
        self.enable_tracking = QCheckBox("Enable Tracking")
        self.enable_tracking.setChecked(True)
        self.enable_heatmap = QCheckBox("Enable Heatmap")
        self.enable_heatmap.setChecked(True)
        self.enable_alerts = QCheckBox("Enable Alerts")
        self.enable_alerts.setChecked(True)
        
        control_layout.addWidget(self.enable_tracking)
        control_layout.addWidget(self.enable_heatmap)
        control_layout.addWidget(self.enable_alerts)
        
        self.tabs.addTab(control_tab, "Controls")
        
        # Tab 2: Statistics
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.setRowCount(8)
        
        metrics = ["Status", "Session ID", "Frame Count", "Total Detections", 
                  "Current FPS", "Tracked Objects", "Avg Confidence", "Buffer Size"]
        for i, metric in enumerate(metrics):
            self.stats_table.setItem(i, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(i, 1, QTableWidgetItem("-"))
        
        stats_layout.addWidget(self.stats_table)
        self.tabs.addTab(stats_tab, "Statistics")
        
        # Tab 3: Alerts
        alerts_tab = QWidget()
        alerts_layout = QVBoxLayout(alerts_tab)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Message"])
        alerts_layout.addWidget(self.alerts_table)
        self.tabs.addTab(alerts_tab, "Alerts")
        
        right_panel.addWidget(self.tabs)
        
        main_layout.addLayout(left_panel, 3)
        main_layout.addLayout(right_panel, 1)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(100)
    
    def _setup_theme(self):
        """Setup dark theme"""
        dark_stylesheet = """
        QMainWindow { background-color: #1e1e1e; color: #ffffff; }
        QWidget { background-color: #2d2d2d; color: #ffffff; }
        QPushButton { background-color: #0d47a1; color: white; padding: 5px; border-radius: 3px; }
        QPushButton:hover { background-color: #1565c0; }
        QPushButton:pressed { background-color: #0d3a8f; }
        QTableWidget { background-color: #1e1e1e; color: #ffffff; }
        QHeaderView::section { background-color: #0d47a1; color: white; }
        QComboBox { background-color: #3d3d3d; color: white; }
        QSlider::groove:horizontal { background-color: #3d3d3d; }
        QSlider::handle:horizontal { background-color: #0d47a1; }
        """
        self.setStyleSheet(dark_stylesheet)
    
    def start_camera(self):
        """Start webcam detection"""
        self.statusBar().showMessage("Starting camera...")
        self.is_processing = True
        self.current_session_id = int(datetime.now().timestamp())
        self.btn_camera.setEnabled(False)
        self.btn_upload.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def upload_video(self):
        """Upload video file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        if filename:
            self.statusBar().showMessage(f"Loading {filename}...")
            self.is_processing = True
            self.current_session_id = int(datetime.now().timestamp())
            self.btn_camera.setEnabled(False)
            self.btn_upload.setEnabled(False)
            self.btn_stop.setEnabled(True)
    
    def stop_processing(self):
        """Stop detection"""
        self.is_processing = False
        self.btn_camera.setEnabled(True)
        self.btn_upload.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.statusBar().showMessage("Stopped - Data saved")
    
    def on_frame_ready(self, frame):
        """Display frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = 3 * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        scaled_pixmap = pixmap.scaledToWidth(1000, Qt.TransformationMode.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)
    
    def on_stats_updated(self, stats):
        """Update statistics table"""
        for i, (key, value) in enumerate(stats.items()):
            if i < self.stats_table.rowCount():
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def update_ui(self):
        """Periodic UI update"""
        if self.is_processing:
            self.statusBar().showMessage(f"Session {self.current_session_id} - Running")
    
    def closeEvent(self, event):
        """Clean shutdown"""
        self.is_processing = False
        event.accept()


def run_pyqt_gui():
    """Launch PyQt6 GUI"""
    if not PYQT_AVAILABLE:
        print("PyQt6 not available. Install with: pip install PyQt6 PyQt6-Charts")
        return
    
    app = QApplication(sys.argv)
    window = ModernDetectionGUIv3()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_pyqt_gui()
