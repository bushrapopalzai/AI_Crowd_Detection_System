"""
AI Detection System v4.0 - One-Click Launcher
Click to run the entire project with automatic setup
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProjectLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AI Detection System v4.0 - Launcher")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Set icon
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        self.processes = []
        self.running = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup launcher UI"""
        # Header
        header = tk.Frame(self.root, bg="#0d47a1", height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="AI Detection System v4.0", 
                        font=("Arial", 20, "bold"), bg="#0d47a1", fg="white")
        title.pack(pady=10)
        
        subtitle = tk.Label(header, text="Production-Ready Detection & Analytics", 
                           font=("Arial", 10), bg="#0d47a1", fg="#e0e0e0")
        subtitle.pack()
        
        # Main content
        content = tk.Frame(self.root, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Mode selection
        mode_label = tk.Label(content, text="Select Launch Mode:", 
                             font=("Arial", 12, "bold"), bg="white")
        mode_label.pack(anchor="w", pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="simple")
        
        modes = [
            ("🎬 Simple Mode (Single Camera)", "simple"),
            ("📹 Multi-Camera Mode (4 Cameras + API)", "multicam"),
            ("🐳 Docker Mode (Full Stack)", "docker"),
            ("📊 Analytics Only (Reports)", "analytics"),
        ]
        
        for text, value in modes:
            rb = tk.Radiobutton(content, text=text, variable=self.mode_var, 
                               value=value, font=("Arial", 10), bg="white")
            rb.pack(anchor="w", pady=5)
        
        # Separator
        sep = ttk.Separator(content, orient="horizontal")
        sep.pack(fill=tk.X, pady=15)
        
        # Features
        features_label = tk.Label(content, text="Features:", 
                                 font=("Arial", 11, "bold"), bg="white")
        features_label.pack(anchor="w", pady=(10, 5))
        
        features_text = """✅ Real-time object detection (YOLOv8s)
✅ Multi-camera support with RTSP streams
✅ REST API with Swagger documentation
✅ Advanced analytics & automated reports
✅ Cloud sync (Google Drive, AWS S3)
✅ Docker containerization"""
        
        features = tk.Label(content, text=features_text, 
                           font=("Arial", 9), bg="white", justify="left")
        features.pack(anchor="w", pady=5)
        
        # Separator
        sep2 = ttk.Separator(content, orient="horizontal")
        sep2.pack(fill=tk.X, pady=15)
        
        # Status
        self.status_label = tk.Label(content, text="Ready to launch", 
                                    font=("Arial", 9), bg="white", fg="#666")
        self.status_label.pack(anchor="w", pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(content, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Buttons
        button_frame = tk.Frame(content, bg="white")
        button_frame.pack(fill=tk.X, pady=20)
        
        self.launch_btn = tk.Button(button_frame, text="🚀 LAUNCH", 
                                   command=self._launch, 
                                   font=("Arial", 12, "bold"),
                                   bg="#2ecc71", fg="white", 
                                   padx=30, pady=10, cursor="hand2")
        self.launch_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = tk.Button(button_frame, text="⏹ STOP", 
                            command=self._stop, 
                            font=("Arial", 12, "bold"),
                            bg="#e74c3c", fg="white", 
                            padx=30, pady=10, cursor="hand2")
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        help_btn = tk.Button(button_frame, text="❓ HELP", 
                            command=self._show_help, 
                            font=("Arial", 10),
                            bg="#3498db", fg="white", 
                            padx=20, pady=10, cursor="hand2")
        help_btn.pack(side=tk.RIGHT, padx=5)
        
        # Footer
        footer = tk.Frame(self.root, bg="#f0f0f0", height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        footer_text = tk.Label(footer, text="API: http://localhost:8000 | Docs: http://localhost:8000/docs", 
                              font=("Arial", 8), bg="#f0f0f0", fg="#666")
        footer_text.pack(pady=8)
    
    def _launch(self):
        """Launch selected mode"""
        if self.running:
            messagebox.showwarning("Already Running", "Project is already running!")
            return
        
        mode = self.mode_var.get()
        self.running = True
        self.launch_btn.config(state="disabled")
        self.progress.start()
        
        # Run in thread to not block UI
        thread = threading.Thread(target=self._run_mode, args=(mode,), daemon=True)
        thread.start()
    
    def _run_mode(self, mode):
        """Run selected mode"""
        try:
            self._update_status(f"Launching {mode} mode...")
            
            if mode == "simple":
                self._run_simple()
            elif mode == "multicam":
                self._run_multicam()
            elif mode == "docker":
                self._run_docker()
            elif mode == "analytics":
                self._run_analytics()
            
        except Exception as e:
            logger.error(f"Launch error: {e}")
            self._update_status(f"Error: {str(e)}")
            messagebox.showerror("Launch Error", f"Failed to launch: {str(e)}")
            self.running = False
            self.launch_btn.config(state="normal")
            self.progress.stop()
    
    def _run_simple(self):
        """Run simple single camera mode"""
        self._update_status("Starting single camera detection...")
        
        # Check dependencies
        if not self._check_dependencies():
            self._update_status("Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_v2.txt"], 
                          capture_output=True)
        
        self._update_status("Launching main application...")
        proc = subprocess.Popen([sys.executable, "main_v2.py"])
        self.processes.append(proc)
        
        self._update_status("✅ Application running! Check window.")
        time.sleep(2)
        self.progress.stop()
    
    def _run_multicam(self):
        """Run multi-camera mode with API"""
        self._update_status("Starting multi-camera system...")
        
        if not self._check_dependencies():
            self._update_status("Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_v2.txt"],
                          capture_output=True)
        
        self._update_status("Launching API server...")
        proc = subprocess.Popen([sys.executable, "phase4_multicamera.py"])
        self.processes.append(proc)
        
        self._update_status("✅ API running on http://localhost:8000")
        time.sleep(3)
        
        # Open API docs
        webbrowser.open("http://localhost:8000/docs")
        self._update_status("✅ Opened API documentation in browser")
        
        self.progress.stop()
    
    def _run_docker(self):
        """Run Docker deployment"""
        self._update_status("Checking Docker installation...")
        
        # Check if Docker is installed
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except:
            messagebox.showerror("Docker Not Found", 
                               "Docker is not installed. Please install Docker Desktop first.\n"
                               "https://www.docker.com/products/docker-desktop")
            self.running = False
            self.launch_btn.config(state="normal")
            self.progress.stop()
            return
        
        self._update_status("Building Docker image...")
        subprocess.run(["docker-compose", "up", "-d"], capture_output=True)
        
        self._update_status("✅ Docker containers running!")
        time.sleep(3)
        
        # Open services
        webbrowser.open("http://localhost:8000/docs")
        self._update_status("✅ Services available:\n  API: http://localhost:8000\n  UI: http://localhost:8501")
        
        self.progress.stop()
    
    def _run_analytics(self):
        """Run analytics and report generation"""
        self._update_status("Starting analytics engine...")
        
        if not self._check_dependencies():
            self._update_status("Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_v2.txt"],
                          capture_output=True)
        
        self._update_status("Generating reports...")
        proc = subprocess.Popen([sys.executable, "phase5_analytics.py"])
        self.processes.append(proc)
        
        self._update_status("✅ Analytics running! Check reports/ folder.")
        time.sleep(2)
        self.progress.stop()
    
    def _check_dependencies(self):
        """Check if all dependencies are installed"""
        try:
            import ultralytics
            import cv2
            import pandas
            return True
        except ImportError:
            return False
    
    def _update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
        self.root.update()
    
    def _stop(self):
        """Stop all running processes"""
        if not self.running:
            messagebox.showinfo("Not Running", "No processes running")
            return
        
        self._update_status("Stopping all processes...")
        
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        
        self.processes = []
        self.running = False
        self.launch_btn.config(state="normal")
        self.progress.stop()
        
        self._update_status("✅ All processes stopped")
        messagebox.showinfo("Stopped", "All processes have been stopped")
    
    def _show_help(self):
        """Show help dialog"""
        help_text = """
AI Detection System v4.0 - Launcher Help

MODES:
• Simple Mode: Single camera detection with GUI
• Multi-Camera: 4+ cameras with REST API
• Docker: Full stack with containers
• Analytics: Report generation only

REQUIREMENTS:
• Python 3.10+
• 4GB+ RAM
• GPU optional (CUDA/OpenVINO)

QUICK START:
1. Select a mode
2. Click LAUNCH
3. Wait for startup
4. Check status bar for URLs

API ENDPOINTS:
• Health: http://localhost:8000/api/health
• Cameras: http://localhost:8000/api/cameras
• Docs: http://localhost:8000/docs

SUPPORT:
• GitHub: https://github.com/bushrapopalzai/AI_Crowd_Detection_System
• Issues: Check GitHub issues page
• Logs: Check detection.log file

For more info, see README.md
        """
        messagebox.showinfo("Help", help_text)
    
    def run(self):
        """Run launcher"""
        self.root.mainloop()


if __name__ == "__main__":
    launcher = ProjectLauncher()
    launcher.run()
