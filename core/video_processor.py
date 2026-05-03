"""Video capture + detection thread."""

import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import List, Set

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# COCO class ID for person
PERSON_CLASS_ID = 0


class VideoProcessor(threading.Thread):
    def __init__(self, model, frame_buffer: queue.Queue, stop_event: threading.Event,
                 db, session_id: int, src_type: str, src_path):
        super().__init__(daemon=True, name=f"VideoProc-{session_id}")
        self.model = model
        self.buffer = frame_buffer
        self.stop_event = stop_event
        self.db = db
        self.session_id = session_id
        self.src_type = src_type
        self.src_path = src_path

        self.frame_count = 0
        self.total_dets = 0
        self.confs: List[float] = []
        self.classes: set[str] = set()

    def run(self) -> None:
        cap = cv2.VideoCapture(self.src_path)
        if not cap.isOpened():
            logger.error("Cannot open source: %s", self.src_path)
            self.stop_event.set()
            return

        prev = time.perf_counter()
        try:
            while not self.stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    break

                now = time.perf_counter()
                fps = 1.0 / max(now - prev, 1e-6)
                prev = now
                self.frame_count += 1

                frame, dets = self.model.detect(frame)
                self.total_dets += len(dets)
                
                # Count people for crowd analysis
                person_count = sum(1 for d in dets if d.get("cls_id") == PERSON_CLASS_ID)
                crowd_density = person_count / (frame.shape[0] * frame.shape[1] / 10000) if frame.shape[0] > 0 else 0

                for det in dets:
                    self.confs.append(det["confidence"])
                    self.classes.add(det["class"])
                    self.db.insert(self.session_id, self.frame_count, det,
                                   fps, self.src_type, str(self.src_path))

                # Enhanced overlay with crowd info
                cv2.putText(frame, f"FPS:{fps:.1f}  Det:{len(dets)}  People:{person_count}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 80), 2)

                try:
                    self.buffer.put_nowait((frame, dets, fps, datetime.now(tz=timezone.utc)))
                except queue.Full:
                    pass  # drop stale frame -- intentional
        finally:
            cap.release()
            avg_conf = sum(self.confs) / len(self.confs) if self.confs else 0.0
            self.db.end_session(self.session_id, self.frame_count,
                                self.total_dets, len(self.classes), avg_conf)
            logger.info("Session %d ended -- %d frames, %d detections",
                        self.session_id, self.frame_count, self.total_dets)
