import json
import time
import zmq
from RealtimeSTT import AudioToTextRecorder

ZMQ_PORT = 5555

def initialize_bus():
    """Initializes ZeroMQ PUB socket."""
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{ZMQ_PORT}")
    return socket

def main():
    print("[+] Initializing ZeroMQ Event Bus on port", ZMQ_PORT)
    bus = initialize_bus()
    # Give ZeroMQ subscribers a moment to register
    time.sleep(1)

    print("[+] Loading RealtimeSTT engine (Silero VAD + faster-whisper)...")
    
    recorder = AudioToTextRecorder(
        model="base.en",
        language="en",
        spinner=False,
        silero_use_onnx=True,
        silero_sensitivity=0.4,
        post_speech_silence_duration=0.6,
        wake_words="",
    )

    print("\n[*] Audio Service Active. Speak into your microphone... (Ctrl+C to stop)\n")

    try:
        while True:
            # Blocks until complete utterance is transcribed
            transcribed_text = recorder.text().strip()

            if transcribed_text:
                print(f"[Mic Capture]: {transcribed_text}")
                payload = {
                    "source": "voice",
                    "content": transcribed_text,
                    "timestamp": time.time()
                }
                bus.send_string(f"VOICE_INPUT {json.dumps(payload)}")

    except KeyboardInterrupt:
        print("\n[!] Stopping Audio Service...")
    finally:
        recorder.shutdown()

if __name__ == "__main__":
    main()