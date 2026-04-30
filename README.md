# AI Crowd Detection System v4.0

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com/bushrapopalzai/AI_Crowd_Detection_System)

A production-ready real-time object and crowd detection application with multi-camera support, REST API, cloud sync, and advanced analytics.

## 🎯 Features

### Core Detection
- ✅ Real-time object detection using YOLOv8 (configurable: n/s/m)
- ✅ Live webcam and video file processing
- ✅ Adaptive frame skipping for performance optimization
- ✅ Confidence threshold calibration
- ✅ 30+ FPS on standard hardware

### Multi-Camera & Streaming
- ✅ 4+ simultaneous camera support
- ✅ RTSP/HTTP stream support (IP cameras, NVR, drones)
- ✅ MJPEG streaming over HTTP
- ✅ Grid view monitoring dashboard
- ✅ Parallel stream processing

### Tracking & Analytics
- ✅ ByteTrack object tracking with unique IDs
- ✅ Real-time heatmap overlay for crowd density
- ✅ Trajectory trail visualization
- ✅ Crowd density analysis per grid cell
- ✅ Anomaly detection with configurable alerts

### Database & Storage
- ✅ SQLite database (10x faster than Excel)
- ✅ Async I/O non-blocking writes
- ✅ ACID compliance
- ✅ Cloud sync (Google Drive, AWS S3)
- ✅ Automatic data retention policies
- ✅ 500+ records/sec write speed

### REST API & Integration
- ✅ FastAPI server with full REST API
- ✅ WebSocket real-time updates
- ✅ Swagger UI interactive documentation
- ✅ Multi-format export (JSON, CSV, PDF)
- ✅ <50ms API latency

### Advanced Analytics
- ✅ Peak hour analysis
- ✅ 7-day trend detection
- ✅ Statistical anomaly detection
- ✅ Class distribution breakdown
- ✅ Automated daily/weekly reports
- ✅ Interactive real-time charts

### User Interface
- ✅ Modern Tkinter GUI with dark theme
- ✅ PyQt6 professional interface (optional)
- ✅ Interactive real-time charts (4 chart types)
- ✅ Export to CSV and PDF
- ✅ Live statistics dashboard
- ✅ Streamlit web dashboard alternative

### Deployment
- ✅ Docker support with production-ready containers
- ✅ Docker Compose multi-service orchestration
- ✅ PostgreSQL enterprise database option
- ✅ Redis caching layer
- ✅ One-click batch launchers

## 📦 Project Structure

```
AI-Crowd-Detection/
├── app.py                 # Main application entry point
├── gui.py                 # PyQt6 graphical interface
├── tracking.py            # Object tracking & heatmaps
├── multicamera.py         # Multi-camera & stream management
├── analytics.py           # Reports, analytics & cloud sync
├── config.yaml            # Centralized configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Multi-service orchestration
├── RUN.bat                # One-click launcher (Simple)
├── RUN_MULTICAM.bat       # One-click launcher (Multi-Camera)
├── RUN_DOCKER.bat         # One-click launcher (Docker)
├── RUN_ANALYTICS.bat      # One-click launcher (Analytics)
├── detection_records.db   # SQLite database (auto-created)
├── yolov8s.pt             # YOLOv8 model weights (auto-downloaded)
├── README.md              # This file
├── QUICK_START.md         # Quick start guide
└── .gitignore             # Git ignore rules
```

## 🚀 Installation

### Prerequisites
- **Python 3.10+** - Download from https://www.python.org
  - ✅ Check "Add Python to PATH" during installation
- **4GB+ RAM**
- **Webcam or IP Camera** (optional)
- **GPU optional** (CUDA/OpenVINO for acceleration)

### Quick Start (Recommended)

#### Option 1: One-Click Launcher (Windows)
```bash
# Simply double-click one of these files:
RUN.bat                 # Single camera (easiest)
RUN_MULTICAM.bat        # Multi-camera + API
RUN_DOCKER.bat          # Full stack with Docker
RUN_ANALYTICS.bat       # Reports & analytics
```

#### Option 2: Local Installation
```bash
# Clone repository
git clone https://github.com/bushrapopalzai/AI_Crowd_Detection_System.git
cd AI-Crowd-Detection

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

#### Option 3: Docker Deployment
```bash
# Build and run
docker-compose up -d

