import asyncio
import agents  # noqa: F401
from core.orchestration.dispatcher import dispatcher

def test_dispatch_valid_research_agent():
    task = {"id": "t1", "title": "Benchmark LLM latency", "agent": "research_agent"}
    result = asyncio.run(dispatcher.dispatch("research_agent", task))
    assert result["status"] == "success"
    assert result["agent"] == "research_agent"

def test_dispatch_unknown_agent_returns_error():
    task = {"id": "t2", "title": "Unknown task"}
    result = asyncio.run(dispatcher.dispatch("non_existent_agent", task))
    assert result["status"] == "error"
    assert "not registered" in result["message"]
