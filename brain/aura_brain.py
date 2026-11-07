"""
Aura-OS Brain Core
Subscribes to Audio (5555) and Telemetry (5557) event buses.
Queries Memory Service (5558) for episodic RAG context.
Streams tokens to TTS Engine (5556) via Ollama (Qwen 2.5:3b).
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
import re
import threading
import time
import requests
import zmq
from config import NET, MODELS

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = (
    "You are Aura, an ambient edge OS companion. Speak concisely, clearly, and naturally "
    "in 1 to 2 short sentences. When diagnosing terminal errors, state the exact root cause "
    "and offer one actionable command fix immediately. If historical context is provided, "
    "use it directly to answer questions about past errors or tasks."
)

MEMORY_KEYWORDS = ["earlier", "past", "history", "previous", "debug", "crash", "error", "what happened", "failed"]

class AuraBrain:
    def __init__(self):
        self.context = zmq.Context()

        # Inbound audio events
        self.sub_audio = self.context.socket(zmq.SUB)
        self.sub_audio.connect(f"tcp://{NET.HOST}:{NET.EVENT_BUS_PORT}")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

        # Telemetry ingestion: Brain binds to 5557
        self.sub_telemetry = self.context.socket(zmq.SUB)
        self.sub_telemetry.bind(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")
        self.sub_telemetry.setsockopt_string(zmq.SUBSCRIBE, "TERMINAL_CRASH")

        # Outbound TTS publisher
        self.pub_tts = self.context.socket(zmq.PUB)
        self.pub_tts.bind(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")

        # REQ client to query Memory Service
        self.req_memory = self.context.socket(zmq.REQ)
        self.req_memory.connect(f"tcp://{NET.HOST}:{NET.MEMORY_QUERY_PORT}")
        self.req_memory.setsockopt(zmq.RCVTIMEO, 1000)  # 1 sec timeout

        self.poller = zmq.Poller()
        self.poller.register(self.sub_audio, zmq.POLLIN)
        self.poller.register(self.sub_telemetry, zmq.POLLIN)

        self.current_generation_id = 0
        self.is_interrupted = False

    def fetch_memory_context(self, query: str) -> str:
        """Retrieves past crash or discussion context via ZeroMQ RPC."""
        try:
            self.req_memory.send_string(json.dumps({"query": query}))
            resp_str = self.req_memory.recv_string()
            data = json.loads(resp_str)
            return data.get("context", "")
        except Exception:
            return ""

    def stream_to_tts(self, prompt: str, prefix_alert: str = ""):
        self.current_generation_id += 1
        gen_id = self.current_generation_id
        self.is_interrupted = False

        if prefix_alert:
            self.pub_tts.send_string(f"TTS_CHUNK {json.dumps({'text': prefix_alert, 'gen_id': gen_id})}")

        payload = {
            "model": MODELS.LLM_MODEL,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": True,
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=10)
            buffer = ""

            for line in response.iter_lines():
                if self.is_interrupted or gen_id != self.current_generation_id:
                    print("[⚡ Inference Aborted via Barge-In]")
                    break

                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    buffer += token

                    if re.search(r"[.!?]\s*$", buffer):
                        chunk = buffer.strip()
                        buffer = ""
                        if chunk:
                            print(f"[Aura Brain -> TTS]: {chunk}")
                            self.pub_tts.send_string(
                                f"TTS_CHUNK {json.dumps({'text': chunk, 'gen_id': gen_id})}"
                            )

            if buffer.strip() and not self.is_interrupted:
                self.pub_tts.send_string(
                    f"TTS_CHUNK {json.dumps({'text': buffer.strip(), 'gen_id': gen_id})}"
                )

        except Exception as e:
            print(f"[!] Brain inference error: {e}")

    def handle_voice_input(self, user_text: str):
        prompt = f"User says: {user_text}"

        # If question references past context, perform RAG retrieval
        if any(k in user_text.lower() for k in MEMORY_KEYWORDS):
            context = self.fetch_memory_context(user_text)
            if context and context != "No relevant memory found.":
                prompt = (
                    f"Historical memory context:\n{context}\n\n"
                    f"Based on this history, answer the user's question: {user_text}"
                )

        self.stream_to_tts(prompt)

    def run(self):
        print("=" * 60)
        print("  🧠 Aura Brain Core Active")
        print(f"  Audio: {NET.EVENT_BUS_PORT} | Telemetry: {NET.TELEMETRY_PORT} | TTS: {NET.TTS_STREAM_PORT} | Memory: {NET.MEMORY_QUERY_PORT}")
        print("=" * 60 + "\n")

        while True:
            socks = dict(self.poller.poll(50))

            if self.sub_audio in socks:
                raw_msg = self.sub_audio.recv_string()
                topic, payload_str = raw_msg.split(" ", 1)
                payload = json.loads(payload_str)

                if topic == "VOICE_INTERRUPT":
                    print("[⚡ Barge-in Received] Cancelling ongoing inference...")
                    self.is_interrupted = True

                elif topic == "VOICE_INPUT":
                    user_text = payload.get("content", "")
                    print(f"\n[Mic Ingestion]: {user_text}")
                    threading.Thread(
                        target=self.handle_voice_input,
                        args=(user_text,),
                        daemon=True,
                    ).start()

            if self.sub_telemetry in socks:
                raw_msg = self.sub_telemetry.recv_string()
                topic, payload_str = raw_msg.split(" ", 1)
                payload = json.loads(payload_str)

                if topic == "TERMINAL_CRASH":
                    cmd = payload.get("command", "")
                    stderr = payload.get("stderr", "")
                    print(f"\n[🚨 Telemetry Ingestion]: Crash detected in '{cmd}'")

                    prompt = (
                        f"The user ran the command '{cmd}' and encountered this error traceback:\n"
                        f"{stderr}\n"
                        f"State the diagnosis and the exact fix."
                    )
                    threading.Thread(
                        target=self.stream_to_tts,
                        args=(prompt, "Rishi, I noticed a terminal crash."),
                        daemon=True,
                    ).start()


if __name__ == "__main__":
    brain = AuraBrain()
    brain.run()