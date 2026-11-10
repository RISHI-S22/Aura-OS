import subprocess
import sys

def main():
    print("Starting AURA-OS server...")
    subprocess.run(["uvicorn", "aura.api.main:app", "--reload", "--port", "8000"])

if __name__ == "__main__":
    main()
