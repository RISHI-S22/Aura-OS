from fastapi.testclient import TestClient
from agents.browser.navigation_agent import NavigationAgent
from aura.api.main import app
from aura.integrations.mcp import MCPToolRegistry

client = TestClient(app)

def test_mcp_tool_registration():
    registry = MCPToolRegistry()
    registry.register_tool(
        name="read_workspace",
        description="Reads a file inside workspace",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda path: f"content of {path}",
    )
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "read_workspace"
    assert registry.get_handler("read_workspace")("notes.md") == "content of notes.md"

def test_navigation_agent_fallback_action():
    nav = NavigationAgent()
    action = nav.decide_next_action(
        goal="Search documentation",
        elements=[{"role": "searchbox", "name": "Search docs"}],
    )
    assert action["role"] == "searchbox"
    assert action["name"] == "Search docs"

def test_capabilities_endpoint():
    resp = client.get("/api/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert "research_agent" in data["agents"]
    assert "browser_agent" in data["agents"]
