# AI Crowd Detection System v4.0

---

## What Is This?

The **AI Crowd Detection System** is a production-ready, real-time computer vision platform that uses **YOLOv8** to detect, track, and analyse people and objects in live video streams or recorded footage. It combines a modern dark-theme GUI dashboard, a full REST API, persistent SQLite storage, and advanced analytics — all in a clean, layered Python architecture.

Whether you are monitoring a public space, analysing foot traffic in a retail environment, or building a smart-city safety solution, this system gives you the full pipeline out of the box: from raw camera feed to actionable insights.

---

## Aim

To provide an accurate, fast, and extensible AI-powered crowd and object detection platform that can be deployed in real-world environments with minimal setup, offering both a visual dashboard for operators and a programmatic API for integration with other systems.

---

## Objectives

- Detect and classify people and objects in real time using state-of-the-art deep learning (YOLOv8)
- Track individual objects across frames using centroid-based tracking with trail visualisation
- Generate crowd density heatmaps to identify high-traffic zones
- Persist all detection data to a local database for historical analysis and reporting
- Expose all functionality through a REST API and WebSocket stream for third-party integration
- Provide a polished, operator-friendly GUI dashboard with live charts and stat cards
- Support flexible deployment: local Python, Windows one-click launcher, or Docker

---

## Key Benefits

| Benefit | Detail |
|---|---|
| Zero cloud dependency | Runs fully on-premise — no data leaves your network |
| Fast inference | 30+ FPS on CPU, 60+ FPS on GPU with YOLOv8s |
| Plug-and-play | Works with webcam, video file, or RTSP stream |
| Actionable analytics | Daily/weekly reports, peak-hour analysis, 7-day trends |
| Developer-friendly | Full REST API + WebSocket + Swagger UI |
| Operator-friendly | Dark-theme GUI with live charts, no coding required |
| Extensible | Clean layered architecture — swap models, add cameras, extend API |
| Secure | Path-traversal protection, UTC-aware timestamps, proper exception logging |

---

## What It Does — Feature Breakdown

### Real-Time Detection
- Runs YOLOv8n / s / m (configurable) on every frame
- Draws colour-coded bounding boxes with class label and confidence score
- Supports 80+ COCO object classes (person, car, bag, bicycle, etc.)
- Confidence and IoU thresholds tunable via `config/settings.yaml`
- **NEW**: Optimized for crowd detection with lowered confidence threshold (0.35)
- **NEW**: Real-time person counting and crowd density analysis

### Object Tracking
- Centroid-based ByteTracker assigns persistent IDs to detected objects
- Trail visualisation shows movement paths across frames
- Configurable max age, min hits, and distance threshold

### Crowd Density Heatmap
- Vectorised Gaussian heatmap overlay rendered on the live frame
- Decays over time (×0.95 per frame) so density reflects current activity
- ~100× faster than a naive pixel loop thanks to NumPy meshgrid

### Alert System
- Thread-safe alert bus with severity levels (INFO / WARNING / CRITICAL)
- Register custom callbacks to trigger notifications, webhooks, or logging
- Stores last 100 alerts in a rolling deque

### GUI Dashboard
- Built with `customtkinter` (falls back to standard Tkinter)
- 5 live stat cards: Status, FPS, Frames Processed, Detections, Avg Confidence
- 2×2 real-time chart grid: detections timeline, FPS over time, class distribution, confidence histogram
- One-click camera start and video file open
- CSV and PDF export built in

### REST API & WebSocket
- FastAPI with auto-generated Swagger UI at `/docs`
- WebSocket live detection stream at `ws://localhost:8000/ws/live`
- Pydantic v2 validated request bodies
- Async database reads (non-blocking event loop)
- Multi-camera management (add / remove / list cameras at runtime)

### Database & Persistence
- SQLite with async-buffered writes (500+ records/sec)
- Stores every detection: timestamp, class, confidence, bounding box, FPS, source
- Session tracking: start/end time, total frames, total detections, unique classes
- UTC-aware timestamps throughout

### Analytics & Reports
- Daily report: total detections, unique classes, peak hours, class distribution, avg confidence, avg FPS
- Weekly report: 7-day totals, daily averages, top 5 classes, trend analysis
- Peak-hour analysis: ranked by detection volume per hour
- 7-day trend detection: total, daily avg, daily max/min
- JSON export with path-traversal protection

