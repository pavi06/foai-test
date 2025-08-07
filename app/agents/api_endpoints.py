"""
API Endpoints for fo.ai Agents
Exposes agent functionality through REST API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from .cog_integration import CogIntegration

# Create router
router = APIRouter(prefix="/agents", tags=["AI Agents"])

# Initialize Cog integration
cog_integration = CogIntegration()

# Pydantic models for API requests/responses
class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class NaturalLanguageRequest(BaseModel):
    query: str

class AgentStatusResponse(BaseModel):
    agents: Dict[str, Any]
    available_agents: List[str]
    total_actions_executed: int

class ToolValidationRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get status of all AI agents"""
    try:
        status = cog_integration.get_agent_status()
        return AgentStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

@router.get("/tools")
async def get_available_tools():
    """Get all available tools in Cog format"""
    try:
        tools = cog_integration.get_tools_schema()
        return {
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

@router.post("/execute")
async def execute_tool(request: ToolExecutionRequest):
    """Execute a specific tool"""
    try:
        result = cog_integration.execute_tool(request.tool_name, request.arguments)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Tool execution failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@router.post("/natural-language")
async def process_natural_language(request: NaturalLanguageRequest):
    """Process natural language query and execute appropriate actions"""
    try:
        result = cog_integration.process_natural_language(request.query)
        
        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error"),
                "suggestions": result.get("result", {}).get("suggestions", [])
            }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Natural language processing failed: {str(e)}")

@router.get("/history")
async def get_action_history(agent_name: Optional[str] = None):
    """Get action history for agents"""
    try:
        history = cog_integration.get_action_history(agent_name)
        return {
            "history": history,
            "agent_filter": agent_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get action history: {str(e)}")

@router.post("/validate")
async def validate_tool_call(request: ToolValidationRequest):
    """Validate a tool call before execution"""
    try:
        validation = cog_integration.validate_tool_call(request.tool_name, request.arguments)
        return validation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.get("/help/{tool_name}")
async def get_tool_help(tool_name: str):
    """Get help text for a specific tool"""
    try:
        help_text = cog_integration.get_tool_help(tool_name)
        return {
            "tool_name": tool_name,
            "help": help_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tool help: {str(e)}")

@router.get("/suggestions")
async def get_suggested_queries():
    """Get suggested natural language queries"""
    try:
        suggestions = cog_integration.get_suggested_queries()
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

# EC2-specific endpoints for convenience
@router.post("/ec2/stop")
async def stop_ec2_instance(instance_id: str, force: bool = False):
    """Stop an EC2 instance"""
    try:
        result = cog_integration.execute_tool("ec2_stop_instance", {
            "instance_id": instance_id,
            "force": force
        })
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to stop instance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop instance: {str(e)}")

@router.post("/ec2/start")
async def start_ec2_instance(instance_id: str):
    """Start an EC2 instance"""
    try:
        result = cog_integration.execute_tool("ec2_start_instance", {
            "instance_id": instance_id
        })
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to start instance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start instance: {str(e)}")

@router.post("/ec2/schedule-shutdown")
async def schedule_ec2_shutdown(instance_id: str, time_period: str, schedule_name: Optional[str] = None):
    """Schedule EC2 instance shutdown"""
    try:
        arguments = {
            "instance_id": instance_id,
            "time_period": time_period
        }
        if schedule_name:
            arguments["schedule_name"] = schedule_name
        
        result = cog_integration.execute_tool("ec2_schedule_shutdown", arguments)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to schedule shutdown"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule shutdown: {str(e)}")

@router.post("/ec2/schedule-startup")
async def schedule_ec2_startup(instance_id: str, time_period: str, schedule_name: Optional[str] = None):
    """Schedule EC2 instance startup"""
    try:
        arguments = {
            "instance_id": instance_id,
            "time_period": time_period
        }
        if schedule_name:
            arguments["schedule_name"] = schedule_name
        
        result = cog_integration.execute_tool("ec2_schedule_startup", arguments)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to schedule startup"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule startup: {str(e)}")

@router.get("/ec2/status/{instance_id}")
async def get_ec2_instance_status(instance_id: str):
    """Get EC2 instance status"""
    try:
        result = cog_integration.execute_tool("ec2_get_instance_status", {
            "instance_id": instance_id
        })
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to get instance status"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get instance status: {str(e)}")

@router.get("/ec2/list")
async def list_ec2_instances(state: Optional[str] = None, instance_type: Optional[str] = None):
    """List EC2 instances"""
    try:
        arguments = {}
        if state:
            arguments["state"] = state
        if instance_type:
            arguments["instance_type"] = instance_type
        
        result = cog_integration.execute_tool("ec2_list_instances", arguments)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to list instances"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list instances: {str(e)}")

@router.delete("/ec2/schedule/{instance_id}")
async def delete_ec2_schedule(instance_id: str, schedule_type: str):
    """Delete EC2 instance schedule"""
    try:
        result = cog_integration.execute_tool("ec2_delete_schedule", {
            "instance_id": instance_id,
            "schedule_type": schedule_type
        })
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to delete schedule"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

@router.get("/ec2/schedules")
async def list_ec2_schedules(instance_id: Optional[str] = None):
    """List EC2 instance schedules"""
    try:
        arguments = {}
        if instance_id:
            arguments["instance_id"] = instance_id
        
        result = cog_integration.execute_tool("ec2_list_schedules", arguments)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("result", {}).get("error", "Failed to list schedules"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")
