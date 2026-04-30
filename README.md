# AI Object Detection System

Real-time object detection with live Excel database logging and a modern GUI.

## Features

- Live webcam or video file detection using YOLOv8
- Real-time results written to `detection_records.xlsx` (buffered, append-only)
- 4 Excel sheets: Live Detections, Sessions, Hourly Analytics, Daily Summary
- Modern GUI with live video feed, stats panel, and matplotlib charts
- Export to CSV, date-range analysis, and in-Excel chart generation

## Requirements

- Python 3.8+
- `yolov8n.pt` model file (auto-downloaded by Ultralytics on first run)

## Installation

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-python Pillow matplotlib customtkinter numpy pandas openpyxl
```

## Usage

```bash
python main.py
```

Then click **Start Camera** for webcam or **Upload Video** to process a video file.

## Output Files

| File | Description |
|------|-------------|
| `detection_records.xlsx` | All detection data with 4 analytics sheets |
| `yolov8n.pt` | YOLOv8 nano model weights |

## Project Structure

```
AI-PROJECT/
├── main.py                  # Main application
├── yolov8n.pt               # YOLO model weights
└── detection_records.xlsx   # Auto-generated detection database
```

## Excel Sheets

- **Live_Detections** — Every detection with timestamp, class, confidence, bounding box, FPS
- **Sessions** — Per-session summary (start/end time, total frames, detections)
- **Hourly_Analytics** — Aggregated stats per hour
- **Daily_Summary** — Daily totals and peak hours
