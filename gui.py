"""
Jarvis GUI - A futuristic assistant interface
Built with tkinter - no extra dependencies beyond main.py requirements
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import datetime
import math
import time
import random

# ── Try importing Jarvis internals ──────────────────────────────────────────
try:
    import pyttsx3
    import speech_recognition as sr
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════
#  PALETTE & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════
BG          = "#050a12"
PANEL       = "#0b1220"
ACCENT      = "#00d4ff"
ACCENT2     = "#0066ff"
WARN        = "#ff6b35"
TEXT        = "#c8e6f0"
TEXT_DIM    = "#3a6070"
GREEN       = "#00ff9d"
RED         = "#ff3355"

FONT_MONO   = ("Courier New", 11)
FONT_TITLE  = ("Courier New", 22, "bold")
FONT_SUB    = ("Courier New", 10)
FONT_LOG    = ("Courier New", 10)
FONT_BTN    = ("Courier New", 11, "bold")


# ═══════════════════════════════════════════════════════════════════════════
#  ANIMATED RADAR CANVAS
# ═══════════════════════════════════════════════════════════════════════════
class RadarWidget(tk.Canvas):
    def __init__(self, parent, size=200, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, **kw)
        self.size   = size
        self.cx     = size // 2
        self.cy     = size // 2
        self.r      = size // 2 - 10
        self.angle  = 0
        self.active = False
        self.blips  = []   # list of (angle_deg, dist_frac, age)
        self._draw()
        self._tick()

    def _draw(self):
        self.delete("all")
        cx, cy, r = self.cx, self.cy, self.r

        # rings
        for i in range(1, 5):
            frac = i / 4
            self.create_oval(cx - r*frac, cy - r*frac,
                             cx + r*frac, cy + r*frac,
                             outline=TEXT_DIM, width=1)

        # cross-hairs
        self.create_line(cx - r, cy, cx + r, cy, fill=TEXT_DIM, width=1)
        self.create_line(cx, cy - r, cx, cy + r, fill=TEXT_DIM, width=1)

        # sweep gradient (arc segments)
        if self.active:
            for i in range(40, 0, -1):
                a_start = self.angle - i
                alpha   = int(180 * (1 - i / 40))
                color   = f"#{0:02x}{alpha:02x}{alpha // 2 + 80:02x}"
                self.create_arc(cx - r, cy - r, cx + r, cy + r,
                                start=a_start, extent=1.5,
                                outline="", fill=color, style=tk.PIESLICE)

        # sweep line
        rad = math.radians(self.angle)
        lx  = cx + r * math.cos(rad)
        ly  = cy - r * math.sin(rad)
        lcolor = ACCENT if self.active else TEXT_DIM
        self.create_line(cx, cy, lx, ly, fill=lcolor,
                         width=2 if self.active else 1)

        # blips
        for bangle, bdist, bage in self.blips:
            brad   = math.radians(bangle)
            bx     = cx + r * bdist * math.cos(brad)
            by     = cy - r * bdist * math.sin(brad)
            bright = max(0, 255 - bage * 15)
            bc     = f"#{0:02x}{bright:02x}{bright // 2:02x}"
            bs     = max(2, 5 - bage // 3)
            self.create_oval(bx - bs, by - bs, bx + bs, by + bs,
                             fill=bc, outline="")

        # center dot
        self.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                         fill=ACCENT, outline="")

    def _tick(self):
        self.angle = (self.angle + 2) % 360
        # age blips
        self.blips = [(a, d, age + 1)
                      for a, d, age in self.blips if age < 18]
        # random blip near sweep
        if self.active and random.random() < 0.08:
            self.blips.append((self.angle + random.uniform(-5, 5),
                               random.uniform(0.2, 0.95), 0))
        self._draw()
        self.after(30, self._tick)

    def set_active(self, state: bool):
        self.active = state


# ═══════════════════════════════════════════════════════════════════════════
#  SCROLLING LOG PANEL
# ═══════════════════════════════════════════════════════════════════════════
class LogPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self.text = tk.Text(self, bg=PANEL, fg=TEXT, font=FONT_LOG,
                            insertbackground=ACCENT, relief="flat",
                            borderwidth=0, state="disabled",
                            wrap="word", padx=8, pady=6)
        sb = tk.Scrollbar(self, orient="vertical",
                          command=self.text.yview,
                          bg=PANEL, troughcolor=BG,
                          activebackground=ACCENT, width=8)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        # tag colours
        self.text.tag_configure("jarvis", foreground=ACCENT)
        self.text.tag_configure("user",   foreground=GREEN)
        self.text.tag_configure("sys",    foreground=TEXT_DIM)
        self.text.tag_configure("error",  foreground=RED)
        self.text.tag_configure("warn",   foreground=WARN)

    def append(self, line: str, tag: str = "sys"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.text.configure(state="normal")
        self.text.insert("end", f"[{ts}] {line}\n", tag)
        self.text.see("end")
        self.text.configure(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════
#  PULSE BUTTON
# ═══════════════════════════════════════════════════════════════════════════
class PulseButton(tk.Canvas):
    """Circular animated button"""
    def __init__(self, parent, label="MIC", radius=48,
                 command=None, **kw):
        d = radius * 2 + 20
        super().__init__(parent, width=d, height=d,
                         bg=BG, highlightthickness=0, **kw)
        self.cx      = d // 2
        self.cy      = d // 2
        self.radius  = radius
        self.label   = label
        self.command = command
        self.pulsing = False
        self.pulse_r = 0
        self._render()
        self.bind("<Button-1>", self._click)
        self._pulse_tick()

    def _render(self):
        self.delete("all")
        cx, cy, r = self.cx, self.cy, self.radius
        color = RED if self.pulsing else ACCENT
        # outer glow
        if self.pulsing:
            self.create_oval(cx - self.pulse_r, cy - self.pulse_r,
                             cx + self.pulse_r, cy + self.pulse_r,
                             outline=color, width=1)
        # ring
        self.create_oval(cx - r - 4, cy - r - 4,
                         cx + r + 4, cy + r + 4,
                         outline=color, width=2)
        # fill
        fill = "#1a0005" if self.pulsing else "#001a22"
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         fill=fill, outline=color, width=2)
        # label
        lcolor = RED if self.pulsing else ACCENT
        self.create_text(cx, cy, text=self.label,
                         fill=lcolor, font=FONT_BTN)

    def _pulse_tick(self):
        if self.pulsing:
            self.pulse_r = (self.pulse_r + 2) % (self.radius + 30)
        else:
            self.pulse_r = self.radius + 4
        self._render()
        self.after(40, self._pulse_tick)

    def _click(self, _event):
        if self.command:
            self.command()

    def set_pulsing(self, state: bool):
        self.pulsing = state


# ═══════════════════════════════════════════════════════════════════════════
#  QUICK-ACTION BUTTON
# ═══════════════════════════════════════════════════════════════════════════
class ActionBtn(tk.Button):
    def __init__(self, parent, text, command, **kw):
        super().__init__(parent, text=text, command=command,
                         bg=PANEL, fg=ACCENT, font=FONT_BTN,
                         relief="flat", activebackground="#0d1f2d",
                         activeforeground=GREEN,
                         cursor="hand2", padx=10, pady=6,
                         highlightthickness=1,
                         highlightbackground=TEXT_DIM,
                         **kw)
        self.bind("<Enter>", lambda _: self.config(
            highlightbackground=ACCENT, fg=GREEN))
        self.bind("<Leave>", lambda _: self.config(
            highlightbackground=TEXT_DIM, fg=ACCENT))


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════
class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S  —  AI Assistant")
        self.root.configure(bg=BG)
        self.root.geometry("900x620")
        self.root.resizable(True, True)
        self.root.minsize(750, 520)

        self.listening = False
        self._build_ui()
        self._clock_tick()

        if TTS_AVAILABLE:
            self.engine = pyttsx3.init()
            self.log.append("Voice engine initialised.", "sys")
        else:
            self.log.append(
                "pyttsx3 / speech_recognition not found — text mode only.", "warn")

        self.log.append("JARVIS online. Welcome, Karan sir.", "jarvis")

    # ── Layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── TOP BAR ──
        topbar = tk.Frame(self.root, bg=BG, pady=6)
        topbar.pack(fill="x", padx=16)

        tk.Label(topbar, text="J.A.R.V.I.S", bg=BG,
                 fg=ACCENT, font=FONT_TITLE).pack(side="left")
        tk.Label(topbar, text="  JUST A RATHER VERY INTELLIGENT SYSTEM",
                 bg=BG, fg=TEXT_DIM, font=FONT_SUB).pack(side="left",
                                                         pady=(10, 0))

        self.clock_lbl = tk.Label(topbar, text="", bg=BG,
                                  fg=TEXT_DIM, font=FONT_MONO)
        self.clock_lbl.pack(side="right")

        # separator
        tk.Frame(self.root, bg=TEXT_DIM, height=1).pack(fill="x",
                                                         padx=16, pady=4)

        # ── MAIN BODY ──
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        # LEFT COLUMN
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 12))

        tk.Label(left, text="[ RADAR ]", bg=BG,
                 fg=TEXT_DIM, font=FONT_SUB).pack(anchor="w")
        self.radar = RadarWidget(left, size=200)
        self.radar.pack(pady=(4, 14))

        self.mic_btn = PulseButton(left, label="MIC",
                                   command=self._toggle_listen)
        self.mic_btn.pack(pady=(0, 14))

        # Quick actions
        tk.Label(left, text="[ QUICK ACTIONS ]", bg=BG,
                 fg=TEXT_DIM, font=FONT_SUB).pack(anchor="w")
        actions = [
            ("▶ YouTube",  self._open_youtube),
            ("🌐 Google",  self._open_google),
            ("📖 Wikipedia", self._open_wiki),
            ("💻 Desktop", self._open_desktop),
            ("⚡ CMD",     self._open_cmd),
        ]
        for label, cmd in actions:
            ActionBtn(left, label, cmd).pack(fill="x", pady=2)

        # RIGHT COLUMN
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        # Status bar
        status_row = tk.Frame(right, bg=BG)
        status_row.pack(fill="x", pady=(0, 6))
        tk.Label(status_row, text="[ SYSTEM LOG ]", bg=BG,
                 fg=TEXT_DIM, font=FONT_SUB).pack(side="left")
        self.status_dot = tk.Label(status_row, text="●  STANDBY",
                                   bg=BG, fg=TEXT_DIM, font=FONT_SUB)
        self.status_dot.pack(side="right")

        # Log panel
        self.log = LogPanel(right)
        self.log.pack(fill="both", expand=True)

        # ── INPUT ROW ──
        input_row = tk.Frame(right, bg=BG, pady=6)
        input_row.pack(fill="x")

        self.entry = tk.Entry(input_row, bg=PANEL, fg=TEXT,
                              insertbackground=ACCENT,
                              font=FONT_MONO, relief="flat",
                              highlightthickness=1,
                              highlightbackground=TEXT_DIM,
                              highlightcolor=ACCENT)
        self.entry.pack(side="left", fill="x", expand=True, ipady=6,
                        padx=(0, 8))
        self.entry.bind("<Return>", self._send_text)
        self.entry.insert(0, "Type a command…")
        self.entry.bind("<FocusIn>",
                        lambda _: self.entry.delete(0, "end")
                        if self.entry.get() == "Type a command…" else None)

        ActionBtn(input_row, "SEND", self._send_text).pack(side="left")

        # ── BOTTOM STATUS ──
        tk.Frame(self.root, bg=TEXT_DIM, height=1).pack(fill="x",
                                                         padx=16, pady=4)
        bottom = tk.Frame(self.root, bg=BG, pady=4)
        bottom.pack(fill="x", padx=16)
        tk.Label(bottom, text="JARVIS v2.0  |  Karan Sir's AI",
                 bg=BG, fg=TEXT_DIM, font=FONT_SUB).pack(side="left")
        tk.Label(bottom, text="BIT Mesra  |  MCA",
                 bg=BG, fg=TEXT_DIM, font=FONT_SUB).pack(side="right")

    # ── Clock ────────────────────────────────────────────────────────────
    def _clock_tick(self):
        now = datetime.datetime.now().strftime("%A  %d %b %Y   %H:%M:%S")
        self.clock_lbl.config(text=now)
        self.root.after(1000, self._clock_tick)

    # ── Mic toggle ───────────────────────────────────────────────────────
    def _toggle_listen(self):
        if self.listening:
            self._stop_listen()
        else:
            self._start_listen()

    def _start_listen(self):
        self.listening = True
        self.mic_btn.set_pulsing(True)
        self.radar.set_active(True)
        self.status_dot.config(text="●  LISTENING", fg=RED)
        self.log.append("Listening… speak now.", "jarvis")
        if TTS_AVAILABLE:
            threading.Thread(target=self._listen_thread, daemon=True).start()
        else:
            self.root.after(2000, self._stop_listen)

    def _stop_listen(self):
        self.listening = False
        self.mic_btn.set_pulsing(False)
        self.radar.set_active(False)
        self.status_dot.config(text="●  STANDBY", fg=TEXT_DIM)

    def _listen_thread(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.pause_threshold = 1
                audio = r.listen(source, timeout=5)
            query = r.recognize_google(audio, language="en-in")
            self.root.after(0, lambda: self._handle_command(query))
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.log.append(
                "No speech detected.", "warn"))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.log.append(
                "Could not understand audio.", "warn"))
        except Exception as ex:
            self.root.after(0, lambda: self.log.append(
                f"Error: {ex}", "error"))
        finally:
            self.root.after(0, self._stop_listen)

    # ── Text input ───────────────────────────────────────────────────────
    def _send_text(self, _event=None):
        cmd = self.entry.get().strip()
        if not cmd or cmd == "Type a command…":
            return
        self.entry.delete(0, "end")
        self._handle_command(cmd)

    # ── Command dispatcher ───────────────────────────────────────────────
    def _handle_command(self, query: str):
        self.log.append(f"You: {query}", "user")
        q = query.lower()

        if "youtube" in q:
            self._open_youtube()
        elif "google" in q:
            self._open_google()
        elif "wikipedia" in q:
            self._open_wiki()
        elif "desktop" in q:
            self._open_desktop()
        elif "cmd" in q or "command prompt" in q:
            self._open_cmd()
        elif "time" in q:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            self._speak(f"Sir, the current time is {t}")
        elif "date" in q:
            d = datetime.datetime.now().strftime("%A, %d %B %Y")
            self._speak(f"Today is {d}")
        elif "hello" in q or "hi" in q:
            self._speak("Hello Karan sir, how may I assist you?")
        elif "bye" in q or "exit" in q or "quit" in q:
            self._speak("Goodbye, Karan sir. Have a great day!")
            self.root.after(1200, self.root.destroy)
        else:
            self._speak(f"Processing: {query}")

    def _speak(self, msg: str):
        self.log.append(f"JARVIS: {msg}", "jarvis")
        if TTS_AVAILABLE:
            threading.Thread(
                target=lambda: self.engine.say(msg) or self.engine.runAndWait(),
                daemon=True).start()

    # ── Quick actions ────────────────────────────────────────────────────
    def _open_youtube(self):
        import webbrowser
        webbrowser.open("https://www.youtube.com/")
        self._speak("Opening YouTube, sir.")

    def _open_google(self):
        import webbrowser
        webbrowser.open("https://www.google.com/")
        self._speak("Opening Google, sir.")

    def _open_wiki(self):
        import webbrowser
        webbrowser.open("https://www.wikipedia.org/")
        self._speak("Opening Wikipedia, sir.")

    def _open_desktop(self):
        import os
        path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(path):
            os.startfile(path)
            self._speak("Opening Desktop, sir.")
        else:
            self.log.append("Desktop path not found.", "warn")

    def _open_cmd(self):
        import os
        os.system("start cmd")
        self._speak("Opening Command Prompt, sir.")

    # ── Run ──────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    JarvisGUI().run()
