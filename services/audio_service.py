"""
Aura-OS Audio Capture & Speech Processing Service
Continuous mic ingestion with Silero VAD, fast barge-in interrupts,
and hallucination-suppressed faster-whisper transcription.
"""

import json
import os
import queue
import sys
import threading
import time
import numpy as np
import sounddevice as sd
import torch
import zmq
from faster_whisper import WhisperModel
from silero_vad import load_silero_vad

# Guarantee project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET, AUDIO, MODELS

# Thread-safe queue for offloading inference
transcription_queue = queue.Queue()

# Hallucination blacklist for low SNR / quiet background audio
HALLUCINATION_BLACKLIST = {
    "thank you.",
    "thank you",
    "thanks for watching.",
    "thanks for watching",
    "see you in the next video.",
    "we'll see you in the next video.",
    "subscribe to the channel.",
    "you",
    ".",
    "next.",
    "invite them.",
    "on this.",
}


def initialize_bus(port: int):
    """Initializes the ZeroMQ PUB socket."""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://{NET.HOST}:{port}")
    return socket


def clean_transcription(text: str) -> str:
    """Filters out empty or repetitive low-energy Whisper artifacts."""
    clean = text.strip()
    if clean.lower() in HALLUCINATION_BLACKLIST:
        return ""
    if len(clean) <= 2:
        return ""
    return clean


def transcription_worker(bus: zmq.Socket):
    """Dedicated background worker running Whisper without blocking the audio stream."""
    print(f"[+] Initializing faster-whisper ({MODELS.WHISPER_MODEL}, {MODELS.WHISPER_COMPUTE})...")
    whisper_model = WhisperModel(
        MODELS.WHISPER_MODEL,
        device="cpu",
        compute_type=MODELS.WHISPER_COMPUTE,
    )
    print("[+] Whisper engine ready.\n")

    while True:
        audio_data = transcription_queue.get()
        if audio_data is None:
            break

        # Discard audio fragments shorter than 0.4 seconds to prevent blip processing
        if len(audio_data) < int(AUDIO.SAMPLE_RATE * 0.4):
            transcription_queue.task_done()
            continue

        print("[Speech Ended - Transcribing...]")
        try:
            # Stricter decoding parameters to reject acoustic noise & phantom text
            segments, _ = whisper_model.transcribe(
                audio_data,
                beam_size=1,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
            )
            raw_text = "".join([segment.text for segment in segments])
            transcribed_text = clean_transcription(raw_text)
            if transcribed_text:
                print(f"[Mic Capture]: {transcribed_text}")
                payload = {
                    "source": "voice",
                    "content": transcribed_text,
                    "timestamp": time.time(),
                }
                bus.send_string(f"VOICE_INPUT {json.dumps(payload)}")
            else:
                print("[!] Audio rejected: Low confidence or background noise artifact.")

        except Exception as e:
            print(f"[!] Error during transcription: {e}")
        finally:
            transcription_queue.task_done()


def main():
    print(f"[+] Initializing ZeroMQ Audio Event Bus on port {NET.EVENT_BUS_PORT}...")
    bus = initialize_bus(NET.EVENT_BUS_PORT)
    time.sleep(0.5)

    print("[+] Loading Silero VAD (Direct ONNX engine)...")
    vad_model = load_silero_vad(onnx=True)

    worker_thread = threading.Thread(target=transcription_worker, args=(bus,), daemon=True)
    worker_thread.start()

    audio_buffer = []
    silent_chunks = 0
    is_recording = False

    # Stricter thresholds: 0.65 probability to trigger speech, 35 chunks (~1.1s) silence limit
    vad_threshold = getattr(AUDIO, "VAD_THRESHOLD", 0.65)
    silence_limit = getattr(AUDIO, "SILENCE_CHUNKS_LIMIT", 35)

    def audio_callback(indata, frames, time_info, status):
        nonlocal silent_chunks, is_recording, audio_buffer

        if status:
            print(f"[!] Audio stream status flag: {status}")

        chunk = indata.copy().squeeze()
        chunk_tensor = torch.from_numpy(chunk)

        # Infer voice activity probability (fast ONNX execution ~1-2ms)
        speech_prob = vad_model(chunk_tensor, AUDIO.SAMPLE_RATE).item()

        if speech_prob > vad_threshold:
            if not is_recording:
                is_recording = True
                audio_buffer = []
                print("[🎙️ Speech Detected]")

                # Instant barge-in broadcast to halt ongoing speech synthesis
                interrupt_event = {
                    "event": "barge_in",
                    "timestamp": time.time(),
                }
                bus.send_string(f"VOICE_INTERRUPT {json.dumps(interrupt_event)}")

            audio_buffer.append(chunk)
            silent_chunks = 0

        elif is_recording:
            audio_buffer.append(chunk)
            silent_chunks += 1

            # Speech completion check (padded to wait through natural conversational pauses)
            if silent_chunks > silence_limit:
                is_recording = False
                full_audio = np.concatenate(audio_buffer, axis=0)
                transcription_queue.put(full_audio)

    print("[*] Audio Service Active. Listening on microphone... (Ctrl+C to stop)\n")

    with sd.InputStream(
        samplerate=AUDIO.SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=AUDIO.CHUNK_SIZE,
        callback=audio_callback,
    ):
        while True:
            sd.sleep(100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Audio Service...")