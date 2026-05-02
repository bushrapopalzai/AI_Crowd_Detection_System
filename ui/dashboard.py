"""
Modern dashboard GUI — CustomTkinter dark theme.
Decoupled from detection: communicates only via queue + VideoProcessor.
"""

import logging
import queue
import threading
import time
import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox, ttk

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

from config import get
from core import get_model, VideoProcessor
from services import SQLiteDB

logger = logging.getLogger(__name__)

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    _CTK = True
except ImportError:
    _CTK = False
    logger.warning("customtkinter not found — falling back to ttk")

# ── Colour palette ────────────────────────────────────────────────────
C = {
    "bg":       "#1a1a2e",
    "panel":    "#16213e",
    "card":     "#0f3460",
    "accent":   "#e94560",
    "green":    "#00d4aa",
    "yellow":   "#f5a623",
    "text":     "#e0e0e0",
    "subtext":  "#8892a4",
    "border":   "#2a2a4a",
}


def _label(parent, text, size=11, color=None, bold=False, **kw):
    font = ("Segoe UI", size, "bold" if bold else "normal")
    fg = color or C["text"]
    if _CTK:
        return ctk.CTkLabel(parent, text=text, font=font, text_color=fg, **kw)
    return tk.Label(parent, text=text, font=font, fg=fg,
                    bg=parent.cget("bg") if hasattr(parent, "cget") else C["bg"], **kw)


def _button(parent, text, cmd, color=None, **kw):
    bg = color or C["accent"]
    if _CTK:
        return ctk.CTkButton(parent, text=text, command=cmd,
                             fg_color=bg, hover_color=C["card"],
                             font=("Segoe UI", 11, "bold"), **kw)
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=C["text"],
                     relief="flat", font=("Segoe UI", 11, "bold"), **kw)


def _frame(parent, **kw):
    if _CTK:
        return ctk.CTkFrame(parent, fg_color=C["panel"], **kw)
    return tk.Frame(parent, bg=C["panel"], **kw)


# ── Stat card widget ──────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, title: str, icon: str = ""):
        super().__init__(parent, bg=C["card"], padx=12, pady=8)
        tk.Label(self, text=f"{icon}  {title}", font=("Segoe UI", 9),
                 fg=C["subtext"], bg=C["card"]).pack(anchor="w")
        self._var = tk.StringVar(value="—")
        tk.Label(self, textvariable=self._var, font=("Segoe UI", 22, "bold"),
                 fg=C["green"], bg=C["card"]).pack(anchor="w")

    def set(self, value: str) -> None:
        self._var.set(value)


# ── Alert badge ───────────────────────────────────────────────────────
class AlertBadge(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["panel"])
        self._text = tk.StringVar(value="No alerts")
        tk.Label(self, textvariable=self._text, font=("Segoe UI", 9),
                 fg=C["yellow"], bg=C["panel"], wraplength=300, justify="left").pack(anchor="w")

    def push(self, msg: str) -> None:
        self._text.set(f"⚠  {msg}")


