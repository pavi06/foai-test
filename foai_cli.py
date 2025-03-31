#!/usr/bin/env python3
import argparse
import os
import subprocess
import signal
import requests
import json
from dotenv import load_dotenv
from version import __version__

load_dotenv()

API_BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
UI_FILE = os.getenv("FOAI_UI_FILE", "foai_ui.py")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
USERNAME = os.getenv("USERNAME", "default")

API_PID_FILE = ".api.pid"
UI_PID_FILE = ".ui.pid"

def write_pid(file, pid):
    with open(file, "w") as f:
        f.write(str(pid))

def read_pid(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return int(f.read())
    return None

def stop_process(pid_file, label):
    pid = read_pid(pid_file)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            os.remove(pid_file)
            print(f"🛑 {label} stopped (PID {pid})")
        except ProcessLookupError:
            print(f"⚠️ {label} not running (stale PID {pid})")
    else:
        print(f"⚠️ No PID file found for {label}")

def kill_process(pid_file, label):
    pid = read_pid(pid_file)
    if pid:
        try:
            os.kill(pid, signal.SIGKILL)
            os.remove(pid_file)
            print(f"☠️  Killed {label} (PID {pid})")
        except Exception as e:
            print(f"⚠️ Could not kill {label}: {e}")
    else:
        print(f"⚠️ No PID file found for {label}")

def start_api():
    log_path = os.path.join("logs", "api.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(["uvicorn", "api:app", "--reload"], stdout=log_file, stderr=log_file)
        write_pid(API_PID_FILE, proc.pid)
        print(f"🚀 API started at {API_BASE_URL} → logs: {log_path}")

def start_ui():
    log_path = os.path.join("logs", "ui.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(["streamlit", "run", UI_FILE], stdout=log_file, stderr=log_file)
        write_pid(UI_PID_FILE, proc.pid)
        print(f"🖥️ UI started from {UI_FILE} → logs: {log_path}")

def tail_log(file):
    try:
        subprocess.run(["tail", "-f", file])
    except KeyboardInterrupt:
        print("✋ Log tailing stopped.")

def server_status():
    try:
        res = requests.get(f"{API_BASE_URL}/status", timeout=2)
        if res.ok:
            print(f"✅ API is running: {res.json().get('message')}")
        else:
            print("🛑 API not responding")
    except Exception:
        print("🛑 API not reachable")

    print("⚠️ UI status not tracked – open http://localhost:8501 manually")

def main():
    parser = argparse.ArgumentParser(prog="foai", description="fo.ai – Cloud Cost Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    server_cmd = subparsers.add_parser("server", help="Manage API/UI dev servers")
    server_cmd.add_argument("action", choices=["start", "api", "ui", "status", "stop"], help="Start/stop services")

    logs_cmd = subparsers.add_parser("logs", help="Tail logs")
    logs_cmd.add_argument("target", choices=["api", "ui"], help="Target log to follow")

    kill_cmd = subparsers.add_parser("kill", help="Force kill API and UI processes")

    memory_cmd = subparsers.add_parser("memory", help="View recent memory from Redis")
    memory_cmd.add_argument("--limit", type=int, default=5, help="Number of chat entries to show")

    parser.add_argument("--query", type=str, help="Ask a cost optimization question")
    parser.add_argument("--status", action="store_true", help="Check API health")
    parser.add_argument("--json", action="store_true", help="Show raw response data")
    parser.add_argument("--mock", action="store_true", help="Use mock data mode")
    parser.add_argument("--debug", action="store_true", help="Show environment debug info")
    parser.add_argument("--version", action="store_true", help="Print CLI version and model info")

    args = parser.parse_args()

    if args.version:
        print(f"fo.ai CLI version: {__version__}")
        print(f"LLM model: {LLM_MODEL}")
        return

    if args.debug:
        print("🛠️ Debug Info:")
        print(f"API_BASE_URL = {API_BASE_URL}")
        print(f"UI_FILE = {UI_FILE}")
        print(f"LLM_MODEL = {LLM_MODEL}")
        print(f"USERNAME = {USERNAME}")
        print(f"Mock Mode = {args.mock}")

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
            stop_process(API_PID_FILE, "API")
            stop_process(UI_PID_FILE, "UI")
        return

    if args.command == "kill":
        print("💣 Force killing all processes (API & UI)...")
        kill_process(API_PID_FILE, "API")
        kill_process(UI_PID_FILE, "UI")
        return

    if args.command == "logs":
        log_file = f"logs/{args.target}.log"
        if os.path.exists(log_file):
            print(f"📄 Tailing {log_file}")
            tail_log(log_file)
        else:
            print(f"⚠️ Log file not found: {log_file}")
        return

    if args.command == "memory":
        try:
            from memory.redis_memory import get_list
            key = f"foai:chat:{USERNAME}"
            entries = get_list(key, limit=args.limit)
            print(f"🧠 Memory for user '{USERNAME}':\n")
            for i, item in enumerate(entries[::-1], 1):
                try:
                    data = json.loads(item)
                    print(f"{i}. Q: {data['query']}")
                    print(f"   A: {data['response']}\n")
                except:
                    print(f"{i}. {item} (unparsed)")
        except Exception as e:
            print(f"❌ Error reading memory: {e}")
        return

    if args.status:
        server_status()
        return

    if not args.query:
        parser.print_help()
        return

    print(f"🧠 Query: {args.query}")
    try:
        res = requests.post(f"{API_BASE_URL}/analyze", json={"query": args.query})
        res.raise_for_status()
        result = res.json()

        print("\n=== Summary ===\n")
        print(result.get("response", "(No summary provided)"))

        if args.json:
            from pprint import pprint
            print("\n=== Raw JSON ===\n")
            pprint(result.get("raw", []))
    except requests.exceptions.ConnectionError:
        print("❌ API server not reachable at", API_BASE_URL)
    except requests.exceptions.HTTPError as err:
        print(f"❌ HTTP {err.response.status_code}: {err.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
