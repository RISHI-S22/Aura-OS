import queue
import threading
import numpy as np
import sounddevice as sd
import torch
from silero_vad import load_silero_vad
from faster_whisper import WhisperModel
import ollama

# ----------------- Configuration -----------------
SAMPLE_RATE = 16000
CHUNK_SIZE = 512          # ~32ms per chunk for Silero VAD
VAD_THRESHOLD = 0.5       # Speech probability threshold
SILENCE_CHUNKS_LIMIT = 25 # ~800ms of silence to finalize utterance
MODEL_SIZE = "base.en"    # Fast local STT model
LLM_MODEL = "qwen2.5:3b"

# ----------------- Queues & Flags -----------------
audio_queue = queue.Queue()
interrupt_event = threading.Event()
is_agent_speaking = threading.Event()

# ----------------- Model Initialization -----------------
print("[+] Loading Silero VAD (Direct ONNX)...")
vad_model = load_silero_vad(onnx=True)

print("[+] Loading faster-whisper...")
whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def audio_callback(indata, frames, time, status):
    """Callback to continuously capture raw mic input."""
    if status:
        print(f"[!] Audio Status: {status}")
    audio_queue.put(indata.copy())

def generate_and_speak(prompt: str):
    """Streams LLM tokens and handles barge-in interrupts."""
    is_agent_speaking.set()
    interrupt_event.clear()
    print(f"\n[Aura]: ", end="", flush=True)

    try:
        stream = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are Aura, an ambient proactive OS co-pilot. Keep responses concise, direct, and under two sentences."},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        for chunk in stream:
            if interrupt_event.is_set():
                print("\n[!] Barge-in detected: Agent speech cancelled.")
                break
            token = chunk["message"]["content"]
            print(token, end="", flush=True)

    except Exception as e:
        print(f"\n[!] LLM Generation Error: {e}")
    finally:
        print()
        is_agent_speaking.clear()

def listen_and_process():
    """VAD processing loop with speech segmentation and interrupt routing."""
    buffer = []
    silent_chunks = 0
    recording = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=CHUNK_SIZE, callback=audio_callback):
        print("\n[*] Aura-OS Listening... (Press Ctrl+C to stop)")
        while True:
            chunk = audio_queue.get()
            chunk_tensor = torch.from_numpy(chunk.squeeze())

            # Evaluate speech probability
            speech_prob = vad_model(chunk_tensor, SAMPLE_RATE).item()

            # Barge-in: If the agent is speaking and user begins talking
            if speech_prob > VAD_THRESHOLD and is_agent_speaking.is_set():
                interrupt_event.set()

            if speech_prob > VAD_THRESHOLD:
                if not recording:
                    recording = True
                    buffer = []
                    print("\n[🎙️ Speech Detected]")
                buffer.append(chunk)
                silent_chunks = 0
            elif recording:
                buffer.append(chunk)
                silent_chunks += 1

                # If silence duration exceeds threshold, finalize and run STT
                if silent_chunks > SILENCE_CHUNKS_LIMIT:
                    recording = False
                    audio_data = np.concatenate(buffer, axis=0).squeeze()
                    
                    segments, _ = whisper_model.transcribe(audio_data, beam_size=1)
                    user_text = "".join([s.text for s in segments]).strip()

                    if user_text:
                        print(f"[User]: {user_text}")
                        t = threading.Thread(target=generate_and_speak, args=(user_text,), daemon=True)
                        t.start()

if __name__ == "__main__":
    try:
        listen_and_process()
    except KeyboardInterrupt:
        print("\n[+] Pipeline stopped.")