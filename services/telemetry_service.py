"""
Aura-OS Terminal Telemetry Service
Intercepts subprocess runtime stderr streams and broadcasts crash context over ZeroMQ.
"""

import json
import subprocess
import sys
import time
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
    socket.send_string(f"TERMINAL_CRASH {json.dumps(payload)}")
    print(f"\n[⚡ Telemetry Broadcasted] Crash detected in '{command}' (Exit Code {exit_code})")

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
    pub_socket.bind(f"tcp://{NET.HOST}:{NET.TELEMETRY_PORT}")
    time.sleep(0.5)

    print(f"[+] Telemetry Service bound to port {NET.TELEMETRY_PORT}")
    print("[*] Ready to monitor shell executions. Pass a command to test.\n")

    # If arguments are passed to the script, run them through the watcher
    if len(sys.argv) > 1:
        target_cmd = " ".join(sys.argv[1:])
        run_monitored_command(target_cmd, pub_socket)
    else:
        print("[!] No command supplied. Running deliberate fail test (python -c '1/0')...")
        run_monitored_command("python -c \"1/0\"", pub_socket)

if __name__ == "__main__":
    main()