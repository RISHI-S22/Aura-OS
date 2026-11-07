"""
Aura-OS Central Configuration Registry
Defines messaging bus ports, audio pipeline rates, and engine models.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkConfig:
    EVENT_BUS_PORT: int = 5555      # Audio events & barge-in interrupts
    TTS_STREAM_PORT: int = 5556     # Streaming text chunks for speech synthesis
    TELEMETRY_PORT: int = 5557      # Terminal stderr & system telemetry stream
    MEMORY_QUERY_PORT: int = 5558   # Memory request/reply retrieval RPC
    HOST: str = "127.0.0.1"


@dataclass(frozen=True)
class AudioConfig:
    SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 512           # 32ms frames for 16kHz
    VAD_THRESHOLD: float = 0.65      # Raised from 0.5 to reject faint speaker bleed
    SILENCE_CHUNKS_LIMIT: int = 35   # Increased to ~1.1s so it doesn't clip your sentences


@dataclass(frozen=True)
class ModelConfig:
    LLM_MODEL: str = "qwen2.5:3b"
    WHISPER_MODEL: str = "base.en"
    WHISPER_COMPUTE: str = "int8"
    VAD_ENGINE: str = "onnx"


NET = NetworkConfig()
AUDIO = AudioConfig()
MODELS = ModelConfig()