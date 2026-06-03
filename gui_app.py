import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import sys
import os
import time
import requests
import qrcode
from PIL import Image, ImageTk
from datetime import datetime
from dotenv import load_dotenv

# Load .env
load_dotenv()

# ============================================================
# CONSTANTS
# ============================================================
WA_BOT_PORT = os.getenv("WA_BOT_PORT", "3000")
WA_TARGET_NUMBER = os.getenv("WA_TARGET_NUMBER", "628xxxxxxxxx@c.us")
DEFAULT_INTERVAL = 60  # seconds

# Colors — dark premium palette
BG_DARK = "#1a1b2e"
BG_CARD = "#232442"
BG_INPUT = "#2d2e56"
FG_TEXT = "#e0e0ff"
FG_DIM = "#8888aa"
FG_ACCENT = "#7c6aff"
FG_ACCENT_HOVER = "#9a8aff"
GREEN = "#4ade80"
RED = "#f87171"
ORANGE = "#fb923c"
BORDER = "#3a3b6e"


class SolverGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Screenshot Gemini Solver")
        self.root.geometry("800x850")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        self.root.minsize(700, 750)

        # State
        self.is_running = False
        self.wa_process: subprocess.Popen | None = None
        self.solver_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.wa_connected = False
        self.qr_image = None
        self.last_qr = None

        # Styles
        self._setup_styles()

        # UI
        self._build_ui()

        # Start WA status polling
        self._poll_wa_status()

        # Graceful close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Styles ─────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("Dark.TFrame", background=BG_DARK)

        style.configure(
            "Title.TLabel",
            background=BG_DARK,
            foreground=FG_ACCENT,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=BG_DARK,
            foreground=FG_DIM,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Card.TLabel",
            background=BG_CARD,
            foreground=FG_TEXT,
            font=("Segoe UI", 10),
        )
        style.configure(
            "SectionTitle.TLabel",
            background=BG_DARK,
            foreground=FG_TEXT,
            font=("Segoe UI", 11, "bold"),
        )

        # Buttons
        style.configure(
            "Start.TButton",
            background="#22c55e",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=(20, 10),
        )
        style.map("Start.TButton", background=[("active", "#16a34a")])

        style.configure(
            "Stop.TButton",
            background="#ef4444",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            padding=(20, 10),
        )
        style.map("Stop.TButton", background=[("active", "#dc2626")])

    # ── UI Build ───────────────────────────────────────────
    def _build_ui(self):
        # Main container
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # ─── Top Section (Header & Info) ───
        header = tk.Frame(main, bg=BG_DARK)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="⚡ Screenshot Gemini Solver", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Automation control panel — Screenshot → Gemini AI → WhatsApp", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 12))

        # ─── Middle Section (Settings & QR) ───
        middle = tk.Frame(main, bg=BG_DARK)
        middle.pack(fill=tk.BOTH, pady=8)

        # Left Column: Settings
        left_col = tk.Frame(middle, bg=BG_DARK)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Status Bar
        status_frame = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        status_inner = tk.Frame(status_frame, bg=BG_CARD)
        status_inner.pack(fill=tk.X, padx=14, pady=10)

        prog_frame = tk.Frame(status_inner, bg=BG_CARD)
        prog_frame.pack(side=tk.LEFT)
        tk.Label(prog_frame, text="Program:", bg=BG_CARD, fg=FG_DIM, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.lbl_program_status = tk.Label(prog_frame, text="⏹ STOPPED", bg=BG_CARD, fg=RED, font=("Segoe UI", 10, "bold"))
        self.lbl_program_status.pack(side=tk.LEFT, padx=(6, 0))

        wa_frame = tk.Frame(status_inner, bg=BG_CARD)
        wa_frame.pack(side=tk.RIGHT)
        tk.Label(wa_frame, text="WhatsApp:", bg=BG_CARD, fg=FG_DIM, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.lbl_wa_status = tk.Label(wa_frame, text="🔴 Disconnected", bg=BG_CARD, fg=RED, font=("Segoe UI", 10, "bold"))
        self.lbl_wa_status.pack(side=tk.LEFT, padx=(6, 0))

        # Settings
        ttk.Label(left_col, text="⚙ Pengaturan", style="SectionTitle.TLabel").pack(anchor="w", pady=(4, 4))
        settings_frame = tk.Frame(left_col, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        settings_inner = tk.Frame(settings_frame, bg=BG_CARD)
        settings_inner.pack(fill=tk.X, padx=14, pady=12)

        tk.Label(settings_inner, text="Nomor WhatsApp:", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 10), anchor="w").pack(fill=tk.X)
        self.entry_number = tk.Entry(settings_inner, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 11), relief="flat", highlightthickness=1, highlightbackground=BORDER, highlightcolor=FG_ACCENT)
        self.entry_number.pack(fill=tk.X, pady=(4, 10), ipady=4)
        self.entry_number.insert(0, WA_TARGET_NUMBER)

        tk.Label(settings_inner, text="Durasi Screenshot (detik):", bg=BG_CARD, fg=FG_TEXT, font=("Segoe UI", 10), anchor="w").pack(fill=tk.X)
        self.entry_interval = tk.Entry(settings_inner, bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_TEXT, font=("Consolas", 11), relief="flat", highlightthickness=1, highlightbackground=BORDER, highlightcolor=FG_ACCENT)
        self.entry_interval.pack(fill=tk.X, pady=(4, 0), ipady=4)
        self.entry_interval.insert(0, str(DEFAULT_INTERVAL))

        # Right Column: QR Code Display
        right_col = tk.Frame(middle, bg=BG_DARK)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))

        ttk.Label(right_col, text="📱 WhatsApp Login", style="SectionTitle.TLabel").pack(anchor="w", pady=(4, 4))
        self.qr_frame = tk.Frame(right_col, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, width=220, height=220)
        self.qr_frame.pack_propagate(False)
        self.qr_frame.pack(fill=tk.Y)
        
        self.qr_canvas = tk.Label(self.qr_frame, bg=BG_CARD, text="Menunggu bot...", fg=FG_DIM)
        self.qr_canvas.pack(expand=True, fill=tk.BOTH)

        # ─── Control Buttons ───
        btn_frame = tk.Frame(main, bg=BG_DARK)
        btn_frame.pack(fill=tk.X, pady=(0, 12))

        self.btn_start = ttk.Button(btn_frame, text="▶  MULAI PROGRAM", style="Start.TButton", command=self._start)
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.btn_stop = ttk.Button(btn_frame, text="■  BERHENTI", style="Stop.TButton", command=self._stop, state="disabled")
        self.btn_stop.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

        # ─── Answer Area ───
        ttk.Label(main, text="📄 Jawaban Gemini Terakhir", style="SectionTitle.TLabel").pack(anchor="w", pady=(4, 4))
        answer_frame = tk.Frame(main, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        answer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.txt_answer = scrolledtext.ScrolledText(answer_frame, bg=BG_INPUT, fg=FG_TEXT, font=("Consolas", 10), relief="flat", wrap=tk.WORD, height=6, state="disabled")
        self.txt_answer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ─── Log Console ───
        ttk.Label(main, text="📋 Log Console", style="SectionTitle.TLabel").pack(anchor="w", pady=(4, 4))
        log_frame = tk.Frame(main, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.txt_log = scrolledtext.ScrolledText(log_frame, bg="#111122", fg="#aaaacc", font=("Consolas", 9), relief="flat", wrap=tk.WORD, height=6, state="disabled")
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.txt_log.tag_configure("stdout", foreground="#aaaacc")
        self.txt_log.tag_configure("stderr", foreground=RED)
        self.txt_log.tag_configure("info", foreground=GREEN)
        self.txt_log.tag_configure("wa", foreground=ORANGE)

    def _log(self, message, tag="stdout"):
        self.txt_log.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.txt_log.see(tk.END)
        self.txt_log.configure(state="disabled")

    def _set_answer(self, text):
        self.txt_answer.configure(state="normal")
        self.txt_answer.delete("1.0", tk.END)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.txt_answer.insert(tk.END, f"[{timestamp}]\n\n{text}")
        self.txt_answer.see("1.0")
        self.txt_answer.configure(state="disabled")

    # ── WA Status & QR Polling ─────────────────────────────
    def _poll_wa_status(self):
        def check():
            try:
                r = requests.get(f"http://localhost:{WA_BOT_PORT}/status", timeout=2)
                data = r.json()
                connected = data.get("connected", False)
                qr_content = data.get("qr")

                # Update Status Text
                if connected:
                    self.wa_connected = True
                    self.root.after(0, lambda: self.lbl_wa_status.config(text="🟢 Connected", fg=GREEN))
                    self.root.after(0, lambda: self.qr_canvas.config(text="✓ TERHUBUNG", image="", fg=GREEN))
                else:
                    self.wa_connected = False
                    self.root.after(0, lambda: self.lbl_wa_status.config(text="🟡 Waiting Scan...", fg=ORANGE))
                    
                    # Update QR Image if exists
                    if qr_content and qr_content != self.last_qr:
                        self.last_qr = qr_content
                        self._generate_qr_image(qr_content)

            except Exception:
                self.wa_connected = False
                self.root.after(0, lambda: self.lbl_wa_status.config(text="🔴 Disconnected", fg=RED))
                self.root.after(0, lambda: self.qr_canvas.config(text="Menunggu bot...", image="", fg=FG_DIM))

        threading.Thread(target=check, daemon=True).start()
        self.root.after(4000, self._poll_wa_status)

    def _generate_qr_image(self, content):
        """Generate and display QR code image."""
        try:
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.qr_image = photo  # keep reference
            self.root.after(0, lambda: self.qr_canvas.config(image=self.qr_image, text=""))
        except Exception as e:
            print(f"Error generating QR image: {e}")

    # ── Start / Stop ───────────────────────────────────────
    def _start(self):
        if self.is_running: return
        self.is_running = True
        self.stop_event.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_program_status.config(text="▶ RUNNING", fg=GREEN)
        self._log("Program dimulai...", "info")
        self._start_wa_bot()
        self.root.after(4000, self._start_solver_loop)

    def _start_wa_bot(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self._log("Menjalankan WhatsApp Bot Service...", "wa")
            self.wa_process = subprocess.Popen(
                ["node", "wa_bot.js"], cwd=script_dir,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            def read_output():
                for line in self.wa_process.stdout:
                    if line.strip(): self.root.after(0, self._log, line.strip(), "wa")
            threading.Thread(target=read_output, daemon=True).start()
        except Exception as e:
            self._log(f"Gagal memulai WA Bot: {e}", "stderr")

    def _start_solver_loop(self):
        def loop():
            while not self.stop_event.is_set():
                try:
                    num = self.entry_number.get().strip()
                    self._log_safe("Mengambil screenshot & memproses ke Gemini AI...", "info")
                    
                    from solver_bot import run_once
                    ans = run_once(target_number=num)
                    
                    if ans:
                        self.root.after(0, self._set_answer, ans)
                        self._log_safe("Jawaban terkirim ke WhatsApp.", "info")
                    else:
                        # Di sini biasanya terjadi error 403 / API Key
                        self._log_safe("Gagal mendapatkan jawaban (Cek API Key atau koneksi).", "stderr")

                except Exception as e:
                    err_msg = str(e)
                    self._log_safe(f"Error: {err_msg}", "stderr")
                    
                    # Deteksi spesifik API Key Invalid (400) atau Leaked (403)
                    is_api_err = "403" in err_msg or "leaked" in err_msg.lower() or "400" in err_msg or "API_KEY_INVALID" in err_msg
                    
                    if is_api_err:
                        self.root.after(0, lambda: messagebox.showerror("API Key Error", 
                            "API Key Gemini Anda tidak valid (Invalid) atau diblokir (Leaked).\n\n"
                            "Harap periksa file .env dan pastikan API Key sudah benar.\n"
                            "Anda bisa mendapatkan key baru di: https://aistudio.google.com/app/apikey"))
                        self.root.after(0, self._stop)
                        break

                try:
                    sec = int(self.entry_interval.get().strip())
                except:
                    sec = DEFAULT_INTERVAL
                
                self._log_safe(f"Menunggu {sec} detik...", "stdout")
                if self.stop_event.wait(timeout=sec): break
        
        self.solver_thread = threading.Thread(target=loop, daemon=True)
        self.solver_thread.start()

    def _log_safe(self, m, t="stdout"):
        self.root.after(0, self._log, m, t)

    def _stop(self):
        self.is_running = False
        self.stop_event.set()
        if self.wa_process:
            self.wa_process.terminate()
            self.wa_process = None
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_program_status.config(text="⏹ STOPPED", fg=RED)
        self._log("Program dihentikan.", "info")

    def _on_close(self):
        self._stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SolverGUI(root)
    root.mainloop()

