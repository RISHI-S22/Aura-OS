from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass
