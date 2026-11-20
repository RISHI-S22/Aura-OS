import asyncio
from fastapi.testclient import TestClient
from agents.computer.action_planner import DesktopActionPlanner
from aura.api.main import app
from core.orchestration.dispatcher import dispatcher

client = TestClient(app)

def test_desktop_action_planner_selects_universal_control():
    planner = DesktopActionPlanner()
    decision = planner.decide_next_action(
        goal="Write code in active editor",
        controls=[{"control_type": "Document", "name": "Code Editor", "is_enabled": True}],
        ocr_blocks=[],
    )
    assert decision["action"] in ("type_text", "click_control", "hotkey", "done")
    assert decision["target_name"] == "Code Editor"

def test_desktop_agent_records_execution_trace():
    task = {
        "id": "d_loop_1",
        "title": "Click run button",
        "ui_controls": [{"control_type": "Button", "name": "Run", "is_enabled": True}],
    }
    res = asyncio.run(dispatcher.dispatch("desktop_agent", task))
    assert res["status"] == "success"
    assert len(res["execution_trace"]) >= 1

def test_pause_and_resume_gated_workflow():
    start_res = client.post("/api/v1/commands", json={"command": "Send email to team with summary"})
    assert start_res.status_code == 200
    body = start_res.json()
    assert body["status"] == "pending_approval"
    session_id = body["session_id"]

    resume_res = client.post(f"/api/v1/sessions/{session_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "completed"