---

## What It Will Become — Upgrade Roadmap

These are the planned enhancements for future versions:

| Version | Planned Feature |
|---|---|
| v4.1 | Re-ID model integration (person re-identification across cameras) |
| v4.1 | Configurable alert thresholds (e.g. trigger when crowd > N people) |
| v4.2 | Web-based dashboard (React/Next.js) replacing the desktop GUI |
| v4.2 | PostgreSQL support alongside SQLite for high-volume deployments |
| v4.3 | YOLOv9 / YOLOv10 model support |
| v4.3 | Anomaly detection (loitering, running, abandoned objects) |
| v5.0 | Cloud deployment templates (AWS ECS, Lambda@Edge for edge inference) |
| v5.0 | Multi-site aggregation dashboard (manage many locations from one UI) |
| v5.0 | Mobile app for remote monitoring and push alerts |

---

## Architecture Overview

```
AI_Crowd_Detection_System/
│
├── core/                        # Detection engine
│   ├── detector.py              # YOLOv8 singleton model — loaded once, shared across threads
│   ├── tracking.py              # ByteTracker, HeatmapGenerator, AlertSystem
│   └── video_processor.py       # Capture + inference thread
│
├── api/                         # REST API layer
│   ├── server.py                # FastAPI app + WebSocket endpoint
│   └── camera_manager.py        # Multi-camera state manager
│
├── ui/                          # GUI layer
│   └── dashboard.py             # Dark-theme dashboard (customtkinter)
│
├── services/                    # Business logic and persistence
│   ├── database.py              # SQLite async-buffered writes
│   └── analytics.py             # Reports, trends, peak-hour stats
│
├── config/                      # Configuration
│   ├── settings.yaml            # Single source of truth for all settings
│   ├── config_manager.py        # Singleton YAML loader
│   └── logger.py                # Rotating file + console logging
│
├── main.py                      # Entry point — python main.py --mode gui|api
├── START.bat                    # Windows one-click launcher
├── requirements.txt             # Pinned dependencies (14 packages)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Layer responsibilities:**

- `core` — pure computer vision, no I/O side effects
- `services` — all database and analytics logic, no GUI or API concerns
- `api` — HTTP/WebSocket interface, delegates to core and services
- `ui` — GUI only, delegates to core and services
- `config` — loaded once at startup, injected everywhere via `get()`

---

## Quick Start

### Prerequisites

- Python 3.10+ — https://www.python.org (tick **Add Python to PATH** during install)
- 4 GB+ RAM recommended
- Webcam or video file (optional — you can test with a local `.mp4`)
- GPU optional — CUDA is auto-detected; CPU works fine for 30 FPS

### Option 1 — Windows one-click

```
Double-click START.bat
Press 1 for GUI dashboard
Press 2 for API-only mode
```

### Option 2 — Command line

```bash
git clone https://github.com/bushrapopalzai/AI_Crowd_Detection_System.git
cd AI_Crowd_Detection_System

pip install -r requirements.txt

# Launch GUI dashboard (default)
python main.py

# Launch API server only
python main.py --mode api
```

### Option 3 — Docker

```bash
docker-compose up -d
# API available at  → http://localhost:8000
# Swagger UI        → http://localhost:8000/docs
```

---

## Usage

### GUI Dashboard

```bash
python main.py
# or explicitly:
python main.py --mode gui
```

1. Click **Start Camera** to begin live webcam detection
2. Click **Open Video** to process a local video file
3. Live stat cards and charts update automatically every 2 seconds
4. Use **Export CSV** or **Export PDF** from the side panel to save session data

### API Server

```bash
python main.py --mode api
# Swagger UI → http://localhost:8000/docs
```

### REST API Examples

```bash
# Health check
curl http://localhost:8000/api/health

# List active cameras
curl http://localhost:8000/api/cameras

# Add a webcam
curl -X POST http://localhost:8000/api/cameras/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"cam0","source":0,"source_type":"camera"}'

# Add an RTSP stream
curl -X POST http://localhost:8000/api/cameras/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"cam1","source":"rtsp://192.168.1.100:554/stream","source_type":"rtsp"}'

# Remove a camera
curl -X DELETE http://localhost:8000/api/cameras/cam1

