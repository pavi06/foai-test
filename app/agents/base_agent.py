"""
Base Agent Class for fo.ai
Provides common functionality for all AI agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

class BaseAgent(ABC):
    """
    Base class for all AI agents in fo.ai
    Provides common functionality and interface
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"foai.agent.{name}")
        self.actions_history = []
        
    @abstractmethod
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Return list of available actions for this agent"""
        pass
    
    @abstractmethod
    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific action with given parameters"""
        pass
    
    @abstractmethod
    def validate_action(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate if an action can be executed with given parameters"""
        pass
    
    def log_action(self, action_name: str, parameters: Dict[str, Any], result: Dict[str, Any]):
        """Log an action execution"""
        action_log = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "action": action_name,
            "parameters": parameters,
            "result": result
        }
        self.actions_history.append(action_log)
        self.logger.info(f"Action executed: {action_name} with result: {result.get('success', False)}")
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get the history of actions executed by this agent"""
        return self.actions_history
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "name": self.name,
            "description": self.description,
            "available_actions": self.get_available_actions(),
            "total_actions_executed": len(self.actions_history)
        }
    
    def format_action_description(self, action: Dict[str, Any]) -> str:
        """Format an action description for display"""
        return f"{action['name']}: {action['description']}"
    
    def get_action_help(self, action_name: str) -> Optional[str]:
        """Get help text for a specific action"""
        actions = self.get_available_actions()
        for action in actions:
            if action['name'] == action_name:
                return action.get('help', 'No help available')
        return None
