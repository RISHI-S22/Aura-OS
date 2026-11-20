from typing import Any, Dict, List
from agents.base.base_agent import BaseAgent
from agents.browser.navigation_agent import NavigationAgent
from tools.browser import UniversalBrowserPrimitive

class BrowserAgent(BaseAgent):
    """Autonomous browser agent operating via iterative ARIA accessibility tree perception."""

    def __init__(self, max_steps: int = 5):
        super().__init__(name="browser_agent", description="General-purpose web navigation and interaction agent")
        self.browser_primitive = UniversalBrowserPrimitive()
        self.navigator = NavigationAgent()
        self.max_steps = max_steps

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("title", "")
        url = task.get("url")
        snapshot = task.get("ui_snapshot", {})
        trace: List[Dict[str, Any]] = []

        interactive_elements = self.browser_primitive.parse_interactive_nodes(snapshot)
        for step_idx in range(self.max_steps):
            next_step = self.navigator.decide_next_action(goal, interactive_elements)
            trace.append({"step": step_idx + 1, "action": next_step})

            if url and next_step.get("action") in ("click", "fill"):
                live_res = await self.browser_primitive.execute_browser_action(
                    url=url if step_idx == 0 else None,
                    role=next_step.get("role"),
                    name=next_step.get("name"),
                    action=next_step["action"],
                    text=next_step.get("text"),
                )
                if live_res.get("status") == "success":
                    interactive_elements = live_res.get("interactive_elements", [])
                    continue
            break

        return {
            "status": "success",
            "agent": self.name,
            "goal": goal,
            "perceived_elements_count": len(interactive_elements),
            "interactive_elements": interactive_elements[:20],
            "planned_action": trace[-1]["action"] if trace else {"action": "done"},
            "execution_trace": trace,
        }
