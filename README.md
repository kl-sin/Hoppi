# Hoppi
AI-powered app that turns the real world into your playground!

<img src="assets/Hoppi_3dText.png" alt="Hoppi Logo" width="300">

<img src="assets/AppMockup.png" alt="App Mockup" width="400">

## ✨ What is Hoppi?
Hoppi encourages people to:
- 🌍 Go outside and interact with real places  
- 🤝 Connect with strangers through light, safe, fun tasks  
- 📸 Create and share quirky memories instantly  

## 🚀 Features
- 🌍 **Location Detection** → Geolocation + Overpass API + geopy  
- 🤖 **Task Generation** → AI-powered prompts (LLM via Ollama)  
- 📸 **Capture Moments** → Camera / mic input (getUserMedia or Streamlit WebRTC)  
- 🎨 **Fun Frames & Points** → Image & video edits with Pillow, OpenCV, MoviePy  
- 🗄️ **Storage & Analysis** → SQLite or Supabase, analytics with PostHog  
- 🚀 **Output & Sharing** → Save locally or share instantly  

## ⚡ Quick Start

### Prerequisites
- Python 3.10+  
- Git installed  
- (Optional) [Ollama](https://ollama.ai) for local LLM tasks  

### Installation
```bash
# Clone this repository
git clone git@github.com:kl-sin/Hoppi.git

# Navigate into the project
cd Hoppi

# (Optional) Set up virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies (when requirements.txt is available)
pip install -r requirements.txt