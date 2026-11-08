"""
Aura-OS Universal Screen & Application State Reader
Inspects Windows UI Automation trees, active window text,
and extracts visible content from desktop software and browsers.
"""

import os
import sys
import time
import win32gui
import win32process

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class ScreenReader:
    @staticmethod
    def get_active_window_details() -> dict:
        """Returns details on the current foreground application."""
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return {"title": "", "class": "", "hwnd": 0}
        
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        return {
            "hwnd": hwnd,
            "title": title,
            "class_name": class_name,
            "pid": pid
        }

    @staticmethod
    def inspect_window_controls(hwnd: int) -> list:
        """Enumerates child UI controls and text inside a target window."""
        controls = []

        def enum_child_proc(child_hwnd, param):
            txt = win32gui.GetWindowText(child_hwnd)
            cls = win32gui.GetClassName(child_hwnd)
            visible = win32gui.IsWindowVisible(child_hwnd)
            if visible and (txt or cls):
                controls.append({"hwnd": child_hwnd, "text": txt, "class": cls})
            return True

        try:
            win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
        except Exception:
            pass
        return controls

    @staticmethod
    def get_running_app_summary() -> str:
        """Generates a contextual text dump of open user applications."""
        app_list = []
        def enum_windows(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and len(title.strip()) > 2 and title not in ["Program Manager", "Settings"]:
                    app_list.append(title.strip())
            return True

        win32gui.EnumWindows(enum_windows, None)
        return "\n".join([f"- {app}" for app in app_list[:15]])