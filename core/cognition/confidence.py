import math
from typing import List, Optional

class ConfidenceScore:
    """Computes normalized confidence metrics for intent classification."""
    @staticmethod
    def calculate(keyword_matches: int, total_criteria: int) -> float:
        if total_criteria == 0:
            return 0.5
        ratio = min(max(keyword_matches / total_criteria, 0.0), 1.0)
        return round(ratio, 2)