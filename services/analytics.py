"""Analytics and report generation service."""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_SAFE_REPORT_DIR = Path("reports").resolve()


def _safe_output_path(output_path: str) -> Path:
    """Resolve path and reject traversal outside reports dir."""
    resolved = Path(output_path).resolve()
    _SAFE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not str(resolved).startswith(str(_SAFE_REPORT_DIR)):
        raise ValueError(f"Output path outside allowed directory: {output_path}")
    return resolved


class AdvancedAnalytics:
    def __init__(self, db):
        self.db = db

    def get_peak_hours(self, date: str | None = None) -> dict:
        df = self.db.read_all()
        if df.empty:
            return {}
        if date:
            df = df[df["date"] == date]
        df["hour"] = pd.to_datetime(df["timestamp"], utc=True).dt.hour
        return dict(sorted(df.groupby("hour").size().items(), key=lambda x: x[1], reverse=True))

    def get_class_distribution(self, date_range: tuple | None = None) -> dict:
        df = self.db.read_all()
        if df.empty:
            return {}
        if date_range:
            start, end = date_range
            df = df[(df["date"] >= start) & (df["date"] <= end)]
        return df["class_name"].value_counts().to_dict()

    def get_confidence_stats(self) -> dict:
        df = self.db.read_all()
        if df.empty:
            return {}
        c = df["confidence"]
        return {
            "mean": round(float(c.mean()), 4),
            "median": round(float(c.median()), 4),
            "std": round(float(c.std()), 4),
            "min": round(float(c.min()), 4),
            "max": round(float(c.max()), 4),
        }

    def detect_trends(self, days: int = 7) -> dict:
        df = self.db.read_all()
        if df.empty:
            return {}
        df["date"] = pd.to_datetime(df["date"], utc=True)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        recent = df[df["date"] >= cutoff]
        counts = recent.groupby("date").size()
        if counts.empty:
            return {}
        return {
            "total": int(counts.sum()),
            "daily_avg": round(float(counts.mean()), 2),
            "daily_max": int(counts.max()),
            "daily_min": int(counts.min()),
        }


class ReportGenerator:
    def __init__(self, db, analytics: AdvancedAnalytics):
        self.db = db
        self.analytics = analytics

    def generate_daily_report(self, date: str | None = None) -> dict:
        if date is None:
            date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        df = self.db.read_all()
        daily = df[df["date"] == date] if not df.empty else pd.DataFrame()
        return {
            "date": date,
            "total_detections": len(daily),
            "unique_classes": int(daily["class_name"].nunique()) if not daily.empty else 0,
            "peak_hours": self.analytics.get_peak_hours(date),
            "class_distribution": daily["class_name"].value_counts().to_dict() if not daily.empty else {},
            "avg_confidence": round(float(daily["confidence"].mean()), 4) if not daily.empty else 0.0,
            "avg_fps": round(float(daily["fps"].mean()), 2) if not daily.empty else 0.0,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def generate_weekly_report(self, end_date: str | None = None) -> dict:
        end = (datetime.fromisoformat(end_date) if end_date
               else datetime.now(tz=timezone.utc))
        start = end - timedelta(days=7)
        df = self.db.read_all()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], utc=True)
            weekly = df[(df["date"] >= start) & (df["date"] <= end)]
        else:
            weekly = pd.DataFrame()
        return {
            "period": f"{start.date()} to {end.date()}",
            "total_detections": len(weekly),
            "daily_avg": round(len(weekly) / 7, 2),
            "unique_classes": int(weekly["class_name"].nunique()) if not weekly.empty else 0,
            "top_classes": weekly["class_name"].value_counts().head(5).to_dict() if not weekly.empty else {},
            "avg_confidence": round(float(weekly["confidence"].mean()), 4) if not weekly.empty else 0.0,
            "trends": self.analytics.detect_trends(days=7),
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        }

    def export_report_json(self, report: dict, output_path: str) -> None:
        try:
            safe = _safe_output_path(output_path)
            with open(safe, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info("Report saved: %s", safe)
        except ValueError as e:
            logger.error("Path traversal blocked: %s", e)
        except OSError:
            logger.exception("Failed to write report to %s", output_path)
