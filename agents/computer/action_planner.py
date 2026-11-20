import json
from typing import Any, Dict, List
from core.model_router.router import model_router

class DesktopActionPlanner:
    """Selects universal OS UI actions dynamically from live Windows UIA and OCR state."""

    SYSTEM_PROMPT = (
        "You are an autonomous desktop control module. Given a goal, live actionable Windows UI "
        "controls, and OCR text blocks, return valid JSON with keys: "
        "'action' ('click_control' | 'type_text' | 'hotkey' | 'done'), 'target_name', and optional 'text'."
    )

    def decide_next_action(
        self,
        goal: str,
        controls: List[Dict[str, Any]],
        ocr_blocks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not controls and not ocr_blocks:
            return {"action": "done", "reason": "No actionable UI elements detected"}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "goal": goal,
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
            return {"action": "done", "reason": "Fallback completion"}
