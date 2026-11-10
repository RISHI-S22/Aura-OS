from fastapi.testclient import TestClient
from aura.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_command_pipeline_runs_in_dry_run():
    payload = {"command": "Research three AI companies and prepare a comparison spreadsheet"}
    response = client.post("/api/v1/commands", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    assert len(data["plan"]) >= 2
    assert data["status"] in ("executing", "completed", "planned")
