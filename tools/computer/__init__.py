import ctypes
import os
import subprocess
from typing import Any, Dict, List, Optional

class UniversalDesktopPrimitive:
    """General-purpose Windows OS perception, window management, and input actuation primitive."""

    ACTIONABLE_TYPES = {"Button", "Edit", "MenuItem", "TabItem", "ListItem", "Document", "CheckBox"}

    @classmethod
    def filter_actionable_controls(cls, ui_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            el for el in ui_elements
            if el.get("control_type") in cls.ACTIONABLE_TYPES and el.get("is_enabled", True)
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

    @staticmethod
    def discover_start_menu_apps() -> Dict[str, str]:
        """Dynamically indexes installed Windows Start Menu shortcuts without hardcoded paths."""
        apps: Dict[str, str] = {}
        roots = [
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        ]
        for root in roots:
            if not root or not os.path.isdir(root):
                continue
            for dirpath, _, filenames in os.walk(root):
                for fname in filenames:
                    if fname.lower().endswith(".lnk"):
                        app_name = os.path.splitext(fname)[0].lower()
                        apps[app_name] = os.path.join(dirpath, fname)
        return apps

    @classmethod
    def focus_or_launch_app(cls, app_query: str, dry_run: bool = True) -> Dict[str, Any]:
        """Focuses a matching open window or launches the closest Start Menu shortcut."""
        query = app_query.strip().lower()
        if not query:
            return {"executed": False, "reason": "Empty application query"}

        if dry_run:
            return {"executed": True, "mode": "dry_run", "action": "focus_or_launch", "app": app_query}

        try:
            from pywinauto import Desktop
            for win in Desktop(backend="uia").windows():
                title = (win.window_text() or "").strip()
                if query in title.lower():
                    win.set_focus()
                    return {"executed": True, "action": "focused_window", "window_title": title}
        except Exception:
            pass

        apps = cls.discover_start_menu_apps()
        for name, shortcut_path in apps.items():
            if query in name:
                os.startfile(shortcut_path)
                return {"executed": True, "action": "launched_shortcut", "app": name}

        try:
            subprocess.Popen(["cmd", "/c", "start", "", app_query], shell=False)
            return {"executed": True, "action": "shell_start", "app": app_query}
        except Exception as exc:
            return {"executed": False, "reason": str(exc)}

    @classmethod
    def capture_active_window_controls(cls) -> List[Dict[str, Any]]:
        """Dynamically inspects the active foreground Windows UI Automation tree."""
        try:
            from pywinauto import Desktop
            active_win = Desktop(backend="uia").active()
            if not active_win:
                return []
            extracted: List[Dict[str, Any]] = []
            for ctrl in active_win.descendants()[:150]:
                info = ctrl.element_info
                ctype = getattr(info, "control_type", "")
                name = (getattr(info, "name", "") or "").strip()
                if ctype in cls.ACTIONABLE_TYPES and name:
                    extracted.append({
                        "control_type": ctype,
                        "name": name,
                        "is_enabled": bool(getattr(info, "enabled", True)),
                    })
            return extracted
        except Exception:
            return []

    @classmethod
    def execute_os_action(
        cls,
        action: str,
        target_name: str = "",
        text: Optional[str] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Executes universal OS UIA actions without hardcoded screen coordinates."""
        if action == "launch_app":
            return cls.focus_or_launch_app(target_name or (text or ""), dry_run=dry_run)

        if dry_run:
            return {
                "executed": True,
                "mode": "dry_run",
                "action": action,
                "target_name": target_name,
            }
        try:
            from pywinauto import Desktop
            from pywinauto.keyboard import send_keys

            if action == "hotkey" and text:
                send_keys(text)
                return {"executed": True, "action": "hotkey", "keys": text}

            active_win = Desktop(backend="uia").active()
            if not active_win:
                return {"executed": False, "reason": "No active foreground window"}

            for ctrl in active_win.descendants()[:150]:
                name = (getattr(ctrl.element_info, "name", "") or "").strip()
                if target_name and name.lower() == target_name.lower():
                    if action == "click_control":
                        ctrl.invoke() if hasattr(ctrl, "invoke") else ctrl.click_input()
                        return {"executed": True, "action": "click_control", "target_name": name}
                    if action == "type_text" and text is not None:
                        ctrl.set_focus()
                        send_keys(text, with_spaces=True)
                        return {"executed": True, "action": "type_text", "target_name": name}

            return {"executed": False, "reason": f"Control '{target_name}' not found in active window"}
        except Exception as exc:
            return {"executed": False, "reason": str(exc)}
