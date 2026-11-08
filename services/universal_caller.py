"""
Aura-OS Universal Runtime Desktop App & Call Inspector
Zero hardcoded apps. Dynamically inspects any Windows application's UI Automation (UIA)
tree to discover calling features, buttons, and interaction modes at runtime.
"""

import time
import pyautogui
import pyperclip
import uiautomation as auto
from services.window_manager import WindowManager

class UniversalCaller:
    def __init__(self, tts_callback=None):
        self.speak = tts_callback or (lambda text: print(f"[Aura Call]: {text}"))
        self.pending_call = None

    def find_contact_in_app(self, recipient: str):
        """
        Attempts universal contact search across any communication app.
        Uses universal shortcuts: Esc (clear view) -> Ctrl+F (or Ctrl+K) -> Type -> Enter.
        """
        pyautogui.press("esc")
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "f")
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.press("backspace")

        pyperclip.copy(recipient)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(1.0)
        pyautogui.press("enter")
        time.sleep(1.0)

    def inspect_active_window_call_capabilities(self, hwnd: int) -> dict:
        """
        Traverses the UI Automation tree of the target window to detect
        what calling buttons or controls actually exist on the screen right now.
        """
        win_control = auto.ControlFromHandle(hwnd)
        if not win_control or not win_control.Exists(0, 0):
            return {"modes": [], "elements": {}}

        discovered_modes = {}

        # Search for interactive controls (Buttons, Hyperlinks, MenuItem, SplitButton)
        for control, depth in auto.WalkControl(win_control, maxDepth=12):
            control_type = control.ControlTypeName
            if control_type in ["ButtonControl", "HyperlinkControl", "MenuItemControl", "SplitButtonControl"]:
                name = (control.Name or "").lower()
                auto_id = (control.AutomationId or "").lower()
                help_text = (control.HelpText or "").lower()

                full_desc = f"{name} {auto_id} {help_text}"

                # Detect Video Call capabilities
                if any(k in full_desc for k in ["video call", "start video", "camera", "video chat"]):
                    if "video" not in discovered_modes:
                        discovered_modes["video"] = control

                # Detect Audio / Voice Call capabilities
                elif any(k in full_desc for k in ["voice call", "audio call", "start audio", "phone call", "call"]):
                    if "audio" not in discovered_modes:
                        discovered_modes["audio"] = control

        return discovered_modes

    def initiate_universal_call(self, app_name: str, recipient: str) -> bool:
        """
        Launches/focuses ANY application, searches recipient, and discovers call modes.
        """
        self.speak(f"Opening {app_name} to connect with {recipient}.")
        
        # 1. Bring app to foreground or launch it
        WindowManager.ensure_foreground(app_name)
        time.sleep(1.2)

        win = WindowManager.get_window_by_keyword(app_name)
        if not win:
            # Fallback launch via Windows Start
            pyautogui.press("win")
            time.sleep(0.3)
            pyperclip.copy(app_name)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(3.0)
            win = WindowManager.get_window_by_keyword(app_name)

        if not win:
            self.speak(f"Could not locate or launch {app_name} on your system.")
            return False

        hwnd = win._hWnd

        # 2. Search for the recipient in the app
        if recipient:
            self.find_contact_in_app(recipient)

        # 3. Read the application's actual UI controls in real-time
        self.speak("Reading application interface for calling options.")
        modes = self.inspect_active_window_call_capabilities(hwnd)

        # Case A: Found both Audio and Video controls
        if "audio" in modes and "video" in modes:
            self.pending_call = {
                "modes": modes,
                "recipient": recipient,
                "app": app_name
            }
            self.speak(f"I found both an audio call and a video call option in {app_name}. Which one would you prefer?")
            return False

        # Case B: Found only Video
        elif "video" in modes and "audio" not in modes:
            self.speak(f"{app_name} only supports video calls. Starting video call now.")
            self.trigger_control(modes["video"])
            return True

        # Case C: Found only Audio / General Call
        elif "audio" in modes:
            self.speak(f"Starting voice call to {recipient} on {app_name}.")
            self.trigger_control(modes["audio"])
            return True

        # Case D: Custom UI / Web-wrapped UI without exposed UIA accessibility names
        else:
            self.speak(f"I couldn't identify specific call buttons in {app_name}. Would you like me to try an audio call shortcut or a video call shortcut?")
            self.pending_call = {
                "modes": "generic",
                "recipient": recipient,
                "app": app_name
            }
            return False

    def handle_call_choice(self, user_response: str) -> bool:
        if not self.pending_call:
            return False

        lower = user_response.lower()
        if any(w in lower for w in ["cancel", "stop", "abort"]):
            self.speak("Call cancelled.")
            self.pending_call = None
            return True

        desired_mode = "video" if "video" in lower else ("audio" if any(w in lower for w in ["audio", "voice"]) else None)

        if not desired_mode:
            self.speak("Please say audio call or video call.")
            return True

        call_data = self.pending_call
        self.pending_call = None

        if isinstance(call_data["modes"], dict):
            control = call_data["modes"].get(desired_mode)
            if control:
                self.speak(f"Starting {desired_mode} call.")
                self.trigger_control(control)
                return True

        # Generic keyboard fallback
        if desired_mode == "video":
            pyautogui.hotkey("ctrl", "shift", "v")
        else:
            pyautogui.hotkey("ctrl", "shift", "c")
        self.speak(f"Triggered {desired_mode} call.")
        return True

    def trigger_control(self, control):
        """Clicks the UI element natively via UIA or coordinates."""
        try:
            pattern = control.GetInvokePattern()
            if pattern:
                pattern.Invoke()
                return
        except Exception:
            pass

        try:
            rect = control.BoundingRectangle
            pyautogui.click(rect.x + rect.width // 2, rect.y + rect.height // 2)
        except Exception as e:
            print(f"[!] UIA Click failed: {e}")