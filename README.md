# 🎮 PocketSense

**Turn your mobile phone into a seamless, virtual DualSense controller for your PC.**

PocketSense is a web-based virtual gamepad that instantly connects to your Windows PC over your local network. Built with a sleek, glassmorphic UI using React and Vite, it sends multi-touch inputs at lightning speed to a Python backend. Using the power of `vgamepad` and `ViGEmBus`, your PC recognizes your phone natively as a physical DualShock 4 / DualSense controller.

## ✨ Features
- **Zero Install on Phone:** Runs entirely in your mobile browser.
- **Ultra-low Latency:** Powered by WebSockets for instant response times.
- **Native PC Support:** Games recognize it out-of-the-box as a connected controller.
- **Multi-Touch Precision:** Custom virtual joysticks and D-Pad built to handle simultaneous inputs perfectly.
- **Premium Design:** A modern, aesthetic dark-mode layout optimized for landscape orientation.

## 🚀 Getting Started

### Prerequisites
- A Windows PC.
- Python 3 installed on your PC.
- Node.js (for building the frontend if you modify it).
- **[ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases)**: Essential. You must install this on your Windows PC so the script can emulate a physical controller.

### Running the Server
1. Clone this repository to your PC.
2. Navigate to the `server` directory.
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python main.py
   ```
5. The console will output a local IP address (e.g., `http://192.168.1.50:8000`).

### Connecting your Phone
1. Ensure your phone is connected to the **same Wi-Fi network** as your PC.
2. Open your phone's browser (Safari, Chrome, etc.).
3. Enter the IP address shown in the console.
4. Rotate your phone to Landscape mode.
5. You're ready to play! 

## 🛠️ Tech Stack
- **Frontend:** React, Vite, Vanilla CSS.
- **Backend:** Python, FastAPI, WebSockets, `vgamepad`.

---
*Created as a weekend project to make local multiplayer and controller emulation accessible without extra hardware.*
