# fo.ai/app/nodes/generate_recommendations.py
from app.state import CostState

def generate_recommendations(state: CostState) -> CostState:
    query_type = state.get("query_type", "general")
    recommendations = []

    if query_type == "ec2":
        for instance in state.get("ec2_data", []):
            utilization = instance.get("CPUUtilization", 100)
            if utilization < 10:
                recommendations.append({
                    "instance_id": instance["InstanceId"],
                    "current_type": instance["InstanceType"],
                    "suggestion": "Consider downsizing or stopping this instance.",
                    "cpu_utilization": utilization,
                })

    elif query_type in ["region", "service"]:
        for service, cost in state.get("cost_data", {}).items():
            if cost > 100:
                recommendations.append({
                    "service": service,
                    "cost": cost,
                    "suggestion": "Review high-spend services for optimization opportunities."
                })

    elif query_type == "general":
        for name, item in state.get("cost_data", {}).items():
            recommendations.append({
                "check_name": name,
                "issue_count": item["count"],
                "potential_savings": item["estimated_monthly_savings"],
                "suggestion": item["recommendation"]
            })

    state["recommendations"] = recommendations
    return state
