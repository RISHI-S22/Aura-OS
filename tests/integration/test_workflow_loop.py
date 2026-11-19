from fastapi.testclient import TestClient
from agents.computer.screen_analyzer import ScreenAnalyzer
from aura.api.main import app
from core.verification.action_checker import ActionChecker

client = TestClient(app)

def test_screen_analyzer_fuses_ui_controls():
    analyzer = ScreenAnalyzer()
    result = analyzer.analyze([
        {"control_type": "Button", "name": "Run", "is_enabled": True},
        {"control_type": "Pane", "name": "Container", "is_enabled": True},
    ])
    assert len(result["actionable_controls"]) == 1
    assert result["resolution"]["width"] > 0

def test_action_checker_validates_matching_agent():
    task = {"id": "t1", "agent": "research_agent"}
    assert ActionChecker.verify_step(task, {"status": "success", "agent": "research_agent"}) is True
    assert ActionChecker.verify_step(task, {"status": "success", "agent": "wrong_agent"}) is False

def test_command_records_to_episodic_history():
    res = client.post("/api/v1/commands", json={"command": "Research multi-agent architectures"})
    assert res.status_code == 200
    hist = client.get("/api/v1/history").json()
    assert len(hist["episodes"]) >= 1
