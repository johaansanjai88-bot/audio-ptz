"""
ONVIF Client
Handles communication with PTZ cameras using the ONVIF protocol.
"""

from onvif import ONVIFCamera
from src.utils.logger import get_logger
from src.utils.config_loader import load_camera_config

logger = get_logger(__name__)


class ONVIFClient:
    """ONVIF protocol client for PTZ camera control."""

    def __init__(self, camera_id: str, config: dict = None):
        self.camera_id = camera_id
        self.config = config or load_camera_config(camera_id)
        self._camera = None
        self._ptz = None
        self._media = None
        self._profile_token = None

    def connect(self) -> bool:
        """Connect to camera via ONVIF."""
        try:
            self._camera = ONVIFCamera(
                self.config["ip"],
                self.config.get("port", 80),
                self.config["username"],
                self.config["password"],
            )
            self._media = self._camera.create_media_service()
            self._ptz = self._camera.create_ptz_service()

            profiles = self._media.GetProfiles()
            if not profiles:
                raise RuntimeError("No media profiles found on camera")
            self._profile_token = profiles[0].token

            logger.info(f"ONVIF connected to {self.config['ip']} (token: {self._profile_token})")
            return True

        except Exception as e:
            logger.error(f"ONVIF connection failed: {e}")
            return False

    def disconnect(self):
        """Clean up resources."""
        self._camera = None
        self._ptz = None
        self._media = None
        self._profile_token = None

    def continuous_move(self, velocity: dict):
        """
        Send continuous move command.

        Args:
            velocity: dict with keys 'pan', 'tilt', 'zoom' (-1.0 to 1.0)
        """
        request = self._ptz.create_type("ContinuousMove")
        request.ProfileToken = self._profile_token
        request.Velocity = {
            "PanTilt": {
                "x": float(velocity.get("pan", 0)),
                "y": float(velocity.get("tilt", 0)),
            },
            "Zoom": {"x": float(velocity.get("zoom", 0))},
        }
        self._ptz.ContinuousMove(request)

    def absolute_move(self, pan: float, tilt: float, zoom: float, speed: float = 0.5):
        """Move camera to absolute position."""
        request = self._ptz.create_type("AbsoluteMove")
        request.ProfileToken = self._profile_token
        request.Position = {
            "PanTilt": {"x": pan, "y": tilt},
            "Zoom": {"x": zoom},
        }
        request.Speed = {
            "PanTilt": {"x": speed, "y": speed},
            "Zoom": {"x": speed},
        }
        self._ptz.AbsoluteMove(request)

    def absolute_zoom(self, level: float, speed: float = 0.5):
        """Set absolute zoom level."""
        # Normalize zoom level (1.0 = no zoom → 0.0 in ONVIF space)
        normalized = min((level - 1.0) / 9.0, 1.0)
        request = self._ptz.create_type("AbsoluteMove")
        request.ProfileToken = self._profile_token
        request.Position = {
            "PanTilt": {"x": 0, "y": 0},
            "Zoom": {"x": normalized},
        }
        request.Speed = {"Zoom": {"x": speed}}
        self._ptz.AbsoluteMove(request)

    def stop(self, pan_tilt: bool = True, zoom: bool = True):
        """Stop camera movement."""
        request = self._ptz.create_type("Stop")
        request.ProfileToken = self._profile_token
        request.PanTilt = pan_tilt
        request.Zoom = zoom
        self._ptz.Stop(request)

    def go_to_home(self):
        """Move to home position."""
        request = self._ptz.create_type("GotoHomePosition")
        request.ProfileToken = self._profile_token
        self._ptz.GotoHomePosition(request)

    def go_to_preset(self, preset_token: str):
        """Move to a saved preset."""
        request = self._ptz.create_type("GotoPreset")
        request.ProfileToken = self._profile_token
        request.PresetToken = preset_token
        self._ptz.GotoPreset(request)

    def set_preset(self, preset_token: str, preset_name: str = ""):
        """Save current position as preset."""
        request = self._ptz.create_type("SetPreset")
        request.ProfileToken = self._profile_token
        request.PresetToken = preset_token
        request.PresetName = preset_name
        self._ptz.SetPreset(request)

    def get_status(self) -> dict:
        """Get current PTZ status."""
        request = self._ptz.create_type("GetStatus")
        request.ProfileToken = self._profile_token
        status = self._ptz.GetStatus(request)
        return {
            "pan": status.Position.PanTilt.x,
            "tilt": status.Position.PanTilt.y,
            "zoom": status.Position.Zoom.x,
            "moving": status.MoveStatus.PanTilt != "IDLE",
        }
