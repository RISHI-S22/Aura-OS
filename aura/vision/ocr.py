from typing import Any, Dict, List

class VisionOCR:
    """Extracts structured text regions from arbitrary screen captures."""

    def extract_text_blocks(self, image_path: str) -> List[Dict[str, Any]]:
        try:
            import pytesseract
            from PIL import Image
            data = pytesseract.image_to_data(Image.open(image_path), output_type=pytesseract.Output.DICT)
            blocks = []
            for i, text in enumerate(data.get("text", [])):
                cleaned = text.strip()
                if cleaned:
                    blocks.append({
                        "text": cleaned,
                        "bbox": [data["left"][i], data["top"][i], data["width"][i], data["height"][i]],
                        "conf": data["conf"][i],
                    })
            return blocks
        except Exception:
            return []
