from agents.base.base_agent import BaseAgent
from typing import Dict, Any

class EmailAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="email_agent", description="Personal communication and email dispatch")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "pending_approval", "agent": self.name, "requires_approval": True}
