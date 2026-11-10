from typing import Dict, Any
from langgraph.graph import StateGraph, END
from core.orchestration.state import AgentState
from core.planning.task_planner import planner

def plan_node(state: AgentState) -> Dict[str, Any]:
    plan_obj = planner.plan(state["command"])
    return {
        "intent": plan_obj.intent,
        "plan": [task.model_dump() for task in plan_obj.subtasks],
        "current_step": 0,
        "status": "planned"
    }

def execute_node(state: AgentState) -> Dict[str, Any]:
    plan = state.get("plan", [])
    step = state.get("current_step", 0)
    if step < len(plan):
        current_task = plan[step]
        if current_task.get("requires_approval"):
            return {"approval_needed": True, "status": "pending_approval"}
        return {
            "current_step": step + 1,
            "status": "executing",
            "artifacts": {current_task["id"]: f"Result from {current_task['agent']}"}
        }
    return {"status": "completed"}

def build_aura_graph():
    builder = StateGraph(AgentState)
    builder.add_node("planner", plan_node)
    builder.add_node("executor", execute_node)
    
    builder.set_entry_point("planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", END)
    
    return builder.compile()

aura_graph = build_aura_graph()
