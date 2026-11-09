from dataclasses import dataclass

@dataclass(frozen=True)
class Intent:
    category: str
    confidence: float
    requires_external_action: bool

KEYWORDS = {
    "research": ("research", "search", "find", "compare", "investigate"),
    "coding": ("code", "debug", "build an app", "implement", "program"),
    "document": ("document", "spreadsheet", "excel", "presentation", "report"),
    "personal": ("email", "calendar", "remind", "schedule", "meeting"),
    "computer": ("open", "click", "browser", "desktop", "computer"),
}

def classify_intent(command: str) -> Intent:
    """Transparent baseline classifier; replace/augment with an LLM later."""
    text = command.casefold()
    matches = [category for category, words in KEYWORDS.items()
               if any(word in text for word in words)]
    if not matches:
        return Intent("general", 0.55, False)
    category = matches[0] if len(matches) == 1 else "multi_step"
    return Intent(category, 0.75 if len(matches) == 1 else 0.82,
                  any(c in matches for c in ("personal", "computer")))
