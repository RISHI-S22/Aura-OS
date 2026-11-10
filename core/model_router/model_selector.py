class ModelSelector:
    """Selects the optimal model based on cost, latency, and reasoning needs."""
    @staticmethod
    def select_model(task_type: str) -> str:
        if task_type in ("coding", "architecture"):
            return "claude-3-5-sonnet-20241022"
        elif task_type in ("fast", "intent"):
            return "gemini/gemini-1.5-flash"
        return "gemini/gemini-1.5-flash"
