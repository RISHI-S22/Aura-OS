"""
Aura-OS Audio Capture & Speech Processing Service
Minimalist, clean console output.
"""

import collections
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

# Silence HuggingFace noise
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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
    if clean.lower() in HALLUCINATION_BLACKLIST or len(clean) <= 1:
        return ""
    return clean

def transcription_worker(bus: zmq.Socket, whisper_model: WhisperModel):
    while True:
        audio_data = transcription_queue.get()
        if audio_data is None:
            break

        if len(audio_data) < int(AUDIO.TARGET_SAMPLE_RATE * 0.4):
            transcription_queue.task_done()
            continue

        try:
            segments, info = whisper_model.transcribe(
                audio_data,
                beam_size=3,
                condition_on_previous_text=False,
                no_speech_threshold=0.5,
                log_prob_threshold=-1.0,
            )
            raw_text = " ".join([segment.text for segment in segments])
            transcribed_text = clean_transcription(raw_text)

            if transcribed_text:
                detected_lang = getattr(info, 'language', 'en')
                print(f"\n[You ({detected_lang})]: {transcribed_text}")
                payload = {
                    "source": "voice",
                    "content": transcribed_text,
                    "language": detected_lang,
                    "timestamp": time.time(),
                }
                bus.send_string(f"VOICE_INPUT {json.dumps(payload)}")
        except Exception:
            pass
        finally:
            transcription_queue.task_done()

def main():
    bus = initialize_bus(NET.EVENT_BUS_PORT)

    whisper_model = WhisperModel(
        MODELS.WHISPER_MODEL,
        device="cpu",
        compute_type=MODELS.WHISPER_COMPUTE,
    )
    vad_model = load_silero_vad(onnx=True)

    worker_thread = threading.Thread(
        target=transcription_worker,
        args=(bus, whisper_model),
        daemon=True
    )
    worker_thread.start()

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

    chunk_size = int(native_rate * 0.032)
    pre_roll_chunks = int(0.5 / 0.032)
    pre_roll_buffer = collections.deque(maxlen=pre_roll_chunks)

    audio_buffer = []
    silent_chunks = 0
    is_recording = False

    def audio_callback(indata, frames, time_info, status):
        nonlocal silent_chunks, is_recording, audio_buffer

        if channels > 1:
            mono = np.mean(indata, axis=1)
        else:
            mono = indata.squeeze()

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
                audio_buffer = list(pre_roll_buffer)
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
                audio_buffer = []
                silent_chunks = 0
                if hasattr(vad_model, 'reset_states'):
                    vad_model.reset_states()
        else:
            pre_roll_buffer.append(resampled_16k)

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
        pass