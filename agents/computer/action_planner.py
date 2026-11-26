import json
from typing import Any, Dict, List, Optional
from core.model_router.router import model_router

class DesktopActionPlanner:
    """Selects universal OS UI actions dynamically from live Windows UIA, OCR, and Set-of-Marks."""

    SYSTEM_PROMPT = (
        "You are an autonomous desktop control module. Given a goal and grounded Set-of-Marks "
        "elements (UIA controls + OCR regions), return valid JSON with keys: "
        "'action' ('launch_app' | 'click_control' | 'click_mark' | 'type_text' | 'hotkey' | 'done'), "
        "'target_name', optional 'mark_id' (int), and optional 'text'."
    )

    def decide_next_action(
        self,
        goal: str,
        controls: List[Dict[str, Any]],
        ocr_blocks: List[Dict[str, Any]],
        grounded_marks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not controls and not ocr_blocks:
            lowered = goal.lower()
            if lowered.startswith(("open ", "launch ", "start ")):
                app_name = goal.split(maxsplit=1)[1].strip()
                return {"action": "launch_app", "target_name": app_name}
            return {"action": "done", "reason": "No actionable UI elements detected"}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "goal": goal,
                    "grounded_marks": (grounded_marks or [])[:25],
                    "controls": controls[:20],
                    "ocr_blocks": ocr_blocks[:15],
                }),
            },
        ]
        try:
            resp = model_router.completion(
                messages=messages,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            if controls:
                first = controls[0]
                act = "type_text" if first.get("control_type") in ("Edit", "Document") else "click_control"
                return {"action": act, "target_name": first.get("name", "")}
            if grounded_marks:
                return {"action": "click_mark", "mark_id": grounded_marks[0]["mark_id"]}
            return {"action": "done", "reason": "Fallback completion"}
