# 🎥 PTZ Camera Control System

A full-stack PTZ (Pan-Tilt-Zoom) camera management system with real-time control, preset positioning, ONVIF/RTSP protocol support, and a live dashboard.

---

## 📁 Project Structure

```
ptz-camera/
├── src/
│   ├── controllers/
│   │   ├── ptz_controller.py       # Core PTZ movement logic
│   │   └── preset_manager.py       # Save/load camera presets
│   ├── protocols/
│   │   ├── onvif_client.py         # ONVIF protocol integration
│   │   └── rtsp_stream.py          # RTSP stream handler
│   └── utils/
│       ├── logger.py               # Logging utility
│       └── config_loader.py        # Config file loader
├── frontend/
│   └── dashboard.html              # Live control dashboard UI
├── tests/
│   └── test_ptz.py                 # Unit tests
├── config/
│   └── cameras.yaml                # Camera configuration
├── docs/
│   └── API.md                      # API documentation
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Features

- Pan, Tilt, Zoom control via ONVIF protocol
- RTSP live stream integration
- Preset position save & recall
- Multi-camera support
- REST API for remote control
- Web dashboard for real-time monitoring
- Logging and error handling

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ptz-camera.git
cd ptz-camera

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your camera credentials
```

---

## ⚙️ Configuration

Edit `config/cameras.yaml`:

```yaml
cameras:
  - id: cam1
    name: "Front Entrance"
    ip: 192.168.1.100
    port: 80
    username: admin
    password: your_password
    rtsp_port: 554
```

---

## 📡 Usage

```python
from src.controllers.ptz_controller import PTZController

cam = PTZController(camera_id="cam1")

cam.pan(speed=0.5, direction="right")
cam.tilt(speed=0.3, direction="up")
cam.zoom(level=2.0)
cam.go_to_preset(1)
cam.save_preset(1, name="Front Gate")
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cameras` | List all cameras |
| POST | `/api/cameras/{id}/pan` | Pan camera |
| POST | `/api/cameras/{id}/tilt` | Tilt camera |
| POST | `/api/cameras/{id}/zoom` | Zoom camera |
| POST | `/api/cameras/{id}/preset/{n}` | Go to preset |
| GET | `/api/cameras/{id}/stream` | Get RTSP stream URL |

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
