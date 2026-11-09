class AgentRegistry:
    def __init__(self):
        self._agents = {}

    def register(self, agent):
        if not getattr(agent, "name", None):
            raise ValueError("Agent must define a non-empty name")
        self._agents[agent.name] = agent

    def get(self, name: str):
        return self._agents.get(name)

    def names(self) -> list[str]:
        return sorted(self._agents)
