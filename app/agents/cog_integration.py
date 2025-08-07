"""
Cog Integration for fo.ai Agents
Exposes agent tools as Cog tools for natural language processing
"""

from typing import Dict, Any, List
import json
from .agent_manager import AgentManager

class CogIntegration:
    """
    Integrates fo.ai agents with Cog for natural language tool execution
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.agent_manager = AgentManager(region=region)
        self.logger = self.agent_manager.logger
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get the schema for all available tools in Cog format
        """
        tools = []
        
        for agent_name in self.agent_manager.get_available_agents():
            agent = self.agent_manager.get_agent(agent_name)
            if not agent:
                continue
            
            actions = agent.get_available_actions()
            for action in actions:
                tool = self._convert_action_to_cog_tool(agent_name, action)
                tools.append(tool)
        
        return tools
    
    def _convert_action_to_cog_tool(self, agent_name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an agent action to Cog tool format
        """
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param_config in action['parameters'].items():
            properties[param_name] = {
                "type": param_config['type'],
                "description": param_config['description']
            }
            
            if param_config.get('required', False):
                required.append(param_name)
        
        return {
            "type": "function",
            "function": {
                "name": f"{agent_name}_{action['name']}",
                "description": f"{action['description']} - {action.get('help', '')}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Cog tool by routing to the appropriate agent
        """
        try:
            # Parse tool name to extract agent and action
            parts = tool_name.split('_', 1)
            if len(parts) != 2:
                return {
                    "success": False,
                    "error": f"Invalid tool name format: {tool_name}. Expected format: agent_action"
                }
            
            agent_name, action_name = parts
            
            # Execute the action
            result = self.agent_manager.execute_action(agent_name, action_name, arguments)
            
            return {
                "success": result.get("success", False),
                "result": result,
                "tool_name": tool_name,
                "agent": agent_name,
                "action": action_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool_name": tool_name
            }
    
    def process_natural_language(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language query and execute appropriate actions
        """
        try:
            result = self.agent_manager.execute_natural_language_request(user_query)
            print(f"[COG INTEGRATION] Result: {result}")

            return {
                "success": result.get("success", False),
                "result": result,
                "query": user_query,
                "parsed_request": result.get("parsed_request", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Natural language processing failed: {str(e)}",
                "query": user_query
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        """
        return {
            "agents": self.agent_manager.get_all_agent_info(),
            "available_agents": self.agent_manager.get_available_agents(),
            "total_actions_executed": sum(
                len(agent.get_action_history()) 
                for agent in self.agent_manager.agents.values()
            )
        }
    
    def get_action_history(self, agent_name: str = None) -> Dict[str, Any]:
        """
        Get action history for agents
        """
        if agent_name:
            return {
                agent_name: self.agent_manager.get_agent_action_history(agent_name)
            }
        else:
            return self.agent_manager.get_all_action_history()
    
    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool call before execution
        """
        try:
            parts = tool_name.split('_', 1)
            if len(parts) != 2:
                return {
                    "valid": False,
                    "error": f"Invalid tool name format: {tool_name}"
                }
            
            agent_name, action_name = parts
            
            is_valid = self.agent_manager.validate_action(agent_name, action_name, arguments)
            
            return {
                "valid": is_valid,
                "agent": agent_name,
                "action": action_name,
                "arguments": arguments
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }
    
    def get_tool_help(self, tool_name: str) -> str:
        """
        Get help text for a specific tool
        """
        try:
            parts = tool_name.split('_', 1)
            if len(parts) != 2:
                return f"Invalid tool name: {tool_name}"
            
            agent_name, action_name = parts
            help_text = self.agent_manager.get_action_help(agent_name, action_name)
            
            return help_text or f"No help available for {tool_name}"
            
        except Exception as e:
            return f"Error getting help: {str(e)}"
    
    def get_suggested_queries(self) -> List[str]:
        """
        Get suggested natural language queries for users
        """
        return [
            "Stop instance i-1234567890abcdef0",
            "Start instance i-1234567890abcdef0",
            "Schedule shutdown for i-1234567890abcdef0 during non-business hours",
            "Schedule startup for i-1234567890abcdef0 at 8 AM",
            "Check status of instance i-1234567890abcdef0",
            "List all running instances",
            "List all scheduled actions",
            "Delete shutdown schedule for i-1234567890abcdef0"
        ]
