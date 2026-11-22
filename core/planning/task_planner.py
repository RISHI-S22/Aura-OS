import json
from typing import List, Optional
from pydantic import BaseModel, Field
from core.cognition.context_engine import context_engine
from core.model_router.router import model_router

class SubTask(BaseModel):
    id: str
    title: str
    agent: str
    dependencies: List[str] = Field(default_factory=list)
    requires_approval: bool = False

class ExecutionPlan(BaseModel):
    intent: str
    subtasks: List[SubTask]

class CognitivePlanner:
    """Decomposes arbitrary natural-language goals into topological multi-agent DAGs."""

    SYSTEM_PROMPT = (
        "You are AURA's Cognitive Planner. Decompose the user's goal into a minimal, ordered DAG "
        "of subtasks using ONLY these agents: 'research_agent', 'document_agent', 'browser_agent', "
        "'desktop_agent'. Set 'requires_approval' to true ONLY for irreversible external actions "
        "(sending messages/emails, purchases, deleting files, terminal execution). "
        "Return valid JSON matching: {\"intent\": str, \"subtasks\": [{\"id\": str, \"title\": str, "
        "\"agent\": str, \"dependencies\": [str], \"requires_approval\": bool}]}."
    )

    def plan(self, command: str) -> ExecutionPlan:
        ctx = context_engine.get_context(command)
        learned = ctx.get("memory", {}).get("learned_procedures", [])

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "command": command,
                    "os": ctx.get("os"),
                    "learned_procedures": learned,
                }),
            },
        ]

        try:
            resp = model_router.completion(
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = json.loads(resp.choices[0].message.content)
            subtasks = [SubTask(**t) for t in raw.get("subtasks", [])]
            if subtasks:
                return ExecutionPlan(intent=raw.get("intent", "autonomous_task"), subtasks=subtasks)
        except Exception:
            pass

        return self._heuristic_plan(command)

    def _heuristic_plan(self, command: str) -> ExecutionPlan:
        cmd = command.lower()
        tasks: List[SubTask] = []

        if "research" in cmd and ("spreadsheet" in cmd or "document" in cmd or "report" in cmd):
            tasks.append(SubTask(id="t1", title=f"Gather data: {command}", agent="research_agent"))
            tasks.append(SubTask(id="t2", title=f"Synthesize output: {command}", agent="document_agent", dependencies=["t1"]))
            return ExecutionPlan(intent="research_and_synthesis", subtasks=tasks)

        if any(w in cmd for w in ("email", "send", "message", "buy", "purchase", "delete")):
            tasks.append(SubTask(id="t1", title=command, agent="desktop_agent", requires_approval=True))
            return ExecutionPlan(intent="gated_action", subtasks=tasks)

        if any(w in cmd for w in ("browse", "website", "search web", "url", "http")):
            tasks.append(SubTask(id="t1", title=command, agent="browser_agent"))
            return ExecutionPlan(intent="web_navigation", subtasks=tasks)

        if any(w in cmd for w in ("open", "click", "type", "window", "app", "draw", "code")):
            tasks.append(SubTask(id="t1", title=command, agent="desktop_agent"))
            return ExecutionPlan(intent="desktop_control", subtasks=tasks)

        tasks.append(SubTask(id="t1", title=command, agent="research_agent"))
        return ExecutionPlan(intent="general_inquiry", subtasks=tasks)

planner = CognitivePlanner()
