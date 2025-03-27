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
        # 👉 Real AWS API fetch logic (service-specific)
        if query_type == "ec2":
            from data.aws.ec2 import fetch_ec2_instances
            state["ec2_data"] = fetch_ec2_instances()

        elif query_type == "service":
            from data.aws.cost_explorer import fetch_cost_by_service
            state["cost_data"] = fetch_cost_by_service()

        elif query_type == "general":
            if ENABLE_TRUSTED_ADVISOR:
                from data.aws.trusted_advisor import fetch_trusted_advisor
                state["cost_data"] = fetch_trusted_advisor()
            else:
                if debug:
                    print("[DEBUG] Trusted Advisor disabled — falling back to alternative logic")
                # TODO: Add fallback logic here in future
                state["cost_data"] = {}

        else:
            state["response"] = f"No AWS integration implemented for query_type: {query_type}"

    return state