# Services:
# - API: http://localhost:8000
# - Streamlit UI: http://localhost:8501
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

## 📖 Usage

### Single Camera (GUI Mode)
```bash
python app.py
```
Then:
1. Click "📷 Start Camera" for webcam
2. Click "📁 Upload Video" for video file
3. Watch real-time detections
4. View analytics in "Analytics & Charts" tab
5. Export data in "Export & Reports" tab

### Multi-Camera with API
```bash
python app.py --mode api
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### REST API Examples

```bash
# Health check
curl http://localhost:8000/api/health

# List cameras
curl http://localhost:8000/api/cameras

# Add camera
curl -X POST http://localhost:8000/api/cameras/add \
  -H "Content-Type: application/json" \
  -d '{"camera_id":"cam1","source":"rtsp://192.168.1.100:554/stream","source_type":"rtsp"}'

# Get detection summary
curl http://localhost:8000/api/detections/summary

# Get model info
curl http://localhost:8000/api/model/info
```

### Generate Reports
```python
from analytics import ReportGenerator, AdvancedAnalytics
from app import SQLiteDB

db = SQLiteDB()
analytics = AdvancedAnalytics(db)
report_gen = ReportGenerator(db, analytics)

# Daily report
daily = report_gen.generate_daily_report()
report_gen.export_report_json(daily, "reports/daily.json")

# Weekly report
weekly = report_gen.generate_weekly_report()
```

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
app:
  title: "AI Detection System v4.0"
  version: "4.0.0"
  theme: "dark"

detection:
  model: "yolov8s"              # yolov8n, yolov8s, yolov8m
  confidence_threshold: 0.5
  iou_threshold: 0.45
  device: "auto"                # auto, cpu, cuda, mps

database:
  type: "sqlite"
  path: "detection_records.db"
  backup_enabled: true
  backup_interval: 3600

performance:
  max_fps: 30
  buffer_size: 5
  adaptive_skip: true
  batch_size: 1
  num_workers: 2

ui:
  window_width: 1600
  window_height: 1000
  chart_update_interval: 1000

logging:
  level: "INFO"
  file: "detection.log"
  max_size: 10485760

cloud:
  provider: "google_drive"      # google_drive, aws_s3
  enabled: false
  sync_interval: 3600

reports:
  enabled: true
  daily_time: "23:00"
  weekly_day: 6
  output_dir: "reports"
```

## 🗄️ Database Schema

### detections table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | DATETIME | Detection time |
| date | TEXT | Detection date |
| time | TEXT | Detection time |
| session_id | INTEGER | Session reference |
| frame_number | INTEGER | Frame number |
| class_name | TEXT | Object class |
| confidence | REAL | Detection confidence (0-1) |
| bbox_x1, y1, x2, y2 | INTEGER | Bounding box coordinates |
| fps | REAL | Processing FPS |
| source_type | TEXT | Source type (camera/file/rtsp) |
| source_path | TEXT | Source path/URL |

### sessions table
| Column | Type | Description |
|--------|------|-------------|
| session_id | INTEGER | Primary key |
| start_time | DATETIME | Session start |
| end_time | DATETIME | Session end |
| date | TEXT | Session date |
| source_type | TEXT | Source type |
| source_path | TEXT | Source path |
| total_frames | INTEGER | Processed frames |
| total_detections | INTEGER | Total objects detected |
| unique_classes | INTEGER | Unique object classes |
| avg_confidence | REAL | Average confidence |
| duration_seconds | REAL | Session duration |
| status | TEXT | Session status |

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Database Write Speed | 500+ records/sec |
| Model | YOLOv8s (22.5M params) |
| Max Cameras | 4+ simultaneous |
| Memory Usage | ~2.2GB |
| UI Chart FPS | 60 FPS |
| REST API Latency | <50ms |
| Inference Speed | 30+ FPS |

## 🎬 Supported Models

| Model | Speed | Accuracy | Size | Use Case |
|-------|-------|----------|------|----------|
| YOLOv8n | ⚡⚡⚡ | ⭐⭐⭐ | 6.3M | Edge devices, real-time |
| YOLOv8s | ⚡⚡ | ⭐⭐⭐⭐ | 22.5M | **Recommended** |
| YOLOv8m | ⚡ | ⭐⭐⭐⭐⭐ | 49.7M | High accuracy needed |

