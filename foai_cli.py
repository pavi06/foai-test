import argparse
import os
import signal
import subprocess
import requests
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
# these are cli specific imports
from cli.cli_chat import start_chat
from cli.cli_prompts import explain_prefs
# Load environment variables
load_dotenv()
# Constants
BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
PID_DIR = Path(".foai")
LOG_DIR = Path("logs")
API_PID_FILE = PID_DIR / "api.pid"
UI_PID_FILE = PID_DIR / "ui.pid"
API_LOG = LOG_DIR / "api.log"
UI_LOG = LOG_DIR / "ui.log"
VERSION = "0.1.6"
# Server Control
def start_server(target):
    PID_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    if target in ("api", "all"):
        with API_LOG.open("w") as api_log:
            api_proc = subprocess.Popen(["uvicorn", "api:app", "--reload"], stdout=api_log, stderr=api_log)
            API_PID_FILE.write_text(str(api_proc.pid))
            print(f"[fo.ai] API started (PID: {api_proc.pid})")
    if target in ("ui", "all"):
        with UI_LOG.open("w") as ui_log:
            ui_proc = subprocess.Popen(["streamlit", "run", "foai_ui.py"], stdout=ui_log, stderr=ui_log)
            UI_PID_FILE.write_text(str(ui_proc.pid))
            print(f"[fo.ai] UI started (PID: {ui_proc.pid})")

def stop_server(target):
    if target in ("api", "all") and API_PID_FILE.exists():
        try:
            os.kill(int(API_PID_FILE.read_text()), signal.SIGTERM)
            print("[fo.ai] API process stopped.")
        except ProcessLookupError:
            print("[fo.ai] API process not found.")
        API_PID_FILE.unlink(missing_ok=True)
    if target in ("ui", "all") and UI_PID_FILE.exists():
        try:
            os.kill(int(UI_PID_FILE.read_text()), signal.SIGTERM)
            print("[fo.ai] UI process stopped.")
        except ProcessLookupError:
            print("[fo.ai] UI process not found.")
        UI_PID_FILE.unlink(missing_ok=True)

def force_kill_all():
    print("[fo.ai] Force killing all known processes...")
    for pid_file in [API_PID_FILE, UI_PID_FILE]:
        if pid_file.exists():
            try:
                os.kill(int(pid_file.read_text()), signal.SIGKILL)
                print(f"[fo.ai] Process {pid_file} force-killed.")
            except Exception as e:
                print(f"[fo.ai] Error: {e}")
            pid_file.unlink()
    subprocess.run("pkill -f 'uvicorn'", shell=True)
    subprocess.run("pkill -f 'streamlit'", shell=True)

def tail_logs(target):
    log_file = API_LOG if target == "api" else UI_LOG
    if log_file.exists():
        subprocess.run(["tail", "-f", str(log_file)])
    else:
        print(f"[fo.ai] No logs found for {target}")

def check_status():
    try:
        res = requests.get(f"{BASE_URL}/status", timeout=2)
        print(f"[fo.ai] API status: {res.json().get('message')}")
    except Exception as e:
        print(f"[fo.ai] API not reachable: {e}")

def run_query(query, stream=False):
    payload = {
        "query": query,
        "user_id": os.getenv("USERNAME", "cli"),
        "region": os.getenv("AWS_REGION", "us-east-1")
    }

    if stream:
        try:
            with requests.post(f"{BASE_URL}/analyze/stream", json=payload, stream=True) as r:
                r.raise_for_status()
                print("[fo.ai] Streaming response:")
                for chunk in r.iter_content(chunk_size=1, decode_unicode=True):
                    print(chunk, end="", flush=True)
        except Exception as e:
            print(f"[fo.ai] Stream error: {e}")
    else:
        try:
            r = requests.post(f"{BASE_URL}/analyze", json=payload)
            r.raise_for_status()
            print(r.json()["response"])
        except Exception as e:
            print(f"[fo.ai] API error: {e}")

