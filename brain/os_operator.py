"""
Aura-OS Universal Screen & UI Operator
Executes arbitrary human workflows across any Windows software, web platform,
music streamer, or video portal using dynamic UI recipes, clipboard injection,
and confirmation gates.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import mss
import pyautogui
import pyperclip
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import MODELS, PATHS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Disable corner fail-safe to prevent sudden thread crashes
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.25

URI_MAP = {
    "whatsapp": "whatsapp:",
    "spotify": "spotify:",
    "calculator": "calculator:",
    "calc": "calculator:",
    "settings": "ms-settings:",
}

class UniversalOSOperator:
    def __init__(self, tts_callback=None):
        self.tts_callback = tts_callback or (lambda text: print(f"[Aura Step]: {text}"))
        self.awaiting_confirmation = None
        self.screenshot_dir = os.path.join(PATHS.WORKSPACE, "screen_debug")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def speak(self, text: str):
        self.tts_callback(text)
        time.sleep(0.7)

    def launch_target(self, target: str):
        clean = target.lower().strip()

        # 1. Direct Web URLs
        if clean.startswith("http://") or clean.startswith("https://"):
            subprocess.Popen(f'start chrome "{target}"', shell=True)
            return

        # 2. Known Protocol URIs
        if clean in URI_MAP:
            subprocess.Popen(f"start {URI_MAP[clean]}", shell=True)
            return
        if ":" in clean and not clean.startswith("c:") and not clean.startswith("e:"):
            subprocess.Popen(f"start {clean}", shell=True)
            return

        # 3. Direct Start execution via PATH
        res = subprocess.run(f"where {clean}", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            subprocess.Popen(f"start {clean}", shell=True)
            return

        # 4. Windows Start Menu lookup
        ps_cmd = f"""
        $app = Get-StartApps | Where-Object {{ $_.Name -like "*{clean}*" }} | Select-Object -First 1
        if ($app) {{
            Start-Process ("shell:AppsFolder\\" + $app.AppID)
            exit 0
        }} else {{
            exit 1
        }}
        """
        ps_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if ps_res.returncode == 0:
            return

        # 5. Windows Key Search Dispatch
        pyautogui.press("win")
        time.sleep(0.3)
        pyperclip.copy(clean)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)
        pyautogui.press("enter")

    def handle_universal_media(self, platform: str, query: str) -> bool:
        """
        Handles search and play across any music or video platform.
        """
        platform = platform.lower().strip()
        self.speak(f"Step one. Opening {platform.capitalize()} to search for {query}.")

        if platform == "spotify":
            self.launch_target("spotify:")
            time.sleep(2.5)

            self.speak(f"Step two. Searching for {query}.")
            pyautogui.hotkey("ctrl", "k")
            time.sleep(0.4)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")

            pyperclip.copy(query)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.3)
            pyautogui.press("enter")

            # Wait for search results to render
            time.sleep(2.0)
            self.speak(f"Step three. Playing {query}.")
            # Tab to Top Result card
            pyautogui.press("tab")
            time.sleep(0.15)
            pyautogui.press("tab")
            time.sleep(0.15)
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        elif platform == "youtube":
            encoded = urllib.parse.quote(query)
            self.launch_target(f"https://www.youtube.com/results?search_query={encoded}")
            time.sleep(3.5)

            self.speak(f"Selecting and playing the first video result for {query}.")
            # Navigate to the first video link in YouTube search results
            pyautogui.press("tab")
            time.sleep(0.1)
            pyautogui.press("tab")
            time.sleep(0.1)
            pyautogui.press("tab")
            time.sleep(0.1)
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        elif platform in ["jiosaavn", "saavn"]:
            encoded = urllib.parse.quote(query)
            self.launch_target(f"https://www.jiosaavn.com/search/{encoded}")
            time.sleep(4.0)

            self.speak(f"Playing top track for {query} on JioSaavn.")
            # Focus search results and trigger first track
            pyautogui.press("tab")
            time.sleep(0.1)
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        elif platform in ["apple music", "applemusic"]:
            self.launch_target("https://music.apple.com")
            time.sleep(3.5)
            pyautogui.press("/")
            time.sleep(0.3)
            pyperclip.copy(query)
            pyautogui.hotkey("ctrl", "v")
            pyautogui.press("enter")
            time.sleep(2.0)
            pyautogui.press("tab")
            pyautogui.press("enter")
            return True

        elif platform in ["netflix"]:
            encoded = urllib.parse.quote(query)
            self.launch_target(f"https://www.netflix.com/search?q={encoded}")
            time.sleep(3.5)
            self.speak(f"Selecting {query} on Netflix.")
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        elif platform in ["prime video", "primevideo", "amazon prime"]:
            encoded = urllib.parse.quote(query)
            self.launch_target(f"https://www.primevideo.com/search/ref=atv_nb_sr?phrase={encoded}")
            time.sleep(4.0)
            self.speak(f"Opening {query} on Prime Video.")
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        elif platform in ["hotstar", "disney+ hotstar", "disney plus hotstar", "jiocinema"]:
            encoded = urllib.parse.quote(query)
            target_url = f"https://www.hotstar.com/in/explore?search_query={encoded}" if "hotstar" in platform else f"https://www.jiocinema.com/search/{encoded}"
            self.launch_target(target_url)
            time.sleep(3.5)
            self.speak(f"Opening {query} on {platform.capitalize()}.")
            pyautogui.press("tab")
            time.sleep(0.2)
            pyautogui.press("enter")
            return True

        return False

    def plan_atomic_steps(self, high_level_goal: str) -> list:
        system = (
            "You are Aura-OS Universal Desktop Executor. Decompose any user command into an ordered list of atomic UI actions.\n\n"
            "Supported actions:\n"
            "- {\"action\": \"LAUNCH\", \"target\": \"<app or URL>\", \"speech\": \"<what to say>\"}\n"
            "- {\"action\": \"WAIT\", \"seconds\": <float>, \"speech\": \"<what to say>\"}\n"
            "- {\"action\": \"HOTKEY\", \"keys\": [\"ctrl\", \"f\"], \"speech\": \"<what to say>\"}\n"
            "- {\"action\": \"PASTE_TEXT\", \"text\": \"<string>\", \"speech\": \"<what to say>\"}\n"
            "- {\"action\": \"PRESS\", \"key\": \"enter\", \"speech\": \"<what to say>\"}\n"
            "- {\"action\": \"CONFIRM\", \"prompt\": \"<question to ask user>\", \"speech\": \"<what to say>\"}\n\n"
            "Rules:\n"
            "1. Messaging apps (WhatsApp, Telegram, Discord): Launch, WAIT 3s, HOTKEY ['ctrl', 'f'], PASTE_TEXT contact name, PRESS enter, WAIT 1s, PASTE_TEXT message, CONFIRM before sending.\n"
            "2. For arbitrary desktop applications: Launch the application, navigate with hotkeys/tabs, and execute the goal.\n"
            "Return valid JSON ONLY matching: {\"steps\": [...]}"
        )

        payload = {
            "model": MODELS.LLM_MODEL,
            "prompt": f"Plan actions for: {high_level_goal}",
            "system": system,
            "format": "json",
            "stream": False
        }

        try:
            res = requests.post(OLLAMA_URL, json=payload, timeout=25).json()
            plan = json.loads(res.get("response", "{}"))
            return plan.get("steps", [])
        except Exception as e:
            print(f"[!] Planning error: {e}")
            return []

    def execute_goal(self, user_command: str):
        lower_cmd = user_command.lower().strip()
        print(f"[*] Processing desktop goal: '{lower_cmd}'")

        # -------------------------------------------------------------------------
        # 1. UNIVERSAL MEDIA / VIDEO / MUSIC DISPATCHER
        # -------------------------------------------------------------------------
        media_platforms = [
            "spotify", "youtube", "jiosaavn", "saavn", "apple music", "applemusic",
            "netflix", "prime video", "primevideo", "amazon prime", "hotstar", "jiocinema"
        ]

        detected_platform = next((p for p in media_platforms if p in lower_cmd), None)

        if detected_platform and any(w in lower_cmd for w in ["play", "search", "watch", "listen"]):
            # Extract query by clearing common verbal patterns
            query = lower_cmd
            words_to_strip = [
                detected_platform, "open", "and", "search for the song", "search for the movie",
                "search for the show", "search for the video", "search for", "search",
                "and play it", "and play", "play it", "play", "watch it", "watch",
                "listen to", "listen", "the song", "the movie", "the video", "song", "movie", "video"
            ]
            for w in words_to_strip:
                query = query.replace(w, "")
            query = query.strip()

            if query:
                if self.handle_universal_media(detected_platform, query):
                    return

        # -------------------------------------------------------------------------
        # 2. MESSAGING FLOWS WITH EXPLICIT CONFIRMATION GATE (WhatsApp, Telegram, etc.)
        # -------------------------------------------------------------------------
        if any(msg_app in lower_cmd for msg_app in ["whatsapp", "telegram", "discord", "slack"]) and any(w in lower_cmd for w in ["message", "write", "send"]):
            # Decompose contact and content
            steps = self.plan_atomic_steps(user_command)
            if steps:
                self.run_planned_steps(steps)
                return

        # -------------------------------------------------------------------------
        # 3. GENERAL DYNAMIC UI OPERATOR PLANNER (FALLBACK FOR ANY OTHER APP)
        # -------------------------------------------------------------------------
        self.speak(f"Synthesizing workflow for: {user_command}")
        steps = self.plan_atomic_steps(user_command)
        if not steps:
            self.speak("Could not synthesize workflow steps for that command.")
            return

        self.run_planned_steps(steps)

    def run_planned_steps(self, steps: list):
        for idx, step in enumerate(steps, 1):
            action_type = step.get("action")
            speech = step.get("speech", "")

            if speech:
                self.speak(speech)

            if action_type == "LAUNCH":
                target = step.get("target", "")
                self.launch_target(target)
                time.sleep(3.0)

            elif action_type == "WAIT":
                time.sleep(step.get("seconds", 1.5))

            elif action_type == "HOTKEY":
                keys = step.get("keys", [])
                pyautogui.hotkey(*keys)
                time.sleep(0.4)

            elif action_type in ["TYPE", "PASTE_TEXT"]:
                text = step.get("text", "")
                pyperclip.copy(text)
                time.sleep(0.1)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.4)

            elif action_type == "PRESS":
                key = step.get("key", "enter")
                pyautogui.press(key)
                time.sleep(0.5)

            elif action_type == "CONFIRM":
                prompt = step.get("prompt", "Proceed with action?")
                self.awaiting_confirmation = {
                    "remaining_steps": steps[idx:],
                    "pending_action": step
                }
                self.speak(f"{prompt} Say yes to proceed or no to cancel.")
                return

        self.speak("Workflow completed.")

    def handle_confirmation(self, user_response: str) -> bool:
        if not self.awaiting_confirmation:
            return False

        lower = user_response.lower()
        if any(w in lower for w in ["yes", "send", "approve", "confirm", "proceed", "do it"]):
            self.speak("Action confirmed. Sending message.")
            remaining = self.awaiting_confirmation["remaining_steps"]
            self.awaiting_confirmation = None

            if not remaining:
                pyautogui.press("enter")
            else:
                for step in remaining:
                    speech = step.get("speech", "")
                    if speech:
                        self.speak(speech)
                    action_type = step.get("action")
                    if action_type == "PRESS":
                        pyautogui.press(step.get("key", "enter"))
                    elif action_type in ["TYPE", "PASTE_TEXT"]:
                        pyperclip.copy(step.get("text", ""))
                        time.sleep(0.1)
                        pyautogui.hotkey("ctrl", "v")
                    elif action_type == "HOTKEY":
                        pyautogui.hotkey(*step.get("keys", []))
                    time.sleep(0.5)

            self.speak("Message sent successfully.")
            return True

        elif any(w in lower for w in ["no", "cancel", "stop", "abort", "don't"]):
            self.speak("Action cancelled. Message discarded.")
            self.awaiting_confirmation = None
            return True

        return False