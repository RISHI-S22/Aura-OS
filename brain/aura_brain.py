"""
Aura-OS Central Brain Orchestrator
Pure LLM-driven dispatching without hardcoded domain lists or regexes.
"""

import asyncio
import json
import os
import sys
import threading
import requests
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET, MODELS, PATHS
from brain.os_operator import UniversalOSOperator
from brain.enterprise_dev_agent import EnterpriseDevAgent
from brain.temporal_memory import TemporalMemoryEngine
from services.universal_caller import UniversalCaller
from services.universal_web_agent import UniversalWebAgent
from services.package_bootstrapper import PackageBootstrapper

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = (
    "You are Aura, an ambient edge operating system intelligence. "
    "Respond in the exact language used by the user. Be direct, natural, and concise."
)

class AuraBrain:
    def __init__(self):
        self.context = zmq.Context()

        self.sub_audio = self.context.socket(zmq.SUB)
        self.sub_audio.connect(f"tcp://{NET.HOST}:{NET.EVENT_BUS_PORT}")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INTERRUPT")

        self.pub_tts = self.context.socket(zmq.PUB)
        self.pub_tts.bind(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")

        # Core Engines
        self.operator = UniversalOSOperator(tts_callback=self.speak_direct)
        self.caller = UniversalCaller(tts_callback=self.speak_direct)
        self.web_agent = UniversalWebAgent(tts_callback=self.speak_direct)
        self.dev_agent = EnterpriseDevAgent(feedback_callback=self.speak_direct)
        self.bootstrapper = PackageBootstrapper(tts_callback=self.speak_direct)
        self.temporal_memory = TemporalMemoryEngine()

        self.pending_temporal_suggestion = None
        self.is_interrupted = False
        self.current_gen_id = 0

    def speak_direct(self, text: str):
        self.current_gen_id += 1
        payload = {"text": text, "gen_id": self.current_gen_id}
        self.pub_tts.send_string(f"TTS_CHUNK {json.dumps(payload)}")
        print(f"[Aura]: {text}")

    def route_speech(self, text: str, detected_lang: str):
        lower = text.lower().strip()

        # Check Active Confirmation Gates First
        if self.caller.pending_call and self.caller.handle_call_choice(lower):
            return
        if self.operator.awaiting_confirmation and self.operator.handle_confirmation(lower):
            return

        # Classify Intent using Local LLM
        prompt = (
            f"Classify the intended operation for this request: '{text}'.\n"
            "Return JSON ONLY:\n"
            "{\n"
            "  \"category\": \"WEB\" | \"DESKTOP_UI\" | \"CALL\" | \"LOCAL_BUILD\" | \"CONVERSATION\"\n"
            "}"
        )
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": MODELS.LLM_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }, timeout=10).json()
            category = json.loads(res.get("response", "{}")).get("category", "CONVERSATION")
        except Exception:
            category = "CONVERSATION"

        # 1. Autonomous Web Agent (Shopping, Video, Coding, Web AI, Browsing)
        if category == "WEB":
            threading.Thread(
                target=lambda: asyncio.run(self.web_agent.execute_task(text)),
                daemon=True
            ).start()
            return

        # 2. Desktop UI Automation (Local Windows Apps)
        elif category == "DESKTOP_UI":
            threading.Thread(
                target=self.operator.execute_goal,
                args=(text,),
                daemon=True
            ).start()
            return

        # 3. Desktop Calling
        elif category == "CALL":
            threading.Thread(
                target=self.caller.initiate_universal_call,
                args=("active window", text),
                daemon=True
            ).start()
            return

        # 4. Local Software Project Generation
        elif category == "LOCAL_BUILD":
            self.speak_direct("Initiating engineering pipeline.")
            threading.Thread(
                target=self.dev_agent.build_enterprise_platform,
                args=("custom-project", text),
                daemon=True
            ).start()
            return

        # 5. Direct Conversation
        self.stream_llm(f"User says: {text}", detected_lang)

    def stream_llm(self, prompt: str, detected_lang: str):
        self.current_gen_id += 1
        gen_id = self.current_gen_id
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": MODELS.LLM_MODEL,
                "prompt": prompt,
                "system": f"{SYSTEM_PROMPT} (Language: {detected_lang})",
                "stream": True
            }, stream=True, timeout=12)

            full_reply = ""
            for line in res.iter_lines():
                if self.is_interrupted or gen_id != self.current_gen_id:
                    break
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    full_reply += token
                    if any(p in token for p in [".", "!", "?", "।", "\n"]):
                        self.pub_tts.send_string(f"TTS_CHUNK {json.dumps({'text': full_reply.strip(), 'gen_id': gen_id})}")
                        full_reply = ""
            if full_reply.strip() and not self.is_interrupted:
                self.pub_tts.send_string(f"TTS_CHUNK {json.dumps({'text': full_reply.strip(), 'gen_id': gen_id})}")
        except Exception:
            pass

    def run(self):
        print("=" * 60)
        print("  🧠 Aura Orchestrator Online (Autonomous Tree-Grounded Engine)")
        print(f"  Bus: Audio={NET.EVENT_BUS_PORT} | TTS={NET.TTS_STREAM_PORT} | Action={NET.ACTION_PORT}")
        print("=" * 60 + "\n")

        while True:
            raw_msg = self.sub_audio.recv_string()
            topic, payload_str = raw_msg.split(" ", 1)
            payload = json.loads(payload_str)

            if topic == "VOICE_INTERRUPT":
                self.is_interrupted = True
            elif topic == "VOICE_INPUT":
                content = payload.get("content", "")
                detected_lang = payload.get("language", "en")
                threading.Thread(
                    target=self.route_speech,
                    args=(content, detected_lang),
                    daemon=True
                ).start()

if __name__ == "__main__":
    brain = AuraBrain()
    brain.run()