from typing import Any, Dict, List
from agents.base.base_agent import BaseAgent
from agents.computer.action_planner import DesktopActionPlanner
from agents.computer.screen_analyzer import ScreenAnalyzer
from core.verification.screen_delta import ScreenDeltaVerifier
from tools.computer import UniversalDesktopPrimitive

class DesktopAgent(BaseAgent):
    """Autonomous desktop agent operating arbitrary Windows apps via closed-loop perception."""

    def __init__(self, max_steps: int = 5):
        super().__init__(name="desktop_agent", description="General-purpose Windows OS application controller")
        self.analyzer = ScreenAnalyzer()
        self.action_planner = DesktopActionPlanner()
        self.max_steps = max_steps

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        goal = task.get("title", "")
        live_mode = bool(task.get("live_os", False))
        raw_controls = task.get("ui_controls")
        if raw_controls is None:
            raw_controls = UniversalDesktopPrimitive.capture_active_window_controls() if live_mode else []

        screenshot_path = task.get("screenshot_path", "")
        history: List[Dict[str, Any]] = []
        actionable: List[Dict[str, Any]] = []

        for step_idx in range(self.max_steps):
            perception = self.analyzer.analyze(raw_controls, screenshot_path=screenshot_path)
            actionable = perception["actionable_controls"]
            before_sig = ScreenDeltaVerifier.compute_state_signature(actionable)

            decision = self.action_planner.decide_next_action(
                goal=goal,
                controls=actionable,
                ocr_blocks=perception["ocr_blocks"],
            )
            act_result = UniversalDesktopPrimitive.execute_os_action(
                action=decision.get("action", "done"),
                target_name=decision.get("target_name", ""),
                text=decision.get("text"),
                dry_run=not live_mode,
            )
            history.append({
                "step": step_idx + 1,
                "before_sig": before_sig,
                "decision": decision,
                "actuation": act_result,
            })

            if decision.get("action") == "done" or not live_mode:
                break

            raw_controls = UniversalDesktopPrimitive.capture_active_window_controls()

        return {
            "status": "success",
            "agent": self.name,
            "goal": goal,
            "actionable_controls_count": len(actionable),
            "actionable_controls": actionable[:20],
            "execution_trace": history,
        }
