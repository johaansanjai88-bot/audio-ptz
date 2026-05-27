"""
PTZ Camera REST API
Flask-based REST API for controlling PTZ cameras remotely.
"""

from flask import Flask, jsonify, request, Response
from src.controllers.ptz_controller import PTZController
from src.protocols.rtsp_stream import RTSPStream, generate_frames
from src.utils.config_loader import load_all_cameras
from src.utils.logger import get_logger

logger = get_logger(__name__)
app = Flask(__name__)

# Cache of active controllers
_controllers: dict[str, PTZController] = {}
_streams: dict[str, RTSPStream] = {}


def get_controller(camera_id: str) -> PTZController:
    if camera_id not in _controllers:
        ctrl = PTZController(camera_id)
        ctrl.connect()
        _controllers[camera_id] = ctrl
    return _controllers[camera_id]


# ──────────────────────────────────────────
# Camera listing
# ──────────────────────────────────────────

@app.route("/api/cameras", methods=["GET"])
def list_cameras():
    cameras = load_all_cameras()
    return jsonify({"cameras": cameras})


# ──────────────────────────────────────────
# PTZ Control
# ──────────────────────────────────────────

@app.route("/api/cameras/<camera_id>/pan", methods=["POST"])
def pan(camera_id):
    data = request.json or {}
    direction = data.get("direction", "right")
    speed = float(data.get("speed", 0.5))
    duration = float(data.get("duration", 1.0))

    ctrl = get_controller(camera_id)
    ctrl.pan(speed=speed, direction=direction, duration=duration)
    return jsonify({"status": "ok", "action": "pan", "direction": direction})


@app.route("/api/cameras/<camera_id>/tilt", methods=["POST"])
def tilt(camera_id):
    data = request.json or {}
    direction = data.get("direction", "up")
    speed = float(data.get("speed", 0.5))
    duration = float(data.get("duration", 1.0))

    ctrl = get_controller(camera_id)
    ctrl.tilt(speed=speed, direction=direction, duration=duration)
    return jsonify({"status": "ok", "action": "tilt", "direction": direction})


@app.route("/api/cameras/<camera_id>/zoom", methods=["POST"])
def zoom(camera_id):
    data = request.json or {}
    level = float(data.get("level", 1.0))
    speed = float(data.get("speed", 0.5))

    ctrl = get_controller(camera_id)
    ctrl.zoom(level=level, speed=speed)
    return jsonify({"status": "ok", "action": "zoom", "level": level})


@app.route("/api/cameras/<camera_id>/move", methods=["POST"])
def move(camera_id):
    """Combined pan/tilt/zoom move."""
    data = request.json or {}
    pan_v = float(data.get("pan", 0))
    tilt_v = float(data.get("tilt", 0))
    zoom_v = float(data.get("zoom", 0))

    ctrl = get_controller(camera_id)
    ctrl.move(pan=pan_v, tilt=tilt_v, zoom=zoom_v)
    return jsonify({"status": "ok", "action": "move"})


@app.route("/api/cameras/<camera_id>/stop", methods=["POST"])
def stop(camera_id):
    ctrl = get_controller(camera_id)
    ctrl.stop()
    return jsonify({"status": "ok", "action": "stop"})


@app.route("/api/cameras/<camera_id>/home", methods=["POST"])
def go_home(camera_id):
    ctrl = get_controller(camera_id)
    ctrl.go_to_home()
    return jsonify({"status": "ok", "action": "home"})


# ──────────────────────────────────────────
# Presets
# ──────────────────────────────────────────

@app.route("/api/cameras/<camera_id>/presets", methods=["GET"])
def list_presets(camera_id):
    ctrl = get_controller(camera_id)
    presets = ctrl.get_presets()
    return jsonify({"presets": presets})


@app.route("/api/cameras/<camera_id>/preset/<int:token>", methods=["POST"])
def goto_preset(camera_id, token):
    ctrl = get_controller(camera_id)
    ctrl.go_to_preset(token)
    return jsonify({"status": "ok", "preset": token})


@app.route("/api/cameras/<camera_id>/preset/<int:token>/save", methods=["POST"])
def save_preset(camera_id, token):
    data = request.json or {}
    name = data.get("name", f"Preset {token}")
    ctrl = get_controller(camera_id)
    ctrl.save_preset(token, name)
    return jsonify({"status": "ok", "saved": token, "name": name})


# ──────────────────────────────────────────
# Status & Stream
# ──────────────────────────────────────────

@app.route("/api/cameras/<camera_id>/status", methods=["GET"])
def status(camera_id):
    ctrl = get_controller(camera_id)
    return jsonify(ctrl.get_status())


@app.route("/api/cameras/<camera_id>/stream")
def video_stream(camera_id):
    if camera_id not in _streams:
        stream = RTSPStream(camera_id)
        stream.start()
        _streams[camera_id] = stream

    return Response(
        generate_frames(_streams[camera_id]),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ──────────────────────────────────────────
# Error handlers
# ──────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import yaml
    with open("config/cameras.yaml") as f:
        cfg = yaml.safe_load(f)
    app_cfg = cfg.get("app", {})
    app.run(
        host=app_cfg.get("host", "0.0.0.0"),
        port=app_cfg.get("port", 5000),
        debug=app_cfg.get("debug", False),
    )
