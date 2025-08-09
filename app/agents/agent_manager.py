"""
Agent Manager for fo.ai
Coordinates multiple AI agents and provides a unified interface
"""

from typing import Dict, Any, List, Optional
import logging
from .base_agent import BaseAgent
from .ec2_agent import EC2Agent
import re

class AgentManager:
    """
    Manages multiple AI agents and provides a unified interface
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.logger = logging.getLogger("foai.agent_manager")
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agents"""
        try:
            self.agents['ec2'] = EC2Agent(region=self.region)
            self.logger.info("EC2 Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return list(self.agents.keys())
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a specific agent by name"""
        return self.agents.get(agent_name)
    
    def execute_action(self, agent_name: str, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action on a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found. Available agents: {self.get_available_agents()}"
            }
        
        return agent.execute_action(action_name, parameters)
    
    def get_available_actions(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get available actions for a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        return agent.get_available_actions()
    
    def validate_action(self, agent_name: str, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate if an action can be executed"""
        agent = self.get_agent(agent_name)
        if not agent:
            return False
        return agent.validate_action(action_name, parameters)
    
    def get_all_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all agents"""
        agent_info = {}
        for name, agent in self.agents.items():
            agent_info[name] = agent.get_agent_info()
        return agent_info
    
    def get_agent_action_history(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get action history for a specific agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return []
        return agent.get_action_history()
    
    def get_all_action_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get action history for all agents"""
        history = {}
        for name, agent in self.agents.items():
            history[name] = agent.get_action_history()
        return history
    
    def get_action_help(self, agent_name: str, action_name: str) -> Optional[str]:
        """Get help text for a specific action of an agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return None
        return agent.get_action_help(action_name)
    
    def parse_natural_language_request(self, user_query: str) -> Dict[str, Any]:
        """
        Parse natural language request and determine which agent and action to use
        """
        query_lower = user_query.lower()
        
        # EC2 Agent detection
        ec2_keywords = ["ec2", "instance", "server", "machine", "virtual", "vm", "compute"]
        ec2_score = sum(1 for keyword in ec2_keywords if keyword in query_lower)
        
        # Instance ID detection
        instance_pattern = r'\bi-[a-f0-9]{8,17}\b'
        instance_matches = re.findall(instance_pattern, query_lower)
        if instance_matches:
            ec2_score = max(ec2_score, 1)
        
        # Action mapping
        action_mapping = {
            "stop_instance": ["stop", "shutdown", "turn off", "power off", "halt"],
            "start_instance": ["start", "turn on", "power on", "boot", "launch"],
            "schedule_shutdown": ["schedule shutdown", "schedule stop", "auto shutdown", "shutdown at"],
            "schedule_startup": ["schedule start", "schedule boot", "auto start", "start at"],
            "get_instance_status": ["status", "state", "check", "info", "details"],
            "list_instances": ["list", "show", "all instances", "running instances"],
            "delete_schedule": ["delete schedule", "remove schedule", "cancel schedule"],
            "list_schedules": ["list schedules", "show schedules", "scheduled"]
        }
        
        # Find best matching action
        best_action = None
        best_score = 0
        
        for action, keywords in action_mapping.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > best_score:
                best_score = score
                best_action = action
        
        # Extract parameters
        instance_id = instance_matches[0] if instance_matches else None
        time_period = None
        
        if "schedule" in query_lower:
            time_keywords = ["at", "during", "from", "to", "non-business", "business hours", "weekend"]
            for keyword in time_keywords:
                if keyword in query_lower:
                    parts = query_lower.split(keyword, 1)
                    if len(parts) > 1:
                        time_period = parts[1].strip()
                        break
        
        # Build parameters
        parameters = {}
        if instance_id:
            parameters['instance_id'] = instance_id
        if time_period:
            parameters['time_period'] = time_period
        
        # Calculate confidence
        confidence = 0.0
        if best_action and ec2_score > 0:
            confidence = 0.6
            if best_action in ["stop_instance", "start_instance", "get_instance_status", "list_instances"]:
                confidence += 0.2
            if instance_id:
                confidence += 0.2
            if best_action.startswith("schedule"):
                confidence += 0.1
            confidence = min(0.95, confidence)
        elif best_action and instance_id:
            confidence = 0.7
        
        return {
            "agent": "ec2" if ec2_score > 0 else None,
            "action": best_action,
            "parameters": parameters,
            "confidence": confidence,
            "raw_query": user_query
        }
    
    def execute_natural_language_request(self, user_query: str) -> Dict[str, Any]:
        """
        Execute a natural language request by parsing and routing to appropriate agent
        """
        parsed = self.parse_natural_language_request(user_query)
        
        if not parsed['agent'] or not parsed['action']:
            return {
                "success": False,
                "error": "Could not understand the request. Please be more specific about what you want to do with your EC2 instances.",
                "suggestions": [
                    "Stop instance i-1234567890abcdef0",
                    "Start instance i-1234567890abcdef0", 
                    "Schedule shutdown for i-1234567890abcdef0 during non-business hours",
                    "List all running instances",
                    "Check status of instance i-1234567890abcdef0"
                ]
            }
        
        if parsed['confidence'] < 0.3:
            return {
                "success": False,
                "error": "Request is unclear. Please provide more specific details.",
                "parsed_request": parsed
            }
        
        # Execute the action
        result = self.execute_action(parsed['agent'], parsed['action'], parsed['parameters'])
        result['parsed_request'] = parsed
        
        return result
