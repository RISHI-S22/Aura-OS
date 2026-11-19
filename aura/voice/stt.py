from typing import Optional

class SpeechToText:
    """Transcribes audio files or buffers using faster-whisper."""

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
