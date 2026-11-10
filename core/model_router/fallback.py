class FallbackHandler:
    @staticmethod
    def get_fallback(current_model: str) -> str:
        if "gemini" in current_model:
            return "gpt-4o-mini"
        return "gemini/gemini-1.5-flash"