# ── Main dashboard ────────────────────────────────────────────────────
class Dashboard:
    def __init__(self):
        self.root = ctk.CTk() if _CTK else tk.Tk()
        self.root.title("AI Crowd Detection System v4.0")
        w = get("ui", "window_width", 1600)
        h = get("ui", "window_height", 960)
        self.root.geometry(f"{w}x{h}")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1200, 700)

        self.db = SQLiteDB()
        self.model = get_model()

        self._frame_buf: queue.Queue = queue.Queue(maxsize=get("performance", "frame_buffer_size", 5))
        self._stop = threading.Event()
        self._proc: VideoProcessor | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._history: deque = deque(maxlen=300)
        self._session_id: int = int(time.time())
        self._chart_update_ms: int = get("ui", "chart_update_ms", 2000)

        self._build_layout()
        self._schedule_updates()

    # ── Layout ────────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_statusbar()

    def _build_header(self) -> None:
        hdr = tk.Frame(self.root, bg=C["panel"], height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        tk.Label(hdr, text="🎯  AI Crowd Detection System",
                 font=("Segoe UI", 16, "bold"), fg=C["accent"], bg=C["panel"]
                 ).pack(side="left", padx=20, pady=10)

        # Camera controls on the right
        ctrl = tk.Frame(hdr, bg=C["panel"])
        ctrl.pack(side="right", padx=16)

        self._btn_cam = _button(ctrl, "📷  Start Camera", self._start_camera, color=C["green"])
        self._btn_cam.pack(side="left", padx=4)

        self._btn_vid = _button(ctrl, "📁  Open Video", self._open_video)
        self._btn_vid.pack(side="left", padx=4)

        self._btn_stop = _button(ctrl, "⏹  Stop", self._stop_detection, color="#555")
        self._btn_stop.pack(side="left", padx=4)
        self._btn_stop.configure(state="disabled")

    def _build_body(self) -> None:
        body = tk.Frame(self.root, bg=C["bg"])
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        body.grid_rowconfigure(1, weight=1)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)

        # ── Stat cards row ────────────────────────────────────────────
        cards_row = tk.Frame(body, bg=C["bg"])
        cards_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        for i in range(5):
            cards_row.grid_columnconfigure(i, weight=1)

        self._card_status  = StatCard(cards_row, "Status",     "🔴")
        self._card_fps     = StatCard(cards_row, "FPS",        "⚡")
        self._card_frames  = StatCard(cards_row, "Frames",     "🎞")
        self._card_dets    = StatCard(cards_row, "Detections", "👁")
        self._card_conf    = StatCard(cards_row, "Avg Conf",   "📊")

        for i, card in enumerate([self._card_status, self._card_fps,
                                   self._card_frames, self._card_dets, self._card_conf]):
            card.grid(row=0, column=i, sticky="ew", padx=4)

        # ── Video feed ────────────────────────────────────────────────
        feed_frame = tk.Frame(body, bg=C["panel"], bd=1, relief="flat")
        feed_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        feed_frame.grid_rowconfigure(0, weight=1)
        feed_frame.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(feed_frame, bg="#0a0a1a", highlightthickness=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._canvas.create_text(400, 300, text="▶  Start Camera or Open Video",
                                  fill=C["subtext"], font=("Segoe UI", 14), tags="placeholder")

        # ── Right panel ───────────────────────────────────────────────
        right = tk.Frame(body, bg=C["bg"])
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=2)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_charts(right)
        self._build_side_panel(right)

    def _build_charts(self, parent) -> None:
        chart_frame = tk.Frame(parent, bg=C["panel"])
        chart_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 4))

        plt.style.use("dark_background")
        self._fig, ((self._ax1, self._ax2), (self._ax3, self._ax4)) = plt.subplots(
            2, 2, figsize=(5, 5), facecolor=C["panel"]
        )
        self._fig.tight_layout(pad=2.5)
        for ax in (self._ax1, self._ax2, self._ax3, self._ax4):
            ax.set_facecolor(C["bg"])

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, chart_frame)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_side_panel(self, parent) -> None:
        side = tk.Frame(parent, bg=C["panel"], padx=10, pady=8)
        side.grid(row=1, column=0, sticky="nsew")

        tk.Label(side, text="Recent Alerts", font=("Segoe UI", 10, "bold"),
                 fg=C["accent"], bg=C["panel"]).pack(anchor="w")

        self._alert_badge = AlertBadge(side)
        self._alert_badge.pack(fill="x", pady=4)

        tk.Frame(side, bg=C["border"], height=1).pack(fill="x", pady=6)

        # Export buttons
        tk.Label(side, text="Export", font=("Segoe UI", 10, "bold"),
                 fg=C["accent"], bg=C["panel"]).pack(anchor="w")

        _button(side, "📊  Export CSV", self._export_csv, color=C["card"]).pack(fill="x", pady=2)
        _button(side, "📄  Export PDF", self._export_pdf, color=C["card"]).pack(fill="x", pady=2)

    def _build_statusbar(self) -> None:
        bar = tk.Frame(self.root, bg=C["panel"], height=24)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self._status_var, font=("Segoe UI", 9),
                 fg=C["subtext"], bg=C["panel"]).pack(side="left", padx=12)

    # ── Detection control ─────────────────────────────────────────────
    def _start_camera(self) -> None:
        self._start(0, "camera")

    def _open_video(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv")]
        )
        if path:
            self._start(path, "file")

    def _start(self, src, src_type: str) -> None:
        if self._proc and self._proc.is_alive():
            return
        self._stop.clear()
        self._history.clear()
        self._session_id = int(time.time())

        self._proc = VideoProcessor(
            self.model, self._frame_buf, self._stop,
            self.db, self._session_id, src_type, src
        )
        self._proc.start()

        self._btn_cam.configure(state="disabled")
        self._btn_vid.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._card_status.set("🟢 Live")
        self._status_var.set(f"Detecting — source: {src}")
        self._canvas.delete("placeholder")

    def _stop_detection(self) -> None:
        self._stop.set()
        self._btn_cam.configure(state="normal")
        self._btn_vid.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        self._card_status.set("⚫ Idle")
        self._status_var.set("Stopped")

    # ── Update loops ──────────────────────────────────────────────────
    def _schedule_updates(self) -> None:
        self._tick_frame()
        self._tick_stats()
        self._tick_charts()

    def _tick_frame(self) -> None:
        try:
            frame, dets, fps, _ = self._frame_buf.get_nowait()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)

            cw = self._canvas.winfo_width() or 800
            ch = self._canvas.winfo_height() or 600
            img.thumbnail((cw, ch), Image.LANCZOS)

            self._photo = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor="center")
            self._history.append({"fps": fps, "dets": len(dets)})
        except queue.Empty:
            pass
        self.root.after(30, self._tick_frame)  # ~33 fps UI cap

    def _tick_stats(self) -> None:
        if self._proc:
            self._card_frames.set(str(self._proc.frame_count))
            self._card_dets.set(str(self._proc.total_dets))
            if self._proc.confs:
                avg = sum(self._proc.confs[-50:]) / min(len(self._proc.confs), 50)
                self._card_conf.set(f"{avg:.2f}")
            if self._history:
                self._card_fps.set(f"{self._history[-1]['fps']:.1f}")
        self.root.after(800, self._tick_stats)

    def _tick_charts(self) -> None:
        self._redraw_charts()
        self.root.after(self._chart_update_ms, self._tick_charts)

    def _redraw_charts(self) -> None:
        try:
            for ax in (self._ax1, self._ax2, self._ax3, self._ax4):
                ax.clear()
                ax.set_facecolor(C["bg"])

            if len(self._history) > 1:
                xs = list(range(len(self._history)))
                dets = [h["dets"] for h in self._history]
                fps_vals = [h["fps"] for h in self._history]

                # Chart 1 — detections timeline
                self._ax1.plot(xs, dets, color=C["accent"], linewidth=1.5)
                self._ax1.fill_between(xs, dets, alpha=0.2, color=C["accent"])
                self._ax1.set_title("Detections / Frame", color=C["text"], fontsize=8)
                self._ax1.tick_params(colors=C["subtext"], labelsize=7)

                # Chart 2 — FPS timeline
                self._ax2.plot(xs, fps_vals, color=C["green"], linewidth=1.5)
                self._ax2.axhline(30, color=C["yellow"], linestyle="--", linewidth=0.8, alpha=0.6)
                self._ax2.set_title("FPS", color=C["text"], fontsize=8)
                self._ax2.tick_params(colors=C["subtext"], labelsize=7)

            # Charts 3 & 4 — DB-backed, only refresh every other cycle
            if self._proc:
                df = self.db.read_all()
                if not df.empty:
                    # Chart 3 — class distribution
                    top = df["class_name"].value_counts().head(8)
                    self._ax3.barh(top.index.tolist(), top.values.tolist(), color=C["card"])
                    self._ax3.set_title("Top Classes", color=C["text"], fontsize=8)
                    self._ax3.tick_params(colors=C["subtext"], labelsize=7)

                    # Chart 4 — confidence histogram
                    self._ax4.hist(df["confidence"], bins=15, color=C["accent"],
                                   alpha=0.75, edgecolor=C["bg"])
                    self._ax4.set_title("Confidence Dist.", color=C["text"], fontsize=8)
                    self._ax4.tick_params(colors=C["subtext"], labelsize=7)

            self._fig.tight_layout(pad=2.0)
            self._mpl_canvas.draw_idle()
        except Exception:
            logger.exception("Chart render error")

    # ── Export ────────────────────────────────────────────────────────
    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            n = self.db.export_csv(path)
            self._alert_badge.push(f"CSV exported — {n} rows")
            messagebox.showinfo("Export", f"Exported {n} records to CSV")
        except Exception:
            logger.exception("CSV export failed")
            messagebox.showerror("Export Error", "CSV export failed — see log")

    def _export_pdf(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
            from reportlab.lib.styles import getSampleStyleSheet

            doc = SimpleDocTemplate(path, pagesize=letter)
            styles = getSampleStyleSheet()
            elems = [Paragraph("AI Detection Report", styles["Heading1"]), Spacer(1, 12)]

            df = self.db.read_all()
            if not df.empty:
                data = [
                    ["Metric", "Value"],
                    ["Total Detections", str(len(df))],
                    ["Unique Classes", str(df["class_name"].nunique())],
                    ["Avg Confidence", f"{df['confidence'].mean():.3f}"],
                    ["Date Range", f"{df['date'].min()} → {df['date'].max()}"],
                ]
                elems.append(Table(data))
            doc.build(elems)
            self._alert_badge.push("PDF exported")
            messagebox.showinfo("Export", "PDF exported successfully")
        except ImportError:
            messagebox.showerror("Missing dep", "Install reportlab: pip install reportlab")
        except Exception:
            logger.exception("PDF export failed")
            messagebox.showerror("Export Error", "PDF export failed — see log")

    # ── Lifecycle ─────────────────────────────────────────────────────
    def _on_close(self) -> None:
        self._stop.set()
        if self._proc and self._proc.is_alive():
            self._proc.join(timeout=3)
        self.db.flush()
        self.root.destroy()

    def run(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
