import os
import time
from typing import Optional

class LiveScreenCapture:
    """Captures live Windows desktop or active foreground window frames for visual grounding."""

    @staticmethod
    def capture_foreground_or_screen(output_dir: str = "workspace/captures") -> Optional[str]:
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"frame_{int(time.time() * 1000)}.png")
        try:
            from PIL import ImageGrab
            bbox = None
            try:
                from pywinauto import Desktop
                active = Desktop(backend="uia").active()
                if active and active.element_info.rectangle:
                    r = active.element_info.rectangle
                    if r.width() > 0 and r.height() > 0:
                        bbox = (r.left, r.top, r.right, r.bottom)
            except Exception:
                bbox = None

            img = ImageGrab.grab(bbox=bbox, all_screens=True)
            img.save(out_path)
            return out_path
        except Exception:
            return None
