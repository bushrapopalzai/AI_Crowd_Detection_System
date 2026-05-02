"""FastAPI REST + WebSocket server."""

import asyncio
import logging
import threading
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get

logger = logging.getLogger(__name__)


# ── Pydantic schemas ──────────────────────────────────────────────────
class CameraAddRequest(BaseModel):
    camera_id: str
    source: str
    source_type: str = "rtsp"


# ── Server ────────────────────────────────────────────────────────────
class APIServer:
    def __init__(self, camera_manager, model, db):
        self.camera_manager = camera_manager
        self.model = model
        self.db = db
        self.port: int = get("api", "port", 8000)
        self.host: str = get("api", "host", "0.0.0.0")
        self._ws_clients: list[WebSocket] = []
        self.app = self._build_app()

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="AI Detection API v4.0", version="4.0.0")

        origins = get("api", "cors_origins", ["*"])
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type"],
        )

        # ── Health ────────────────────────────────────────────────────
        @app.get("/api/health")
        async def health():
            return {"status": "healthy", "ts": datetime.now(tz=timezone.utc).isoformat()}

        # ── Model ─────────────────────────────────────────────────────
        @app.get("/api/model/info")
        async def model_info():
            return {
                "model": self.model.model_name,
                "classes": len(self.model.classes),
                "confidence_threshold": self.model.conf,
            }

        # ── Cameras ───────────────────────────────────────────────────
        @app.get("/api/cameras")
        async def list_cameras():
            return self.camera_manager.get_camera_list()

        @app.post("/api/cameras/add", status_code=201)
        async def add_camera(req: CameraAddRequest):
            try:
                self.camera_manager.add_camera(req.camera_id, req.source, req.source_type)
                return {"status": "created", "camera_id": req.camera_id}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.delete("/api/cameras/{camera_id}")
        async def remove_camera(camera_id: str):
            self.camera_manager.remove_camera(camera_id)
            return {"status": "removed", "camera_id": camera_id}

        # ── Detections ────────────────────────────────────────────────
        @app.get("/api/detections/summary")
        async def detection_summary():
            df = await asyncio.get_event_loop().run_in_executor(None, self.db.read_all)
            if df.empty:
                return {"total": 0, "by_class": {}, "avg_confidence": 0.0}
            return {
                "total": len(df),
                "by_class": df["class_name"].value_counts().to_dict(),
                "avg_confidence": round(float(df["confidence"].mean()), 4),
            }

        # ── WebSocket live feed ───────────────────────────────────────
        @app.websocket("/ws/live")
        async def ws_live(ws: WebSocket):
            await ws.accept()
            self._ws_clients.append(ws)
            try:
                while True:
                    await ws.receive_text()  # keep-alive ping
            except WebSocketDisconnect:
                self._ws_clients.remove(ws)

        return app

    async def broadcast(self, data: dict) -> None:
        dead = []
        for ws in self._ws_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._ws_clients.remove(ws)

    def run_in_thread(self) -> threading.Thread:
        def _run():
            uvicorn.run(self.app, host=self.host, port=self.port,
                        log_level="warning", access_log=False)
        t = threading.Thread(target=_run, daemon=True, name="API-Server")
        t.start()
        logger.info("API server started on http://%s:%d", self.host, self.port)
        return t
