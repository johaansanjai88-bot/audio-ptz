"""
PTZ Camera Controller
Handles Pan, Tilt, Zoom operations via ONVIF protocol.
"""

import time
import logging
from typing import Optional
from src.protocols.onvif_client import ONVIFClient
from src.controllers.preset_manager import PresetManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PTZController:
    """Main controller for PTZ camera operations."""

    DIRECTIONS = {
        "pan": {"left": (-1, 0), "right": (1, 0)},
        "tilt": {"up": (0, 1), "down": (0, -1)},
    }

    def __init__(self, camera_id: str, config: Optional[dict] = None):
        self.camera_id = camera_id
        self.config = config or {}
        self.client = ONVIFClient(camera_id, self.config)
        self.preset_manager = PresetManager(camera_id)
        self._connected = False

    def connect(self) -> bool:
        """Establish connection to the camera."""
        try:
            self._connected = self.client.connect()
            if self._connected:
                logger.info(f"Connected to camera: {self.camera_id}")
            return self._connected
        except Exception as e:
            logger.error(f"Failed to connect to camera {self.camera_id}: {e}")
            return False

    def disconnect(self):
        """Disconnect from the camera."""
        self.client.disconnect()
        self._connected = False
        logger.info(f"Disconnected from camera: {self.camera_id}")

    def pan(self, speed: float = 0.5, direction: str = "right", duration: float = 1.0):
        """
        Pan the camera left or right.

        Args:
            speed: Speed of movement (0.0 to 1.0)
            direction: 'left' or 'right'
            duration: How long to move in seconds
        """
        self._validate_speed(speed)
        if direction not in self.DIRECTIONS["pan"]:
            raise ValueError(f"Invalid pan direction: {direction}. Use 'left' or 'right'.")

        pan_x, pan_y = self.DIRECTIONS["pan"][direction]
        velocity = {"pan": pan_x * speed, "tilt": 0, "zoom": 0}

        logger.info(f"[{self.camera_id}] Panning {direction} at speed {speed}")
        self.client.continuous_move(velocity)
        time.sleep(duration)
        self.stop()

    def tilt(self, speed: float = 0.5, direction: str = "up", duration: float = 1.0):
        """
        Tilt the camera up or down.

        Args:
            speed: Speed of movement (0.0 to 1.0)
            direction: 'up' or 'down'
            duration: How long to move in seconds
        """
        self._validate_speed(speed)
        if direction not in self.DIRECTIONS["tilt"]:
            raise ValueError(f"Invalid tilt direction: {direction}. Use 'up' or 'down'.")

        tilt_x, tilt_y = self.DIRECTIONS["tilt"][direction]
        velocity = {"pan": 0, "tilt": tilt_y * speed, "zoom": 0}

        logger.info(f"[{self.camera_id}] Tilting {direction} at speed {speed}")
        self.client.continuous_move(velocity)
        time.sleep(duration)
        self.stop()

    def zoom(self, level: float = 1.0, speed: float = 0.5):
        """
        Set zoom level.

        Args:
            level: Zoom multiplier (1.0 = no zoom, max depends on camera)
            speed: Speed of zoom (0.0 to 1.0)
        """
        if level < 1.0:
            raise ValueError("Zoom level must be >= 1.0")

        logger.info(f"[{self.camera_id}] Zooming to level {level}")
        self.client.absolute_zoom(level, speed)

    def zoom_in(self, speed: float = 0.5, duration: float = 1.0):
        """Continuously zoom in."""
        self._validate_speed(speed)
        velocity = {"pan": 0, "tilt": 0, "zoom": speed}
        self.client.continuous_move(velocity)
        time.sleep(duration)
        self.stop()

    def zoom_out(self, speed: float = 0.5, duration: float = 1.0):
        """Continuously zoom out."""
        self._validate_speed(speed)
        velocity = {"pan": 0, "tilt": 0, "zoom": -speed}
        self.client.continuous_move(velocity)
        time.sleep(duration)
        self.stop()

    def move(self, pan: float = 0.0, tilt: float = 0.0, zoom: float = 0.0):
        """
        Move camera with combined pan/tilt/zoom velocity.

        Args:
            pan: Pan velocity (-1.0 to 1.0)
            tilt: Tilt velocity (-1.0 to 1.0)
            zoom: Zoom velocity (-1.0 to 1.0)
        """
        velocity = {"pan": pan, "tilt": tilt, "zoom": zoom}
        logger.debug(f"[{self.camera_id}] Moving: {velocity}")
        self.client.continuous_move(velocity)

    def stop(self):
        """Stop all camera movement."""
        logger.debug(f"[{self.camera_id}] Stopping movement")
        self.client.stop()

    def go_to_home(self):
        """Move camera to home position."""
        logger.info(f"[{self.camera_id}] Moving to home position")
        self.client.go_to_home()

    def go_to_preset(self, preset_token: int):
        """
        Move camera to a saved preset position.

        Args:
            preset_token: Preset number (1-based)
        """
        logger.info(f"[{self.camera_id}] Going to preset {preset_token}")
        self.client.go_to_preset(str(preset_token))

    def save_preset(self, preset_token: int, name: str = ""):
        """
        Save current position as a preset.

        Args:
            preset_token: Preset number to save to
            name: Human-readable name for this preset
        """
        logger.info(f"[{self.camera_id}] Saving preset {preset_token}: '{name}'")
        self.client.set_preset(str(preset_token), name)
        self.preset_manager.save(preset_token, name)

    def get_status(self) -> dict:
        """Get current camera status including position."""
        status = self.client.get_status()
        logger.debug(f"[{self.camera_id}] Status: {status}")
        return status

    def get_presets(self) -> list:
        """List all saved presets."""
        return self.preset_manager.list_all()

    def _validate_speed(self, speed: float):
        if not (0.0 <= speed <= 1.0):
            raise ValueError(f"Speed must be between 0.0 and 1.0, got {speed}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
