# J.A.R.V.I.S — AI Desktop Assistant

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-informational)
![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20LLaMA3-purple)
![TTS](https://img.shields.io/badge/TTS-pyttsx3-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> *"Just A Rather Very Intelligent System"*

A **dark-themed, voice-enabled AI desktop assistant** built with Python and Tkinter, inspired by the JARVIS AI from Iron Man. Features an animated radar UI, real-time weather, a built-in AI chatbot (powered by Groq's LLaMA 3), voice recognition, WhatsApp messaging, and more.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 🎙️ **Voice Recognition** | Listens to spoken commands via microphone using `speech_recognition` |
| 🔊 **Text-to-Speech** | Responds vocally using `pyttsx3` |
| 🤖 **AI Chatbot (FRIDAY)** | Separate chatbot window powered by Groq's `llama-3.3-70b-versatile` model |
| 🌤️ **Live Weather** | Fetches real-time weather data via OpenWeatherMap API |
| 📡 **Animated Radar UI** | Custom animated radar widget with blip effects |
| ▶️ **Quick Actions** | One-click access to YouTube, Google, Wikipedia, Desktop, CMD |
| 💬 **WhatsApp Messaging** | Send WhatsApp messages via `pywhatkit` |
| 🧮 **Math Operations** | Voice/text-based arithmetic (add, subtract, multiply, divide) |
| 🕐 **Live Clock** | Real-time date and time display |
| 📷 **Camera Access** | Opens the system webcam on command |

---

## 🖥️ UI Overview

```
┌─────────────────────────────────────────────────────────┐
│  J.A.R.V.I.S          JUST A RATHER VERY...    HH:MM:SS │
├──────────────┬──────────────────────────────────────────┤
│  [ RADAR ]   │  [ WEATHER ]   City | Temp | Desc        │
│   (animated) │                                          │
│              │  [ SYSTEM LOG ]                          │
│  [ MIC ]     │   scrollable log with timestamps         │
│              │                                          │
│  [Quick      │  > Type a command...          [ SEND ]   │
│   Actions ]  │                                          │
└──────────────┴──────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Library / Service |
|-----------|-------------------|
| GUI Framework | `tkinter` |
| Voice Input | `speech_recognition` |
| Voice Output | `pyttsx3` |
| AI Chatbot | Groq API (`llama-3.3-70b-versatile`) |
| Weather | OpenWeatherMap API |
| WhatsApp | `pywhatkit` |
| Browser Control | `webbrowser` |
| HTTP Requests | `requests` |

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/karan635/jarvis.git
cd jarvis
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install pyttsx3 speechrecognition pywhatkit requests pyaudio
```

> **Note:** `pyaudio` may require additional setup on Windows.  
> Download the appropriate `.whl` from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install via `pip install <file>.whl`.

---

## 🔑 API Keys Setup

Open `main.py` and replace the placeholders with your actual API keys:

```python
OWM_API_KEY  = "YOUR_OPENWEATHERMAP_API_KEY"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
DEFAULT_CITY = "Jaipur"   # Change to your city
```

- **OpenWeatherMap:** Get a free key at [openweathermap.org](https://openweathermap.org/api)
- **Groq:** Get a free key at [console.groq.com](https://console.groq.com/)

---

## 🚀 Running the App

```bash
python main.py
```

JARVIS will greet you with a time-based salutation and await your command.

---

## 🗣️ Voice / Text Commands

| Command | Action |
|---------|--------|
| `"open youtube"` | Opens YouTube in browser |
| `"open google"` | Opens Google in browser |
| `"open wikipedia"` | Opens Wikipedia in browser |
| `"open desktop"` | Opens the Desktop folder |
| `"open cmd"` | Opens Command Prompt |
| `"what time is it"` | Speaks the current time |
| `"what is today's date"` | Speaks the current date |
| `"weather in Jaipur"` | Fetches weather for the given city |
| `"add 5 and 10"` | Performs arithmetic |
| `"send message"` | Opens dialog to send a WhatsApp message |
| `"open camera"` | Opens system webcam |
| `"open word"` | Opens Microsoft Word |
| `"hello"` | Greets you |
| `"bye"` / `"exit"` | Closes JARVIS |

---

## 🤖 FRIDAY — AI Chatbot

Click the **🤖 Chatbot** button to open FRIDAY, a conversational AI assistant powered by **Groq's LLaMA 3.3 70B** model. It maintains conversation history within the session and can answer general knowledge, coding, and logic questions.

---

## 📁 Project Structure

```
jarvis/
├── main.py            # Main application — UI + all logic
└── README.md
```

---

## 🔮 Planned Features

- [ ] Spotify / music playback integration
- [ ] News headlines fetching
- [ ] System resource monitoring (CPU, RAM)
- [ ] Multi-city weather dashboard
- [ ] Custom wake word detection

---

## 👤 Author

**Karan Parwani**  
MCA Student — BIT Mesra  
📧 karanparwani9904@gmail.com  
🔗 [GitHub: karan635](https://github.com/karan635)

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
