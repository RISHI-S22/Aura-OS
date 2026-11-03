import json
import queue
import threading
import time
import numpy as np
import sounddevice as sd
import torch
import zmq
from silero_vad import load_silero_vad
from faster_whisper import WhisperModel

# Networking configuration
ZMQ_PORT = 5555

# Audio & VAD configuration
SAMPLE_RATE = 16000
CHUNK_SIZE = 512          # 32ms window at 16kHz
VAD_THRESHOLD = 0.5       # Probability threshold to register human voice
SILENCE_CHUNKS_LIMIT = 24 # ~750ms trailing silence

# Thread-safe queue for offloading inference
transcription_queue = queue.Queue()

def initialize_bus(port: int):
    """Initializes the ZeroMQ PUB socket."""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{port}")
    return socket

def transcription_worker(bus: zmq.Socket):
    """Dedicated background worker running Whisper without blocking mic input."""
    print("[+] Initializing faster-whisper (base.en, int8)...")
    whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
    print("[+] Whisper engine ready.\n")

    while True:
        audio_data = transcription_queue.get()
        if audio_data is None:
            break

        print("[Speech Ended - Transcribing...]")
        try:
            segments, _ = whisper_model.transcribe(audio_data, beam_size=1)
            transcribed_text = "".join([segment.text for segment in segments]).strip()

            if transcribed_text:
                print(f"[Mic Capture]: {transcribed_text}")
                payload = {
                    "source": "voice",
                    "content": transcribed_text,
                    "timestamp": time.time()
                }
                bus.send_string(f"VOICE_INPUT {json.dumps(payload)}")
            else:
                print("[!] Transcription resulted in empty text.")
        except Exception as e:
            print(f"[!] Error during transcription: {e}")
        finally:
            transcription_queue.task_done()

def main():
    print(f"[+] Initializing ZeroMQ Audio Event Bus on port {ZMQ_PORT}...")
    bus = initialize_bus(ZMQ_PORT)
    time.sleep(1)

    print("[+] Loading Silero VAD (Direct ONNX engine)...")
    vad_model = load_silero_vad(onnx=True)

    # Start the worker thread
    worker_thread = threading.Thread(target=transcription_worker, args=(bus,), daemon=True)
    worker_thread.start()

    audio_buffer = []
    silent_chunks = 0
    is_recording = False

    def audio_callback(indata, frames, time_info, status):
        nonlocal silent_chunks, is_recording, audio_buffer

        if status:
            print(f"[!] Audio stream status flag: {status}")

        chunk = indata.copy().squeeze()
        chunk_tensor = torch.from_numpy(chunk)

        # Infer voice activity probability (fast ONNX execution ~1-2ms)
        speech_prob = vad_model(chunk_tensor, SAMPLE_RATE).item()

        if speech_prob > VAD_THRESHOLD:
            if not is_recording:
                is_recording = True
                audio_buffer = []
                print("[🎙️ Speech Detected]")
                
                # Instant barge-in broadcast
                interrupt_event = {
                    "event": "barge_in",
                    "timestamp": time.time()
                }
                bus.send_string(f"VOICE_INTERRUPT {json.dumps(interrupt_event)}")

            audio_buffer.append(chunk)
            silent_chunks = 0

        elif is_recording:
            audio_buffer.append(chunk)
            silent_chunks += 1

            # Speech completion check
            if silent_chunks > SILENCE_CHUNKS_LIMIT:
                is_recording = False
                full_audio = np.concatenate(audio_buffer, axis=0)
                # Offload heavy audio processing to worker thread immediately
                transcription_queue.put(full_audio)

    print("[*] Audio Service Active. Listening on microphone... (Ctrl+C to stop)\n")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SIZE,
        callback=audio_callback,
    ):
        while True:
            sd.sleep(100)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Audio Service...")