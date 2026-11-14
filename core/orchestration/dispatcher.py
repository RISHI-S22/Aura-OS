from typing import Any, Dict
from agents.base.agent_registry import agent_registry
from core.verification.result_validator import validator

class Dispatcher:
    """Dispatches tasks to registered specialist agents and verifies outputs."""

    async def dispatch(self, agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
        agent = agent_registry.get(agent_name)
        if not agent:
            return {
                "status": "error",
                "agent": agent_name,
                "message": f"Specialist agent '{agent_name}' is not registered",
            }

        result = await agent.run(task)
        if not validator.validate(result):
            return {
                "status": "error",
                "agent": agent_name,
                "message": f"Agent '{agent_name}' returned invalid output",
                "raw_result": result,
            }
        return result

dispatcher = Dispatcher()
