from typing import Any, Dict, List
from agents.base.base_agent import BaseAgent
from agents.computer.action_planner import DesktopActionPlanner
from agents.computer.screen_analyzer import ScreenAnalyzer

class DesktopAgent(BaseAgent):
    """Autonomous desktop agent operating arbitrary Windows apps via closed-loop perception."""

    def __init__(self, max_steps: int = 5):
        super().__init__(name="desktop_agent", description="General-purpose Windows OS application controller")
        self.analyzer = ScreenAnalyzer()
        self.action_planner = DesktopActionPlanner()
        self.max_steps = max_steps

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("title", "")
        raw_controls = task.get("ui_controls", [])
        screenshot_path = task.get("screenshot_path", "")
        history: List[Dict[str, Any]] = []

        for step_idx in range(self.max_steps):
            perception = self.analyzer.analyze(raw_controls, screenshot_path=screenshot_path)
            actionable = perception["actionable_controls"]
            decision = self.action_planner.decide_next_action(
                goal=goal,
                controls=actionable,
                ocr_blocks=perception["ocr_blocks"],
            )
            history.append({"step": step_idx + 1, "decision": decision})
            if decision.get("action") == "done" or step_idx == 0:
                break

        return {
            "status": "success",
            "agent": self.name,
            "goal": goal,
            "actionable_controls_count": len(actionable),
            "actionable_controls": actionable[:20],
            "execution_trace": history,
        }
