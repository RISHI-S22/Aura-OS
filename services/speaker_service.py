"""
Aura-OS Speaker Service
Subscribes to TTS_CHUNK events on port 5556 and plays speech via local TTS.
"""

import json
import os
import queue
import sys
import threading
import time
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET
import pyttsx3

speech_queue = queue.Queue()


def tts_worker():
    """Worker handling sequential speech synthesis without freezing SAPI5."""
    while True:
        item = speech_queue.get()
        if item is None:
            break

        text = item.get("text", "").strip()
        if text:
            try:
                engine = pyttsx3.init("sapi5")
                engine.setProperty("rate", 180)
                voices = engine.getProperty("voices")
                if len(voices) > 1:
                    engine.setProperty("voice", voices[1].id)
                
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                print(f"[!] Speaker playback error: {e}")
        speech_queue.task_done()


def main():
    context = zmq.Context()

    sub_tts = context.socket(zmq.SUB)
    sub_tts.connect(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")
    sub_tts.setsockopt_string(zmq.SUBSCRIBE, "TTS_CHUNK")

    sub_interrupt = context.socket(zmq.SUB)
    sub_interrupt.connect(f"tcp://{NET.HOST}:{NET.EVENT_BUS_PORT}")
    sub_interrupt.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

    poller = zmq.Poller()
    poller.register(sub_tts, zmq.POLLIN)
    poller.register(sub_interrupt, zmq.POLLIN)

    threading.Thread(target=tts_worker, daemon=True).start()
    print("[*] Aura Speaker Service active. Ready for audio playback...")

    try:
        while True:
            socks = dict(poller.poll(50))

            if sub_interrupt in socks:
                raw_msg = sub_interrupt.recv_string()
                while not speech_queue.empty():
                    try:
                        speech_queue.get_nowait()
                        speech_queue.task_done()
                    except queue.Empty:
                        break
                print("[⚡ Barge-In Triggered] Clearing audio playback queue!")

            if sub_tts in socks:
                raw_msg = sub_tts.recv_string()
                _, payload_str = raw_msg.split(" ", 1)
                payload = json.loads(payload_str)
                speech_queue.put(payload)

    except KeyboardInterrupt:
        print("\n[!] Shutting down Speaker Service...")


if __name__ == "__main__":
    main()