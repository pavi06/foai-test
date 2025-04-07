import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
USER_ID = os.getenv("USERNAME", "default_user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def start_chat():
    print("[fo.ai] Streaming chat session started. Type 'exit' to quit.\n")
    # Load prefs once at session start
    prefs = requests.get(
        f"{API_URL}/preferences/load", params={"user_id": USER_ID}
    ).json().get("preferences", {})
    # print(f"🔍 Loaded preferences for {USER_ID}: {prefs}")
    try:
        while True:
            query = input(f"🧠 You ({USER_ID}) :")
            if query.strip().lower() in ("exit", "quit"):
                print("👋 Ending chat session.")
                break

            print("🤖 fo.ai:", end=" ", flush=True)
            full_response = ""
            try:
                with requests.post(
                    f"{API_URL}/analyze/stream",
                    json={
                        "query": query,
                        "user_id": USER_ID,
                        "region": AWS_REGION,
                        "preferences": prefs  # Include preferences in the request
                    },
                    stream=True
                ) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=1, decode_unicode=True):
                        if chunk:
                            full_response += chunk
                            print(chunk, end="", flush=True)
                print("\n")
            except Exception as e:
                print(f"⚠️  Error: {e}\n")

    except KeyboardInterrupt:
        print("\n👋 Chat interrupted by user. Goodbye.")
