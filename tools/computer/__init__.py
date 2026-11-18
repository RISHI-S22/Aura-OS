import ctypes
from typing import Any, Dict, List

class UniversalDesktopPrimitive:
    """General-purpose Windows OS perception and input primitive."""

    @staticmethod
    def filter_actionable_controls(ui_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actionable_types = {"Button", "Edit", "MenuItem", "TabItem", "ListItem", "Document", "CheckBox"}
        return [
            el for el in ui_elements
            if el.get("control_type") in actionable_types and el.get("is_enabled", True)
        ]

    @staticmethod
    def get_screen_resolution() -> Dict[str, int]:
        try:
            user32 = ctypes.windll.user32
            return {
                "width": int(user32.GetSystemMetrics(0)),
                "height": int(user32.GetSystemMetrics(1)),
            }
        except Exception:
            return {"width": 1920, "height": 1080}
