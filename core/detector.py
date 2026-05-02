"""YOLOv8 detection engine — loaded once, shared across threads."""

import logging
import numpy as np
import cv2
from config import get

logger = logging.getLogger(__name__)

_MODEL_INSTANCE = None


def get_model() -> "DetectionModel":
    """Return the singleton model, loading it on first call."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = DetectionModel()
    return _MODEL_INSTANCE


class DetectionModel:
    def __init__(self):
        model_name: str = get("detection", "model", "yolov8s.pt")
        self.model_name = model_name
        self.conf: float = get("detection", "confidence_threshold", 0.5)
        self.iou: float = get("detection", "iou_threshold", 0.45)
        self.model = None
        self.classes: dict = {}
        self._colors: dict = {}
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        try:
            from ultralytics import YOLO
            logger.info("Loading model: %s", self.model_name)
            self.model = YOLO(self.model_name)
            self.classes = self.model.names
            rng = np.random.default_rng(42)
            self._colors = {
                name: tuple(int(c) for c in rng.integers(60, 230, 3))
                for name in self.classes.values()
            }
            logger.info("Model ready — %d classes", len(self.classes))
        except ImportError:
            logger.error("ultralytics not installed. Run: pip install ultralytics")
            raise
        except Exception:
            logger.exception("Failed to load model %s", self.model_name)
            raise

    # ------------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict]]:
        """Run inference and draw boxes. Returns (annotated_frame, detections)."""
        if self.model is None:
            return frame, []
        try:
            results = self.model(frame, conf=self.conf, iou=self.iou, verbose=False)
            dets: list[dict] = []
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.classes[cls_id]
                dets.append({"class": cls_name, "confidence": conf, "bbox": (x1, y1, x2, y2)})

            annotated = frame.copy()
            for det in dets:
                x1, y1, x2, y2 = det["bbox"]
                color = self._colors.get(det["class"], (0, 255, 0))
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                label = f"{det['class']} {det['confidence']:.2f}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                cv2.rectangle(annotated, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
                cv2.putText(annotated, label, (x1 + 2, y1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            return annotated, dets
        except Exception:
            logger.exception("Detection error")
            return frame, []
