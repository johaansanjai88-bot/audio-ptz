"""
Unit Tests for PTZ Camera System
"""

import pytest
from unittest.mock import MagicMock, patch
from src.controllers.ptz_controller import PTZController
from src.controllers.preset_manager import PresetManager


# ──────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────

@pytest.fixture
def mock_config():
    return {
        "id": "test_cam",
        "name": "Test Camera",
        "ip": "192.168.1.99",
        "port": 80,
        "username": "admin",
        "password": "test",
        "rtsp_port": 554,
        "rtsp_path": "/stream1",
    }


@pytest.fixture
def controller(mock_config):
    with patch("src.controllers.ptz_controller.ONVIFClient") as mock_client_cls, \
         patch("src.controllers.ptz_controller.PresetManager"):
        ctrl = PTZController("test_cam", config=mock_config)
        ctrl.client = MagicMock()
        ctrl._connected = True
        yield ctrl


# ──────────────────────────────────────────
# PTZController Tests
# ──────────────────────────────────────────

class TestPTZController:

    def test_pan_right(self, controller):
        controller.pan(speed=0.5, direction="right", duration=0)
        controller.client.continuous_move.assert_called_once()
        args = controller.client.continuous_move.call_args[0][0]
        assert args["pan"] == pytest.approx(0.5)
        assert args["tilt"] == 0

    def test_pan_left(self, controller):
        controller.pan(speed=0.3, direction="left", duration=0)
        args = controller.client.continuous_move.call_args[0][0]
        assert args["pan"] == pytest.approx(-0.3)

    def test_tilt_up(self, controller):
        controller.tilt(speed=0.7, direction="up", duration=0)
        args = controller.client.continuous_move.call_args[0][0]
        assert args["tilt"] == pytest.approx(0.7)

    def test_tilt_down(self, controller):
        controller.tilt(speed=0.4, direction="down", duration=0)
        args = controller.client.continuous_move.call_args[0][0]
        assert args["tilt"] == pytest.approx(-0.4)

    def test_invalid_speed_raises(self, controller):
        with pytest.raises(ValueError):
            controller.pan(speed=1.5, direction="right")
        with pytest.raises(ValueError):
            controller.pan(speed=-0.1, direction="right")

    def test_invalid_direction_raises(self, controller):
        with pytest.raises(ValueError):
            controller.pan(direction="diagonal")
        with pytest.raises(ValueError):
            controller.tilt(direction="sideways")

    def test_zoom_invalid_level_raises(self, controller):
        with pytest.raises(ValueError):
            controller.zoom(level=0.5)

    def test_stop_called(self, controller):
        controller.stop()
        controller.client.stop.assert_called_once()

    def test_go_to_home(self, controller):
        controller.go_to_home()
        controller.client.go_to_home.assert_called_once()

    def test_go_to_preset(self, controller):
        controller.go_to_preset(3)
        controller.client.go_to_preset.assert_called_with("3")

    def test_save_preset(self, controller):
        controller.save_preset(2, name="Lobby")
        controller.client.set_preset.assert_called_with("2", "Lobby")

    def test_get_status(self, controller):
        controller.client.get_status.return_value = {
            "pan": 0.1, "tilt": -0.2, "zoom": 0.5, "moving": False
        }
        status = controller.get_status()
        assert "pan" in status
        assert "zoom" in status


# ──────────────────────────────────────────
# PresetManager Tests
# ──────────────────────────────────────────

class TestPresetManager:

    @pytest.fixture
    def manager(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.controllers.preset_manager.PRESETS_DIR", str(tmp_path))
        return PresetManager("test_cam")

    def test_save_and_get(self, manager):
        manager.save(1, "Entrance")
        preset = manager.get(1)
        assert preset is not None
        assert preset["name"] == "Entrance"

    def test_get_nonexistent(self, manager):
        assert manager.get(99) is None

    def test_delete(self, manager):
        manager.save(2, "Parking")
        assert manager.delete(2) is True
        assert manager.get(2) is None

    def test_delete_nonexistent(self, manager):
        assert manager.delete(99) is False

    def test_list_all_sorted(self, manager):
        manager.save(3, "C")
        manager.save(1, "A")
        manager.save(2, "B")
        presets = manager.list_all()
        tokens = [p["token"] for p in presets]
        assert tokens == [1, 2, 3]

    def test_clear_all(self, manager):
        manager.save(1, "A")
        manager.save(2, "B")
        manager.clear_all()
        assert manager.list_all() == []
