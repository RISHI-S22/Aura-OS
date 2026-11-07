"""
Aura-OS Persistent Episodic Memory Service
Embeds and indexes voice interactions, terminal crashes, and diagnostic fixes.
Exposes a ZeroMQ REP socket (5558) for semantic memory search queries.
"""

import json
import os
import sys
import time
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET
import chromadb
from chromadb.utils import embedding_functions

STORAGE_DIR = os.path.join(ROOT_DIR, "storage", "aura_memory")
os.makedirs(STORAGE_DIR, exist_ok=True)


class AuraMemoryService:
    def __init__(self):
        print(f"[+] Initializing Persistent Vector Memory at {STORAGE_DIR}...")
        self.client = chromadb.PersistentClient(path=STORAGE_DIR)
        
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.conv_collection = self.client.get_or_create_collection(
            name="conversations", embedding_function=self.embed_fn
        )
        self.telemetry_collection = self.client.get_or_create_collection(
            name="telemetry_events", embedding_function=self.embed_fn
        )

        self.context = zmq.Context()
        
        # Audio subscriber
        self.sub_audio = self.context.socket(zmq.SUB)
        self.sub_audio.connect(f"tcp://{NET.HOST}:{NET.EVENT_BUS_PORT}")
        self.sub_audio.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")

        # Telemetry subscriber
        self.sub_telemetry = self.context.socket(zmq.SUB)
        self.sub_telemetry.connect(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")
        self.sub_telemetry.setsockopt_string(zmq.SUBSCRIBE, "TERMINAL_CRASH")

        # Memory Query Server (REP) for Brain RAG searches
        self.rep_query = self.context.socket(zmq.REP)
        self.rep_query.bind(f"tcp://{NET.HOST}:{NET.MEMORY_QUERY_PORT}")

        self.poller = zmq.Poller()
        self.poller.register(self.sub_audio, zmq.POLLIN)
        self.poller.register(self.sub_telemetry, zmq.POLLIN)
        self.poller.register(self.rep_query, zmq.POLLIN)

    def log_conversation(self, text: str):
        event_id = f"conv_{int(time.time() * 1000)}"
        self.conv_collection.add(
            documents=[text],
            metadatas=[{"timestamp": time.time(), "type": "user_voice"}],
            ids=[event_id]
        )
        print(f"[💾 Memory Logged] Indexed speech event: '{text[:50]}...'")

    def log_crash(self, command: str, stderr: str, exit_code: int):
        event_id = f"crash_{int(time.time() * 1000)}"
        doc = f"Command: {command}\nExit Code: {exit_code}\nError: {stderr}"
        self.telemetry_collection.add(
            documents=[doc],
            metadatas=[{
                "timestamp": time.time(),
                "command": command,
                "exit_code": exit_code,
                "type": "terminal_crash"
            }],
            ids=[event_id]
        )
        print(f"[💾 Memory Logged] Indexed crash event for: '{command}'")

    def query_memory(self, query: str, n_results: int = 2) -> str:
        """Searches conversation and crash history for relevant context."""
        retrieved_snippets = []
        try:
            telemetry_res = self.telemetry_collection.query(
                query_texts=[query], n_results=n_results
            )
            docs = telemetry_res.get("documents", [[]])[0]
            if docs:
                retrieved_snippets.extend(docs)

            conv_res = self.conv_collection.query(
                query_texts=[query], n_results=n_results
            )
            conv_docs = conv_res.get("documents", [[]])[0]
            if conv_docs:
                retrieved_snippets.extend(conv_docs)

        except Exception as e:
            print(f"[!] Query memory failed: {e}")

        return "\n---\n".join(retrieved_snippets) if retrieved_snippets else "No relevant memory found."

    def run(self):
        print(f"[*] Memory Service active. Query RPC bound on port {NET.MEMORY_QUERY_PORT}...")
        try:
            while True:
                socks = dict(self.poller.poll(100))
                
                # Handle incoming memory search queries from Brain
                if self.rep_query in socks:
                    request_str = self.rep_query.recv_string()
                    req = json.loads(request_str)
                    query_text = req.get("query", "")
                    print(f"[🔍 Memory Search]: Querying for '{query_text}'")
                    result_context = self.query_memory(query_text)
                    self.rep_query.send_string(json.dumps({"context": result_context}))

                if self.sub_audio in socks:
                    raw_msg = self.sub_audio.recv_string()
                    topic, payload_str = raw_msg.split(" ", 1)
                    payload = json.loads(payload_str)
                    content = payload.get("content", "")
                    if content:
                        self.log_conversation(content)

                if self.sub_telemetry in socks:
                    raw_msg = self.sub_telemetry.recv_string()
                    topic, payload_str = raw_msg.split(" ", 1)
                    payload = json.loads(payload_str)
                    cmd = payload.get("command", "")
                    stderr = payload.get("stderr", "")
                    exit_code = payload.get("exit_code", 1)
                    self.log_crash(cmd, stderr, exit_code)

        except KeyboardInterrupt:
            print("\n[!] Shutting down Memory Service...")


if __name__ == "__main__":
    service = AuraMemoryService()
    service.run()