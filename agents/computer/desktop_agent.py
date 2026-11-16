from typing import Any, Dict
from agents.base.base_agent import BaseAgent
from tools.computer import UniversalDesktopPrimitive

class DesktopAgent(BaseAgent):
    """Autonomous desktop agent operating arbitrary Windows applications via UI trees."""

    def __init__(self):
        super().__init__(name="desktop_agent", description="General-purpose Windows OS application controller")
        self.desktop_primitive = UniversalDesktopPrimitive()

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        raw_controls = task.get("ui_controls", [])
        actionable = self.desktop_primitive.filter_actionable_controls(raw_controls)
        return {
            "status": "success",
            "agent": self.name,
            "goal": task.get("title", ""),
            "actionable_controls_count": len(actionable),
            "actionable_controls": actionable[:20],
        }
