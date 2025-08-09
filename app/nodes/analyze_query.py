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
    """Analyze the user query to determine the type of analysis needed"""
    query = state.get("query", "")
    
    try:
        # Use the agentic service detector
        detection_result = service_detector.detect_service_type(query)
        
        # Extract service type and confidence
        service_type = detection_result.get("service_type", "general")
        confidence = detection_result.get("confidence", 0.0)
        reasoning = detection_result.get("reasoning", "")
        
        # Map service types to query types
        service_type_mapping = {
            "ec2": "ec2",
            "s3": "s3", 
            "mixed": "general",
            "general": "general"
        }
        
        query_type = service_type_mapping.get(service_type, "general")
        
        # Update state with analysis results
        state.update({
            "query_type": query_type,
            "service_type": service_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "detection_result": detection_result
        })
        
        return state
        
    except Exception as e:
        # Fallback to general analysis on error
        state.update({
            "query_type": "general",
            "service_type": "general", 
            "confidence": 0.0,
            "reasoning": f"Error in query analysis: {str(e)}",
            "detection_result": {}
        })
        return state