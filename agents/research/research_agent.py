from agents.base.base_agent import BaseAgent
from typing import Dict, Any

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="research_agent", description="Web search and fact verification")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query = task.get("title", "")
        return {"status": "success", "agent": self.name, "findings": f"Gathered data on: {query}"}
