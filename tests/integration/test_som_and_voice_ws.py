import struct
from unittest.mock import patch
from fastapi.testclient import TestClient
from aura.api.main import app, voice_engine
from tools.vision.som_grounding import SetOfMarksGrounder

client = TestClient(app)

def test_set_of_marks_grounding_and_center_resolution():
    marks = SetOfMarksGrounder.build_grounded_elements(
        uia_controls=[{"control_type": "Button", "name": "Brush", "bbox": [100, 200, 40, 20]}],
        ocr_blocks=[{"text": "Canvas", "bbox": [300, 400, 100, 50]}],
    )
    assert len(marks) == 2
    assert marks[0]["mark_id"] == 1
    assert SetOfMarksGrounder.resolve_mark_center(marks, 1) == {"x": 120, "y": 210}
    assert SetOfMarksGrounder.resolve_mark_center(marks, 2) == {"x": 350, "y": 425}

def test_websocket_voice_stream_vad_and_transcription():
    speech_pcm = struct.pack("<160h", *([2500, -2500] * 80))
    with patch.object(voice_engine.stt, "transcribe_pcm_buffer", return_value="Open Notepad"):
        with client.websocket_connect("/ws/voice") as ws:
            ws.send_bytes(speech_pcm)
            vad_msg = ws.receive_json()
            assert vad_msg["event"] == "vad_speech"

            ws.send_text("FLUSH")
            done_msg = ws.receive_json()
            assert done_msg["event"] == "voice_completed"
            assert done_msg["transcript"] == "Open Notepad"
            assert done_msg["status"] == "completed"
