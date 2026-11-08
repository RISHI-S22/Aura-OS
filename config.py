"""
Aura-OS Central Configuration Registry
Defines messaging bus ports, audio pipeline rates, and engine models.
"""

import os
from dataclasses import dataclass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass(frozen=True)
class NetworkConfig:
    EVENT_BUS_PORT: int = 5555      # Audio events & barge-in interrupts (PUB/SUB)
    TTS_STREAM_PORT: int = 5556     # Streaming text chunks for speech synthesis (PUB/SUB)
    TELEMETRY_PORT: int = 5557      # Terminal stderr & system telemetry stream (PUB/SUB)
    MEMORY_QUERY_PORT: int = 5558   # Memory request/reply retrieval RPC (REQ/REP)
    ACTION_PORT: int = 5559         # OS & Browser Action execution bus (PUSH/PULL)
    HOST: str = "127.0.0.1"

@dataclass(frozen=True)
class AudioConfig:
    TARGET_SAMPLE_RATE: int = 16000 # Required by Silero VAD and Whisper
    VAD_THRESHOLD: float = 0.55     # Balanced speech detection sensitivity
    SILENCE_CHUNKS_LIMIT: int = 40  # ~1.2s trailing silence buffer

@dataclass(frozen=True)
class ModelConfig:
    LLM_MODEL: str = "qwen2.5:3b"
    WHISPER_MODEL: str = "small.en"  # Enhanced phonetic clarity for accents & names
    WHISPER_COMPUTE: str = "int8"
    VAD_ENGINE: str = "onnx"

@dataclass(frozen=True)
class PathsConfig:
    DYNAMIC_TOOLS: str = os.path.join(ROOT_DIR, "storage", "dynamic_tools")
    WORKSPACE: str = os.path.join(ROOT_DIR, "storage", "workspace")
    MEMORY: str = os.path.join(ROOT_DIR, "storage", "aura_memory")

NET = NetworkConfig()
AUDIO = AudioConfig()
MODELS = ModelConfig()
PATHS = PathsConfig()