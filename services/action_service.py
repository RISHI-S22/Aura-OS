"""
Aura-OS Universal Action Execution Service
Handles universal desktop application resolution, universal browser dispatch,
media controls, and scheduled actions.
"""

import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import pyautogui
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET

URI_SHORTCUTS = {
    "whatsapp": "whatsapp:",
    "spotify": "spotify:",
    "calculator": "calculator:",
    "calc": "calculator:",
    "settings": "ms-settings:",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "store": "ms-windows-store:",
    "mail": "outlookmail:",
    "calendar": "outlookcal:",
}

WIN_EXECUTABLES = {
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "notepad": "notepad",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "paint": "mspaint",
    "task manager": "taskmgr",
    "file explorer": "explorer",
    "explorer": "explorer",
    "control panel": "control",
}

BROWSER_BINARIES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "brave": "brave",
    "opera": "opera",
}

class ActionExecutor:
    def __init__(self):
        self.context = zmq.Context()
        self.pull_actions = self.context.socket(zmq.PULL)
        self.pull_actions.bind(f"tcp://{NET.HOST}:{NET.ACTION_PORT}")

        self.pub_tts = self.context.socket(zmq.PUB)
        self.pub_tts.connect(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")

    def speak(self, text: str):
        payload = {"text": text, "gen_id": int(time.time() * 1000)}
        self.pub_tts.send_string(f"TTS_CHUNK {json.dumps(payload)}")
        print(f"[Aura Step]: {text}")
        time.sleep(1.0)

    def launch_universal_app(self, app_name: str):
        target = app_name.lower().strip()
        self.speak(f"Opening {app_name} on your desktop.")

        # 1. Direct URI Protocol
        if target in URI_SHORTCUTS:
            try:
                subprocess.Popen(f"start {URI_SHORTCUTS[target]}", shell=True)
                return
            except Exception:
                pass

        # 2. Known Windows Executable
        if target in WIN_EXECUTABLES:
            try:
                subprocess.Popen(f"start {WIN_EXECUTABLES[target]}", shell=True)
                return
            except Exception:
                pass

        # 3. Direct execution via Windows PATH
        res = subprocess.run(f"where {target}", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.Popen(f"start {target}", shell=True)
            return

        # 4. Search and Launch via Windows Start Menu / shell:AppsFolder via PowerShell
        ps_command = f"""
        $app = Get-StartApps | Where-Object {{ $_.Name -like "*{target}*" }} | Select-Object -First 1
        if ($app) {{
            Start-Process ("shell:AppsFolder\\" + $app.AppID)
            exit 0
        }} else {{
            exit 1
        }}
        """
        ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, text=True)
        if ps_res.returncode == 0:
            return

        # 5. Direct Windows Shell Search Keystroke Fallback
        print(f"[!] Resolving '{app_name}' via Windows Shell Dispatch...")
        pyautogui.press("win")
        time.sleep(0.3)
        pyautogui.write(target, interval=0.03)
        time.sleep(0.5)
        pyautogui.press("enter")

    def normalize_destination(self, raw_target: str) -> str:
        target = raw_target.strip().lower()
        if target.startswith("http://") or target.startswith("https://"):
            return target
        if any(target.endswith(tld) for tld in [".com", ".org", ".net", ".io", ".edu", ".gov", ".in", ".co", ".ai", ".tv"]):
            return f"https://{target}"

        domain_lookup = {
            "youtube": "https://www.youtube.com",
            "netflix": "https://www.netflix.com",
            "github": "https://www.github.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://www.x.com",
            "x": "https://www.x.com",
            "linkedin": "https://www.linkedin.com",
            "amazon": "https://www.amazon.com",
            "chatgpt": "https://chatgpt.com",
        }
        for name, url in domain_lookup.items():
            if name in target:
                return url

        encoded = urllib.parse.quote(raw_target)
        return f"https://www.google.com/search?q={encoded}"

    def execute_universal_browse(self, browser_name: str, site_or_query: str):
        browser_key = browser_name.lower().strip()
        binary = BROWSER_BINARIES.get(browser_key, "chrome")
        display_name = browser_name.capitalize() if browser_name else "Chrome"
        target_url = self.normalize_destination(site_or_query)

        self.speak(f"Step one. Launching {display_name} on your desktop.")
        try:
            subprocess.Popen(f"start {binary}", shell=True)
        except Exception:
            subprocess.Popen("start chrome", shell=True)
        time.sleep(2.5)

        self.speak(f"Step two. Navigating to {site_or_query}.")
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.4)
        pyautogui.write(target_url, interval=0.03)
        pyautogui.press("enter")
        time.sleep(2.0)
        self.speak(f"{site_or_query} is now open in {display_name}.")

    def schedule_pause(self, seconds: int):
        self.speak(f"Timer set. I will pause playback in {seconds} seconds.")
        def timer_thread():
            time.sleep(seconds)
            pyautogui.press("playpause")
            self.speak("Time elapsed. Media playback paused.")
        threading.Thread(target=timer_thread, daemon=True).start()

    def run(self):
        print(f"[*] Universal Action Service active on port {NET.ACTION_PORT}...")
        while True:
            raw_action = self.pull_actions.recv_string()
            data = json.loads(raw_action)
            action_type = data.get("action")

            if action_type == "LAUNCH_APP":
                app = data.get("app", "")
                threading.Thread(target=self.launch_universal_app, args=(app,), daemon=True).start()

            elif action_type == "UNIVERSAL_BROWSE":
                browser = data.get("browser", "chrome")
                target = data.get("target", "")
                threading.Thread(
                    target=self.execute_universal_browse,
                    args=(browser, target),
                    daemon=True
                ).start()

            elif action_type == "SCHEDULED_PAUSE":
                seconds = data.get("seconds", 0)
                self.schedule_pause(seconds)

            elif action_type == "MEDIA_TOGGLE":
                pyautogui.press("playpause")
                self.speak("Toggled media playback.")

if __name__ == "__main__":
    executor = ActionExecutor()
    executor.run()