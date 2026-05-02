"""Multi-camera stream manager."""

import logging
import queue
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MultiCameraManager:
    def __init__(self, max_cameras: int = 4):
        self.max_cameras = max_cameras
        self._cameras: dict = {}
        self._buffers: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()

    def add_camera(self, camera_id: str, source: str, source_type: str = "rtsp") -> str:
        with self._lock:
            if len(self._cameras) >= self.max_cameras:
                raise ValueError(f"Max {self.max_cameras} cameras already connected")
            self._cameras[camera_id] = {
                "source": source,
                "type": source_type,
                "status": "CONNECTING",
                "frame_count": 0,
                "detections": 0,
                "fps": 0.0,
                "connected_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            self._buffers[camera_id] = queue.Queue(maxsize=5)
        logger.info("Camera added: %s → %s", camera_id, source)
        return camera_id

    def remove_camera(self, camera_id: str) -> None:
        with self._lock:
            self._cameras.pop(camera_id, None)
            self._buffers.pop(camera_id, None)
        logger.info("Camera removed: %s", camera_id)

    def get_camera_list(self) -> dict:
        with self._lock:
            return {
                cid: {k: v for k, v in cam.items() if k != "source"}
                for cid, cam in self._cameras.items()
            }

    def put_frame(self, camera_id: str, frame) -> None:
        buf = self._buffers.get(camera_id)
        if buf:
            try:
                buf.put_nowait(frame)
            except queue.Full:
                pass
