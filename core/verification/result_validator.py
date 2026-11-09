def validate_pipeline_result(state: dict) -> dict:
    plan = state.get("plan", [])
    log = state.get("execution_log", [])
    valid_ids = {task["task_id"] for task in plan}
    logged_ids = {item["task_id"] for item in log}
    return {
        "valid": bool(plan) and valid_ids == logged_ids,
        "planned_task_count": len(plan),
        "logged_task_count": len(log),
        "all_actions_executed": any(item.get("executed", False) for item in log),
        "mode": "dry_run",
    }
