"""
Aura-OS Universal Desktop UI Inspector & Operator
Equipped with COM Thread Initialization, UIA inspection,
and reliable focus-locked clipboard injection for modern desktop apps.
"""

import json
import os
import sys
import time
import pyautogui
import pyperclip
import requests
import uiautomation as auto

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import MODELS
from services.window_manager import WindowManager

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

pyautogui.FAILSAFE = False

class UniversalOSOperator:
    def __init__(self, tts_callback=None):
        self.speak = tts_callback or (lambda text: print(f"[Aura]: {text}"))
        self.awaiting_confirmation = None

    def launch_or_focus(self, app_keyword: str) -> auto.Control:
        clean = app_keyword.lower().strip()
        win = WindowManager.get_window_by_keyword(clean)

        if not win:
            self.speak(f"Opening {clean}.")
            pyautogui.press("win")
            time.sleep(0.3)
            pyperclip.copy(clean)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)
            pyautogui.press("enter")

            for _ in range(12):
                time.sleep(0.5)
                win = WindowManager.get_window_by_keyword(clean)
                if win:
                    break

        if win:
            WindowManager.ensure_foreground(win)
            time.sleep(1.0)
            return auto.ControlFromHandle(win._hWnd)

        return None

    def find_and_focus_chat_input(self, root_control: auto.Control) -> bool:
        """
        Reliably locates the text composer inside WhatsApp, Telegram, or any chat client.
        Combines UIA search with fallback coordinate targeting.
        """
        # Try finding EditControl from bottom up
        for control, _ in auto.WalkControl(root_control, maxDepth=12):
            if control.ControlTypeName == "EditControl":
                name = (control.Name or "").lower()
                auto_id = (control.AutomationId or "").lower()
                # Exclude the search bar
                if "search" not in name and "search" not in auto_id:
                    try:
                        control.SetFocus()
                        time.sleep(0.2)
                        return True
                    except Exception:
                        pass

        # Fallback: Click directly into the lower quarter of the window where input boxes always live
        try:
            rect = root_control.BoundingRectangle
            click_x = rect.x + int(rect.width * 0.60)   # 60% across (inside chat pane, away from sidebar)
            click_y = rect.y + int(rect.height * 0.94)  # 94% down (inside message bar)
            pyautogui.click(click_x, click_y)
            time.sleep(0.3)
            return True
        except Exception:
            return False

    def execute_goal(self, user_command: str):
        with auto.UIAutomationInitializerInThread():
            extraction_prompt = (
                f"Analyze this command: '{user_command}'.\n"
                "Return JSON ONLY with this schema:\n"
                "{\n"
                "  \"app_name\": \"<app name to open, e.g. whatsapp, notepad>\",\n"
                "  \"contact\": \"<contact or person name if mentioned, or null>\",\n"
                "  \"text_to_input\": \"<the exact message or note body to write, or null>\",\n"
                "  \"requires_confirmation\": <true if sending a message/email/file, false otherwise>\n"
                "}"
            )
            try:
                res = requests.post(OLLAMA_URL, json={
                    "model": MODELS.LLM_MODEL,
                    "prompt": extraction_prompt,
                    "format": "json",
                    "stream": False
                }, timeout=15).json()
                intent = json.loads(res.get("response", "{}"))
            except Exception:
                intent = {
                    "app_name": "whatsapp" if "whatsapp" in user_command.lower() else "active window",
                    "contact": None,
                    "text_to_input": None,
                    "requires_confirmation": True
                }

            app_name = intent.get("app_name") or "active window"
            contact = intent.get("contact")
            text_to_input = intent.get("text_to_input")
            requires_conf = intent.get("requires_confirmation", True)

            root_control = self.launch_or_focus(app_name) if app_name != "active window" else auto.GetForegroundControl()

            if not root_control:
                self.speak(f"Could not connect to {app_name}.")
                return

            # Step 1: Search and select the contact
            if contact and "null" not in str(contact).lower():
                self.speak(f"Searching for {contact} in {app_name}.")
                pyautogui.press("esc")
                time.sleep(0.2)
                pyautogui.hotkey("ctrl", "f")
                time.sleep(0.4)
                pyautogui.hotkey("ctrl", "a")
                pyautogui.press("backspace")
                time.sleep(0.2)

                pyperclip.copy(contact)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(1.2)  # Wait for search results to populate
                pyautogui.press("enter")
                time.sleep(1.0)  # Wait for chat view to load

            # Step 2: Ensure focus is locked onto the message composer
            if text_to_input and "null" not in str(text_to_input).lower():
                self.find_and_focus_chat_input(root_control)
                time.sleep(0.3)

                # Clear any lingering placeholder/search text
                pyautogui.hotkey("ctrl", "a")
                time.sleep(0.1)

                # Paste via clipboard (universal and reliable across all app types)
                pyperclip.copy(text_to_input)
                time.sleep(0.2)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.5)

                if requires_conf:
                    self.awaiting_confirmation = {
                        "action": "SEND_ENTER",
                        "app_control": root_control,
                        "text": text_to_input
                    }
                    self.speak(f"Message prepared for {contact or app_name}. Say yes to send or no to cancel.")
                    return
                else:
                    pyautogui.press("enter")
                    self.speak("Message sent.")
                    return

            self.speak(f"Connected to {app_name}. What should I do next?")

    def handle_confirmation(self, user_response: str) -> bool:
        if not self.awaiting_confirmation:
            return False

        lower = user_response.lower()
        if any(w in lower for w in ["yes", "send", "proceed", "do it", "confirm"]):
            self.speak("Sending message.")
            
            # Ensure window is still foreground before sending Enter
            root = self.awaiting_confirmation.get("app_control")
            if root:
                try:
                    WindowManager.ensure_foreground(root.NativeWindowHandle)
                except Exception:
                    pass
            time.sleep(0.3)
            
            pyautogui.press("enter")
            self.awaiting_confirmation = None
            self.speak("Message sent successfully.")
            return True

        elif any(w in lower for w in ["no", "cancel", "stop", "abort"]):
            self.speak("Action cancelled. Message removed.")
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            self.awaiting_confirmation = None
            return True

        return False