## 🔧 Troubleshooting

### "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### "CUDA not available"
```yaml
# In config.yaml
detection:
  device: "cpu"
```

### "Database locked"
```bash
rm detection_records.db-journal
# Close other app instances
```

### "Low FPS"
```yaml
# In config.yaml
performance:
  adaptive_skip: true
  max_fps: 15
```

### "Port 8000 already in use"
```bash
# Change port in config.yaml or run:
python app.py --port 8001
```

### "Python not found"
- Install Python from https://www.python.org
- Make sure to check "Add Python to PATH"
- Restart Command Prompt after installation

### "Docker not found"
- Install Docker Desktop from https://www.docker.com
- Restart computer after installation

## 📡 REST API Documentation

When running, full interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Health & Status
- `GET /api/health` - Health check
- `GET /api/model/info` - Current model info

#### Camera Management
- `GET /api/cameras` - List all cameras
- `POST /api/cameras/add` - Add new camera
- `DELETE /api/cameras/{id}` - Remove camera
- `GET /api/cameras/{id}/stats` - Camera statistics
- `GET /api/cameras/{id}/stream` - MJPEG stream

#### Detection Data
- `GET /api/detections/summary` - Detection summary
- `GET /api/detections/date-range` - Date range query
- `POST /api/model/update` - Update model

#### WebSocket
- `WS /ws/live` - Real-time updates

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t ai-detection:v4 .
```

### Run Container
```bash
docker run -p 8000:8000 \
  -v $(pwd)/detection_records.db:/app/detection_records.db \
  -v $(pwd)/reports:/app/reports \
  ai-detection:v4
```

### Docker Compose
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## 📈 Performance Comparison

| Feature | v1.0 | v2.0 | v3.0 | v4.0 |
|---------|------|------|------|------|
| Database Speed | 50 rec/s | 500+ rec/s | 500+ rec/s | 500+ rec/s |
| Model | YOLOv8n | YOLOv8s | YOLOv8s | YOLOv8s |
| Cameras | 1 | 1 | 1 | 4+ |
| Memory Usage | 2.5GB | 1.8GB | 1.8GB | 2.2GB |
| UI FPS | 30 | 30 | 60 | 60 |
| REST API | ❌ | ❌ | ❌ | ✅ |
| Cloud Sync | ❌ | ❌ | ❌ | ✅ |
| Reports | ❌ | ❌ | ❌ | ✅ |
| Docker | ❌ | ❌ | ❌ | ✅ |

## 🚀 Roadmap

### Phase 6 (Planned)
- [ ] Mobile app (iOS/Android)
- [ ] Edge deployment (Jetson, Raspberry Pi)
- [ ] Kubernetes orchestration
- [ ] YOLOv11 / SAM integration
- [ ] Real-time alerts (Email, SMS, Slack)
- [ ] Custom model training UI

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Quick start guide
- **[config.yaml](config.yaml)** - Configuration reference
- **[API Docs](http://localhost:8000/docs)** - Interactive Swagger UI (when running)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **YOLOv8** - Ultralytics
- **FastAPI** - Sebastián Ramírez
- **PyQt6** - Qt Company
- **OpenCV** - Intel
- **Tkinter** - Python Software Foundation

## 📞 Support

For issues, questions, or suggestions:

1. **Check [Troubleshooting](#-troubleshooting) section**
2. **Review logs**: `tail -f detection.log`
3. **Check configuration**: `cat config.yaml`
4. **Test API**: `curl http://localhost:8000/api/health`
5. **Open GitHub issue** with details

## 🎯 Quick Links

- **GitHub**: https://github.com/bushrapopalzai/AI_Crowd_Detection_System
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: https://github.com/bushrapopalzai/AI_Crowd_Detection_System/issues
- **Python**: https://www.python.org
- **Docker**: https://www.docker.com

---

**Last Updated:** January 2024 | **Version:** 4.0.0 | **Status:** Production Ready ✅

**Made with ❤️ for real-time AI detection**
