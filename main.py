"""AI Crowd Detection System v4.0 — entry point."""

import sys
import argparse
from pathlib import Path

# Make project root importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

import config.logger as _log_setup
_log_setup.setup()

import logging
logger = logging.getLogger(__name__)


def run_gui() -> None:
    from ui.dashboard import Dashboard
    logger.info("Starting GUI dashboard")
    Dashboard().run()


def run_api() -> None:
    from core import get_model
    from services import SQLiteDB
    from api import APIServer, MultiCameraManager

    db = SQLiteDB()
    model = get_model()
    cam_mgr = MultiCameraManager()
    server = APIServer(cam_mgr, model, db)
    logger.info("Starting API-only mode")
    import uvicorn
    from config import get
    uvicorn.run(server.app, host=get("api", "host", "0.0.0.0"),
                port=get("api", "port", 8000))


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Crowd Detection System v4.0")
    parser.add_argument("--mode", choices=["gui", "api"], default="gui",
                        help="gui (default) or api-only")
    args = parser.parse_args()

    print("=" * 52)
    print("  AI Crowd Detection System v4.0")
    print("=" * 52)

    if args.mode == "api":
        run_api()
    else:
        run_gui()


if __name__ == "__main__":
    main()
