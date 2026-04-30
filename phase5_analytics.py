"""Phase 5: Cloud Sync, Advanced Analytics, Automated Reports"""

import threading, logging, json, os, time
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class CloudSyncManager:
    """Sync detection data to cloud storage"""
    
    def __init__(self, provider="google_drive", credentials_path=None):
        self.provider = provider
        self.credentials_path = credentials_path
        self.sync_interval = 3600  # 1 hour
        self.last_sync = time.time()
        self.lock = threading.Lock()
        
        if provider == "google_drive":
            self._init_google_drive()
        elif provider == "aws_s3":
            self._init_aws_s3()
    
    def _init_google_drive(self):
        """Initialize Google Drive sync"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build
            
            self.credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            logger.info("Google Drive sync initialized")
        except Exception as e:
            logger.error(f"Google Drive init error: {e}")
    
    def _init_aws_s3(self):
        """Initialize AWS S3 sync"""
        try:
            import boto3
            self.s3_client = boto3.client('s3')
            logger.info("AWS S3 sync initialized")
        except Exception as e:
            logger.error(f"AWS S3 init error: {e}")
    
    def sync_database(self, db_path, remote_path):
        """Sync database to cloud"""
        try:
            if self.provider == "google_drive":
                self._upload_to_google_drive(db_path, remote_path)
            elif self.provider == "aws_s3":
                self._upload_to_s3(db_path, remote_path)
            
            self.last_sync = time.time()
            logger.info(f"Database synced to {self.provider}")
        except Exception as e:
            logger.error(f"Sync error: {e}")
    
    def _upload_to_google_drive(self, local_path, remote_path):
        """Upload to Google Drive"""
        try:
            file_metadata = {'name': Path(local_path).name}
            media = __import__('googleapiclient.http', fromlist=['MediaFileUpload']).MediaFileUpload(local_path)
            self.drive_service.files().create(body=file_metadata, media_body=media).execute()
        except Exception as e:
            logger.error(f"Google Drive upload error: {e}")
    
    def _upload_to_s3(self, local_path, bucket, key):
        """Upload to AWS S3"""
        try:
            self.s3_client.upload_file(local_path, bucket, key)
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
    
    def should_sync(self):
        """Check if sync is needed"""
        return (time.time() - self.last_sync) >= self.sync_interval


class AdvancedAnalytics:
    """Advanced detection analytics and insights"""
    
    def __init__(self, db):
        self.db = db
    
    def get_peak_hours(self, date=None):
        """Get peak detection hours"""
        df = self.db.read_all()
        if df.empty:
            return {}
        
        if date:
            df = df[df['date'] == date]
        
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        peak_hours = df.groupby('hour').size().to_dict()
        return dict(sorted(peak_hours.items(), key=lambda x: x[1], reverse=True))
    
    def get_class_distribution(self, date_range=None):
        """Get detection class distribution"""
        df = self.db.read_all()
        if df.empty:
            return {}
        
        if date_range:
            start, end = date_range
            df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        return df['class_name'].value_counts().to_dict()
    
    def get_confidence_stats(self):
        """Get confidence score statistics"""
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
    
    def get_fps_stats(self):
        """Get FPS statistics"""
        df = self.db.read_all()
        if df.empty:
            return {}
        
        return {
            'mean': float(df['fps'].mean()),
            'median': float(df['fps'].median()),
            'min': float(df['fps'].min()),
            'max': float(df['fps'].max())
        }
    
    def detect_trends(self, days=7):
        """Detect detection trends over time"""
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
    
    def get_anomalies(self, threshold_std=2):
        """Detect anomalous detection patterns"""
        df = self.db.read_all()
        if df.empty:
            return []
        
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        hourly_counts = df.groupby('hour').size()
        
        mean = hourly_counts.mean()
        std = hourly_counts.std()
        
        anomalies = []
        for hour, count in hourly_counts.items():
            if abs(count - mean) > threshold_std * std:
                anomalies.append({
                    'hour': int(hour),
                    'count': int(count),
                    'deviation': float((count - mean) / std)
                })
        
        return anomalies


class ReportGenerator:
    """Generate automated detection reports"""
    
    def __init__(self, db, analytics):
        self.db = db
        self.analytics = analytics
    
    def generate_daily_report(self, date=None):
        """Generate daily report"""
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
        """Generate weekly report"""
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
            'anomalies': self.analytics.get_anomalies(),
            'generated_at': datetime.now().isoformat()
        }
        return report
    
    def export_report_pdf(self, report, output_path):
        """Export report as PDF"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
            from reportlab.lib.styles import getSampleStyleSheet
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"Detection Report - {report.get('date', 'Weekly')}", styles['Heading1'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            
            # Summary
            summary_data = [
                ['Metric', 'Value'],
                ['Total Detections', str(report.get('total_detections', 0))],
                ['Unique Classes', str(report.get('unique_classes', 0))],
                ['Avg Confidence', f"{report.get('avg_confidence', 0):.2f}"],
                ['Avg FPS', f"{report.get('avg_fps', 0):.1f}"]
            ]
            
            summary_table = Table(summary_data)
            elements.append(summary_table)
            
            doc.build(elements)
            logger.info(f"Report exported to {output_path}")
        except Exception as e:
            logger.error(f"PDF export error: {e}")
    
    def export_report_json(self, report, output_path):
        """Export report as JSON"""
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report exported to {output_path}")
        except Exception as e:
            logger.error(f"JSON export error: {e}")
    
    def export_report_csv(self, output_path):
        """Export all detections as CSV"""
        try:
            df = self.db.read_all()
            df.to_csv(output_path, index=False)
            logger.info(f"CSV exported to {output_path}")
        except Exception as e:
            logger.error(f"CSV export error: {e}")


class ScheduledReportGenerator:
    """Generate reports on schedule"""
    
    def __init__(self, report_gen, output_dir="reports"):
        self.report_gen = report_gen
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.running = False
    
    def start_daily_reports(self, time_of_day="23:00"):
        """Start daily report generation"""
        self.running = True
        
        def generate():
            while self.running:
                now = datetime.now()
                target_time = datetime.strptime(time_of_day, "%H:%M").time()
                
                if now.time() >= target_time:
                    report = self.report_gen.generate_daily_report()
                    
                    date = report['date']
                    self.report_gen.export_report_json(
                        report, 
                        self.output_dir / f"daily_{date}.json"
                    )
                    self.report_gen.export_report_pdf(
                        report,
                        self.output_dir / f"daily_{date}.pdf"
                    )
                    
                    logger.info(f"Daily report generated for {date}")
                    time.sleep(86400)  # Wait 24 hours
                else:
                    time.sleep(3600)  # Check every hour
        
        threading.Thread(target=generate, daemon=True).start()
    
    def start_weekly_reports(self, day_of_week=6, time_of_day="23:00"):
        """Start weekly report generation"""
        self.running = True
        
        def generate():
            while self.running:
                now = datetime.now()
                if now.weekday() == day_of_week:
                    target_time = datetime.strptime(time_of_day, "%H:%M").time()
                    if now.time() >= target_time:
                        report = self.report_gen.generate_weekly_report()
                        
                        week_start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
                        self.report_gen.export_report_json(
                            report,
                            self.output_dir / f"weekly_{week_start}.json"
                        )
                        self.report_gen.export_report_pdf(
                            report,
                            self.output_dir / f"weekly_{week_start}.pdf"
                        )
                        
                        logger.info(f"Weekly report generated")
                        time.sleep(604800)  # Wait 7 days
                
                time.sleep(3600)  # Check every hour
        
        threading.Thread(target=generate, daemon=True).start()


# Example usage
if __name__ == "__main__":
    from main_v2 import SQLiteDB
    
    db = SQLiteDB()
    analytics = AdvancedAnalytics(db)
    report_gen = ReportGenerator(db, analytics)
    
    # Generate reports
    daily = report_gen.generate_daily_report()
    print("Daily Report:", json.dumps(daily, indent=2, default=str))
    
    weekly = report_gen.generate_weekly_report()
    print("Weekly Report:", json.dumps(weekly, indent=2, default=str))
    
    # Export
    report_gen.export_report_json(daily, "reports/daily_report.json")
    report_gen.export_report_csv("reports/detections.csv")
    
    # Schedule reports
    scheduler = ScheduledReportGenerator(report_gen)
    scheduler.start_daily_reports("23:00")
    scheduler.start_weekly_reports(day_of_week=6, time_of_day="23:00")
