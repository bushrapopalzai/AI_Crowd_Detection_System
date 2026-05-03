"""YOLOv8 detection engine — loaded once, shared across threads."""

import logging
from typing import Tuple, List, Dict, Optional
import numpy as np
import cv2
from config import get

logger = logging.getLogger(__name__)

_MODEL_INSTANCE = None
_LOAD_ERROR = None

# COCO class IDs for crowd detection
PERSON_CLASS_ID = 0
CROWD_CLASSES = {0}  # person


def get_model() -> "DetectionModel":
    """Return the singleton model, loading it on first call."""
    global _MODEL_INSTANCE, _LOAD_ERROR
    if _MODEL_INSTANCE is None and _LOAD_ERROR is None:
        try:
            _MODEL_INSTANCE = DetectionModel()
        except Exception as e:
            _LOAD_ERROR = e
            logger.error("Model load failed: %s", e)
            raise
    if _LOAD_ERROR:
        raise _LOAD_ERROR
    return _MODEL_INSTANCE


class DetectionModel:
    def __init__(self):
        model_name: str = get("detection", "model", "yolov8s.pt")
        self.model_name = model_name
        self.conf: float = get("detection", "confidence_threshold", 0.35)  # Lowered for better crowd detection
        self.iou: float = get("detection", "iou_threshold", 0.45)
        self.model: Optional[object] = None
        self.classes: Dict = {}
        self._colors: Dict = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        try:
            import sys
            # Prevent transformers from being imported by ultralytics
            sys.modules['transformers'] = None
            
            from ultralytics import YOLO
            logger.info("Loading model: %s", self.model_name)
            self.model = YOLO(self.model_name)
            self.classes = self.model.names
            rng = np.random.default_rng(42)
            self._colors = {
                name: tuple(int(c) for c in rng.integers(60, 230, 3))
                for name in self.classes.values()
            }
            logger.info("Model ready -- %d classes", len(self.classes))
        except ImportError as e:
            logger.error("ultralytics not installed. Run: pip install ultralytics")
            raise
        except Exception as e:
            logger.error("Failed to load model %s: %s", self.model_name, e)
            logger.warning("Continuing without model -- detection will be disabled")
            self.model = None

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """Run inference and draw boxes. Returns (annotated_frame, detections)."""
        if self.model is None:
            return frame, []
        try:
            results = self.model(frame, conf=self.conf, iou=self.iou, verbose=False)
            dets: List[Dict] = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.classes[cls_id]
                dets.append({"class": cls_name, "confidence": conf, "bbox": (x1, y1, x2, y2), "cls_id": cls_id})

            annotated = frame.copy()
            person_count = sum(1 for d in dets if d["cls_id"] == PERSON_CLASS_ID)
            
            for det in dets:
                x1, y1, x2, y2 = det["bbox"]
                color = self._colors.get(det["class"], (0, 255, 0))
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"{det['class']} {det['confidence']:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            
            # Draw crowd count overlay
            h, w = frame.shape[:2]
            cv2.rectangle(annotated, (10, 10), (250, 60), (0, 0, 0), -1)
            cv2.putText(annotated, f"People: {person_count}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
            
            return annotated, dets
        except Exception:
            logger.exception("Detection error")
            return frame, []
