import math
import struct
from typing import Iterable

class VoiceActivityDetector:
    """Detects speech segments in 16-bit PCM audio frames using RMS energy thresholding."""

    def __init__(self, energy_threshold: float = 500.0):
        self.energy_threshold = energy_threshold

    def compute_rms(self, pcm_bytes: bytes) -> float:
        count = len(pcm_bytes) // 2
        if count == 0:
            return 0.0
        samples = struct.unpack(f"<{count}h", pcm_bytes[: count * 2])
        mean_sq = sum(s * s for s in samples) / count
        return math.sqrt(mean_sq)

    def is_speech(self, pcm_bytes: bytes) -> bool:
        return self.compute_rms(pcm_bytes) >= self.energy_threshold

    def filter_speech_frames(self, frames: Iterable[bytes]) -> list[bytes]:
        return [frame for frame in frames if self.is_speech(frame)]
