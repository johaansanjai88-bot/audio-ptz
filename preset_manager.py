"""
Preset Manager
Handles saving, loading, and managing PTZ camera preset positions.
"""

import json
import os
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

PRESETS_DIR = "config/presets"


class PresetManager:
    """Manages PTZ camera preset positions stored as JSON."""

    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.presets_file = os.path.join(PRESETS_DIR, f"{camera_id}_presets.json")
        self._ensure_dir()
        self.presets = self._load()

    def _ensure_dir(self):
        os.makedirs(PRESETS_DIR, exist_ok=True)

    def _load(self) -> dict:
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load presets for {self.camera_id}: {e}")
        return {}

    def _persist(self):
        with open(self.presets_file, "w") as f:
            json.dump(self.presets, f, indent=2)

    def save(self, token: int, name: str, position: Optional[dict] = None):
        """Save a preset."""
        self.presets[str(token)] = {
            "token": token,
            "name": name,
            "position": position or {}
        }
        self._persist()
        logger.info(f"Preset {token} saved: '{name}'")

    def get(self, token: int) -> Optional[dict]:
        """Get a preset by token."""
        return self.presets.get(str(token))

    def delete(self, token: int) -> bool:
        """Delete a preset."""
        key = str(token)
        if key in self.presets:
            del self.presets[key]
            self._persist()
            logger.info(f"Preset {token} deleted")
            return True
        return False

    def list_all(self) -> list:
        """Return all presets as a sorted list."""
        return sorted(self.presets.values(), key=lambda x: x["token"])

    def clear_all(self):
        """Remove all presets."""
        self.presets = {}
        self._persist()
