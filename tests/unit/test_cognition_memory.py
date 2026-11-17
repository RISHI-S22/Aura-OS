from core.cognition.context_engine import context_engine
from core.orchestration.supervisor import supervisor
from memory.manager import memory_manager

def test_context_engine_aggregates_memory():
    memory_manager.episodic.record("s1", "Inspect repo", "completed", {"t1": "ok"})
    ctx = context_engine.get_context("Inspect repo")
    assert "os" in ctx
    assert len(ctx["memory"]["recent_episodes"]) >= 1

def test_supervisor_routing_states():
    assert supervisor.supervise({"error": "timeout"}) == "REPLAN"
    assert supervisor.supervise({"approval_needed": True}) == "WAIT_FOR_APPROVAL"
    assert supervisor.supervise({"current_step": 2, "plan": [{}, {}]}) == "COMPLETED"
    assert supervisor.supervise({"current_step": 0, "plan": [{}, {}]}) == "CONTINUE"
