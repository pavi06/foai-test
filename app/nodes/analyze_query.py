# fo.ai/app/nodes/analyze_query.py
from app.state import CostState
from app.agents.service_detector import AgenticServiceDetector
import os
from dotenv import load_dotenv

load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Initialize the agentic service detector
service_detector = AgenticServiceDetector()

def analyze_query(state: CostState) -> CostState:
    """Use agentic approach to analyze and classify the query"""
    query = state["query"]
    
    if DEBUG:
        print(f"[DEBUG] analyze_query → analyzing query: '{query}'")
    
    try:
        # Use agentic service detection
        detection_result = service_detector.detect_service_type(query)
        
        # Map service types to query types
        service_type = detection_result["service_type"]
        confidence = detection_result.get("confidence", 0.5)
        reasoning = detection_result.get("reasoning", "No reasoning provided")
        
        # Map service types to query types (for backward compatibility)
        if service_type == "ec2":
            query_type = "ec2"
        elif service_type == "s3":
            query_type = "s3"
        elif service_type == "agent_ec2":
            query_type = "ec2"  # Agent actions are still EC2-related
        elif service_type == "mixed":
            query_type = "general"  # Mixed queries go to general
        else:
            query_type = "general"
        
        state["query_type"] = query_type
        
        # Store additional detection information
        state["detection_result"] = detection_result
        state["detection_confidence"] = confidence
        state["detection_reasoning"] = reasoning
        
        if DEBUG:
            print(f"[DEBUG] analyze_query → query='{query}'")
            print(f"[DEBUG] analyze_query → detected service: {service_type}")
            print(f"[DEBUG] analyze_query → mapped to query_type: {query_type}")
            print(f"[DEBUG] analyze_query → confidence: {confidence:.2f}")
            print(f"[DEBUG] analyze_query → reasoning: {reasoning}")
        
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] analyze_query → error: {e}")
        
        # Fallback to general if detection fails
        state["query_type"] = "general"
        state["detection_result"] = {"service_type": "general", "method": "fallback"}
        state["detection_confidence"] = 0.0
        state["detection_reasoning"] = f"Detection failed: {str(e)}"

    return state