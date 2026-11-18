from typing import Any, Dict
from agents.base.base_agent import BaseAgent
from agents.browser.navigation_agent import NavigationAgent
from tools.browser import UniversalBrowserPrimitive

class BrowserAgent(BaseAgent):
    """Autonomous browser agent operating via live accessibility tree perception."""

    def __init__(self):
        super().__init__(name="browser_agent", description="General-purpose web navigation and interaction agent")
        self.browser_primitive = UniversalBrowserPrimitive()
        self.navigator = NavigationAgent()

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("title", "")
        snapshot = task.get("ui_snapshot", {})
        interactive_elements = self.browser_primitive.parse_interactive_nodes(snapshot)
        next_step = self.navigator.decide_next_action(goal, interactive_elements)
        return {
            "status": "success",
            "agent": self.name,
            "goal": goal,
            "perceived_elements_count": len(interactive_elements),
            "interactive_elements": interactive_elements[:20],
            "planned_action": next_step,
        }
