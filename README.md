# AI Crowd Detection System v4.0

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green)](https://github.com/ultralytics/ultralytics)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/bushrapopalzai/AI_Crowd_Detection_System)

A production-ready, modular real-time crowd and object detection system built on YOLOv8.  
Features a modern dark-theme dashboard GUI, REST API, SQLite database, and advanced analytics — all in a clean layered architecture.

---

## ✨ What's New in v4.0 (Refactored)

| Area | Change |
|---|---|
| Architecture | Flat scripts → clean `/core` `/api` `/ui` `/services` `/config` packages |
| Entry point | Single `main.py --mode gui\|api` replaces 5 redundant `.bat` launchers |
| GUI | Full dark-theme dashboard with stat cards, live charts, alert panel |
| Performance | Vectorised NumPy heatmap (100× faster), singleton model, `draw_idle()` charts |
| Security | Path-traversal fix, UTC-aware datetimes, proper exception logging |
| Config | Single `config/settings.yaml` (old `config.yaml` was stuck at v2.0) |
| Dependencies | Trimmed from 22 → 14 pinned packages, dev/prod separated |

---

## 🎯 Features

### Core Detection
- Real-time object detection — YOLOv8n / s / m (configurable)
- Live webcam and video file processing
- 30+ FPS on standard CPU hardware
- Confidence & IoU threshold tuning via config

### Tracking & Heatmaps
- Centroid-based ByteTracker with trail visualisation
- Vectorised Gaussian heatmap overlay (crowd density)
- Thread-safe alert system with callback hooks

### Dashboard GUI
- Modern dark theme (`customtkinter` with Tkinter fallback)
- 5 live stat cards — Status, FPS, Frames, Detections, Avg Confidence
- 2×2 real-time chart grid — detections timeline, FPS, class distribution, confidence histogram
- One-click camera start / video open
- CSV and PDF export built-in

### REST API
- FastAPI with Swagger UI at `/docs`
- WebSocket live feed at `ws://localhost:8000/ws/live`
- Pydantic-validated request bodies
- Async DB reads (non-blocking event loop)

### Database & Analytics
- SQLite with async-buffered writes (500+ rec/s)
- UTC-aware timestamps throughout
- Daily and weekly report generation (JSON export)
- Peak-hour analysis, class distribution, confidence stats, 7-day trends

### Deployment
- Docker + Docker Compose ready
- Single `START.bat` launcher for Windows

---

## 📦 Project Structure

```
AI_Crowd_Detection_System/
│
├── core/                        # Detection engine
│   ├── detector.py              # YOLOv8 singleton model
│   ├── tracking.py              # ByteTracker, HeatmapGenerator, AlertSystem
│   └── video_processor.py       # Capture + inference thread
│
├── api/                         # REST API layer
│   ├── server.py                # FastAPI app + WebSocket
│   └── camera_manager.py        # Multi-camera state manager
│
├── ui/                          # GUI layer
│   └── dashboard.py             # Dark-theme dashboard (customtkinter)
│
├── services/                    # Business logic / persistence
│   ├── database.py              # SQLite buffered writes
│   └── analytics.py             # Reports, trends, stats
│
├── config/                      # Configuration
│   ├── settings.yaml            # All settings in one place
│   ├── config_manager.py        # Singleton loader
│   └── logger.py                # Rotating file + console logging
│
├── main.py                      # Entry point
├── START.bat                    # Windows one-click launcher
├── requirements.txt             # Pinned dependencies
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ — https://www.python.org (check **Add Python to PATH**)
- 4 GB+ RAM
- Webcam or video file (optional for testing)
- GPU optional (CUDA auto-detected)

### Option 1 — Windows one-click
```
Double-click START.bat
Select 1 for GUI, 2 for API-only
```

### Option 2 — Command line
```bash
git clone https://github.com/bushrapopalzai/AI_Crowd_Detection_System.git
cd AI_Crowd_Detection_System

pip install -r requirements.txt

# GUI dashboard (default)
python main.py

# API server only
python main.py --mode api
```

### Option 3 — Docker
```bash
docker-compose up -d
# API → http://localhost:8000
# Docs → http://localhost:8000/docs
```

---

## 📖 Usage

### GUI Dashboard
```bash
python main.py
# or
python main.py --mode gui
```
1. Click **📷 Start Camera** for live webcam detection
2. Click **📁 Open Video** to process a video file
3. Watch live stat cards and charts update in real time
4. Use **Export CSV / PDF** buttons in the side panel

### API Server
```bash
python main.py --mode api
# Swagger UI → http://localhost:8000/docs
```

### REST API Examples
```bash
# Health check
curl http://localhost:8000/api/health

# List cameras
curl http://localhost:8000/api/cameras

# Add RTSP camera
curl -X POST http://localhost:8000/api/cameras/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"cam1","source":"rtsp://192.168.1.100:554/stream","source_type":"rtsp"}'

# Remove camera
curl -X DELETE http://localhost:8000/api/cameras/cam1

# Detection summary
curl http://localhost:8000/api/detections/summary

# Model info
curl http://localhost:8000/api/model/info
```

### Generate Reports (Python)
```python
from services import SQLiteDB, AdvancedAnalytics, ReportGenerator

db = SQLiteDB()
analytics = AdvancedAnalytics(db)
reports = ReportGenerator(db, analytics)

daily = reports.generate_daily_report()
reports.export_report_json(daily, "reports/daily.json")

weekly = reports.generate_weekly_report()
```

---

## ⚙️ Configuration

Edit `config/settings.yaml`:

```yaml
detection:
  model: "yolov8s.pt"          # yolov8n.pt | yolov8s.pt | yolov8m.pt
  confidence_threshold: 0.5
  iou_threshold: 0.45
  device: "auto"               # auto | cpu | cuda | mps

database:
  path: "detection_records.db"
  buffer_size: 50
  flush_interval: 5            # seconds

api:
  host: "0.0.0.0"
  port: 8000

performance:
  max_fps: 30
  frame_buffer_size: 5

ui:
  window_width: 1600
  window_height: 960
  chart_update_ms: 2000

logging:
  level: "INFO"
  file: "detection.log"
  max_bytes: 10485760
  backup_count: 3
```

---

## 🗄️ Database Schema

### `detections` table
| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| timestamp | TEXT | ISO-8601 UTC timestamp |
| date | TEXT | YYYY-MM-DD |
| time | TEXT | HH:MM:SS |
| session_id | INTEGER | Session reference |
| frame_number | INTEGER | Frame index |
| class_name | TEXT | Detected object class |
| confidence | REAL | Score 0–1 |
| bbox_x1/y1/x2/y2 | INTEGER | Bounding box pixels |
| fps | REAL | Processing FPS at capture |
| source_type | TEXT | camera / file / rtsp |
| source_path | TEXT | Source path or URL |

### `sessions` table
| Column | Type | Description |
|---|---|---|
| session_id | INTEGER | Primary key |
| start_time | TEXT | ISO-8601 UTC |
| end_time | TEXT | ISO-8601 UTC |
| total_frames | INTEGER | Frames processed |
| total_detections | INTEGER | Objects detected |
| unique_classes | INTEGER | Distinct classes seen |
| avg_confidence | REAL | Mean confidence score |
| status | TEXT | COMPLETED / RUNNING |

---

## 📊 Performance

| Metric | Value |
|---|---|
| Inference speed | 30+ FPS (CPU), 60+ FPS (GPU) |
| DB write speed | 500+ records/sec |
| API latency | < 50 ms |
| Max simultaneous cameras | 4+ |
| Heatmap update | Vectorised NumPy (~100× vs loop) |
| Memory (YOLOv8s) | ~2.2 GB |

---

## 🎬 Supported Models

| Model | Params | Speed | Accuracy | Best For |
|---|---|---|---|---|
| YOLOv8n | 3.2M | ⚡⚡⚡ | ⭐⭐⭐ | Edge / Raspberry Pi |
| YOLOv8s | 11.2M | ⚡⚡ | ⭐⭐⭐⭐ | **Recommended** |
| YOLOv8m | 25.9M | ⚡ | ⭐⭐⭐⭐⭐ | High-accuracy deployments |

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/model/info` | Model name, classes, threshold |
| GET | `/api/cameras` | List active cameras |
| POST | `/api/cameras/add` | Add camera (JSON body) |
| DELETE | `/api/cameras/{id}` | Remove camera |
| GET | `/api/detections/summary` | Total detections + class breakdown |
| WS | `/ws/live` | Real-time detection stream |

Full interactive docs: **http://localhost:8000/docs**

---

## 🐳 Docker

```bash
# Build
docker build -t ai-crowd-detection:v4 .

# Run API
docker run -p 8000:8000 \
  -v $(pwd)/detection_records.db:/app/detection_records.db \
  -v $(pwd)/reports:/app/reports \
  ai-crowd-detection:v4 python main.py --mode api

# Full stack
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'ultralytics'` | `pip install ultralytics` |
| Low FPS | Set `device: cpu` or lower `max_fps` in settings.yaml |
| Database locked | Delete `detection_records.db-journal`, close other instances |
| Port 8000 in use | Change `api.port` in `config/settings.yaml` |
| `customtkinter` not found | `pip install customtkinter` — falls back to ttk automatically |
| CUDA not detected | Set `detection.device: cpu` in settings.yaml |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com)
- [OpenCV](https://opencv.org)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [ReportLab](https://www.reportlab.com)

---

**Last Updated:** July 2025 | **Version:** 4.0.0 | **Status:** Production Ready ✅

**GitHub:** https://github.com/bushrapopalzai/AI_Crowd_Detection_System
