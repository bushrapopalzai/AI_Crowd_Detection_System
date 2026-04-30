# AI Crowd Detection System

A real-time object and crowd detection application built with YOLOv8, featuring live Excel database logging, a modern GUI, and live analytics charts.

---

## Features

- **Live webcam** or **video file** detection using YOLOv8 nano
- **Real-time Excel logging** — buffered, append-only writes to `detection_records.xlsx`
- **4 Excel sheets** — Live Detections, Sessions, Hourly Analytics, Daily Summary
- **Modern GUI** — built with CustomTkinter (falls back to standard Tkinter)
- **Live matplotlib charts** — detections per frame and FPS timeline
- **Session management** — each run is tracked with a unique session ID
- **Date-range analysis** — filter and summarize detections by date
- **CSV export** and **in-Excel chart generation**
- **Smart frame buffering** — auto frame-skipping to maintain performance

---

## Requirements

- Python 3.8+
- Webcam (for live detection) or a video file (`.mp4`, `.avi`, `.mov`, `.mkv`)
- `yolov8n.pt` — auto-downloaded by Ultralytics on first run

---

## Installation

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-python Pillow matplotlib customtkinter numpy pandas openpyxl
```

---

## Usage

```bash
python main.py
```

| Action | Description |
|--------|-------------|
| **Start Camera** | Opens webcam and starts live detection |
| **Upload Video** | Select a local video file for detection |
| **Stop** | Ends the session and saves all data to Excel |
| **Analyze** | Filter detections by date range |
| **Create Charts** | Generates a pie chart inside the Excel file |
| **Force Save** | Immediately flushes buffered data to disk |
| **Export CSV** | Exports all detection records to a `.csv` file |

---

## Project Structure

```
AI-PROJECT/
├── main.py                  # Main application entry point
├── README.md                # Project documentation
├── .gitignore               # Git ignore rules
├── yolov8n.pt               # YOLOv8 nano model weights (auto-downloaded)
└── detection_records.xlsx   # Auto-generated detection database
```

---

## Excel Database — Sheet Details

| Sheet | Description |
|-------|-------------|
| `Live_Detections` | Every detection: timestamp, class, confidence, bounding box, FPS, session ID |
| `Sessions` | Per-session summary: start/end time, total frames, detections, unique classes, duration |
| `Hourly_Analytics` | Aggregated detection counts and average confidence per hour |
| `Daily_Summary` | Daily totals: sessions, detections, most detected class, peak hour |
| `Charts` | Auto-generated pie chart of top 10 detected objects (created on demand) |

---

## Architecture

```
main.py
├── ExcelLiveDatabase       — Buffered Excel writer with background flush thread
├── SmartVideoBuffer        — Thread-safe frame queue with auto frame-skipping
├── DetectionModel          — YOLOv8 wrapper with bounding box annotation
├── VideoProcessor          — Threaded video capture + detection + DB writing
└── ModernDetectionGUI      — CustomTkinter UI with 3 tabs:
    ├── Live Detection       — Video feed, controls, stats, live charts
    ├── History & Analytics  — Session table, date-range filter
    └── Database View        — Raw data viewer, CSV export
```

---

## How It Works

1. A new **session** is created each time you start detection
2. Each detected object is written to a **buffer** (flushed every 10 records or 5 seconds)
3. When the session ends, a **session summary** is written and the **daily summary** is updated
4. All data persists across runs — the Excel file is **append-only**

---

## Notes

- `yolov8n.pt` and `detection_records.xlsx` are excluded from Git (see `.gitignore`)
- The app gracefully falls back to standard Tkinter if CustomTkinter is not installed
- Confidence threshold defaults to `0.5` — adjustable in `DetectionModel`
