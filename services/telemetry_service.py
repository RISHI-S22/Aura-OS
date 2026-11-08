"""
Aura-OS Terminal Telemetry Service
Intercepts subprocess runtime stderr streams and broadcasts crash context over ZeroMQ.
"""

import json
import os
import subprocess
import sys
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import zmq
from config import NET

def publish_crash_telemetry(socket: zmq.Socket, command: str, stderr_data: str, exit_code: int):
    payload = {
        "source": "terminal_interceptor",
        "command": command,
        "exit_code": exit_code,
        "stderr": stderr_data.strip(),
        "timestamp": time.time(),
    }
    time.sleep(0.2)
    socket.send_string(f"TERMINAL_CRASH {json.dumps(payload)}")
    print(f"\n[⚡ Telemetry Broadcasted] Crash detected in '{command}' (Exit Code {exit_code})")
    time.sleep(0.5)

def run_monitored_command(command: str, pub_socket: zmq.Socket):
    print(f"[*] Monitoring execution: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout.strip())

    if result.returncode != 0 and result.stderr:
        print(f"[-] Command exited with status {result.returncode}")
        publish_crash_telemetry(pub_socket, command, result.stderr, result.returncode)

def main():
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")

    if len(sys.argv) > 1:
        target_cmd = " ".join(sys.argv[1:])
        run_monitored_command(target_cmd, pub_socket)
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()