from typing import Any, Dict, List

class UniversalDesktopPrimitive:
    """Inspects active Windows UI Automation trees for arbitrary desktop applications."""

    @staticmethod
    def filter_actionable_controls(ui_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actionable_types = {"Button", "Edit", "MenuItem", "TabItem", "ListItem", "Document"}
        return [
            el for el in ui_elements
            if el.get("control_type") in actionable_types and el.get("is_enabled", True)
        ]
