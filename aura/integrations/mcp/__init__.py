from typing import Any, Callable, Dict, List, Optional

class MCPToolRegistry:
    """Dynamic registry for Model Context Protocol (MCP) tools and schemas."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[..., Any],
    ):
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "handler": handler,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in self._tools.values()
        ]

    def get_handler(self, name: str) -> Optional[Callable[..., Any]]:
        tool = self._tools.get(name)
        return tool["handler"] if tool else None

mcp_registry = MCPToolRegistry()
