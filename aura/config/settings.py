import os

class Settings:
    PRIMARY_MODEL: str = os.getenv("AURA_PRIMARY_MODEL", "gemini/gemini-1.5-flash")
    FAST_MODEL: str = os.getenv("AURA_FAST_MODEL", "gemini/gemini-1.5-flash")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()
