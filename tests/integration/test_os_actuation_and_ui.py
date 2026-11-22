import asyncio
from fastapi.testclient import TestClient
from aura.api.main import app
from core.orchestration.dispatcher import dispatcher
from core.verification.screen_delta import ScreenDeltaVerifier
from tools.computer import UniversalDesktopPrimitive

client = TestClient(app)

def test_screen_delta_verifier_detects_state_changes():
    before = [{"control_type": "Button", "name": "Submit"}]
    after = [{"control_type": "Document", "name": "Confirmation"}]
    assert ScreenDeltaVerifier.has_state_changed(before, before) is False
    assert ScreenDeltaVerifier.has_state_changed(before, after) is True

def test_universal_os_actuation_dry_run():
    res = UniversalDesktopPrimitive.execute_os_action("click_control", target_name="Save", dry_run=True)
    assert res["executed"] is True
    assert res["mode"] == "dry_run"
    assert res["target_name"] == "Save"

def test_desktop_agent_records_state_signature_and_actuation():
    task = {
        "id": "os_act_1",
        "title": "Submit form",
        "ui_controls": [{"control_type": "Button", "name": "Submit", "is_enabled": True}],
    }
    res = asyncio.run(dispatcher.dispatch("desktop_agent", task))
    assert res["status"] == "success"
    step = res["execution_trace"][0]
    assert "before_sig" in step
    assert step["actuation"]["executed"] is True

def test_websocket_pause_and_http_resume_cycle():
    with client.websocket_connect("/ws/commands") as ws:
        ws.send_json({"command": "Send email update to project lead"})
        paused_session = None
        while True:
            msg = ws.receive_json()
            if msg["event"] == "pending_approval":
                paused_session = msg["session_id"]
                break
        assert paused_session is not None

    resume_res = client.post(f"/api/v1/sessions/{paused_session}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "completed"