# === MAIN CLI ===
parser = argparse.ArgumentParser(
    prog="foai_cli.py",
    description="""fo.ai – Cloud Cost Intelligence CLI

Use this CLI to:
- Analyze EC2 cost and performance
- Set and view user preferences stored in Redis
- Manage backend servers (FastAPI & Streamlit)
- View live logs and system status

Examples:
  python foai_cli.py ask "How can I save on EC2?"
  python foai_cli.py prefs view --user vedanta
  python foai_cli.py prefs set --user vedanta --cpu-threshold 5 --uptime 100
  python foai_cli.py server start all
  python foai_cli.py logs api
  
Alias:
    Set alias for this script in your shell:
    # alias foai='python /path/to/foai_cli.py'
""",
    formatter_class=argparse.RawDescriptionHelpFormatter
)

parser.add_argument("--version", action="version", version=f"fo.ai CLI v{VERSION}")
subparsers = parser.add_subparsers(dest="command")


# chat
subparsers.add_parser("chat", help="Start interactive streaming chat session")


# Server management
server_cmd = subparsers.add_parser("server", help="Start/stop/kill servers")
server_cmd.add_argument("action", choices=["start", "stop", "forcekill"])
server_cmd.add_argument("target", choices=["api", "ui", "all"])

# Logs
logs_cmd = subparsers.add_parser("logs", help="Tail logs for API or UI")
logs_cmd.add_argument("target", choices=["api", "ui"])

# Status check
status_cmd = subparsers.add_parser("status", help="Check API status")

# Ask query
ask_cmd = subparsers.add_parser("ask", help="Ask fo.ai a question")
ask_cmd.add_argument("query", help="Natural language query")
ask_cmd.add_argument("--stream", action="store_true", help="Stream response")

# Preferences
prefs_cmd = subparsers.add_parser("prefs", help="Manage user preferences")
prefs_sub = prefs_cmd.add_subparsers(dest="prefs_command")

prefs_view = prefs_sub.add_parser("view", help="View preferences")
prefs_view.add_argument("--user", required=True)

prefs_set = prefs_sub.add_parser("set", help="Set preferences")
prefs_set.add_argument("--user", required=True)
prefs_set.add_argument("--cpu-threshold", type=float)
prefs_set.add_argument("--uptime", type=int)
prefs_set.add_argument("--min-savings", type=float)
prefs_set.add_argument("--exclude-tags", nargs="*")
prefs_set.add_argument("--idle-cpu", type=float)

# Explain Preferences
explain_cmd = subparsers.add_parser("explain-prefs", help="Use LLM to explain current user preferences")
explain_cmd.add_argument("--user", default="default_user", help="User ID (default: 'default_user')")
explain_cmd.add_argument("--persona", default="engineer", help="Persona style (e.g., engineer, finance, executive)")

# === Execution ===
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
    
# Add this in your CLI main section
elif args.command == "chat":
    start_chat()

elif args.command == "prefs":
    if args.prefs_command == "view":
        try:
            r = requests.get(f"{BASE_URL}/preferences/load", params={"user_id": args.user})
            r.raise_for_status()
            print(json.dumps(r.json(), indent=2))
        except Exception as e:
            print(f"[fo.ai] Error loading preferences: {e}")
    elif args.prefs_command == "set":
        prefs = {}
        if args.cpu_threshold is not None:
            prefs["cpu_threshold"] = args.cpu_threshold
        if args.uptime is not None:
            prefs["min_uptime_hours"] = args.uptime
        if args.min_savings is not None:
            prefs["min_savings_usd"] = args.min_savings
        if args.exclude_tags is not None:
            prefs["excluded_tags"] = args.exclude_tags
        if args.idle_cpu is not None:
            prefs["idle_7day_cpu_threshold"] = args.idle_cpu
        payload = {
            "user_id": args.user,
            "preferences": prefs
        }
        try:
            r = requests.post(f"{BASE_URL}/preferences/save", json=payload)
            r.raise_for_status()
            print("[fo.ai] Preferences saved successfully.")
        except Exception as e:
            print(f"[fo.ai] Error saving preferences: {e}")
elif args.command == "explain-prefs":
    explain_prefs(user_id=args.user, persona=args.persona)
else:
    parser.print_help()
