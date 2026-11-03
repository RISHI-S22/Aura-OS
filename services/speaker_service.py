import json
import queue
import threading
import sounddevice as sd
import pyttsx3
import zmq

TTS_SUB_ADDR = "tcp://127.0.0.1:5556"
EVENT_BUS_ADDR = "tcp://127.0.0.1:5555"

tts_queue = queue.Queue()
stop_playback = threading.Event()

def tts_worker():
    """Worker thread that executes speech and allows hardware stop."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 185)

    while True:
        text = tts_queue.get()
        if text is None:
            break

        stop_playback.clear()
        print(f"[Aura Speaking]: {text}")

        # Quick sentence playback with interruption checks
        engine.say(text)
        engine.runAndWait()
        tts_queue.task_done()

def main():
    context = zmq.Context()

    # Subscribe to Brain's TTS sentences
    brain_sub = context.socket(zmq.SUB)
    brain_sub.connect(TTS_SUB_ADDR)
    brain_sub.setsockopt_string(zmq.SUBSCRIBE, "TTS_TEXT")

    # Subscribe to Mic's VAD interrupt signals
    mic_sub = context.socket(zmq.SUB)
    mic_sub.connect(EVENT_BUS_ADDR)
    mic_sub.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

    # Start speech worker
    threading.Thread(target=tts_worker, daemon=True).start()

    print("[*] Aura Speaker Service active. Ready for audio playback...")

    poller = zmq.Poller()
    poller.register(brain_sub, zmq.POLLIN)
    poller.register(mic_sub, zmq.POLLIN)

    try:
        while True:
            socks = dict(poller.poll(50))

            # Hardware barge-in interrupt from mic
            if mic_sub in socks:
                msg = mic_sub.recv_string()
                print("\n[⚡ Barge-In Triggered] Clearing audio playback queue!")
                # Empty any pending sentences immediately
                while not tts_queue.empty():
                    try:
                        tts_queue.get_nowait()
                        tts_queue.task_done()
                    except queue.Empty:
                        break
                stop_playback.set()

            # New speech sentences from LLM brain
            if brain_sub in socks:
                msg = brain_sub.recv_string()
                _, text = msg.split(" ", 1)
                tts_queue.put(text.strip())

    except KeyboardInterrupt:
        print("\n[!] Stopping Speaker Service...")

if __name__ == "__main__":
    main()