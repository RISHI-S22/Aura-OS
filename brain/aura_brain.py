"""
Aura-OS Central Brain Orchestrator
Routes intents between conversational inference, episodic RAG,
the Universal OS Operator, and background dev agents.
"""

import json
import os
import re
import sys
import threading
import time
import requests
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET, MODELS
from brain.os_operator import UniversalOSOperator
from brain.dynamic_synthesizer import DynamicSynthesizer
from brain.dev_agent import AutonomousDevAgent

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = (
    "You are Aura, an ambient edge operating system intelligence. "
    "Be concise, direct, and conversational. You never cite hardware limits or say you cannot perform a task. "
    "When a task requires desktop control, you invoke the OS operator."
)

class AuraBrain:
    def __init__(self):
        self.context = zmq.Context()

        self.sub_audio = self.context.socket(zmq.SUB)
        self.sub_audio.connect(f"tcp://{NET.HOST}:{NET.EVENT_BUS_PORT}")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

        self.sub_telemetry = self.context.socket(zmq.SUB)
        self.sub_telemetry.bind(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")
        self.sub_telemetry.setsockopt_string(zmq.SUBSCRIBE, "TERMINAL_CRASH")

        self.pub_tts = self.context.socket(zmq.PUB)
        self.pub_tts.bind(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")

        self.push_action = self.context.socket(zmq.PUSH)
        self.push_action.connect(f"tcp://{NET.HOST}:{NET.ACTION_PORT}")

        self.req_memory = self.context.socket(zmq.REQ)
        self.req_memory.connect(f"tcp://{NET.HOST}:{NET.MEMORY_QUERY_PORT}")
        self.req_memory.setsockopt(zmq.RCVTIMEO, 1000)

        self.poller = zmq.Poller()
        self.poller.register(self.sub_audio, zmq.POLLIN)
        self.poller.register(self.sub_telemetry, zmq.POLLIN)

        self.operator = UniversalOSOperator(tts_callback=self.speak_direct)
        self.synthesizer = DynamicSynthesizer()
        self.dev_agent = AutonomousDevAgent(feedback_callback=self.speak_direct)
        self.is_interrupted = False
        self.current_gen_id = 0

    def speak_direct(self, text: str):
        self.current_gen_id += 1
        payload = {"text": text, "gen_id": self.current_gen_id}
        self.pub_tts.send_string(f"TTS_CHUNK {json.dumps(payload)}")
        print(f"[Aura Brain -> Direct TTS]: {text}")

    def fetch_memory_context(self, query: str) -> str:
        try:
            self.req_memory.send_string(json.dumps({"query": query}))
            resp = json.loads(self.req_memory.recv_string())
            return resp.get("context", "")
        except Exception:
            return ""

    def parse_and_route(self, text: str):
        lower = text.lower().strip()
        print(f"[Brain Routing Input]: '{lower}'")

        # 1. Handle Active Confirmation Gate First (e.g., "Yes", "Send it", "Cancel")
        if self.operator.awaiting_confirmation:
            if self.operator.handle_confirmation(lower):
                return

        # 2. Simple Media Pause / Resume Hotkey
        if lower in ["pause", "resume", "stop playback", "play media"]:
            self.push_action.send_string(json.dumps({"action": "MEDIA_TOGGLE"}))
            return

        # 3. Timed Pause Timer ("pause at 1 hour 50 mins", "pause in 10 seconds")
        match = re.search(r"pause\s+(?:at|in)?\s*(\d+)\s*(hour|hr|minute|min|sec)", lower)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            secs = val * 3600 if "h" in unit else (val * 60 if "m" in unit else val)
            self.push_action.send_string(json.dumps({"action": "SCHEDULED_PAUSE", "seconds": secs}))
            return

        # 4. Autonomous Project Scaffolding
        if "build" in lower and any(k in lower for k in ["system", "app", "project", "hospital"]):
            self.speak_direct("Initiating autonomous development pipeline.")
            threading.Thread(
                target=self.dev_agent.scaffold_project,
                args=("hospital-system", "Spring Boot Java 17"),
                daemon=True
            ).start()
            return

        # 5. Complex Desktop Human Actions (Universal Operator)
        # Matches: messaging, composing, search-and-play across any site/app (YouTube, JioSaavn, WhatsApp, etc.)
        complex_intent_keywords = [
            "search for", "play", "send a message", "write a message", "message",
            "whatsapp", "youtube", "jiosaavn", "spotify", "music", "email",
            "type", "compose", "telegram", "discord"
        ]
        is_complex_action = any(k in lower for k in complex_intent_keywords) and len(lower.split()) > 3

        if is_complex_action:
            threading.Thread(
                target=self.operator.execute_goal,
                args=(text,),
                daemon=True
            ).start()
            return

        # 6. Single App / Single Site Quick Launcher
        app_match = re.match(r"^(?:open|launch|start)\s+(.+)$", lower)
        if app_match:
            raw_target = app_match.group(1).strip()
            self.push_action.send_string(json.dumps({
                "action": "LAUNCH_APP",
                "app": raw_target
            }))
            return

        # 7. Conversational Inference Fallback
        self.stream_llm(f"User says: {text}")

    def stream_llm(self, prompt: str, prefix_alert: str = ""):
        self.current_gen_id += 1
        gen_id = self.current_gen_id
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
            res = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=10)
            buffer = ""
            for line in res.iter_lines():
                if self.is_interrupted or gen_id != self.current_gen_id:
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
                            self.pub_tts.send_string(f"TTS_CHUNK {json.dumps({'text': chunk, 'gen_id': gen_id})}")

            if buffer.strip() and not self.is_interrupted:
                self.pub_tts.send_string(f"TTS_CHUNK {json.dumps({'text': buffer.strip(), 'gen_id': gen_id})}")
        except Exception as e:
            print(f"[!] Brain inference error: {e}")

    def run(self):
        print("=" * 60)
        print("  🧠 Aura Orchestrator Online (Universal OS Operator Active)")
        print(f"  Audio: {NET.EVENT_BUS_PORT} | Telemetry: {NET.TELEMETRY_PORT} | TTS: {NET.TTS_STREAM_PORT} | Action: {NET.ACTION_PORT}")
        print("=" * 60 + "\n")

        while True:
            socks = dict(self.poller.poll(50))

            if self.sub_audio in socks:
                raw_msg = self.sub_audio.recv_string()
                topic, payload_str = raw_msg.split(" ", 1)
                payload = json.loads(payload_str)

                if topic == "VOICE_INTERRUPT":
                    self.is_interrupted = True
                elif topic == "VOICE_INPUT":
                    content = payload.get("content", "")
                    print(f"\n[Mic Ingestion]: {content}")
                    threading.Thread(target=self.parse_and_route, args=(content,), daemon=True).start()

            if self.sub_telemetry in socks:
                raw_msg = self.sub_telemetry.recv_string()
                _, payload_str = raw_msg.split(" ", 1)
                payload = json.loads(payload_str)
                cmd = payload.get("command", "")
                stderr = payload.get("stderr", "")
                self.stream_llm(f"Terminal crash in '{cmd}':\n{stderr}\nDiagnose and fix:", "Crash detected.")

if __name__ == "__main__":
    brain = AuraBrain()
    brain.run()