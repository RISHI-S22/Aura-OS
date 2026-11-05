"""
Aura-OS Unified Process Manager
Orchestrates audio, brain, speaker, and telemetry services under a single supervised lifecycle.
"""

import subprocess
import sys
import time

SERVICES = [
    ("Audio Service", [sys.executable, "services/audio_service.py"]),
    ("Speaker Service", [sys.executable, "services/speaker_service.py"]),
    ("Aura Brain", [sys.executable, "brain/aura_brain.py"]),
]

def main():
    processes = []
    print("=" * 60)
    print("  🚀 Initializing Aura-OS Full-Duplex System Stack")
    print("=" * 60)

    try:
        for name, cmd in SERVICES:
            print(f"[+] Launching {name}...")
            p = subprocess.Popen(cmd)
            processes.append((name, p))
            time.sleep(1)  # Stagger launch to let ZMQ sockets bind cleanly

        print("\n[*] All Aura-OS subsystems active and running. Press Ctrl+C to stop all.\n")

        while True:
            time.sleep(0.5)
            # Check if any process unexpectedly died
            for name, p in processes:
                if p.poll() is not None:
                    print(f"[!] Warning: {name} terminated with returncode {p.returncode}")

    except KeyboardInterrupt:
        print("\n[!] Gracefully shutting down all Aura-OS subsystems...")
        for name, p in processes:
            print(f"[-] Terminating {name}...")
            p.terminate()
            p.wait()
        print("[✓] All processes stopped cleanly.")

if __name__ == "__main__":
    main()