"""SQLite persistence service — async-buffered writes, thread-safe."""

import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import get

logger = logging.getLogger(__name__)


class SQLiteDB:
    def __init__(self):
        self.db_path: str = get("database", "path", "detection_records.db")
        self._buffer_size: int = get("database", "buffer_size", 50)
        self._flush_interval: float = get("database", "flush_interval", 5)
        self._lock = threading.Lock()
        self._buffer: list = []
        self._last_flush = time.monotonic()
        self._init_schema()
        threading.Thread(target=self._bg_flush, daemon=True, name="DB-Flush").start()

    # ------------------------------------------------------------------
    def _init_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS detections (
                    id          INTEGER PRIMARY KEY,
                    timestamp   TEXT NOT NULL,
                    date        TEXT NOT NULL,
                    time        TEXT NOT NULL,
                    session_id  INTEGER NOT NULL,
                    frame_number INTEGER,
                    class_name  TEXT,
                    confidence  REAL,
                    bbox_x1     INTEGER, bbox_y1 INTEGER,
                    bbox_x2     INTEGER, bbox_y2 INTEGER,
                    fps         REAL,
                    source_type TEXT,
                    source_path TEXT
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id       INTEGER PRIMARY KEY,
                    start_time       TEXT,
                    end_time         TEXT,
                    date             TEXT,
                    source_type      TEXT,
                    source_path      TEXT,
                    total_frames     INTEGER,
                    total_detections INTEGER,
                    unique_classes   INTEGER,
                    avg_confidence   REAL,
                    duration_seconds REAL,
                    status           TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_det_date    ON detections(date);
                CREATE INDEX IF NOT EXISTS idx_det_session ON detections(session_id);
            """)

    # ------------------------------------------------------------------
    def _bg_flush(self) -> None:
        while True:
            time.sleep(1)
            elapsed = time.monotonic() - self._last_flush
            if len(self._buffer) >= self._buffer_size or (elapsed >= self._flush_interval and self._buffer):
                self.flush()

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            batch, self._buffer = self._buffer[:], []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    """INSERT INTO detections
                       (timestamp, date, time, session_id, frame_number,
                        class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                        fps, source_type, source_path)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    batch,
                )
            self._last_flush = time.monotonic()
        except sqlite3.Error:
            logger.exception("DB flush error — re-queuing %d rows", len(batch))
            with self._lock:
                self._buffer = batch + self._buffer

    # ------------------------------------------------------------------
    def insert(self, session_id: int, frame_num: int, det: dict,
               fps: float, src_type: str, src_path: str) -> None:
        now = datetime.now(tz=timezone.utc)
        row = (
            now.isoformat(), now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
            session_id, frame_num,
            det["class"], round(det["confidence"], 4),
            det["bbox"][0], det["bbox"][1], det["bbox"][2], det["bbox"][3],
            round(fps, 2), src_type, src_path,
        )
        with self._lock:
            self._buffer.append(row)
        if len(self._buffer) >= self._buffer_size:
            threading.Thread(target=self.flush, daemon=True).start()

    # ------------------------------------------------------------------
    def end_session(self, sid: int, frames: int, dets: int,
                    classes: int, avg_conf: float) -> None:
        self.flush()
        now = datetime.now(tz=timezone.utc).isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT date, source_type, source_path, MIN(timestamp) "
                    "FROM detections WHERE session_id=? LIMIT 1", (sid,)
                ).fetchone()
                date, src_type, src_path, start_time = row if row else ("", "", "", now)
                conn.execute(
                    """INSERT OR REPLACE INTO sessions
                       (session_id, start_time, end_time, date, source_type, source_path,
                        total_frames, total_detections, unique_classes, avg_confidence,
                        duration_seconds, status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid, start_time, now, date, src_type, src_path,
                     frames, dets, classes, round(avg_conf, 4), 0, "COMPLETED"),
                )
        except sqlite3.Error:
            logger.exception("Failed to write session %d", sid)

    # ------------------------------------------------------------------
    def read_all(self) -> pd.DataFrame:
        self.flush()
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query("SELECT * FROM detections", conn)
        except Exception:
            logger.exception("read_all failed")
            return pd.DataFrame()

    def export_csv(self, filepath: str) -> int:
        df = self.read_all()
        df.to_csv(filepath, index=False)
        return len(df)
