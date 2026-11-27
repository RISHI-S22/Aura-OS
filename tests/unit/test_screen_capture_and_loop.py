import asyncio
import os
from unittest.mock import patch
from core.orchestration.dispatcher import dispatcher
from tools.vision.screen_capture import LiveScreenCapture

def test_live_screen_capture_handles_missing_display_gracefully():
    with patch("PIL.ImageGrab.grab", side_effect=RuntimeError("headless")):
        res = LiveScreenCapture.capture_foreground_or_screen(output_dir="workspace/test_captures")
        assert res is None
    if os.path.isdir("workspace/test_captures"):
        os.rmdir("workspace/test_captures")

def test_desktop_agent_records_screenshot_field_in_trace():
    res = asyncio.run(
        dispatcher.dispatch(
            "desktop_agent",
            {
                "id": "cap_1",
                "title": "Click OK",
                "ui_controls": [{"control_type": "Button", "name": "OK", "is_enabled": True}],
            },
        )
    )
    assert res["status"] == "success"
    assert "screenshot" in res["execution_trace"][0]
