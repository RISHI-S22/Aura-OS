from typing import Any, Dict, List, Optional

class SetOfMarksGrounder:
    """Assigns numeric visual markers [1..N] to detected UI controls and OCR bounding boxes."""

    @staticmethod
    def build_grounded_elements(
        uia_controls: List[Dict[str, Any]],
        ocr_blocks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        marks: List[Dict[str, Any]] = []
        idx = 1

        for ctrl in uia_controls:
            marks.append({
                "mark_id": idx,
                "source": "uia",
                "type": ctrl.get("control_type", "Control"),
                "label": ctrl.get("name", ""),
                "bbox": ctrl.get("bbox"),
            })
            idx += 1

        for block in ocr_blocks:
            text = (block.get("text") or "").strip()
            if not text:
                continue
            marks.append({
                "mark_id": idx,
                "source": "ocr",
                "type": "TextRegion",
                "label": text,
                "bbox": block.get("bbox"),
            })
            idx += 1

        return marks

    @staticmethod
    def resolve_mark_center(marks: List[Dict[str, Any]], mark_id: int) -> Optional[Dict[str, int]]:
        for item in marks:
            if item.get("mark_id") == mark_id and item.get("bbox"):
                x, y, w, h = item["bbox"]
                return {"x": int(x + w / 2), "y": int(y + h / 2)}
        return None
