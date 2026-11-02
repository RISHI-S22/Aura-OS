import json
import threading
import zmq
import ollama

ZMQ_ADDR = "tcp://127.0.0.1:5555"
LLM_MODEL = "qwen2.5:3b"

is_generating = threading.Event()
cancel_generation = threading.Event()

def execute_reasoning(user_text: str):
    """Streams LLM tokens and aborts if a new interruption signal arrives."""
    global is_generating
    is_generating.set()
    cancel_generation.clear()

    print(f"\n[Aura]: ", end="", flush=True)

    try:
        stream = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Aura, an ambient and proactive edge OS co-pilot. "
                        "Keep answers short, concise, and focused on systems engineering."
                    ),
                },
                {"role": "user", "content": user_text},
            ],
            stream=True,
        )

        for chunk in stream:
            if cancel_generation.is_set():
                print("\n[!] Output aborted by incoming command.")
                break
            token = chunk["message"]["content"]
            print(token, end="", flush=True)

    except Exception as e:
        print(f"\n[!] Inference Error: {e}")
    finally:
        print()
        is_generating.clear()

def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect(ZMQ_ADDR)
    subscriber.setsockopt_string(zmq.SUBSCRIBE, "VOICE_INPUT")

    print(f"[*] Aura Cognitive Brain initialized. Listening on {ZMQ_ADDR}...")

    try:
        while True:
            message = subscriber.recv_string()
            _, payload_str = message.split(" ", 1)
            event = json.loads(payload_str)

            user_query = event.get("content", "").strip()
            if not user_query:
                continue

            # If user speaks while previous answer is outputting, cancel it (barge-in)
            if is_generating.is_set():
                cancel_generation.set()

            print(f"\n[Event Ingested - {event.get('source')}]: {user_query}")
            
            # Run in worker thread so message bus never blocks
            worker = threading.Thread(target=execute_reasoning, args=(user_query,), daemon=True)
            worker.start()

    except KeyboardInterrupt:
        print("\n[!] Shutting down Brain...")

if __name__ == "__main__":
    main()