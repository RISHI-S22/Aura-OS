from typing import Any, Dict
from langgraph.graph import END, StateGraph
from core.orchestration.dispatcher import dispatcher
from core.orchestration.state import AgentState
from core.planning.dependency_graph import DependencyGraph
from core.planning.task_planner import planner

def plan_node(state: AgentState) -> Dict[str, Any]:
    plan_obj = planner.plan(state["command"])
    subtasks = [t.model_dump() for t in plan_obj.subtasks]

    dag = DependencyGraph()
    for t in subtasks:
        dag.add_node(t["id"], t.get("dependencies", []))
    ordered_ids = dag.topological_sort()
    id_map = {t["id"]: t for t in subtasks}
    ordered_plan = [id_map[tid] for tid in ordered_ids]

    return {
        "intent": plan_obj.intent,
        "plan": ordered_plan,
        "current_step": 0,
        "status": "planned",
    }

async def execute_node(state: AgentState) -> Dict[str, Any]:
    plan = state.get("plan", [])
    step = state.get("current_step", 0)
    artifacts = dict(state.get("artifacts", {}))

    while step < len(plan):
        task = dict(plan[step])
        if task.get("requires_approval"):
            return {
                "current_step": step,
                "artifacts": artifacts,
                "approval_needed": True,
                "status": "pending_approval",
            }

        # Attach upstream dependency outputs so downstream agents have full context
        dep_outputs = {
            dep_id: artifacts[dep_id]
            for dep_id in task.get("dependencies", [])
            if dep_id in artifacts
        }
        task["context"] = dep_outputs

        result = await dispatcher.dispatch(task["agent"], task)
        if result.get("status") == "error":
            return {
                "current_step": step,
                "artifacts": artifacts,
                "status": "failed",
                "error": result.get("message", "Subtask execution failed"),
            }

        artifacts[task["id"]] = result
        step += 1

    return {
        "current_step": step,
        "artifacts": artifacts,
        "approval_needed": False,
        "status": "completed",
    }

def build_aura_graph():
    builder = StateGraph(AgentState)
    builder.add_node("planner", plan_node)
    builder.add_node("executor", execute_node)
    builder.set_entry_point("planner")
    builder.add_edge("planner", "executor")
    builder.add_edge("executor", END)
    return builder.compile()

aura_graph = build_aura_graph()
