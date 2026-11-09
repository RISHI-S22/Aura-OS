from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    name = "base"

    @abstractmethod
    async def run(self, task: dict[str, Any]) -> dict[str, Any]:
        """Implementations must return structured results and must respect permissions."""
        raise NotImplementedError
