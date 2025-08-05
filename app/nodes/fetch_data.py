# this is a router that fetches data from the various cloud cost APIs or can be toggled to use mock data.
import json
from app.state import CostState
from data.aws.settings import ENABLE_TRUSTED_ADVISOR

def fetch_data(state: CostState) -> CostState:
    query_type = state.get("query_type", "general")
    use_mock = state.get("use_mock", True)
    debug = state.get("debug", False)

    if debug:
        print(f"[DEBUG] fetch_data → use_mock={use_mock}, query_type={query_type}")

    if use_mock:
        if query_type == "ec2":
            with open("data/ec2_instances.json") as f:
                state["ec2_data"] = json.load(f)

        elif query_type == "service":
            with open("data/cost_explorer.json") as f:
                state["cost_data"] = json.load(f)

        elif query_type == "general":
            with open("data/trusted_advisor.json") as f:
                state["cost_data"] = json.load(f)
    else:
        # Real AWS API fetch logic (service-specific)
        if query_type == "ec2":
            from data.aws.ec2 import fetch_ec2_instances
            state["ec2_data"] = fetch_ec2_instances()
        elif query_type == "s3":
            from data.aws.s3 import fetch_s3_data
            state["s3_data"] = fetch_s3_data()
        else:
            state["response"] = f"No AWS integration implemented for query_type: {query_type}"
    return state
