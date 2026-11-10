import subprocess
import sys

def main():
    print("Setting up AURA-OS environment...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    print("AURA-OS environment installed successfully!")

if __name__ == "__main__":
    main()
