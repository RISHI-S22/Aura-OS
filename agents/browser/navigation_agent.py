import json
from typing import Any, Dict, List
from core.model_router.router import model_router

class NavigationAgent:
    """Selects universal ARIA browser actions dynamically using LLM reasoning."""

    SYSTEM_PROMPT = (
        "You are an autonomous web navigation module. Given a user goal and a list of "
        "live interactive ARIA elements (role and name), return valid JSON with keys: "
        "'action' ('click' | 'fill' | 'done'), 'role', 'name', and optional 'text'."
    )

    def decide_next_action(self, goal: str, elements: List[Dict[str, str]]) -> Dict[str, Any]:
        if not elements:
            return {"action": "done", "reason": "No interactive elements perceived"}

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"goal": goal, "elements": elements[:20]})},
        ]
        try:
            resp = model_router.completion(
                messages=messages,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content)
        except Exception:
            first = elements[0]
            return {"action": "click", "role": first["role"], "name": first["name"]}