# Detection summary
curl http://localhost:8000/api/detections/summary

# Model info
curl http://localhost:8000/api/model/info
```

### WebSocket Live Stream

Connect to `ws://localhost:8000/ws/live` to receive a real-time JSON stream of detection events as they happen.

### Generate Reports (Python)

```python
from services import SQLiteDB, AdvancedAnalytics, ReportGenerator

db = SQLiteDB()
analytics = AdvancedAnalytics(db)
reports = ReportGenerator(db, analytics)

# Daily report
daily = reports.generate_daily_report()
reports.export_report_json(daily, "reports/daily.json")

# Weekly report
weekly = reports.generate_weekly_report()
reports.export_report_json(weekly, "reports/weekly.json")

# Peak hours for today
print(analytics.get_peak_hours())

# 7-day trend
print(analytics.detect_trends(days=7))
```

---

## Configuration

All settings live in `config/settings.yaml`. Edit this file to tune the system without touching any code.

```yaml
detection:
  model: "yolov8s.pt"          # yolov8n.pt | yolov8s.pt | yolov8m.pt
  confidence_threshold: 0.35   # Lowered for better crowd detection (was 0.5)
  iou_threshold: 0.45          # overlap threshold for NMS
  device: "auto"               # auto | cpu | cuda | mps

database:
  path: "detection_records.db"
  buffer_size: 50              # records buffered before flush
  flush_interval: 5            # seconds between forced flushes

api:
  host: "0.0.0.0"
  port: 8000

performance:
  max_fps: 30
  frame_buffer_size: 5

ui:
  window_width: 1600
  window_height: 960
  chart_update_ms: 2000        # chart refresh interval in milliseconds

logging:
  level: "INFO"                # DEBUG | INFO | WARNING | ERROR
  file: "detection.log"
  max_bytes: 10485760          # 10 MB per log file
  backup_count: 3              # number of rotated log files to keep
```

---

## Database Schema

### `detections` table

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key (auto-increment) |
| timestamp | TEXT | ISO-8601 UTC timestamp |
| date | TEXT | YYYY-MM-DD |
| time | TEXT | HH:MM:SS |
| session_id | INTEGER | Foreign key → sessions |
| frame_number | INTEGER | Frame index within session |
| class_name | TEXT | Detected object class (e.g. "person") |
| confidence | REAL | Detection confidence score 0–1 |
| bbox_x1 | INTEGER | Bounding box left pixel |
| bbox_y1 | INTEGER | Bounding box top pixel |
| bbox_x2 | INTEGER | Bounding box right pixel |
| bbox_y2 | INTEGER | Bounding box bottom pixel |
| fps | REAL | Processing FPS at time of capture |
| source_type | TEXT | camera / file / rtsp |
| source_path | TEXT | Source identifier or URL |

### `sessions` table

| Column | Type | Description |
|---|---|---|
| session_id | INTEGER | Primary key |
| start_time | TEXT | ISO-8601 UTC session start |
| end_time | TEXT | ISO-8601 UTC session end |
| total_frames | INTEGER | Total frames processed |
| total_detections | INTEGER | Total objects detected |
| unique_classes | INTEGER | Number of distinct classes seen |
| avg_confidence | REAL | Mean confidence across all detections |
| status | TEXT | RUNNING / COMPLETED |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | System health check |
| GET | `/api/model/info` | Model name, class list, thresholds |
| GET | `/api/cameras` | List all active camera streams |
| POST | `/api/cameras/add` | Add a new camera (JSON body) |
| DELETE | `/api/cameras/{id}` | Remove a camera by ID |
| GET | `/api/detections/summary` | Total detections and class breakdown |
| WS | `/ws/live` | Real-time detection event stream |

Full interactive documentation: **http://localhost:8000/docs**

---

## Supported Models

| Model | Parameters | Speed | Accuracy | Best For |
|---|---|---|---|---|
| YOLOv8n | 3.2M | ⚡⚡⚡ | ⭐⭐⭐ | Edge devices, Raspberry Pi |
| YOLOv8s | 11.2M | ⚡⚡ | ⭐⭐⭐⭐ | **Recommended — best balance** |
| YOLOv8m | 25.9M | ⚡ | ⭐⭐⭐⭐⭐ | High-accuracy deployments with GPU |

---

## Performance Benchmarks

