import os
import tempfile
import wave

class SpeechToText:
    """Transcribes audio files or raw 16kHz mono PCM buffers using faster-whisper."""

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model_size = model_size
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device=self.device, compute_type="int8")

    def transcribe_file(self, audio_path: str) -> str:
        try:
            self._load_model()
            segments, _ = self._model.transcribe(audio_path, beam_size=5)
            return " ".join(seg.text.strip() for seg in segments).strip()
        except Exception as exc:
            raise RuntimeError(f"STT transcription unavailable: {exc}") from exc

    def transcribe_pcm_buffer(self, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)
            return self.transcribe_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
