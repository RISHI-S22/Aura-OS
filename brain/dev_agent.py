"""
Aura-OS Autonomous Software Engineering Agent
Scaffolds full-stack projects, checks builds, commits to Git, and triggers deployment commands.
"""

import json
import os
import subprocess
import sys
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import PATHS, MODELS

OLLAMA_URL = "[http://127.0.0.1:11434/api/generate](http://127.0.0.1:11434/api/generate)"

class AutonomousDevAgent:
    def __init__(self, feedback_callback=None):
        self.feedback = feedback_callback or (lambda text: print(f"[DevAgent]: {text}"))

    def scaffold_project(self, project_name: str, tech_stack: str):
        target_dir = os.path.join(PATHS.WORKSPACE, project_name)
        os.makedirs(target_dir, exist_ok=True)
        self.feedback(f"Scaffolding {project_name} using {tech_stack} in workspace.")

        plan_prompt = (
            f"Generate a file manifest for a production {tech_stack} project named {project_name}. "
            "Return JSON only: {\"files\": [{\"path\": \"relative/path/file.ext\", \"content\": \"full code\"}]}"
        )
        res = requests.post(
            OLLAMA_URL,
            json={"model": MODELS.LLM_MODEL, "prompt": plan_prompt, "stream": False, "format": "json"},
            timeout=60
        ).json()

        manifest = json.loads(res.get("response", "{}"))
        for item in manifest.get("files", []):
            full_path = os.path.join(target_dir, item["path"])
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(item["content"])

        self.feedback("Project files generated. Initializing local git repository.")
        self.git_commit_and_push(target_dir, project_name)

    def git_commit_and_push(self, project_path: str, repo_name: str):
        try:
            subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "feat: autonomous initial build by Aura-OS"], cwd=project_path, check=True, capture_output=True)
            self.feedback("Local repository initialized and changes committed.")

            # Optional remote push if GitHub CLI is logged in
            create_res = subprocess.run(
                ["gh", "repo", "create", repo_name, "--public", "--source=.", "--remote=origin", "--push"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if create_res.returncode == 0:
                self.feedback(f"Project pushed to GitHub repository {repo_name} successfully.")
            else:
                self.feedback("Git committed locally. Configure gh CLI credentials to push automatically.")
        except Exception as e:
            self.feedback(f"Git integration notice: {e}")