| Metric | Value |
|---|---|
| Inference speed (CPU) | 30+ FPS |
| Inference speed (GPU) | 60+ FPS |
| Database write throughput | 500+ records/sec |
| REST API latency | < 50 ms |
| Max simultaneous cameras | 4+ |
| Heatmap generation | ~100× faster than naive loop (vectorised NumPy) |
| Memory usage (YOLOv8s) | ~2.2 GB |

---

## Docker Deployment

```bash
# Build image
docker build -t ai-crowd-detection:v4 .

# Run API server
docker run -p 8000:8000 \
  -v $(pwd)/detection_records.db:/app/detection_records.db \
  -v $(pwd)/reports:/app/reports \
  ai-crowd-detection:v4 python main.py --mode api

# Full stack with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named 'ultralytics'` | `pip install ultralytics` |
| `No module named 'customtkinter'` | `pip install customtkinter` |
| Camera not opening | Check webcam index in settings — try `source: 1` instead of `0` |
| Low FPS on CPU | Switch to `yolov8n.pt` in `config/settings.yaml` |
| Port 8000 already in use | Change `api.port` in `config/settings.yaml` |
| CUDA not detected | Install PyTorch with CUDA: https://pytorch.org/get-started/locally |
| `Permission denied` on report export | Ensure the `reports/` directory exists and is writable |
| Model file not found | Run once — YOLOv8 auto-downloads the `.pt` file on first launch |

---

## Dependencies

| Package | Purpose |
|---|---|
| `ultralytics` | YOLOv8 model inference |
| `opencv-python` | Frame capture, drawing, image processing |
| `numpy` | Vectorised heatmap and array operations |
| `customtkinter` | Modern dark-theme GUI widgets |
| `matplotlib` | Live charts in the dashboard |
| `Pillow` | Image handling for GUI |
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server for FastAPI |
| `pydantic` | Request/response validation |
| `websockets` | WebSocket live stream |
| `pandas` | Analytics and report data processing |
| `openpyxl` | Excel export support |
| `pyyaml` | YAML config loading |
| `reportlab` | PDF report generation |

---

## Complete VS Code Setup & Run Guide

This section walks you through everything from a blank Windows machine to a fully running project inside VS Code — step by step, nothing skipped.

---

### Step 1 — Install Python 3.10+

1. Go to https://www.python.org/downloads/
2. Download the latest **Python 3.10, 3.11, or 3.12** Windows installer
3. Run the installer — **tick "Add Python to PATH"** before clicking Install
4. Open a new Command Prompt and verify:

```cmd
python --version
pip --version
```

Both commands must return a version number. If they don't, Python was not added to PATH — reinstall and tick the checkbox.

---

### Step 2 — Install VS Code

1. Go to https://code.visualstudio.com/
2. Download and install the Windows version
3. Launch VS Code

---

### Step 3 — Install Required VS Code Extensions

Open VS Code, press `Ctrl+Shift+X` to open the Extensions panel, search for and install:

| Extension | Why You Need It |
|---|---|
| **Python** (by Microsoft) | Python language support, IntelliSense, linting |
| **Pylance** (by Microsoft) | Fast type checking and autocomplete |
| **Python Debugger** (by Microsoft) | Run and debug with breakpoints |

Optionally also install:

| Extension | Why |
|---|---|
| **YAML** (by Red Hat) | Syntax highlighting for `settings.yaml` |
| **GitLens** | Git history and blame inside VS Code |
| **SQLite Viewer** | Browse `detection_records.db` visually inside VS Code |

---

### Step 4 — Get the Project

**Option A — Clone with Git (recommended)**

