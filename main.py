import tkinter as tk
from tkinter import font as tkfont
import threading
import datetime
import math
import time
import random
import os
import pywhatkit as k
from tkinter import simpledialog
import webbrowser
import requests
import re


# ── API SECTION ──────────────────────────────────────────
OWM_API_KEY       = "YOUR API"
GROQ_API_KEY      = "YOUR API"      
DEFAULT_CITY      = "Jaipur"

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
        self.blips  = []   
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
#  JARVIS KNOWLEDGE BASE  (fed to the chatbot as system context)
# ═══════════════════════════════════════════════════════════════════════════
JARVIS_SYSTEM_PROMPT = """
You are JARVIS (Just A Rather Very Intelligent System), a smart desktop AI assistant 
built with Python + Tkinter by Anish  (MCA student at BIT Mesra).

You can:
1. Answer general knowledge questions (history, science, current affairs, etc.)
2. Help with coding, math, and logic problems.
3. Explain what JARVIS the desktop app can and cannot do.
4. Have casual conversations.

Be concise (1-4 sentences), friendly, and slightly formal like the JARVIS from Iron Man.
Always address the user as "sir"
""".strip()


def _call_groq_api(messages: list) -> str:
    """Blocking call to Groq /openai/v1/chat/completions. Returns assistant text."""
    full_messages = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}] + messages

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 512,
                "messages": full_messages,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        return f"[API error {e.response.status_code}] {e.response.text[:200]}"
    except Exception as ex:
        return f"[Error] {ex}"

