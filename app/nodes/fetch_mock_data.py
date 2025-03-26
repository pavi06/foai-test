# fo.ai/app/nodes/fetch_mock_data.py
import json
from app.state import CostState

# Map query types to filenames
DATA_MAP = {
    "ec2": "data/ec2_instances.json",
    "service": "data/cost_explorer.json",
    "region": "data/cost_explorer.json",
    "general": "data/trusted_advisor.json",
}

def fetch_mock_data(state: CostState) -> CostState:
    query_type = state.get("query_type", "general")
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
