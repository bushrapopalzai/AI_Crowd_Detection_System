"""Advanced Analytics, Reports, and Cloud Sync"""

import threading, logging, json, time
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """Advanced detection analytics"""
    
    def __init__(self, db):
        self.db = db
    
    def get_peak_hours(self, date=None):
        df = self.db.read_all()
        if df.empty:
            return {}
        
        if date:
            df = df[df['date'] == date]
        
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        peak_hours = df.groupby('hour').size().to_dict()
        return dict(sorted(peak_hours.items(), key=lambda x: x[1], reverse=True))
    
    def get_class_distribution(self, date_range=None):
        df = self.db.read_all()
        if df.empty:
            return {}
        
        if date_range:
            start, end = date_range
            df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        return df['class_name'].value_counts().to_dict()
    
    def get_confidence_stats(self):
        df = self.db.read_all()
        if df.empty:
            return {}
        
        return {
            'mean': float(df['confidence'].mean()),
            'median': float(df['confidence'].median()),
            'std': float(df['confidence'].std()),
            'min': float(df['confidence'].min()),
            'max': float(df['confidence'].max())
        }
    
    def detect_trends(self, days=7):
        df = self.db.read_all()
        if df.empty:
            return {}
        
        df['date'] = pd.to_datetime(df['date'])
        recent = df[df['date'] >= (datetime.now() - timedelta(days=days))]
        
        daily_counts = recent.groupby('date').size()
        trend = {
            'total': int(daily_counts.sum()),
            'daily_avg': float(daily_counts.mean()),
            'daily_max': int(daily_counts.max()),
            'daily_min': int(daily_counts.min())
        }
        return trend


class ReportGenerator:
    """Generate automated reports"""
    
    def __init__(self, db, analytics):
        self.db = db
        self.analytics = analytics
    
    def generate_daily_report(self, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        df = self.db.read_all()
        daily_df = df[df['date'] == date]
        
        report = {
            'date': date,
            'total_detections': len(daily_df),
            'unique_classes': daily_df['class_name'].nunique() if not daily_df.empty else 0,
            'peak_hour': self.analytics.get_peak_hours(date),
            'class_distribution': daily_df['class_name'].value_counts().to_dict() if not daily_df.empty else {},
            'avg_confidence': float(daily_df['confidence'].mean()) if not daily_df.empty else 0,
            'avg_fps': float(daily_df['fps'].mean()) if not daily_df.empty else 0,
            'generated_at': datetime.now().isoformat()
        }
        return report
    
    def generate_weekly_report(self, end_date=None):
        if end_date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.fromisoformat(end_date)
        
        start_date = end_date - timedelta(days=7)
        
        df = self.db.read_all()
        df['date'] = pd.to_datetime(df['date'])
        weekly_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        report = {
            'period': f"{start_date.date()} to {end_date.date()}",
            'total_detections': len(weekly_df),
            'daily_avg': float(len(weekly_df) / 7) if len(weekly_df) > 0 else 0,
            'unique_classes': weekly_df['class_name'].nunique() if not weekly_df.empty else 0,
            'top_classes': weekly_df['class_name'].value_counts().head(5).to_dict() if not weekly_df.empty else {},
            'avg_confidence': float(weekly_df['confidence'].mean()) if not weekly_df.empty else 0,
            'trends': self.analytics.detect_trends(days=7),
            'generated_at': datetime.now().isoformat()
        }
        return report
    
    def export_report_json(self, report, output_path):
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report exported to {output_path}")
        except Exception as e:
            logger.error(f"JSON export error: {e}")


class CloudSyncManager:
    """Cloud sync manager"""
    
    def __init__(self, provider="google_drive", credentials_path=None):
        self.provider = provider
        self.credentials_path = credentials_path
        self.sync_interval = 3600
        self.last_sync = time.time()
        self.lock = threading.Lock()
        logger.info(f"Cloud sync initialized: {provider}")
    
    def sync_database(self, db_path, remote_path):
        try:
            logger.info(f"Syncing database to {self.provider}")
            self.last_sync = time.time()
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    def should_sync(self):
        return (time.time() - self.last_sync) >= self.sync_interval


if __name__ == "__main__":
    print("Analytics Module - Use with app.py")
