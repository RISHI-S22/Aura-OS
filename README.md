<div align="center">

# ⚡ Aura-OS
### Ambient, Proactive Edge Operating System Agent with Multimodal Grounding & Episodic Memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Local Inference](https://img.shields.io/badge/Inference-Local_First-10B981?style=for-the-badge)](https://github.com/ollama/ollama)
[![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-8B5CF6?style=for-the-badge)](https://zeromq.org/)

<p align="center">
  <b>Aura-OS breaks the traditional reactive chatbot paradigm.</b><br>
  Rather than waiting for manual prompts, it continuously monitors system telemetry, terminal runtime streams, and spatial vision feeds to autonomously intervene, diagnose errors, and execute system actions in real time.
</p>

</div>

---

## 🎯 Engineering Thesis: Beyond Toy Voice Wrappers

Most consumer and open-source assistants are **reactive wrappers around an LLM chat endpoint**: they wait for a wake word, make an API call, and read back text. 

**Aura-OS** is engineered as an **ambient autonomous OS co-pilot**:

* ⚡ **Proactive & Ambient Interventions:** Hooks directly into OS processes and terminal `stderr` to diagnose failed builds, memory leaks, or container crashes without being prompted.
* 🧠 **Hierarchical Episodic Memory:** Dual-layer memory combining short-term working state with a temporal knowledge graph to recall past architectural decisions and bug resolutions across weeks.
* 🎙️ **Full-Duplex Interruption (Barge-in):** Low-latency duplex voice streaming with instant cancellation—interrupting the assistant mid-sentence immediately clears generation buffers and captures the new command.
* 👁️ **Edge Multimodal Grounding:** Local vision models running on webcam and screen feeds for spatial presence awareness, automated screen locking, and GUI coordinate interaction.

---

## 🏗️ System Architecture
                  ┌───────────────────────────────────────────────┐
                  │            SENSORY PERCEPTION TIER            │
                  │  • Mic: Silero VAD ──► faster-whisper (STT)   │
                  │  • Cam: YOLOv8 (Presence & Gaze Tracking)     │
                  │  • Screen: mss (1 FPS Frame-Diff) ──► Vision  │
                  │  • OS Daemon: Subprocess stderr / psutil Hook │
                  └──────────────────────┬────────────────────────┘
                                         │ ZeroMQ Pub/Sub (Event Bus)
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │          ARBITER & COGNITIVE ENGINE           │
                  │  • Event Priority Queue & Threshold Filter    │
                  │  • Working Memory (SQLite) + Graph-RAG        │
                  │  • Local LLM: Qwen 2.5 / Llama 3.2 (3B / 7B)  │
                  │  • Decision: [IGNORE] vs [PROACTIVE ACTION]   │
                  └──────────────────────┬────────────────────────┘
                                         │ Structured Dispatch
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │              OUTPUT & ACTION TIER             │
                  │  • Full-Duplex Audio: Piper TTS / Kokoro-82M  │
                  │  • OS Drivers: PowerShell & Bash CLI runner   │
                  │  • GUI Automation: Direct Mouse/Key Injector  │
                  └───────────────────────────────────────────────┘

        ---

## 🛠️ Model Matrix & Sensory Subsystems

| Subsystem | Target Model / Engine | Runtime Layer | Latency / Footprint |
| :--- | :--- | :--- | :--- |
| **Voice Activity Detection** | `Silero VAD` | Local CPU (`onnxruntime`) | < 5ms per chunk |
| **Speech-to-Text (STT)** | `faster-whisper (base.en / small.en)` | INT8 Quantized CTranslate2 | ~180ms latency |
| **Cognitive Brain (LLM)** | `Qwen 2.5 (3B/7B)` or `Llama 3.2 (3B)` | Ollama / vLLM (4-bit GGUF) | > 55 tokens/sec |
| **Text-to-Speech (TTS)** | `Piper TTS` or `Kokoro-82M` | Local CPU / CUDA C++ engine | < 50ms first-chunk |
| **Presence & Spatial Vision** | `YOLOv8-nano` | OpenCV Video Loop (1 FPS) | < 12ms inference |
| **Screen Perception** | `Moondream2` / `PaliGemma 2` | 4-bit Quantized Vision-Language | < 1.8 GB VRAM |
| **Memory Engine** | `NetworkX` + `sqlite-vec` | Local Vector & Graph Store | Sub-millisecond lookup |

---

## 💻 Quick Start & Setup

### 1. Prerequisites
* Python 3.11+
* NVIDIA GPU with CUDA 12+ (or 16GB+ System RAM for CPU quantized mode)
* [Ollama](https://ollama.com/) installed and running

### 2. Pull Required Base Models
```bash
ollama run qwen2.5:3b
ollama pull moondream
# Clone the repository
git clone [https://github.com/rishi-s22/aura-os.git](https://github.com/rishi-s22/aura-os.git)
cd aura-os

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux / WSL2:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt   

                  
