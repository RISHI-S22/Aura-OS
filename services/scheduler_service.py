"""
Aura-OS Background Scheduler Service
Dispatches proactive time-based actions, timed pauses,
and recurring background tasks over ZeroMQ.
"""

import json
import os
import sys
import threading
import time
import zmq

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import NET

class SchedulerService:
    def __init__(self):
        self.context = zmq.Context()
        self.pub_tts = self.context.socket(zmq.PUB)
        self.pub_tts.connect(f"tcp://{NET.HOST}:{NET.TTS_STREAM_PORT}")

        self.push_action = self.context.socket(zmq.PUSH)
        self.push_action.connect(f"tcp://{NET.HOST}:{NET.ACTION_PORT}")

    def speak(self, text: str):
        payload = {"text": text, "gen_id": int(time.time() * 1000)}
        self.pub_tts.send_string(f"TTS_CHUNK {json.dumps(payload)}")

    def schedule_reminder(self, task_description: str, delay_seconds: int):
        def worker():
            time.sleep(delay_seconds)
            self.speak(f"Reminder alert: {task_description}")
            print(f"[⏰ Reminder Fired]: {task_description}")
        threading.Thread(target=worker, daemon=True).start()

    def run(self):
        print("[*] Scheduler Service online and ready.")
        while True:
            time.sleep(60)

if __name__ == "__main__":
    scheduler = SchedulerService()
    scheduler.run()