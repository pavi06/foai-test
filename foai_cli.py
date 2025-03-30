#!/usr/bin/env python3
import argparse
import os
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
UI_FILE = os.getenv("FOAI_UI_FILE", "foai_ui.py")

# ----------- Server Commands -----------

def start_api():
    log_path = os.path.join("logs", "api.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        subprocess.Popen(["uvicorn", "api:app", "--reload"], stdout=log_file, stderr=log_file)
    print(f"🚀 API server started at http://localhost:8000 → logs at {log_path}")

def start_ui():
    log_path = os.path.join("logs", "ui.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        subprocess.Popen(["streamlit", "run", UI_FILE], stdout=log_file, stderr=log_file)
    print(f"🖥️ UI started from `{UI_FILE}` at http://localhost:8501 → logs at {log_path}")

def server_status():
    try:
        res = requests.get(f"{API_BASE_URL}/status", timeout=2)
        if res.ok:
            print(f"✅ API running: {res.json().get('message')}")
        else:
            print("🛑 API not responding")
    except Exception:
        print("🛑 API not reachable")

    print("⚠️ UI status: open http://localhost:8501 to verify")

# ----------- CLI Entry Point -----------

def main():
    parser = argparse.ArgumentParser(prog="foai", description="fo.ai – Cloud Cost Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    # server commands
    server_cmd = subparsers.add_parser("server", help="Manage API/UI dev servers")
    server_cmd.add_argument("action", choices=["start", "api", "ui", "status", "stop"], help="Action to perform")

    # logs (optional future)
    # logs_cmd = subparsers.add_parser("logs", help="Tail logs")
    # logs_cmd.add_argument("target", choices=["api", "ui"], help="Log target")

    # default behavior
    parser.add_argument("--query", type=str, help="Ask a cost question (e.g. EC2 savings)")
    parser.add_argument("--status", action="store_true", help="Check API health")
    parser.add_argument("--json", action="store_true", help="Show raw response")
    parser.add_argument("--mock", action="store_true", help="Use mock mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # server commands
    if args.command == "server":
        if args.action == "start":
            start_api()
            start_ui()
        elif args.action == "api":
            start_api()
        elif args.action == "ui":
            start_ui()
        elif args.action == "status":
            server_status()
        elif args.action == "stop":
            print("🛑 No process tracking yet. Use Ctrl+C or kill manually.")
        return

    # health check only
    if args.status:
        server_status()
        return

    # query flow
    if not args.query:
        parser.error("You must specify --query or use `foai server ...`")

    if args.verbose:
        print(f"[DEBUG] Sending request to: {API_BASE_URL}/analyze")
        print(f"[DEBUG] Query: {args.query}")

    try:
        res = requests.post(f"{API_BASE_URL}/analyze", json={"query": args.query})
        res.raise_for_status()
        result = res.json()

        print("\n=== 🧠 Summary ===\n")
        print(result.get("response", "(No summary provided)"))

        if args.json:
            print("\n=== 📦 Raw JSON ===\n")
            from pprint import pprint
            pprint(result.get("raw", []))
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
