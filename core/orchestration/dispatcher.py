from typing import Dict, Any
from agents.base.agent_registry import agent_registry

class Dispatcher:
    """Dispatches tasks to the designated specialist agent from registry."""
    async def dispatch(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        agent = agent_registry.get(agent_name)
        if not agent:
            return {"status": "error", "message": f"Agent {agent_name} not found"}
        return await agent.run(task)

dispatcher = Dispatcher()
