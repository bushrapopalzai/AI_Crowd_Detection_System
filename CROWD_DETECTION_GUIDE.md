# Crowd Detection Fix Guide

## Problem
The system was not detecting crowds effectively when uploading videos because:
1. **Confidence threshold too high (0.5)** - Filtered out many valid detections
2. **No crowd-specific analysis** - System detected all objects but didn't focus on people
3. **Missing crowd metrics** - No person counting or density analysis

## Solution Implemented

### 1. Lowered Confidence Threshold
- **Before**: 0.5 (very strict, missed many people)
- **After**: 0.35 (balanced, catches more people while maintaining accuracy)
- **Location**: `config/settings.yaml` and `core/detector.py`

### 2. Added Person Counting
- Tracks COCO class ID 0 (person) specifically
- Counts total people in each frame
- Displays person count on video overlay
- Stores person count in detection records

### 3. Enhanced Video Overlay
Now displays:
```
FPS: 30.5  Det: 45  People: 12
```
Instead of just:
```
FPS: 30.5  Det: 45
```

### 4. Crowd Density Analysis
- Calculates crowd density = people_count / (frame_area / 10000)
- Useful for identifying high-traffic zones
- Can be used for alerts when density exceeds threshold

## How to Use

### Upload and Process Video
1. Click **"📁 Open Video"** in the dashboard
2. Select your video file (MP4, AVI, MOV, MKV, WMV)
3. System will automatically:
   - Detect all objects (people, cars, bags, etc.)
   - Count people in each frame
   - Display crowd metrics
   - Store data in database

### View Results
- **Live Display**: See person count and detection count in real-time
- **Charts**: View detection trends and class distribution
- **Database**: All detections stored with person count
- **Export**: CSV/PDF reports with crowd statistics

## Configuration

Edit `config/settings.yaml` to fine-tune:

```yaml
detection:
  model: "yolov8s.pt"           # Model size (n=nano, s=small, m=medium)
  confidence_threshold: 0.35    # Lower = more detections (0.25-0.45 recommended)
  iou_threshold: 0.45           # Overlap threshold for NMS
  device: "auto"                # auto | cpu | cuda
```

### Threshold Recommendations
- **0.25**: Very sensitive, catches all people but may have false positives
- **0.35**: Balanced (current default) - good for most scenarios
- **0.45**: Conservative, fewer false positives but may miss some people
- **0.55+**: Very strict, only high-confidence detections

## Performance Tips

### For Better Crowd Detection
1. **Use YOLOv8s or YOLOv8m** (not nano for crowds)
2. **Lower confidence to 0.30-0.35** for crowded scenes
3. **Ensure good lighting** in video
4. **Use 1080p or higher** resolution videos

### For Faster Processing
1. **Use YOLOv8n** (nano model)
2. **Increase confidence to 0.45+**
3. **Use GPU** if available (CUDA)
4. **Lower video resolution** if needed

## Troubleshooting

### No Detections Appearing
- Check confidence threshold (try lowering to 0.25)
- Verify video file is valid (try MP4 format)
- Check model loaded successfully in logs
- Ensure video has people/objects to detect

### Too Many False Positives
- Increase confidence threshold (try 0.45-0.50)
- Switch to larger model (yolov8m)
- Check video quality and lighting

### Slow Processing
- Use smaller model (yolov8n)
- Increase confidence threshold
- Enable GPU acceleration
- Reduce video resolution

## Database Schema

Detections are stored with:
- `timestamp`: When detected
- `class_name`: Object type (person, car, etc.)
- `confidence`: Detection confidence (0-1)
- `bbox_x1, bbox_y1, bbox_x2, bbox_y2`: Bounding box coordinates
- `fps`: Processing speed
- `source_type`: camera or file
- `source_path`: Video file path

## API Integration

### Get Crowd Statistics
```bash
curl http://localhost:8000/api/detections/summary
```

Response:
```json
{
  "total": 1250,
  "by_class": {
    "person": 850,
    "car": 200,
    "backpack": 200
  },
  "avg_confidence": 0.72
}
```

### WebSocket Live Stream
```javascript
ws = new WebSocket("ws://localhost:8000/ws/live");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("People detected:", data.person_count);
};
```

## Advanced Features

### Crowd Alerts
Set up alerts when crowd exceeds threshold:
```python
from services import AdvancedAnalytics

analytics = AdvancedAnalytics(db)
peak_hours = analytics.get_peak_hours()
print("Peak hours:", peak_hours)
```

### Generate Reports
```python
from services import ReportGenerator

reports = ReportGenerator(db, analytics)
daily = reports.generate_daily_report()
reports.export_report_json(daily, "reports/daily.json")
```

## Recent Changes

### v4.0.1 - Crowd Detection Fix
- Lowered confidence threshold to 0.35
- Added person counting and crowd density
- Enhanced video overlay with people count
- Fixed torch/transformers compatibility
- Improved crowd metrics tracking

## Support

For issues or questions:
1. Check logs in `detection.log`
2. Review configuration in `config/settings.yaml`
3. Test with sample video first
4. Check GitHub issues: https://github.com/bushrapopalzai/AI_Crowd_Detection_System

---

**Last Updated**: 2026-05-03
**Version**: 4.0.1
