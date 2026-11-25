import asyncio
from fastapi.testclient import TestClient
from aura.api.main import app
from core.orchestration.graph import execute_node

client = TestClient(app)

def test_websocket_command_streaming():
    with client.websocket_connect("/ws/commands") as ws:
        ws.send_json({"command": "Research three AI companies and prepare a comparison spreadsheet"})
        received_events = []
        while True:
            msg = ws.receive_json()
            received_events.append(msg["event"])
            if msg["event"] in ("completed", "pending_approval", "error"):
                break
        assert "planned" in received_events
        assert "step_started" in received_events
        assert "step_verified" in received_events
        assert received_events[-1] == "completed"

def test_voice_utterance_endpoint():
    resp = client.post(
        "/api/v1/voice/utterance",
        json={"command": "Research neural architecture search"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "Completed your" in data["spoken_reply"]

def test_closed_loop_replanning_on_unregistered_agent():
    state = {
        "command": "Test recovery",
        "intent": "test",
        "plan": [{"id": "t1", "title": "Fail step", "agent": "missing_agent", "requires_approval": False}],
        "current_step": 0,
        "artifacts": {},
        "approval_needed": False,
        "status": "planned",
        "error": None,
    }
    out = asyncio.run(execute_node(state))
    assert out["status"] == "failed"
    assert out["plan"][0]["id"] == "recover_t1"
