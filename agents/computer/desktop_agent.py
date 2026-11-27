from typing import Any, Dict, List
from agents.base.base_agent import BaseAgent
from agents.computer.action_planner import DesktopActionPlanner
from agents.computer.screen_analyzer import ScreenAnalyzer
from core.verification.screen_delta import ScreenDeltaVerifier
from tools.computer import UniversalDesktopPrimitive
from tools.vision.screen_capture import LiveScreenCapture
from tools.vision.som_grounding import SetOfMarksGrounder

class DesktopAgent(BaseAgent):
    """Autonomous desktop agent operating arbitrary Windows apps via UIA + OCR + Set-of-Marks."""

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

        history: List[Dict[str, Any]] = []
        actionable: List[Dict[str, Any]] = []

        for step_idx in range(self.max_steps):
            screenshot_path = task.get("screenshot_path", "")
            if live_mode and not screenshot_path:
                screenshot_path = LiveScreenCapture.capture_foreground_or_screen() or ""

            perception = self.analyzer.analyze(raw_controls, screenshot_path=screenshot_path)
            actionable = perception["actionable_controls"]
            marks = SetOfMarksGrounder.build_grounded_elements(actionable, perception["ocr_blocks"])
            before_sig = ScreenDeltaVerifier.compute_state_signature(actionable)

            decision = self.action_planner.decide_next_action(
                goal=goal,
                controls=actionable,
                ocr_blocks=perception["ocr_blocks"],
                grounded_marks=marks,
            )
            coords = None
            if decision.get("mark_id") is not None:
                coords = SetOfMarksGrounder.resolve_mark_center(marks, int(decision["mark_id"]))

            act_result = UniversalDesktopPrimitive.execute_os_action(
                action=decision.get("action", "done"),
                target_name=decision.get("target_name", ""),
                text=decision.get("text"),
                coords=coords,
                dry_run=not live_mode,
            )

            if decision.get("action") == "done" or not live_mode:
                history.append({
                    "step": step_idx + 1,
                    "before_sig": before_sig,
                    "screenshot": screenshot_path or None,
                    "state_changed": False,
                    "decision": decision,
                    "actuation": act_result,
                })
                break

            next_controls = UniversalDesktopPrimitive.capture_active_window_controls()
            next_actionable = self.analyzer.analyze(next_controls)["actionable_controls"]
            changed = ScreenDeltaVerifier.has_state_changed(actionable, next_actionable)

            history.append({
                "step": step_idx + 1,
                "before_sig": before_sig,
                "screenshot": screenshot_path or None,
                "state_changed": changed,
                "decision": decision,
                "actuation": act_result,
            })
            raw_controls = next_controls

        return {
            "status": "success",
            "agent": self.name,
            "goal": goal,
            "actionable_controls_count": len(actionable),
            "actionable_controls": actionable[:20],
            "execution_trace": history,
        }
