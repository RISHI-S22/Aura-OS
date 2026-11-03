import json
import re
import sys
import threading
import time
import ollama
import zmq

# ZeroMQ Endpoints
AUDIO_BUS_ADDR = "tcp://127.0.0.1:5555"   # Receives VOICE_INPUT and VOICE_INTERRUPT
TTS_BUS_PORT = 5556                       # Publishes TTS_TEXT chunks for speaker_service

MODEL_NAME = "qwen2.5:3b"

SYSTEM_PROMPT = """You are Aura, an ambient, autonomous edge OS copilot.
Be direct, technically precise, and concise. 
Avoid robotic filler. Respond in natural, conversational sentences suitable for speech synthesis."""

abort_generation = threading.Event()
generation_lock = threading.Lock()

def create_tts_publisher(port: int):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{port}")
    return socket

def process_and_stream_llm(user_prompt: str, tts_socket: zmq.Socket):
    """Streams Qwen 2.5 tokens, buffers into sentences, and publishes them to TTS."""
    with generation_lock:
        abort_generation.clear()
        print(f"\n[Aura Brain] Thinking...")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        sentence_delimiters = re.compile(r"([.?!:\n]+)")
        sentence_buffer = ""

        try:
            stream = ollama.chat(model=MODEL_NAME, messages=messages, stream=True)
            print("[Aura Brain Streaming]: ", end="", flush=True)

            for chunk in stream:
                # Check if user spoke mid-sentence (barge-in interrupt)
                if abort_generation.is_set():
                    print("\n[!] Generation aborted by incoming user speech.")
                    return

                token = chunk.get("message", {}).get("content", "")
                print(token, end="", flush=True)
                sentence_buffer += token

                # Check if a sentence is complete
                parts = sentence_delimiters.split(sentence_buffer)
                if len(parts) > 1:
                    # parts will alternate: [sentence_text, delimiter, sentence_text, delimiter, ...]
                    complete_sentence = parts[0].strip() + parts[1].strip()
                    sentence_buffer = "".join(parts[2:])

                    if complete_sentence:
                        # Publish directly to speaker_service
                        tts_socket.send_string(f"TTS_TEXT {complete_sentence}")

            # Flush any trailing words left in the buffer
            remaining = sentence_buffer.strip()
            if remaining and not abort_generation.is_set():
                tts_socket.send_string(f"TTS_TEXT {remaining}")

            print("\n[Aura Brain] Turn complete.\n")

        except Exception as e:
            print(f"\n[!] Error during LLM generation: {e}")

def main():
    print(f"[+] Binding TTS Stream Publisher on port {TTS_BUS_PORT}...")
    tts_socket = create_tts_publisher(TTS_BUS_PORT)
    time.sleep(0.5)

    context = zmq.Context()
    audio_sub = context.socket(zmq.SUB)
    audio_sub.connect(AUDIO_BUS_ADDR)
    audio_sub.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")
    audio_sub.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

    print(f"[+] Connected to Audio Event Bus at {AUDIO_BUS_ADDR}")
    print(f"[*] Aura Brain initialized with {MODEL_NAME}. Awaiting audio events...\n")

    current_worker_thread = None

    try:
        while True:
            raw_msg = audio_sub.recv_string()
            topic, payload_str = raw_msg.split(" ", 1)

            if topic == "VOICE_INTERRUPT":
                # Immediately trip the abort event
                abort_generation.set()

            elif topic == "VOICE_INPUT":
                payload = json.loads(payload_str)
                user_text = payload.get("content", "").strip()

                if not user_text:
                    continue

                print(f"\n[Mic Capture Ingested]: \"{user_text}\"")

                # Launch generation in a thread so main loop remains responsive to interrupts
                current_worker_thread = threading.Thread(
                    target=process_and_stream_llm,
                    args=(user_text, tts_socket),
                    daemon=True
                )
                current_worker_thread.start()

    except KeyboardInterrupt:
        print("\n[!] Shutting down Aura Brain...")

if __name__ == "__main__":
    main()