"""
Aura-OS Window Manager & Process State Monitor
Detects both active windows and background/tray processes (WhatsApp, Spotify, etc.)
"""

import subprocess
import time
import pygetwindow as gw
import win32con
import win32gui
import win32process

class WindowManager:
    @staticmethod
    def get_window_by_keyword(keyword: str):
        target = keyword.lower().strip()
        
        # 1. Search all visible/minimized windows first
        windows = gw.getAllWindows()
        for w in windows:
            if w.title and target in w.title.lower():
                return w
                
        # 2. Check for UWP or background processes running without title
        try:
            ps_cmd = f"(Get-Process | Where-Object {{ $_.ProcessName -like '*{target}*' }}).Count"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if int(res.stdout.strip() or 0) > 0:
                # Target process is running; wake its window
                for w in windows:
                    if w._hWnd:
                        _, pid = win32process.GetWindowThreadProcessId(w._hWnd)
                        proc_check = subprocess.run(
                            ["powershell", "-NoProfile", f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName"],
                            capture_output=True, text=True
                        )
                        if target in proc_check.stdout.lower():
                            return w
        except Exception:
            pass

        return None

    @staticmethod
    def ensure_foreground(window_or_title) -> bool:
        win = None
        if isinstance(window_or_title, str):
            win = WindowManager.get_window_by_keyword(window_or_title)
        else:
            win = window_or_title

        if not win:
            # Fallback launch via URI protocol if registered
            if isinstance(window_or_title, str):
                target = window_or_title.lower().strip()
                try:
                    subprocess.Popen(f"start {target}:", shell=True)
                    time.sleep(1.0)
                    win = WindowManager.get_window_by_keyword(target)
                except Exception:
                    pass

        if not win:
            return False

        hwnd = win._hWnd
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)

            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.4)
            return True
        except Exception:
            try:
                win32gui.BringWindowToTop(hwnd)
                win32gui.SetFocus(hwnd)
                return True
            except Exception:
                return False

    @staticmethod
    def is_app_running(app_name: str) -> bool:
        return WindowManager.get_window_by_keyword(app_name) is not None