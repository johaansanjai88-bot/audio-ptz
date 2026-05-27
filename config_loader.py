"""
Config Loader
Loads camera and app configuration from YAML files and environment variables.
"""

import os
import yaml
from src.utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_FILE = os.getenv("CAMERA_CONFIG", "config/cameras.yaml")


def load_all_cameras() -> list:
    """Load all camera configs from YAML."""
    try:
        with open(CONFIG_FILE, "r") as f:
            data = yaml.safe_load(f)
        return data.get("cameras", [])
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_FILE}")
        return []
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config: {e}")
        return []


def load_camera_config(camera_id: str) -> dict:
    """Load config for a specific camera by ID."""
    cameras = load_all_cameras()
    for cam in cameras:
        if cam.get("id") == camera_id:
            # Override with env vars if present
            cam["username"] = os.getenv(f"CAM_{camera_id.upper()}_USER", cam.get("username", "admin"))
            cam["password"] = os.getenv(f"CAM_{camera_id.upper()}_PASS", cam.get("password", ""))
            return cam
    raise ValueError(f"Camera '{camera_id}' not found in config")
