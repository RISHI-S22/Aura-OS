from dataclasses import dataclass

@dataclass(frozen=True)
class PlannedTask:
    task_id: str
    description: str
    agent: str
    depends_on: tuple[str, ...] = ()
    requires_approval: bool = False

def decompose_command(command: str, intent: str) -> list[PlannedTask]:
    """Create a conservative starter plan. No task is executed here."""
    text = command.casefold()
    tasks: list[PlannedTask] = []

    if any(word in text for word in ("research", "search", "find", "compare")):
        tasks.append(PlannedTask("research", f"Research and gather sources for: {command}", "research"))
        tasks.append(PlannedTask("verify", "Verify important claims against their sources", "research", ("research",)))

    if any(word in text for word in ("spreadsheet", "excel", "report", "presentation", "document")):
        dependency = ("verify",) if any(t.task_id == "verify" for t in tasks) else ()
        tasks.append(PlannedTask("create_artifact", "Prepare the requested document or artifact", "document", dependency))

    if any(word in text for word in ("email", "send", "message")):
        dependency = tuple(t.task_id for t in tasks)
        tasks.append(PlannedTask("send_message", "Prepare and send the requested message", "personal", dependency, True))

    if any(word in text for word in ("schedule", "calendar", "remind")):
        tasks.append(PlannedTask("calendar_action", "Prepare the requested calendar or reminder action", "personal", (), True))

    if not tasks:
        tasks.append(PlannedTask("analyze", f"Analyze and respond to: {command}", "general"))

    return tasks
