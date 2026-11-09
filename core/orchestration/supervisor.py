from core.planning.task_planner import create_plan
from core.orchestration.dispatcher import dry_run_dispatch

def understand_and_plan(state: dict) -> dict:
    result = create_plan(state["command"])
    return {"intent": result["intent"], "plan": result["tasks"]}

def dispatch_tasks(state: dict) -> dict:
    return {"execution_log": dry_run_dispatch(state.get("plan", []))}

def build_response(state: dict) -> dict:
    count = len(state.get("plan", []))
    return {
        "response": (
            f"Aura understood the command and created {count} task(s). "
            "This milestone ran in dry-run mode; no external actions were performed."
        )
    }
