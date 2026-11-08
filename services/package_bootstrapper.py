"""
Aura-OS Autonomous Package Bootstrapper & Auto-Installer
Detects missing applications, fetches installers via Windows Package Manager (winget),
installs silently, and passes control to credential injection.
"""

import os
import subprocess
import sys
import time
import pyautogui
import pyperclip

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from services.window_manager import WindowManager

class PackageBootstrapper:
    def __init__(self, tts_callback=None):
        self.speak = tts_callback or (lambda text: print(f"[Bootstrapper]: {text}"))

    def is_installed(self, app_name: str) -> bool:
        """Checks if application is installed or reachable in system."""
        clean = app_name.lower().strip()
        if WindowManager.get_window_by_keyword(clean):
            return True

        # Check PATH
        res = subprocess.run(f"where {clean}", shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            return True

        # Check Windows Start Apps
        ps_cmd = f'(Get-StartApps | Where-Object {{ $_.Name -like "*{clean}*" }}).Count'
        check_res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        try:
            return int(check_res.stdout.strip()) > 0
        except Exception:
            return False

    def search_and_install_winget(self, app_name: str) -> bool:
        """Searches winget catalog and executes silent installation."""
        self.speak(f"{app_name} is not installed on this system. Searching repository to install it.")
        print(f"[*] Querying winget for: {app_name}...")

        # Search package
        search_proc = subprocess.run(
            ["winget", "search", app_name, "--accept-source-agreements"],
            capture_output=True,
            text=True,
            shell=True
        )

        lines = search_proc.stdout.splitlines()
        package_id = None
        for line in lines:
            if app_name.lower() in line.lower() and not line.startswith("Name") and not line.startswith("-"):
                parts = line.split()
                if len(parts) >= 2:
                    package_id = parts[1]
                    break

        target_pkg = package_id or app_name
        self.speak(f"Downloading and installing {app_name}. Please wait.")

        install_proc = subprocess.run(
            ["winget", "install", target_pkg, "--silent", "--accept-package-agreements", "--accept-source-agreements"],
            capture_output=True,
            text=True,
            shell=True
        )

        if install_proc.returncode == 0:
            self.speak(f"{app_name} successfully installed.")
            return True
        else:
            print(f"[!] Winget error: {install_proc.stderr}")
            self.speak(f"Could not complete automated installation for {app_name}.")
            return False

    def bootstrap_and_authenticate(self, app_name: str, saved_creds: dict):
        """Installs if missing, launches app, and injects saved credentials."""
        if not self.is_installed(app_name):
            success = self.search_and_install_winget(app_name)
            if not success:
                return False

        # Launch the application
        self.speak(f"Launching {app_name}.")
        WindowManager.ensure_foreground(app_name)
        time.sleep(3.0)

        # Automated Credential Handshake
        if saved_creds and saved_creds.get("email"):
            self.speak(f"Injecting your saved profile for {saved_creds['email']}.")
            time.sleep(1.0)
            
            # Universal Auth Shortcut Sequence for Desktop Apps:
            # Tab into input -> Paste email -> Enter / Tab -> Paste password
            pyperclip.copy(saved_creds["email"])
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(1.0)

            if saved_creds.get("password"):
                pyperclip.copy(saved_creds["password"])
                pyautogui.hotkey("ctrl", "v")
                pyautogui.press("enter")

        self.speak(f"{app_name} is ready for use.")
        return True