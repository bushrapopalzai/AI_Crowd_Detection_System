"""Tracking, Heatmaps, and Alert System"""

import cv2, numpy as np, threading, logging
from collections import defaultdict, deque
from datetime import datetime

logger = logging.getLogger(__name__)


class ByteTracker:
    """Lightweight object tracker"""
    
    def __init__(self, max_age=30, min_hits=3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.tracks = {}
        self.next_id = 0
        self.frame_count = 0
    
    def update(self, detections):
        self.frame_count += 1
        matched_tracks = set()
        
        centroids = np.array([
            [(d['bbox'][0] + d['bbox'][2]) / 2, (d['bbox'][1] + d['bbox'][3]) / 2]
            for d in detections
        ]) if detections else np.array([])
        
        for track_id, track in list(self.tracks.items()):
            if len(centroids) == 0:
                track['age'] += 1
                continue
            
            distances = np.linalg.norm(centroids - track['centroid'], axis=1)
            closest_idx = np.argmin(distances)
            
            if distances[closest_idx] < 50:
                track['centroid'] = centroids[closest_idx]
                track['bbox'] = detections[closest_idx]['bbox']
                track['class'] = detections[closest_idx]['class']
                track['confidence'] = detections[closest_idx]['confidence']
                track['hits'] += 1
                track['age'] = 0
                matched_tracks.add(closest_idx)
                track['trail'].append(tuple(track['centroid']))
        
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
        
        for track_id in list(self.tracks.keys()):
            if self.tracks[track_id]['age'] > self.max_age:
                del self.tracks[track_id]
        
        return {tid: t for tid, t in self.tracks.items() if t['hits'] >= self.min_hits}


class HeatmapGenerator:
    """Generate crowd density heatmaps"""
    
    def __init__(self, frame_shape, kernel_size=50):
        self.h, self.w = frame_shape[:2]
        self.kernel_size = kernel_size
        self.heatmap = np.zeros((self.h, self.w), dtype=np.float32)
    
    def update(self, detections):
        self.heatmap *= 0.95
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
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
        heatmap_norm = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        heatmap_color = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 0.7, heatmap_color, 0.3, 0)


class AlertSystem:
    """Real-time alert management"""
    
    def __init__(self):
        self.alerts = deque(maxlen=100)
        self.alert_callbacks = []
        self.lock = threading.Lock()
    
    def register_callback(self, callback):
        self.alert_callbacks.append(callback)
    
    def trigger_alert(self, alert_type, message, severity="INFO", data=None):
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'severity': severity,
            'data': data
        }
        
        with self.lock:
            self.alerts.append(alert)
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def get_recent_alerts(self, count=10):
        with self.lock:
            return list(self.alerts)[-count:]
