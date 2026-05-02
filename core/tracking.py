"""Object tracking and heatmap generation."""

import logging
import threading
from collections import deque
from datetime import datetime, timezone

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ByteTracker:
    """Lightweight centroid-based tracker."""

    def __init__(self, max_age: int = 30, min_hits: int = 3, dist_thresh: float = 60.0):
        self.max_age = max_age
        self.min_hits = min_hits
        self.dist_thresh = dist_thresh
        self.tracks: dict = {}
        self.next_id = 0

    def update(self, detections: list[dict]) -> dict:
        if not detections:
            for t in self.tracks.values():
                t["age"] += 1
            self._prune()
            return self._active()

        centroids = np.array(
            [[(d["bbox"][0] + d["bbox"][2]) / 2, (d["bbox"][1] + d["bbox"][3]) / 2]
             for d in detections],
            dtype=np.float32,
        )
        matched: set[int] = set()

        for track in self.tracks.values():
            dists = np.linalg.norm(centroids - track["centroid"], axis=1)
            idx = int(np.argmin(dists))
            if dists[idx] < self.dist_thresh:
                track.update({
                    "centroid": centroids[idx],
                    "bbox": detections[idx]["bbox"],
                    "class": detections[idx]["class"],
                    "confidence": detections[idx]["confidence"],
                    "hits": track["hits"] + 1,
                    "age": 0,
                })
                track["trail"].append(tuple(centroids[idx].tolist()))
                matched.add(idx)
            else:
                track["age"] += 1

        for idx, det in enumerate(detections):
            if idx not in matched:
                cx = (det["bbox"][0] + det["bbox"][2]) / 2
                cy = (det["bbox"][1] + det["bbox"][3]) / 2
                self.tracks[self.next_id] = {
                    "id": self.next_id,
                    "centroid": np.array([cx, cy], dtype=np.float32),
                    "bbox": det["bbox"],
                    "class": det["class"],
                    "confidence": det["confidence"],
                    "hits": 1,
                    "age": 0,
                    "trail": deque(maxlen=30),
                }
                self.next_id += 1

        self._prune()
        return self._active()

    def _prune(self) -> None:
        dead = [tid for tid, t in self.tracks.items() if t["age"] > self.max_age]
        for tid in dead:
            del self.tracks[tid]

    def _active(self) -> dict:
        return {tid: t for tid, t in self.tracks.items() if t["hits"] >= self.min_hits}


class HeatmapGenerator:
    """Vectorised Gaussian heatmap — replaces the O(n²) pixel loop."""

    def __init__(self, frame_shape: tuple, kernel_size: int = 50):
        self.h, self.w = frame_shape[:2]
        self.sigma = kernel_size / 3.0
        self.heatmap = np.zeros((self.h, self.w), dtype=np.float32)

        # Pre-build coordinate grids once
        xs = np.arange(self.w, dtype=np.float32)
        ys = np.arange(self.h, dtype=np.float32)
        self._xx, self._yy = np.meshgrid(xs, ys)

    def update(self, detections: list[dict]) -> np.ndarray:
        self.heatmap *= 0.95
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            g = np.exp(-((self._xx - cx) ** 2 + (self._yy - cy) ** 2) / (2 * self.sigma ** 2))
            self.heatmap += g.astype(np.float32)
        return self.heatmap

    def render(self, frame: np.ndarray) -> np.ndarray:
        norm = cv2.normalize(self.heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        colored = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 0.7, colored, 0.3, 0)


class AlertSystem:
    """Thread-safe alert bus."""

    def __init__(self, maxlen: int = 100):
        self._alerts: deque = deque(maxlen=maxlen)
        self._callbacks: list = []
        self._lock = threading.Lock()

    def register_callback(self, cb) -> None:
        self._callbacks.append(cb)

    def trigger(self, alert_type: str, message: str, severity: str = "INFO", data=None) -> None:
        alert = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "type": alert_type,
            "message": message,
            "severity": severity,
            "data": data,
        }
        with self._lock:
            self._alerts.append(alert)
        for cb in self._callbacks:
            try:
                cb(alert)
            except Exception:
                logger.exception("Alert callback error")

    def recent(self, n: int = 10) -> list:
        with self._lock:
            return list(self._alerts)[-n:]