If you have Git installed (https://git-scm.com/download/win):

```cmd
git clone https://github.com/bushrapopalzai/AI_Crowd_Detection_System.git
```

**Option B — Download ZIP**

1. Go to the GitHub repository
2. Click the green **Code** button → **Download ZIP**
3. Extract the ZIP to a folder, e.g. `C:\Projects\AI_Crowd_Detection_System`

---

### Step 5 — Open the Project in VS Code

1. Open VS Code
2. Go to **File → Open Folder**
3. Navigate to and select the `AI_Crowd_Detection_System` folder (the one containing `main.py`)
4. Click **Select Folder**

You should now see the full project tree in the Explorer panel on the left.

---

### Step 6 — Create a Virtual Environment

A virtual environment keeps this project's dependencies isolated from your system Python.

Open the VS Code integrated terminal: press `` Ctrl+` `` or go to **Terminal → New Terminal**.

Make sure you are inside the project folder, then run:

```cmd
python -m venv venv
```

This creates a `venv/` folder. Now activate it:

```cmd
venv\Scripts\activate
```

Your terminal prompt will change to show `(venv)` at the start — this means the virtual environment is active.

---

### Step 7 — Select the Virtual Environment in VS Code

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type **Python: Select Interpreter** and press Enter
3. Select the one that shows `venv` in the path, e.g. `.\venv\Scripts\python.exe`

This tells VS Code to use your virtual environment for IntelliSense, linting, and running code.

---

### Step 8 — Install All Dependencies

In the terminal (with `(venv)` active), run:

```cmd
pip install -r requirements.txt
```

This installs all 14 packages. It will take 1–3 minutes. To confirm everything installed:

```cmd
pip list
```

You should see `ultralytics`, `opencv-python`, `fastapi`, `customtkinter`, and the rest in the list.

---

### Step 9 — Run the Project

**Option A — GUI Dashboard (recommended for first run)**

```cmd
python main.py
```

The dark-theme dashboard window will open. Click **Start Camera** to begin live detection.

**Option B — API Server only**

```cmd
python main.py --mode api
```

Then open your browser:
- `http://localhost:8000/docs` — Swagger UI with all endpoints
- `http://localhost:8000/api/health` — quick health check

**Option C — Windows one-click (no terminal needed)**

Double-click `START.bat` in File Explorer. Press `1` for GUI or `2` for API.

---

### Step 10 — Run with VS Code Debugger (optional)

1. Click the **Run and Debug** icon in the left sidebar (`Ctrl+Shift+D`)
2. Click **create a launch.json file** → select **Python File**
3. Replace the contents of `.vscode/launch.json` with:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "GUI Dashboard",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "args": ["--mode", "gui"],
      "console": "integratedTerminal"
    },
    {
      "name": "API Server",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "args": ["--mode", "api"],
      "console": "integratedTerminal"
    }
  ]
}
```

4. Select **GUI Dashboard** or **API Server** from the dropdown at the top of the Debug panel
5. Press `F5` to start — set breakpoints by clicking the left margin of any line

---

### Step 11 — Edit Configuration

Open `config/settings.yaml` in VS Code and edit values — no code changes needed. Save and restart.

Common changes:

```yaml
# Use a faster but less accurate model
detection:
  model: "yolov8n.pt"

# Detect more objects by lowering the threshold
  confidence_threshold: 0.35

# Change API port if 8000 is already taken
api:
  port: 8080
```

---

### Common Setup Problems and Fixes

| Problem | Fix |
|---|---|
| `python` not recognised in terminal | Reinstall Python and tick **Add Python to PATH** |
| `venv\Scripts\activate` gives an error | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` in PowerShell first |
| VS Code does not show `venv` interpreter | `Ctrl+Shift+P` → Python: Select Interpreter → enter path manually: `.\venv\Scripts\python.exe` |
| `pip install` fails with SSL error | Run `python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt` |
| `No module named 'ultralytics'` after install | Make sure `(venv)` is active in the terminal before running `pip install` |
| GUI window does not open | Headless servers have no display — use `--mode api` instead |
| Camera index error | Try `source: 1` or `source: 2` in `config/settings.yaml` |
| Port 8000 already in use | Change `api.port` in `config/settings.yaml` to `8080` or any free port |

---

### Full Setup Checklist

- [ ] Python 3.10+ installed and in PATH (`python --version` works)
- [ ] VS Code installed
- [ ] Python + Pylance + Python Debugger extensions installed
- [ ] Project folder opened in VS Code
- [ ] Virtual environment created (`venv/` folder exists)
- [ ] Virtual environment activated (`(venv)` shown in terminal)
- [ ] Correct interpreter selected in VS Code (`venv\Scripts\python.exe`)
- [ ] `pip install -r requirements.txt` completed without errors
- [ ] `python main.py` launches the dashboard or API successfully

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Bushra Popalzai**
GitHub: [bushrapopalzai](https://github.com/bushrapopalzai/AI_Crowd_Detection_System)
