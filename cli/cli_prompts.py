# cli_prompts.py

import requests
import os
from dotenv import load_dotenv
from rich import print

load_dotenv()

API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
DEFAULT_USER = os.getenv("USERNAME", "default_user")

def explain_prefs(user_id: str = DEFAULT_USER):
    """
    CLI wrapper to explain preferences via LLM.
    """
    try:
        response = requests.get(f"{API_URL}/preferences/explain", params={"user_id": user_id})
        response.raise_for_status()
        data = response.json()

        print(f"[bold cyan]User ID:[/bold cyan] {data['user_id']}\n")

        print(f"[bold yellow]Preferences:[/bold yellow]")
        for k, v in data["preferences"].items():
            print(f"  • [green]{k}[/green]: {v}")

        print(f"\n[bold magenta]LLM Explanation:[/bold magenta]\n")
        print(data["explanation"]["content"])
    except Exception as e:
        print(f"[bold red]Error:[/bold red] {e}")
