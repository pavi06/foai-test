# fo.ai/app/nodes/fetch_mock_data.py
import json
import os
from dotenv import load_dotenv
from app.state import CostState

load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


DATA_MAP = {
    "ec2": "data/ec2_instances.json",
    "service": "data/cost_explorer.json",
    "region": "data/cost_explorer.json",
    "general": "data/trusted_advisor.json",
}

def fetch_mock_data(state: CostState) -> CostState:
    # print("[DEBUG] fetch_mock_data state:", state)
    use_mock = state.get("use_mock",True)
    query_type = state.get("query_type", "general")

    if DEBUG:
        print(f"[DEBUG] fetch_mock_data → use_mock={use_mock}, query_type={query_type}")

    if not use_mock:
        state["response"] = "Live AWS API integration not implemented yet."
        return state

    file_path = DATA_MAP.get(query_type, "data/trusted_advisor.json")

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        if query_type == "ec2":
            state["ec2_data"] = data
        else:
            state["cost_data"] = data

    except Exception as e:
        state["response"] = f"Error loading mock data: {str(e)}"

    return state