# ═══════════════════════════════════════════════════════════════════════════
#  MINI CHATBOT WINDOW
# ═══════════════════════════════════════════════════════════════════════════
class ChatbotWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Friday  —  AI Chatbot")
        self.configure(bg=BG)
        self.geometry("520x560")
        self.resizable(True, True)
        self.minsize(400, 400)
        self._history = []   # list of {"role": ..., "content": ...}
        self._build()

    def _build(self):
        # ── header ──
        hdr = tk.Frame(self, bg=BG, pady=6)
        hdr.pack(fill="x", padx=14)
        tk.Label(hdr, text="🤖  FRIDAY", bg=BG,
                 fg=ACCENT, font=("Courier New", 14, "bold")).pack(side="left")
        tk.Label(hdr, text="  Ask me anything about JARVIS",
                 bg=BG, fg=TEXT_DIM, font=FONT_SUB).pack(side="left", pady=(6, 0))

        tk.Frame(self, bg=TEXT_DIM, height=1).pack(fill="x", padx=14, pady=4)

        # ── chat display ──
        chat_frame = tk.Frame(self, bg=PANEL)
        chat_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        self._chat = tk.Text(chat_frame, bg=PANEL, fg=TEXT, font=FONT_LOG,
                             relief="flat", borderwidth=0, state="disabled",
                             wrap="word", padx=10, pady=8)
        sb = tk.Scrollbar(chat_frame, orient="vertical",
                          command=self._chat.yview,
                          bg=PANEL, troughcolor=BG,
                          activebackground=ACCENT, width=8)
        self._chat.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._chat.pack(side="left", fill="both", expand=True)

        self._chat.tag_configure("user",      foreground=GREEN)
        self._chat.tag_configure("assistant", foreground=ACCENT)
        self._chat.tag_configure("thinking",  foreground=TEXT_DIM)
        self._chat.tag_configure("error",     foreground=RED)

        # ── input row ──
        input_row = tk.Frame(self, bg=BG, pady=6)
        input_row.pack(fill="x", padx=14)

        self._entry = tk.Entry(input_row, bg=PANEL, fg=TEXT,
                               insertbackground=ACCENT,
                               font=FONT_MONO, relief="flat",
                               highlightthickness=1,
                               highlightbackground=TEXT_DIM,
                               highlightcolor=ACCENT)
        self._entry.pack(side="left", fill="x", expand=True, ipady=6,
                         padx=(0, 8))
        self._entry.bind("<Return>", self._send)
        self._entry.insert(0, "Ask about FRIDAY")
        self._entry.bind("<FocusIn>",
                         lambda _: self._entry.delete(0, "end")
                         if self._entry.get() == "Ask about JARVIS…" else None)

        ActionBtn(input_row, "ASK", self._send).pack(side="left")

        # welcome message
        self._append("FRIDAY",
                     "Hello, sir! I'm here to answer any questions about general knowledg and coding logic",
                     "assistant")

    # ── helpers ─────────────────────────────────────────────────────────
    def _append(self, who: str, text: str, tag: str):
        self._chat.configure(state="normal")
        self._chat.insert("end", f"{who}: ", tag)
        self._chat.insert("end", f"{text}\n\n", "sys" if tag == "thinking" else tag)
        self._chat.see("end")
        self._chat.configure(state="disabled")

    def _send(self, _event=None):
        q = self._entry.get().strip()
        if not q or q == "Ask about JARVIS…":
            return
        self._entry.delete(0, "end")
        self._append("You", q, "user")
        self._history.append({"role": "user", "content": q})

        # show thinking indicator
        self._append("JARVIS", "thinking…", "thinking")

        # call API in background thread
        threading.Thread(target=self._fetch_reply, daemon=True).start()

    def _fetch_reply(self):
        reply = _call_groq_api(list(self._history))
        self._history.append({"role": "assistant", "content": reply})
        self.after(0, self._show_reply, reply)

    def _show_reply(self, reply: str):
        # remove the "thinking…" line
        self._chat.configure(state="normal")
        content = self._chat.get("1.0", "end")
        thinking_marker = "JARVIS: thinking…\n\n"
        idx = content.rfind(thinking_marker)
        if idx != -1:
            start = f"1.0 + {idx} chars"
            end   = f"1.0 + {idx + len(thinking_marker)} chars"
            self._chat.delete(start, end)
        self._chat.configure(state="disabled")

        self._append("FRIDAY", reply, "assistant")


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
            self._speech_queue = []
            self._speaking = False
            self.log.append("Voice engine initialised.", "sys")
        else:
            self.log.append(
                "pyttsx3 / speech_recognition not found — text mode only.", "warn")
        self.root.after(500, self._wish)

        self.root.after(1000, lambda: threading.Thread(target=self._fetch_weather, daemon=True).start())

        #self.log.append("JARVIS online. Welcome, Karan sir.", "jarvis")

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
            ("▶ YouTube",    self._open_youtube),
            ("🌐 Google",    self._open_google),
            ("📖 Wikipedia", self._open_wiki),
            ("💻 Desktop",   self._open_desktop),
            ("⚡ CMD",       self._open_cmd),
            ("🤖 Chatbot",   self._open_chatbot),
        ]
        for label, cmd in actions:
            ActionBtn(left, label, cmd).pack(fill="x", pady=2)

        # RIGHT COLUMN
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        weather_row = tk.Frame(right, bg=PANEL, pady=6, padx=10)
        weather_row.pack(fill="x", pady=(0, 8))

        tk.Label(weather_row, text="[ WEATHER ]", bg=PANEL,
            fg=TEXT_DIM, font=FONT_SUB).pack(anchor="w")

        weather_inner = tk.Frame(weather_row, bg=PANEL)
        weather_inner.pack(fill="x")

        self.weather_city_lbl = tk.Label(weather_inner, text="📍 --",
                                  bg=PANEL, fg=ACCENT, font=FONT_MONO)
        self.weather_city_lbl.pack(side="left")

        self.weather_temp_lbl = tk.Label(weather_inner, text="🌡 --°C",
                                  bg=PANEL, fg=GREEN, font=FONT_BTN)
        self.weather_temp_lbl.pack(side="left", padx=(16, 0))

        self.weather_desc_lbl = tk.Label(weather_inner, text="☁ --",
                                  bg=PANEL, fg=TEXT, font=FONT_SUB)
        self.weather_desc_lbl.pack(side="left", padx=(16, 0))

        self.weather_humidity_lbl = tk.Label(weather_inner, text="💧 --%",
                                      bg=PANEL, fg=TEXT_DIM, font=FONT_SUB)
        self.weather_humidity_lbl.pack(side="right")

        tk.Button(weather_row, text="⟳ Refresh", bg=PANEL, fg=TEXT_DIM,
                font=FONT_SUB, relief="flat", cursor="hand2",
                activebackground=PANEL, activeforeground=ACCENT,
                command=lambda: threading.Thread(
                    target=self._fetch_weather, daemon=True).start()
                ).pack(anchor="e")

        # ── COMMUNICATOR PANEL ──
        comm_row = tk.Frame(right, bg=PANEL, pady=6, padx=10)
        comm_row.pack(fill="x", pady=(0, 8))

        tk.Label(comm_row, text="[ COMMUNICATOR ]", bg=PANEL,
                 fg=TEXT_DIM, font=FONT_SUB).pack(anchor="w")


        
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
        tk.Label(bottom, text="JARVIS v2.0  |  Anish Sir's AI",
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
    
    def _wish(self):
        hour = datetime.datetime.now().hour

        if 0 <= hour < 12:
            self._speak("Good morning,sir.")
        elif 12 <= hour < 15:
            self._speak("Good afternoon,sir.")
        elif 15 <= hour < 19:
            self._speak("Good evening,sir.")
        else:
            self._speak("Good night,sir.")

        self._speak("I am JARVIS, sir. Please tell me how can I help you.")

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
    # ── Wather function ───────────────────────────────────────────────────────
    def _fetch_weather(self, city: str = None):
        city = city or DEFAULT_CITY
        try:
            url = (f"https://api.openweathermap.org/data/2.5/weather"
                   f"?q={city}&appid={OWM_API_KEY}&units=metric")
            res = requests.get(url, timeout=5).json()

            if res.get("cod") != 200:
                self.root.after(0, lambda: self.log.append(
                    f"Weather error: {res.get('message', 'Unknown error')}", "error"))
                return

            temp    = round(res["main"]["temp"])
            feels   = round(res["main"]["feels_like"])
            desc    = res["weather"][0]["description"].capitalize()
            humidity= res["main"]["humidity"]
            name    = res["name"]

            self.root.after(0, lambda: self._update_weather_ui(
                name, temp, feels, desc, humidity))
            self.root.after(0, lambda: self.log.append(
                f"Weather updated: {name} — {temp}°C, {desc}", "sys"))

        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self.log.append(
                "Weather fetch failed: No internet connection.", "warn"))
        except Exception as ex:
            self.root.after(0, lambda: self.log.append(
                f"Weather fetch failed: {ex}", "error"))

    def _update_weather_ui(self, city, temp, feels, desc, humidity):
        self.weather_city_lbl.config(text=f"📍 {city}")
        self.weather_temp_lbl.config(text=f"🌡 {temp}°C  (feels {feels}°C)")
        self.weather_desc_lbl.config(text=f"☁ {desc}")
        self.weather_humidity_lbl.config(text=f"💧 {humidity}%")

    # ── Command dispatcher ───────────────────────────────────────────────
    def _handle_command(self, query: str):
        self.log.append(f"You: {query}", "user")
        q = query.lower()


        if "youtube" in q:
            self._open_youtube()
            self._speak("youtube opend sir ")
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
        elif"open camera" in q:
            import  cv2
            cap = cv2.VideoCapture(0)  # 0 is for internal camera and 1 for outer camera
            while True:
                ret, frame = cap.read()  # read a frame from camera
                cv2.imshow('camera', frame)  # display the frame
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
        elif"word" in q:
            qpath = "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Word"
            os.startfile(qpath)
        elif"send message" in q:
            n = simpledialog.askstring(
                "WhatsApp Number",
                "Enter number with country code (e.g. +91XXXXXXXXXX):",
                parent=self.root
            )
            if not n:
                self.log.append("Send message cancelled.", "warn")
                return
            
            message = simpledialog.askstring(
            "Message",
            "Enter the message to send:",
            parent=self.root
            )
            if not message:
                self.log.append("Send message cancelled.", "warn")
                return

            ct = datetime.datetime.now()
            h = ct.hour
            m = ct.minute + 2          # give pywhatkit enough buffer time
            if m >= 60:                # ✅ handle overflow
                h = (h + 1) % 24
                m = m - 60

            try:
                k.sendwhatmsg(n, message, h, m, wait_time=35
                              , tab_close=True, close_time=3)
                self._speak("Message scheduled, sir.")
            except Exception as ex:
                self.log.append(f"WhatsApp error: {ex}", "error")
                
        elif "weather" in q:
            city = DEFAULT_CITY  # fallback
            for keyword in ["of", "in", "for"]:
                if keyword in q:
                    part = q.split(keyword)[-1].strip()
                    if part:
                        city = part.title()  # capitalise properly e.g. "jaipur" → "Jaipur"
                        break
            threading.Thread(target=lambda: self._fetch_weather(city), daemon=True).start()
            self._speak(f"Fetching weather for {city}, sir.")
        elif any(word in q for word in ["add", "plus", "subtract", "minus", "multiply", "times", "divide","+"]):
            numbers = re.findall(r'\d+\.?\d*', q)
            if len(numbers) < 2:
                self._speak("Please provide two numbers, sir.")
            else:
                a, b = float(numbers[0]), float(numbers[1])
                if "add" in q or "plus" in q or "sum" in q or "+" in q:
                    result = a + b
                    op = "plus"
                elif "subtract" in q or "minus" in q:
                    result = a - b
                    op = "minus"
                elif "multiply" in q or "times" in q:
                    result = a * b
                    op = "times"
                elif "divide" in q or "divided" in q:
                    if b == 0:
                        self._speak("Sir, division by zero is not possible.")
                        return
                    result = a / b
                    op = "divided by"
        
                result_str = str(int(result)) if result == int(result) else str(round(result, 4))
                self._speak(f"Sir, {int(a)} {op} {int(b)} is {result_str}.")
        elif "hello" in q or "hi" in q:
            self._speak("Hello sir, how may I assist you?")
        elif "bye" in q or "exit" in q or "quit" in q:
            self._speak("Goodbye, sir. Have a great day!")
            self.root.after(1200, self.root.destroy)
        else:
            self._speak(f"Processing: {query}")

    def _speak(self, msg: str):
        self.log.append(f"JARVIS: {msg}", "jarvis")
        if TTS_AVAILABLE:
            self._speech_queue.append(msg)
            if not self._speaking:
                    threading.Thread(target=self._speech_worker, daemon=True).start()

    def _speech_worker(self):
        self._speaking = True
        while self._speech_queue:
            msg = self._speech_queue.pop(0)
            try:
                self.engine.say(msg)
                self.engine.runAndWait()
            except RuntimeError:
                pass  # skip if engine is momentarily busy
        self._speaking = False

   

    # ── Quick actions ────────────────────────────────────────────────────
    def _open_chatbot(self):
        ChatbotWindow(self.root)

    def _open_youtube(self):
        webbrowser.open("https://www.youtube.com/")
        self._speak("Opening YouTube, sir.")

    def _open_google(self):
        webbrowser.open("https://www.google.com/")
        self._speak("Opening Google, sir.")

    def _open_wiki(self):
        webbrowser.open("https://www.wikipedia.org/")
        self._speak("Opening Wikipedia, sir.")

    def _open_desktop(self):
        path = r"C:\Users\karan\OneDrive\Desktop"
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