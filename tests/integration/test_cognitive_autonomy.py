from fastapi.testclient import TestClient
from aura.api.main import app
from core.planning.task_planner import CognitivePlanner

client = TestClient(app)

def test_cognitive_planner_routes_browser_and_desktop_tasks():
    cp = CognitivePlanner()
    web_plan = cp.plan("Browse website documentation for FastAPI")
    assert web_plan.subtasks[0].agent == "browser_agent"

    os_plan = cp.plan("Open editor window and write solution")
    assert os_plan.subtasks[0].agent == "desktop_agent"

def test_command_records_procedural_trace_and_exposes_via_api():
    res = client.post(
        "/api/v1/commands",
        json={"command": "Open window and click button", "live_mode": False},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"

    proc_res = client.get("/api/v1/memory/procedures", params={"q": "Open window"})
    assert proc_res.status_code == 200
    assert len(proc_res.json()["procedures"]) >= 1
