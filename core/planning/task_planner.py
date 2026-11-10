import json
from typing import List, Optional
from pydantic import BaseModel, Field
from core.model_router.router import model_router

class SubTask(BaseModel):
    id: str
    title: str
    agent: str = Field(description="Assigned agent: research_agent, document_agent, email_agent, browser_agent, desktop_agent")
    requires_approval: bool = False
    dependencies: List[str] = Field(default_factory=list)

class PlanDecomposition(BaseModel):
    intent: str
    subtasks: List[SubTask]

class CognitivePlanner:
    """Uses LLM reasoning or heuristic fallback to decompose natural language requests."""

    SYSTEM_PROMPT = """You are AURA's central cognitive planner.
Analyze the user command and decompose it into an ordered task graph of discrete subtasks.
Assign each subtask to the most appropriate agent:
- research_agent: Web searches, reading documentation, gathering information
- document_agent: Generating spreadsheets, markdown, presentations, code files
- email_agent: Drafting or sending emails (always set requires_approval=True)
- browser_agent: Navigating live websites, forms, and online workflows
- desktop_agent: Operating local OS applications and desktop software

Return valid JSON conforming to the schema with fields 'intent' and 'subtasks'."""

    def plan(self, command: str) -> PlanDecomposition:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Command: {command}"}
        ]

        try:
            response = model_router.completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content
            data = json.loads(raw_content)
            return PlanDecomposition(**data)
        except Exception:
            return self._heuristic_fallback(command)

    def _heuristic_fallback(self, command: str) -> PlanDecomposition:
        cmd_lower = command.lower()
        subtasks = []
        if "research" in cmd_lower or "search" in cmd_lower:
            subtasks.append(SubTask(id="task_1", title="Conduct deep research", agent="research_agent"))
        if "spreadsheet" in cmd_lower or "presentation" in cmd_lower or "slides" in cmd_lower or "prepare" in cmd_lower:
            subtasks.append(SubTask(id="task_2", title="Synthesize document artifact", agent="document_agent", dependencies=["task_1"] if subtasks else []))
        if "email" in cmd_lower or "send" in cmd_lower:
            deps = [s.id for s in subtasks]
            subtasks.append(SubTask(id="task_3", title="Draft and dispatch email", agent="email_agent", requires_approval=True, dependencies=deps))

        if not subtasks:
            subtasks.append(SubTask(id="task_1", title="General task execution", agent="research_agent"))

        return PlanDecomposition(intent="compound_task", subtasks=subtasks)

planner = CognitivePlanner()
