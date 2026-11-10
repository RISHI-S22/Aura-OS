from typing import Protocol, Dict, Any

class AgentProtocol(Protocol):
    name: str
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        ...
