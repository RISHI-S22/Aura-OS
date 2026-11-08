"""
Aura-OS Audio Capture & Speech Processing Service
Hardware-matched audio capture with native-rate downsampling,
Silero VAD segmentation, and faster-whisper transcription.
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
from scipy.signal import resample_poly

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET, AUDIO, MODELS

transcription_queue = queue.Queue()

HALLUCINATION_BLACKLIST = {
    "thank you.", "thank you", "thanks for watching.", "thanks for watching",
    "see you in the next video.", "we'll see you in the next video.",
    "subscribe to the channel.", "you", ".", "next.", "invite them.", "on this."
}

def initialize_bus(port: int):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://{NET.HOST}:{port}")
    return socket

def clean_transcription(text: str) -> str:
    clean = text.strip()
    if clean.lower() in HALLUCINATION_BLACKLIST or len(clean) <= 2:
        return ""
    return clean

def transcription_worker(bus: zmq.Socket):
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

        # Discard clips shorter than 0.35s
        if len(audio_data) < int(AUDIO.TARGET_SAMPLE_RATE * 0.35):
            transcription_queue.task_done()
            continue

        try:
            segments, _ = whisper_model.transcribe(
                audio_data,
                beam_size=3,
                condition_on_previous_text=False,
                no_speech_threshold=0.5,
                log_prob_threshold=-1.0,
            )
            raw_text = " ".join([segment.text for segment in segments])
            transcribed_text = clean_transcription(raw_text)

            if transcribed_text:
                print(f"[Mic Capture]: {transcribed_text}")
                payload = {
                    "source": "voice",
                    "content": transcribed_text,
                    "timestamp": time.time(),
                }
                bus.send_string(f"VOICE_INPUT {json.dumps(payload)}")
        except Exception as e:
            print(f"[!] Transcription error: {e}")
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

    # Detect high-fidelity microphone (prefer Realtek internal array over bluetooth hands-free)
    input_devices = sd.query_devices()
    chosen_device_idx = None
    for idx, dev in enumerate(input_devices):
        if dev['max_input_channels'] > 0 and 'Realtek' in dev['name']:
            chosen_device_idx = idx
            break

    if chosen_device_idx is None:
        device_info = sd.query_devices(kind='input')
        chosen_device_idx = device_info['index']
    else:
        device_info = sd.query_devices(chosen_device_idx)

    native_rate = int(device_info['default_samplerate'])
    channels = min(int(device_info['max_input_channels']), 2)
    print(f"[+] Audio hardware: [{chosen_device_idx}] '{device_info['name']}' @ {native_rate}Hz ({channels} ch)")

    chunk_size = int(native_rate * 0.032)
    audio_buffer = []
    silent_chunks = 0
    is_recording = False

    def audio_callback(indata, frames, time_info, status):
        nonlocal silent_chunks, is_recording, audio_buffer

        if channels > 1:
            mono = np.mean(indata, axis=1)
        else:
            mono = indata.squeeze()

        # Polyphase anti-aliasing resampling to 16 kHz
        resampled_16k = resample_poly(mono, AUDIO.TARGET_SAMPLE_RATE, native_rate).astype(np.float32)

        if len(resampled_16k) > 512:
            vad_chunk = resampled_16k[:512]
        elif len(resampled_16k) < 512:
            vad_chunk = np.pad(resampled_16k, (0, 512 - len(resampled_16k)))
        else:
            vad_chunk = resampled_16k

        chunk_tensor = torch.from_numpy(vad_chunk)
        speech_prob = vad_model(chunk_tensor, AUDIO.TARGET_SAMPLE_RATE).item()

        if speech_prob > AUDIO.VAD_THRESHOLD:
            if not is_recording:
                is_recording = True
                audio_buffer = []
                print("[🎙️ Speech Detected]")
                interrupt_event = {"event": "barge_in", "timestamp": time.time()}
                bus.send_string(f"VOICE_INTERRUPT {json.dumps(interrupt_event)}")

            audio_buffer.append(resampled_16k)
            silent_chunks = 0
        elif is_recording:
            audio_buffer.append(resampled_16k)
            silent_chunks += 1

            if silent_chunks > AUDIO.SILENCE_CHUNKS_LIMIT:
                is_recording = False
                full_audio = np.concatenate(audio_buffer, axis=0)
                transcription_queue.put(full_audio)

    print("[*] Audio Service Active. Listening on microphone... (Ctrl+C to stop)\n")

    with sd.InputStream(
        device=chosen_device_idx,
        samplerate=native_rate,
        channels=channels,
        dtype="float32",
        blocksize=chunk_size,
        callback=audio_callback,
    ):
        while True:
            sd.sleep(100)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Shutting down Audio Service...")