import os
import json
from typing import Dict, Any
from agents.base.base_agent import BaseAgent

class DocumentAgent(BaseAgent):
    def __init__(self, output_dir: str = "workspace"):
        super().__init__(name="document_agent", description="Synthesizes documents, markdown, and reports")
        self.output_dir = output_dir

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        os.makedirs(self.output_dir, exist_ok=True)
        title = task.get("title", "document")
        safe_name = "".join(c if c.isalnum() else "_" for c in title).lower()
        filepath = os.path.join(self.output_dir, f"{safe_name}.md")
        
        content = f"# Generated Artifact: {title}\n\nProduced autonomously by AURA DocumentAgent."
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "agent": self.name,
            "artifact_path": filepath,
            "artifact_created": True
        }