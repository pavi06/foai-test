#!/usr/bin/env python3
import argparse
import os
import subprocess
import signal
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
UI_FILE = os.getenv("FOAI_UI_FILE", "foai_ui.py")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
API_PID_FILE = ".api.pid"
UI_PID_FILE = ".ui.pid"

from version import __version__

def write_pid(file, pid):
    with open(file, "w") as f:
        f.write(str(pid))

def read_pid(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return int(f.read())
    return None

def stop_process(pid_file, service_name):
    pid = read_pid(pid_file)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            print("🛑 {} stopped (PID {})".format(service_name, pid))
            os.remove(pid_file)
        except ProcessLookupError:
            print("⚠️ {} not running (stale PID {})".format(service_name, pid))
    else:
        print("⚠️ No PID file found for {}".format(service_name))

def start_api():
    log_path = os.path.join("logs", "api.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(["uvicorn", "api:app", "--reload"], stdout=log_file, stderr=log_file)
        write_pid(API_PID_FILE, proc.pid)
        print("🚀 API started at {} → logs: {}".format(API_BASE_URL, log_path))

def start_ui():
    log_path = os.path.join("logs", "ui.log")
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w") as log_file:
        proc = subprocess.Popen(["streamlit", "run", UI_FILE], stdout=log_file, stderr=log_file)
        write_pid(UI_PID_FILE, proc.pid)
        print("🖥️ UI started from {} → logs: {}".format(UI_FILE, log_path))

def tail_log(file):
    try:
        subprocess.run(["tail", "-f", file])
    except KeyboardInterrupt:
        print("✋ Log tailing stopped.")

def server_status():
    try:
        res = requests.get(f"{API_BASE_URL}/status", timeout=2)
        if res.ok:
            print("✅ API is running: {}".format(res.json().get('message')))
        else:
            print("🛑 API not responding")
    except Exception:
        print("🛑 API not reachable")

    print("⚠️ UI status not tracked – open http://localhost:8501 manually")

def main():
    parser = argparse.ArgumentParser(prog="foai", description="fo.ai – Cloud Cost Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    server_cmd = subparsers.add_parser("server", help="Manage API/UI dev servers")
    server_cmd.add_argument("action", choices=["start", "api", "ui", "status", "stop"], help="Action to perform")

    logs_cmd = subparsers.add_parser("logs", help="Tail logs")
    logs_cmd.add_argument("target", choices=["api", "ui"], help="Log target")

    parser.add_argument("--query", type=str, help="Ask a cost optimization question")
    parser.add_argument("--status", action="store_true", help="Check API health")
    parser.add_argument("--json", action="store_true", help="Show raw response data")
    parser.add_argument("--mock", action="store_true", help="Use mock data mode")
    parser.add_argument("--debug", action="store_true", help="Show environment debug info")
    parser.add_argument("--version", action="store_true", help="Print CLI version and model info")

    args = parser.parse_args()

    if args.version:
        print("fo.ai CLI version: {}".format(__version__))
        print("LLM model: {}".format(LLM_MODEL))
        return

    if args.debug:
        print("🛠️ Debug Info:")
        print("API_BASE_URL = {}".format(API_BASE_URL))
        print("UI_FILE = {}".format(UI_FILE))
        print("LLM_MODEL = {}".format(LLM_MODEL))
        print("Mock Mode = {}".format(args.mock))

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

    if args.command == "logs":
        log_file = "logs/{}.log".format(args.target)
        if os.path.exists(log_file):
            print("📄 Tailing {}".format(log_file))
            tail_log(log_file)
        else:
            print("⚠️ Log file not found: {}".format(log_file))
        return

    if args.status:
        server_status()
        return

    if not args.query:
        parser.print_help()
        return

    print("🧠 Query: {}".format(args.query))
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
        print("❌ HTTP {}: {}".format(err.response.status_code, err.response.text))
    except Exception as e:
        print("❌ Unexpected error: {}".format(e))

if __name__ == "__main__":
    main()
