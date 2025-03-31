
import argparse
import os
import signal
import subprocess
import time
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
PID_DIR = Path(".foai")
LOG_DIR = Path("logs")
API_PID_FILE = PID_DIR / "api.pid"
UI_PID_FILE = PID_DIR / "ui.pid"
API_LOG = LOG_DIR / "api.log"
UI_LOG = LOG_DIR / "ui.log"

def start_server(target):
    PID_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    if target in ("api", "all"):
        with API_LOG.open("w") as api_log:
            api_proc = subprocess.Popen(["uvicorn", "api:app", "--reload"], stdout=api_log, stderr=api_log)
            API_PID_FILE.write_text(str(api_proc.pid))
            print(f"[fo.ai] API server started with PID {api_proc.pid}")
    if target in ("ui", "all"):
        with UI_LOG.open("w") as ui_log:
            ui_proc = subprocess.Popen(["streamlit", "run", "foai_ui.py"], stdout=ui_log, stderr=ui_log)
            UI_PID_FILE.write_text(str(ui_proc.pid))
            print(f"[fo.ai] UI started with PID {ui_proc.pid}")

def stop_server(target):
    if target in ("api", "all") and API_PID_FILE.exists():
        pid = int(API_PID_FILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[fo.ai] API process {pid} stopped.")
        except ProcessLookupError:
            print("[fo.ai] API process not found.")
        API_PID_FILE.unlink(missing_ok=True)
    if target in ("ui", "all") and UI_PID_FILE.exists():
        pid = int(UI_PID_FILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[fo.ai] UI process {pid} stopped.")
        except ProcessLookupError:
            print("[fo.ai] UI process not found.")
        UI_PID_FILE.unlink(missing_ok=True)

def force_kill_all():
    print("[fo.ai] Force killing API and UI...")
    if API_PID_FILE.exists():
        try:
            os.kill(int(API_PID_FILE.read_text()), signal.SIGKILL)
            print("✅ API force-killed")
        except Exception as e:
            print(f"API forcekill error: {e}")
        API_PID_FILE.unlink(missing_ok=True)
    if UI_PID_FILE.exists():
        try:
            os.kill(int(UI_PID_FILE.read_text()), signal.SIGKILL)
            print("✅ UI force-killed")
        except Exception as e:
            print(f"UI forcekill error: {e}")
        UI_PID_FILE.unlink(missing_ok=True)
    print("[fo.ai] Attempting killall fallback...")
    subprocess.run("pkill -f 'uvicorn'", shell=True)
    subprocess.run("pkill -f 'streamlit'", shell=True)
    print("[fo.ai] All known processes terminated.")

def tail_logs(target):
    if target == "api" and API_LOG.exists():
        subprocess.run(["tail", "-f", str(API_LOG)])
    elif target == "ui" and UI_LOG.exists():
        subprocess.run(["tail", "-f", str(UI_LOG)])
    else:
        print(f"[fo.ai] No log file found for {target}")

def check_status():
    try:
        res = requests.get(f"{BASE_URL}/status", timeout=2)
        print(f"[fo.ai] API status: {res.json()['message']}")
    except Exception as e:
        print(f"[fo.ai] API not reachable: {e}")

def run_query(query, stream=False):
    if stream:
        try:
            with requests.post(
                f"{BASE_URL}/analyze/stream",
                json={"user_id": "cli", "instance_ids": []},
                stream=True,
            ) as r:
                r.raise_for_status()
                print("[fo.ai] Streaming response:")
                for chunk in r.iter_content(chunk_size=1, decode_unicode=True):
                    print(chunk, end="", flush=True)
                print()
        except Exception as e:
            print(f"[fo.ai] Stream error: {e}")
    else:
        try:
            r = requests.post(f"{BASE_URL}/analyze", json={"query": query})
            r.raise_for_status()
            print(r.json()["response"])
        except Exception as e:
            print(f"[fo.ai] API error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="fo.ai – Cloud Cost Intelligence CLI",
        epilog="Use 'foai_cli.py <command> --help' for more details on each command."
    )

    subparsers = parser.add_subparsers(dest="command")

    server_cmd = subparsers.add_parser("server", help="Manage API and UI processes")
    server_cmd.add_argument("action", choices=["start", "stop", "forcekill"], help="Start, stop, or force-kill the servers")
    server_cmd.add_argument("target", choices=["api", "ui", "all"], help="Which process to manage")

    logs_cmd = subparsers.add_parser("logs", help="Tail the API or UI logs")
    logs_cmd.add_argument("target", choices=["api", "ui"], help="Which log file to tail")

    status_cmd = subparsers.add_parser("status", help="Check if the fo.ai API is online")

    query_cmd = subparsers.add_parser("ask", help="Ask a question about your AWS costs")
    query_cmd.add_argument("query", help="The natural language query to ask fo.ai")
    query_cmd.add_argument(
        "--stream", action="store_true",
        help="Stream the LLM response token-by-token (uses /analyze/stream)"
    )

    args = parser.parse_args()

    if args.command == "server":
        if args.action == "start":
            start_server(args.target)
        elif args.action == "stop":
            stop_server(args.target)
        elif args.action == "forcekill":
            force_kill_all()
    elif args.command == "logs":
        tail_logs(args.target)
    elif args.command == "status":
        check_status()
    elif args.command == "ask":
        run_query(args.query, stream=args.stream)
    else:
        parser.print_help()
