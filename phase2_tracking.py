"""
Phase 2: Object Tracking, Heatmaps, Crowd Density & Alerts
Features: ByteTrack, heatmap overlay, density estimation, alert system
"""

import cv2
import numpy as np
from collections import defaultdict, deque
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class ByteTracker:
    """Lightweight object tracker using centroid tracking"""
    
    def __init__(self, max_age=30, min_hits=3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.tracks = {}
        self.next_id = 0
        self.frame_count = 0
        
    def update(self, detections):
        """Update tracks with new detections"""
        self.frame_count += 1
        matched_tracks = set()
        
        # Calculate centroids from detections
        centroids = np.array([
            [(d['bbox'][0] + d['bbox'][2]) / 2, (d['bbox'][1] + d['bbox'][3]) / 2]
            for d in detections
        ])
        
        # Match detections to existing tracks
        for track_id, track in list(self.tracks.items()):
            if len(centroids) == 0:
                track['age'] += 1
                continue
            
            # Find closest detection
            distances = np.linalg.norm(centroids - track['centroid'], axis=1)
            closest_idx = np.argmin(distances)
            
            if distances[closest_idx] < 50:  # Distance threshold
                track['centroid'] = centroids[closest_idx]
                track['bbox'] = detections[closest_idx]['bbox']
                track['class'] = detections[closest_idx]['class']
                track['confidence'] = detections[closest_idx]['confidence']
                track['hits'] += 1
                track['age'] = 0
                matched_tracks.add(closest_idx)
                track['trail'].append(tuple(track['centroid']))
        
        # Create new tracks for unmatched detections
        for idx, det in enumerate(detections):
            if idx not in matched_tracks:
                centroid = [(det['bbox'][0] + det['bbox'][2]) / 2, 
                           (det['bbox'][1] + det['bbox'][3]) / 2]
                self.tracks[self.next_id] = {
                    'id': self.next_id,
                    'centroid': np.array(centroid),
                    'bbox': det['bbox'],
                    'class': det['class'],
                    'confidence': det['confidence'],
                    'hits': 1,
                    'age': 0,
                    'trail': deque(maxlen=30)
                }
                self.next_id += 1
        
        # Remove old tracks
        for track_id in list(self.tracks.keys()):
            if self.tracks[track_id]['age'] > self.max_age:
                del self.tracks[track_id]
        
        # Return confirmed tracks
        return {
            tid: t for tid, t in self.tracks.items() 
            if t['hits'] >= self.min_hits
        }


class HeatmapGenerator:
    """Generate crowd density heatmaps"""
    
    def __init__(self, frame_shape, kernel_size=50):
        self.h, self.w = frame_shape[:2]
        self.kernel_size = kernel_size
        self.heatmap = np.zeros((self.h, self.w), dtype=np.float32)
        
    def update(self, detections):
        """Update heatmap with detection centroids"""
        self.heatmap *= 0.95  # Decay
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            # Add Gaussian blob
            y_min = max(0, cy - self.kernel_size)
            y_max = min(self.h, cy + self.kernel_size)
            x_min = max(0, cx - self.kernel_size)
            x_max = min(self.w, cx + self.kernel_size)
            
            for y in range(y_min, y_max):
                for x in range(x_min, x_max):
                    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                    self.heatmap[y, x] += np.exp(-(dist**2) / (2 * self.kernel_size**2))
        
        return self.heatmap
    
    def render(self, frame):
        """Overlay heatmap on frame"""
        heatmap_norm = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
        
        return cv2.addWeighted(frame, 0.7, heatmap_color, 0.3, 0)


class CrowdDensityAnalyzer:
    """Analyze crowd density and detect anomalies"""
    
    def __init__(self, grid_size=10):
        self.grid_size = grid_size
        self.density_history = deque(maxlen=100)
        
    def calculate_density(self, detections, frame_shape):
        """Calculate people per grid cell"""
        h, w = frame_shape[:2]
        cell_h, cell_w = h // self.grid_size, w // self.grid_size
        
        grid = defaultdict(int)
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            grid_x = min(cx // cell_w, self.grid_size - 1)
            grid_y = min(cy // cell_h, self.grid_size - 1)
            grid[(grid_y, grid_x)] += 1
        
        self.density_history.append(grid)
        return grid
    
    def detect_anomaly(self, current_density, threshold=5):
        """Detect sudden crowd changes"""
        if len(self.density_history) < 2:
            return False
        
        prev_density = self.density_history[-2]
        max_current = max(current_density.values()) if current_density else 0
        max_prev = max(prev_density.values()) if prev_density else 0
        
        # Detect sudden spike
        if max_current > threshold and max_current > max_prev * 1.5:
            return True
        return False


class AlertSystem:
    """Real-time alert management"""
    
    def __init__(self):
        self.alerts = deque(maxlen=100)
        self.alert_callbacks = []
        self.lock = threading.Lock()
        
    def register_callback(self, callback):
        """Register alert callback"""
        self.alert_callbacks.append(callback)
    
    def trigger_alert(self, alert_type, message, severity="INFO", data=None):
        """Trigger an alert"""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'severity': severity,
            'data': data
        }
        
        with self.lock:
            self.alerts.append(alert)
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def get_recent_alerts(self, count=10):
        """Get recent alerts"""
        with self.lock:
            return list(self.alerts)[-count:]


class TrackingVisualizer:
    """Visualize tracks and trajectories"""
    
    @staticmethod
    def draw_tracks(frame, tracks, draw_trails=True):
        """Draw tracked objects with IDs and trails"""
        for track_id, track in tracks.items():
            x1, y1, x2, y2 = track['bbox']
            
            # Draw bounding box
            color = (0, 255, 0) if track['hits'] >= 3 else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw ID
            label = f"ID:{track_id} {track['class']}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw trail
            if draw_trails and len(track['trail']) > 1:
                trail = list(track['trail'])
                for i in range(len(trail) - 1):
                    cv2.line(frame, tuple(map(int, trail[i])), 
                            tuple(map(int, trail[i+1])), (255, 0, 0), 1)
        
        return frame
    
    @staticmethod
    def draw_density_grid(frame, density, grid_size=10):
        """Draw density grid overlay"""
        h, w = frame.shape[:2]
        cell_h, cell_w = h // grid_size, w // grid_size
        
        max_density = max(density.values()) if density else 1
        
        for (gy, gx), count in density.items():
            x1 = gx * cell_w
            y1 = gy * cell_h
            x2 = x1 + cell_w
            y2 = y1 + cell_h
            
            # Color intensity based on density
            intensity = int(255 * (count / max_density))
            color = (0, 255 - intensity, intensity)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
            cv2.putText(frame, str(count), (x1 + 5, y1 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame


class AdvancedVideoProcessor(threading.Thread):
    """Enhanced video processor with tracking and heatmaps"""
    
    def __init__(self, model, buffer, stop_event, db, session_id, 
                 source_type, source_path, enable_tracking=True, 
                 enable_heatmap=True, enable_alerts=True):
        super().__init__(daemon=True)
        self.model = model
        self.buffer = buffer
        self.stop_event = stop_event
        self.db = db
        self.session_id = session_id
        self.source_type = source_type
        self.source_path = source_path
        
        self.tracker = ByteTracker() if enable_tracking else None
        self.heatmap_gen = None
        self.density_analyzer = CrowdDensityAnalyzer() if enable_heatmap else None
        self.alert_system = AlertSystem() if enable_alerts else None
        
        self.cap = None
        self.frame_count = 0
        self.total_detections = 0
        self.all_confidences = []
        self.unique_classes = set()
        
    def run(self):
        self.cap = cv2.VideoCapture(self.source_path)
        if not self.cap.isOpened():
            logger.error("Failed to open video source")
            self.stop_event.set()
            return
        
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        frame_shape = None
        
        import time
        prev_time = time.time()
        
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                break
            
            if frame_shape is None:
                frame_shape = frame.shape
                if self.density_analyzer:
                    self.heatmap_gen = HeatmapGenerator(frame_shape)
            
            current_time = time.time()
            actual_fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0
            prev_time = current_time
            
            self.frame_count += 1
            
            # Detection
            annotated_frame, detections = self.model.detect(frame)
            
            # Tracking
            if self.tracker:
                tracks = self.tracker.update(detections)
                annotated_frame = TrackingVisualizer.draw_tracks(annotated_frame, tracks)
            
            # Heatmap
            if self.heatmap_gen:
                self.heatmap_gen.update(detections)
                annotated_frame = self.heatmap_gen.render(annotated_frame)
            
            # Density analysis
            if self.density_analyzer:
                density = self.density_analyzer.calculate_density(detections, frame_shape)
                if self.density_analyzer.detect_anomaly(density):
                    if self.alert_system:
                        self.alert_system.trigger_alert(
                            "CROWD_ANOMALY",
                            f"Sudden crowd increase detected",
                            "WARNING"
                        )
                annotated_frame = TrackingVisualizer.draw_density_grid(annotated_frame, density)
            
            # Stats
            self.total_detections += len(detections)
            for det in detections:
                self.all_confidences.append(det['confidence'])
                self.unique_classes.add(det['class'])
                self.db.insert_detection(
                    self.session_id, self.frame_count, det, actual_fps,
                    self.source_type, str(self.source_path)
                )
            
            # FPS overlay
            cv2.putText(annotated_frame, f"FPS: {actual_fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Tracked: {len(self.tracker.tracks) if self.tracker else 0}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            self.buffer.put(annotated_frame, detections, actual_fps)
        
        self._cleanup()
    
    def _cleanup(self):
        if self.cap:
            self.cap.release()
        
        avg_conf = sum(self.all_confidences) / len(self.all_confidences) if self.all_confidences else 0
        self.db.end_session(
            self.session_id, self.frame_count, self.total_detections,
            len(self.unique_classes), avg_conf
        )
        logger.info(f"Session {self.session_id} completed with tracking")
