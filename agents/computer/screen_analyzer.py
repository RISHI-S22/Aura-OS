from typing import Any, Dict, List
from aura.vision.ocr import VisionOCR
from tools.computer import UniversalDesktopPrimitive

class ScreenAnalyzer:
    """Fuses Windows UI Automation trees with OCR regions for universal screen understanding."""

    def __init__(self):
        self.ocr = VisionOCR()
        self.desktop = UniversalDesktopPrimitive()

    def analyze(self, ui_controls: List[Dict[str, Any]], screenshot_path: str = "") -> Dict[str, Any]:
        actionable = self.desktop.filter_actionable_controls(ui_controls)
        text_blocks = self.ocr.extract_text_blocks(screenshot_path) if screenshot_path else []
        return {
            "resolution": self.desktop.get_screen_resolution(),
            "actionable_controls": actionable[:25],
            "ocr_blocks": text_blocks[:25],
        }
