# AI Detection System v4.0 - Quick Start Guide

## 🚀 One-Click Launch

Simply **double-click** one of these files to start:

### 1. **RUN.bat** - Single Camera (Recommended for beginners)
- Start with webcam or video file
- Simple GUI interface
- Best for testing

### 2. **RUN_MULTICAM.bat** - Multi-Camera + API
- Support 4+ simultaneous cameras
- REST API on http://localhost:8000
- RTSP/HTTP stream support
- Best for production

### 3. **RUN_DOCKER.bat** - Full Stack (Docker)
- Complete containerized deployment
- PostgreSQL + Redis included
- Requires Docker Desktop installed
- Best for enterprise

### 4. **RUN_ANALYTICS.bat** - Reports & Analytics
- Generate daily/weekly reports
- Advanced analytics
- Cloud sync
- Best for data analysis

---

## ⚙️ Prerequisites

### Required
- **Python 3.10+** - Download from https://www.python.org
  - ✅ Check "Add Python to PATH" during installation
- **4GB+ RAM**

### Optional
- **GPU** (NVIDIA CUDA or AMD) - For faster processing
- **Docker Desktop** - For RUN_DOCKER.bat
- **Webcam or IP Camera** - For video input

---

## 🎯 First Time Setup

### Step 1: Install Python
1. Go to https://www.python.org/downloads/
2. Download Python 3.10 or higher
3. Run installer
4. ✅ **IMPORTANT**: Check "Add Python to PATH"
5. Click Install

### Step 2: Verify Installation
Open Command Prompt and type:
```bash
python --version
```
Should show: `Python 3.10.x` or higher

### Step 3: Run the Project
Double-click **RUN.bat** in the project folder

---

## 📖 Usage Guide

### Simple Mode (RUN.bat)
```
1. Double-click RUN.bat
2. Wait for dependencies to install
3. GUI window opens
4. Click "Start Camera" or "Upload Video"
5. Watch detections in real-time
```

### Multi-Camera Mode (RUN_MULTICAM.bat)
```
1. Double-click RUN_MULTICAM.bat
2. Wait for API to start
3. Open browser: http://localhost:8000/docs
4. Add cameras via API
5. View streams and detections
```

### Docker Mode (RUN_DOCKER.bat)
```
1. Install Docker Desktop first
2. Double-click RUN_DOCKER.bat
3. Wait for containers to start
4. Open browser: http://localhost:8000
5. Access all services
```

### Analytics Mode (RUN_ANALYTICS.bat)
```
1. Double-click RUN_ANALYTICS.bat
2. Reports generated automatically
3. Check reports/ folder for PDF/JSON files
4. View analytics and trends
```

---

## 🌐 Access Points

Once running, access these URLs:

| Service | URL | Mode |
|---------|-----|------|
| API Docs | http://localhost:8000/docs | Multi-Cam, Docker |
| API Health | http://localhost:8000/api/health | Multi-Cam, Docker |
| Streamlit UI | http://localhost:8501 | Docker |
| PostgreSQL | localhost:5432 | Docker |
| Redis | localhost:6379 | Docker |

---

## 🔧 Troubleshooting

### "Python not found"
- Install Python from https://www.python.org
- Make sure to check "Add Python to PATH"
- Restart Command Prompt after installation

### "Port 8000 already in use"
- Another app is using port 8000
- Close other applications or use different port
- Edit config.yaml to change port

### "CUDA not available"
- GPU support is optional
- System will use CPU automatically
- Processing will be slower but still works

### "Docker not found"
- Install Docker Desktop from https://www.docker.com
- Restart computer after installation
- Run RUN_DOCKER.bat again

### "Low FPS"
- Reduce video resolution
- Lower confidence threshold in config.yaml
- Use smaller model (yolov8n instead of yolov8s)

---

## 📊 Example Workflows

### Workflow 1: Quick Test
```
1. Double-click RUN.bat
2. Click "Start Camera"
3. See detections in real-time
4. Click "Stop" when done
```

### Workflow 2: Multi-Camera Monitoring
```
1. Double-click RUN_MULTICAM.bat
2. Open http://localhost:8000/docs
3. Add 4 cameras via API
4. View grid dashboard
5. Check analytics
```

### Workflow 3: Full Production Stack
```
1. Double-click RUN_DOCKER.bat
2. Wait for all services to start
3. Open http://localhost:8000
4. Configure cameras
5. Generate reports
6. Sync to cloud
```

---

## 📝 Configuration

Edit `config.yaml` to customize:

```yaml
detection:
  model: "yolov8s"           # yolov8n, yolov8s, yolov8m
  confidence_threshold: 0.5  # 0.0 to 1.0
  device: "auto"             # auto, cpu, cuda

performance:
  max_fps: 30                # Target FPS
  adaptive_skip: true        # Dynamic frame skipping
```

---

## 🆘 Getting Help

1. **Check logs**: Open `detection.log` file
2. **Read docs**: See README.md and PHASE4_5_README.md
3. **API docs**: http://localhost:8000/docs (when running)
4. **GitHub**: https://github.com/bushrapopalzai/AI_Crowd_Detection_System

---

## 🎓 Learning Path

### Beginner
1. Run RUN.bat
2. Test with webcam
3. Read README.md

### Intermediate
1. Run RUN_MULTICAM.bat
2. Add RTSP cameras
3. Explore REST API

### Advanced
1. Run RUN_DOCKER.bat
2. Configure PostgreSQL
3. Setup cloud sync
4. Generate reports

---

## 📞 Support

- **Issues**: https://github.com/bushrapopalzai/AI_Crowd_Detection_System/issues
- **Docs**: README.md, PHASE4_5_README.md, UPGRADE_GUIDE.md
- **API**: http://localhost:8000/docs

---

**Happy Detecting! 🎯**

Last Updated: January 2024 | Version: 4.0.0
