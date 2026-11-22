import os
import struct
import tempfile
from aura.voice.vad import VoiceActivityDetector
from memory.procedural.procedural_memory import ProceduralMemory

def test_procedural_memory_persists_and_recalls():
    fd, tmp_file = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.remove(tmp_file)
    try:
        pm = ProceduralMemory(storage_path=tmp_file)
        pm.record_procedure(
            goal="Compile and run Python benchmark",
            agent="desktop_agent",
            action_sequence=[{"step": 1, "action": "click_control", "target_name": "Run"}],
        )
        reloaded = ProceduralMemory(storage_path=tmp_file)
        matches = reloaded.recall("Run Python benchmark")
        assert len(matches) == 1
        assert matches[0]["agent"] == "desktop_agent"
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

def test_vad_distinguishes_silence_from_speech():
    vad = VoiceActivityDetector(energy_threshold=500.0)
    silence = struct.pack("<100h", *([0] * 100))
    speech = struct.pack("<100h", *([2500, -2500] * 50))
    assert vad.is_speech(silence) is False
    assert vad.is_speech(speech) is True
    assert len(vad.filter_speech_frames([silence, speech])) == 1
