from typing import Dict, Any

class ContextEngine:
    """Aggregates contextual state across conversations, working memory, and system state."""
    def get_context(self) -> Dict[str, Any]:
        return {
            "os": "Windows 11",
            "active_mode": "autonomous",
            "working_directory": "E:\\projects\\Aura-OS"
        }
