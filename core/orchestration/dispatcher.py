def dry_run_dispatch(plan: list[dict]) -> list[dict]:
    """Record what would be dispatched; deliberately performs no external action."""
    return [
        {
            "task_id": task["task_id"],
            "agent": task["agent"],
            "status": "ready_for_tool_integration",
            "executed": False,
            "note": "Dry run only: no external action was performed.",
        }
        for task in plan
    ]
