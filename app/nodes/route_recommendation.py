# fo.ai/app/nodes/route_recommendation.py
from app.state import CostState

def route_recommendation(state: CostState) -> str:
    """
    Routes to the appropriate recommendation generator based on query type.
    Returns the next node name in the graph.
    """
    query_type = state.get("query_type", "general")
    
    if query_type == "s3":
        return "generate_s3_recommendations"
    elif query_type == "ec2":
        return "generate_recommendations"
    else:
        # Default to EC2 for general queries
        return "generate_recommendations" 