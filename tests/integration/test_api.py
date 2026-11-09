from fastapi.testclient import TestClient
from aura.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_command_pipeline_runs_in_dry_run():
    response = client.post("/api/v1/commands", json={
        "command": "Research three AI companies and prepare a comparison spreadsheet"
    })
    assert response.status_code == 200
    body = response.json()
    assert len(body["plan"]) >= 2
    assert body["verification"]["valid"] is True
    assert body["verification"]["all_actions_executed"] is False
