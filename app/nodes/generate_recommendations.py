from app.state import CostState

def generate_recommendations(state: CostState) -> CostState:
    query_type = state.get("query_type", "")
    recommendations = []

    # Handle EC2 instance analysis only
    if query_type == "ec2" and "ec2_data" in state:
        for instance in state["ec2_data"]:
            utilization = instance.get("CPUUtilization", 100.0)
            # If CPU utilization is less than 10%, recommend downsizing or stopping the instance
            # this will move to a rules logic in the future
            if utilization < 10.0:
                recommendations.append({
                    "instance_id": instance["InstanceId"],
                    "current_type": instance["InstanceType"],
                    "cpu_utilization": round(utilization, 2),
                    "suggestion": "Consider downsizing or stopping this instance."
                })

        state["recommendations"] = recommendations

    return state
