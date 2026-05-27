"""
RTSP Stream Handler
Manages RTSP live stream connections and frame capture.
"""

import cv2
import threading
import time
from src.utils.logger import get_logger
from src.utils.config_loader import load_camera_config

logger = get_logger(__name__)


class RTSPStream:
    """Handles RTSP video stream from PTZ camera."""

    def __init__(self, camera_id: str, config: dict = None):
        self.camera_id = camera_id
        self.config = config or load_camera_config(camera_id)
        self._cap = None
        self._frame = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def get_stream_url(self) -> str:
        """Build RTSP stream URL from config."""
        ip = self.config["ip"]
        port = self.config.get("rtsp_port", 554)
        user = self.config["username"]
        pwd = self.config["password"]
        path = self.config.get("rtsp_path", "/stream1")
        return f"rtsp://{user}:{pwd}@{ip}:{port}{path}"

    def start(self):
        """Start capturing stream in background thread."""
        url = self.get_stream_url()
        self._cap = cv2.VideoCapture(url)

        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open RTSP stream: {url}")

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"RTSP stream started: {url}")

    def _capture_loop(self):
        """Background thread that continuously reads frames."""
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                with self._lock:
                    self._frame = frame
            else:
                logger.warning(f"[{self.camera_id}] Frame read failed, retrying...")
                time.sleep(0.1)

    def get_frame(self):
        """Get the latest captured frame."""
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def get_jpeg_frame(self) -> bytes:
        """Get latest frame encoded as JPEG bytes."""
        frame = self.get_frame()
        if frame is None:
            return b""
        _, buffer = cv2.imencode(".jpg", frame)
        return buffer.tobytes()

    def stop(self):
        """Stop the stream."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        logger.info(f"[{self.camera_id}] RTSP stream stopped")

    def is_running(self) -> bool:
        return self._running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def generate_frames(stream: RTSPStream):
    """
    Generator for MJPEG streaming (used with Flask).

    Usage:
        return Response(generate_frames(stream),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    """
    while stream.is_running():
        frame_bytes = stream.get_jpeg_frame()
        if frame_bytes:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
        time.sleep(0.03)  # ~30 FPS
