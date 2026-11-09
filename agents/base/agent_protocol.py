from typing import Protocol, Any

class AgentProtocol(Protocol):
    name: str
    async def run(self, task: dict[str, Any]) -> dict[str, Any]: ...
