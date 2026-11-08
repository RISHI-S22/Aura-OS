"""
Aura-OS Dynamic Tool Synthesizer
Generates, tests, and executes ephemeral Python tools when no pre-existing tool exists.
"""

import json
import os
import subprocess
import sys
import time
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import PATHS, MODELS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

class DynamicSynthesizer:
    def __init__(self):
        os.makedirs(PATHS.DYNAMIC_TOOLS, exist_ok=True)

    def write_tool(self, prompt: str) -> str:
        system = (
            "You are an autonomous Python automation engineer for Windows. "
            "Write ONLY executable, complete Python code wrapped in ```python ... ``` fences. "
            "Do not include explanation text. Use standard libraries, pyautogui, requests, or subprocess."
        )
        payload = {
            "model": MODELS.LLM_MODEL,
            "prompt": f"Write a self-contained Python script to accomplish this task: {prompt}",
            "system": system,
            "stream": False
        }
        res = requests.post(OLLAMA_URL, json=payload, timeout=30).json()
        raw_code = res.get("response", "")

        # Extract code from Markdown blocks
        if "```python" in raw_code:
            code = raw_code.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_code:
            code = raw_code.split("```")[1].split("```")[0].strip()
        else:
            code = raw_code.strip()

        tool_path = os.path.join(PATHS.DYNAMIC_TOOLS, f"tool_{int(time.time())}.py")
        with open(tool_path, "w", encoding="utf-8") as f:
            f.write(code)

        return tool_path

    def execute_and_heal(self, tool_path: str, max_retries: int = 2) -> bool:
        for attempt in range(max_retries + 1):
            res = subprocess.run([sys.executable, tool_path], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[✓ Tool Succeeded]: {res.stdout.strip()}")
                return True

            print(f"[!] Dynamic tool failed (Attempt {attempt + 1}). Stderr: {res.stderr.strip()}")
            if attempt < max_retries:
                # Healing prompt
                heal_payload = {
                    "model": MODELS.LLM_MODEL,
                    "prompt": f"The script produced this error:\n{res.stderr}\nFix the script:\n{open(tool_path).read()}",
                    "system": "Return ONLY fixed executable Python code in ```python ``` fences.",
                    "stream": False
                }
                fixed = requests.post(OLLAMA_URL, json=heal_payload, timeout=30).json().get("response", "")
                if "```python" in fixed:
                    fixed_code = fixed.split("```python")[1].split("```")[0].strip()
                    with open(tool_path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)

        return False