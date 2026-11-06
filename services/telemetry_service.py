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
    """Encapsulates a crash event and broadcasts it to the Aura Event Bus."""
    payload = {
        "source": "terminal_interceptor",
        "command": command,
        "exit_code": exit_code,
        "stderr": stderr_data.strip(),
        "timestamp": time.time(),
    }
    # Allow ZeroMQ handshake to establish before sending
    time.sleep(0.2)
    socket.send_string(f"TERMINAL_CRASH {json.dumps(payload)}")
    print(f"\n[⚡ Telemetry Broadcasted] Crash detected in '{command}' (Exit Code {exit_code})")
    time.sleep(0.3)


def run_monitored_command(command: str, pub_socket: zmq.Socket):
    """Executes a command and monitors stderr for failures."""
    print(f"[*] Monitoring execution: {command}")

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate()

    if stdout:
        print(stdout.strip())

    if process.returncode != 0 and stderr:
        publish_crash_telemetry(pub_socket, command, stderr, process.returncode)


def main():
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")

    if len(sys.argv) > 1:
        target_cmd = " ".join(sys.argv[1:])
        run_monitored_command(target_cmd, pub_socket)
    else:
        # Keep alive if started by supervisor runner
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()