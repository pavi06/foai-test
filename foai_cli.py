#!/usr/bin/env python3
import requests
import argparse
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")  # ✅ base only

def main():
    parser = argparse.ArgumentParser(
        prog="foai",
        description="fo.ai – Cloud Cost Intelligence CLI Tool",
        epilog="Example: foai --query 'Where can I save on EC2?' --json"
    )
    parser.add_argument("--query", type=str, help="Optimization question (e.g. 'Where can I save on EC2?')")
    parser.add_argument("--status", action="store_true", help="Check API health status")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--mock", action="store_true", help="Use mock mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.status:
        try:
            res = requests.get(f"{API_BASE_URL}/status")
            res.raise_for_status()
            data = res.json()
            print(f"✅ {data['message']}")
        except Exception as e:
            print(f"❌ API not reachable: {e}")
        return

    if not args.query:
        parser.error("You must specify --query or --status")

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
