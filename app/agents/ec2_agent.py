"""
EC2 Agent for fo.ai
Provides AI agent tools for EC2 instance management
"""

import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
import json
import re
from botocore.exceptions import ClientError, NoCredentialsError
from .base_agent import BaseAgent
from data.aws.settings import get_boto3_client

class EC2Agent(BaseAgent):
    """
    AI Agent for EC2 instance management
    Provides actions for starting, stopping, and scheduling EC2 instances
    """
    
    def __init__(self, region: str = "us-east-1"):
        super().__init__(
            name="EC2Agent",
            description="AI agent for managing EC2 instances - start, stop, schedule, and monitor"
        )
        self.region = region
        self.ec2_client = None
        self.events_client = None
        self.lambda_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self.ec2_client = get_boto3_client('ec2', self.region)
            self.events_client = get_boto3_client('events', self.region)
            self.lambda_client = get_boto3_client('lambda', self.region)
            self.logger.info(f"EC2 Agent initialized for region: {self.region}")
        except Exception as e:
            self.logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """Return list of available EC2 actions"""
        return [
            {
                "name": "stop_instance",
                "description": "Stop an EC2 instance immediately",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"},
                    "force": {"type": "boolean", "required": False, "description": "Force stop the instance", "default": False}
                },
                "help": "Stops an EC2 instance. Use force=True to force stop if the instance is stuck."
            },
            {
                "name": "start_instance",
                "description": "Start an EC2 instance",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"}
                },
                "help": "Starts an EC2 instance that is currently stopped."
            },
            {
                "name": "schedule_shutdown",
                "description": "Schedule an EC2 instance to shutdown at a specific time",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"},
                    "time_period": {"type": "string", "required": True, "description": "Time period (e.g., '6 PM', 'non-business hours', 'weekend')"},
                    "schedule_name": {"type": "string", "required": False, "description": "Custom name for the schedule"}
                },
                "help": "Creates a schedule to automatically shutdown an EC2 instance. Supports natural language time descriptions."
            },
            {
                "name": "schedule_startup",
                "description": "Schedule an EC2 instance to start at a specific time",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"},
                    "time_period": {"type": "string", "required": True, "description": "Time period (e.g., '8 AM', 'business hours')"},
                    "schedule_name": {"type": "string", "required": False, "description": "Custom name for the schedule"}
                },
                "help": "Creates a schedule to automatically start an EC2 instance. Supports natural language time descriptions."
            },
            {
                "name": "get_instance_status",
                "description": "Get the current status of an EC2 instance",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"}
                },
                "help": "Returns the current state and details of an EC2 instance."
            },
            {
                "name": "list_instances",
                "description": "List all EC2 instances in the region",
                "parameters": {
                    "state": {"type": "string", "required": False, "description": "Filter by state (running, stopped, etc.)"},
                    "instance_type": {"type": "string", "required": False, "description": "Filter by instance type"}
                },
                "help": "Lists EC2 instances with optional filtering by state or instance type."
            },
            {
                "name": "delete_schedule",
                "description": "Delete a scheduled action for an EC2 instance",
                "parameters": {
                    "instance_id": {"type": "string", "required": True, "description": "EC2 instance ID"},
                    "schedule_type": {"type": "string", "required": True, "description": "Type of schedule (shutdown/startup)"}
                },
                "help": "Removes a scheduled action for an EC2 instance."
            },
            {
                "name": "list_schedules",
                "description": "List all scheduled actions for EC2 instances",
                "parameters": {
                    "instance_id": {"type": "string", "required": False, "description": "Filter by specific instance ID"}
                },
                "help": "Lists all scheduled actions, optionally filtered by instance ID."
            }
        ]
    

    
    def validate_action(self, action_name: str, parameters: Dict[str, Any]) -> bool:
        """Validate if an action can be executed with given parameters"""
        actions = {action['name']: action for action in self.get_available_actions()}
        
        if action_name not in actions:
            return False
        
        action = actions[action_name]
        required_params = [param for param, config in action['parameters'].items() if config.get('required', False)]
        
        # Check required parameters
        for param in required_params:
            if param not in parameters or parameters[param] is None:
                return False
        
        # Validate instance_id format if present
        if 'instance_id' in parameters:
            if not self._validate_instance_id(parameters['instance_id']):
                return False
        
        return True
    
    def _validate_instance_id(self, instance_id: str) -> bool:
        """Validate EC2 instance ID format"""
        pattern = r'^i-[a-f0-9]{8,17}$'
        return bool(re.match(pattern, instance_id))
    
    def execute_action(self, action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific EC2 action"""
        if not self.validate_action(action_name, parameters):
            return {
                "success": False,
                "error": f"Invalid parameters for action: {action_name}",
                "action": action_name
            }
        
        try:
            if action_name == "stop_instance":
                result = self._stop_instance(parameters)
            elif action_name == "start_instance":
                result = self._start_instance(parameters)
            elif action_name == "schedule_shutdown":
                result = self._schedule_shutdown(parameters)
            elif action_name == "schedule_startup":
                result = self._schedule_startup(parameters)
            elif action_name == "get_instance_status":
                result = self._get_instance_status(parameters)
            elif action_name == "list_instances":
                result = self._list_instances(parameters)
            elif action_name == "delete_schedule":
                result = self._delete_schedule(parameters)
            elif action_name == "list_schedules":
                result = self._list_schedules(parameters)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "action": action_name
                }
            
            # Log the action
            self.log_action(action_name, parameters, result)
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Action execution failed: {str(e)}",
                "action": action_name
            }
            self.log_action(action_name, parameters, error_result)
            return error_result
    
    def _stop_instance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Stop an EC2 instance"""
        instance_id = parameters['instance_id']
        force = parameters.get('force', False)
        
        try:
            response = self.ec2_client.stop_instances(
                InstanceIds=[instance_id],
                Force=force
            )
            
            state = response['StoppingInstances'][0]['CurrentState']['Name']
            
            return {
                "success": True,
                "message": f"Successfully initiated stop for instance {instance_id}",
                "instance_id": instance_id,
                "current_state": state,
                "force": force
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS error: {e.response['Error']['Message']}",
                "instance_id": instance_id
            }
    
    def _start_instance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Start an EC2 instance"""
        instance_id = parameters['instance_id']
        
        try:
            response = self.ec2_client.start_instances(
                InstanceIds=[instance_id]
            )
            
            state = response['StartingInstances'][0]['CurrentState']['Name']
            
            return {
                "success": True,
                "message": f"Successfully initiated start for instance {instance_id}",
                "instance_id": instance_id,
                "current_state": state
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS error: {e.response['Error']['Message']}",
                "instance_id": instance_id
            }
    
    def _parse_time_period(self, time_text: str) -> Dict[str, Any]:
        """Parse natural language time descriptions"""
        time_text_lower = time_text.lower().strip()
        
        # Predefined schedules
        if "non-business" in time_text_lower:
            return {
                "type": "daily",
                "start_time": "18:00",  # 6 PM
                "end_time": "08:00",    # 8 AM
                "days": ["MON", "TUE", "WED", "THU", "FRI"],
                "description": "Non-business hours (6 PM - 8 AM weekdays)"
            }
        elif "business hours" in time_text_lower:
            return {
                "type": "daily",
                "start_time": "08:00",  # 8 AM
                "end_time": "18:00",    # 6 PM
                "days": ["MON", "TUE", "WED", "THU", "FRI"],
                "description": "Business hours (8 AM - 6 PM weekdays)"
            }
        elif "weekend" in time_text_lower:
            return {
                "type": "weekly",
                "start_time": "18:00",  # 6 PM Friday
                "end_time": "08:00",    # 8 AM Monday
                "days": ["FRI", "SAT", "SUN"],
                "description": "Weekends (Friday 6 PM - Monday 8 AM)"
            }
        elif "overnight" in time_text_lower or "night" in time_text_lower:
            return {
                "type": "daily",
                "start_time": "22:00",  # 10 PM
                "end_time": "06:00",    # 6 AM
                "days": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
                "description": "Overnight (10 PM - 6 AM daily)"
            }
        
        # Parse specific times like "6 PM" or "18:00"
        time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        match = re.search(time_pattern, time_text_lower)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            # Convert to 24-hour format
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            time_str = f"{hour:02d}:{minute:02d}"
            
            return {
                "type": "specific",
                "time": time_str,
                "description": f"At {time_str}"
            }
        
        # Default fallback
        return {
            "type": "daily",
            "start_time": "18:00",
            "end_time": "08:00",
            "days": ["MON", "TUE", "WED", "THU", "FRI"],
            "description": "Default schedule (6 PM - 8 AM weekdays)"
        }
    
    def _create_lambda_function(self, instance_id: str, action: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Lambda function for scheduled actions"""
        function_name = f"foai-{instance_id}-{action}"
        
        # Lambda function code
        lambda_code = f"""
            import boto3
            import json
            import logging

            logger = logging.getLogger()
            logger.setLevel(logging.INFO)

            def lambda_handler(event, context):
                ec2 = boto3.client('ec2', region_name='{self.region}')
                
                try:
                    response = ec2.{action}_instances(InstanceIds=['{instance_id}'])
                    logger.info(f"Successfully {{action}}ed instance {{instance_id}}")
                    return {{
                        'statusCode': 200,
                        'body': json.dumps(f'Successfully {{action}}ed {{instance_id}}')
                    }}
                except Exception as e:
                    logger.error(f"Error {{action}}ing instance: {{e}}")
                    return {{
                        'statusCode': 500,
                        'body': json.dumps(f'Error: {{str(e)}}')
                    }}
            """
        
        try:
            # Create Lambda function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=f'arn:aws:iam::{boto3.client("sts").get_caller_identity()["Account"]}:role/foai-lambda-ec2-role',
                Handler='index.lambda_handler',
                Code={'ZipFile': lambda_code.encode()},
                Description=f'fo.ai {action} action for {instance_id}',
                Timeout=30
            )
            
            return {
                "success": True,
                "function_name": function_name,
                "function_arn": response['FunctionArn']
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to create Lambda function: {e.response['Error']['Message']}"
            }
    
    def _create_cloudwatch_rule(self, instance_id: str, action: str, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create CloudWatch Events rule for scheduling"""
        rule_name = f"foai-{instance_id}-{action}"
        
        # Create cron expression
        if schedule_data['type'] == 'daily':
            start_hour, start_minute = map(int, schedule_data['start_time'].split(':'))
            cron_expression = f"cron({start_minute} {start_hour} ? * {','.join(schedule_data['days'])} *)"
        elif schedule_data['type'] == 'weekly':
            start_hour, start_minute = map(int, schedule_data['start_time'].split(':'))
            cron_expression = f"cron({start_minute} {start_hour} ? * {','.join(schedule_data['days'])} *)"
        else:  # specific time
            hour, minute = map(int, schedule_data['time'].split(':'))
            cron_expression = f"cron({minute} {hour} * * ? *)"
        
        try:
            response = self.events_client.put_rule(
                Name=rule_name,
                ScheduleExpression=cron_expression,
                State='ENABLED',
                Description=f"fo.ai {action} schedule for {instance_id}: {schedule_data['description']}"
            )
            
            return {
                "success": True,
                "rule_name": rule_name,
                "rule_arn": response['RuleArn'],
                "cron_expression": cron_expression
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to create CloudWatch rule: {e.response['Error']['Message']}"
            }
    
    def _schedule_shutdown(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an EC2 instance shutdown"""
        instance_id = parameters['instance_id']
        time_period = parameters['time_period']
        schedule_name = parameters.get('schedule_name', f"shutdown-{instance_id}")
        
        # Parse time period
        schedule_data = self._parse_time_period(time_period)
        
        # Create Lambda function
        lambda_result = self._create_lambda_function(instance_id, "stop", schedule_data)
        if not lambda_result['success']:
            return lambda_result
        
        # Create CloudWatch rule
        rule_result = self._create_cloudwatch_rule(instance_id, "stop", schedule_data)
        if not rule_result['success']:
            return rule_result
        
        # Add target to rule
        try:
            self.events_client.put_targets(
                Rule=rule_result['rule_name'],
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_result['function_arn']
                }]
            )
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to add target to rule: {e.response['Error']['Message']}"
            }
        
        return {
            "success": True,
            "message": f"Successfully scheduled shutdown for {instance_id}",
            "instance_id": instance_id,
            "schedule": schedule_data,
            "schedule_name": schedule_name,
            "lambda_function": lambda_result['function_name'],
            "cloudwatch_rule": rule_result['rule_name']
        }
    
    def _schedule_startup(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule an EC2 instance startup"""
        instance_id = parameters['instance_id']
        time_period = parameters['time_period']
        schedule_name = parameters.get('schedule_name', f"startup-{instance_id}")
        
        # Parse time period
        schedule_data = self._parse_time_period(time_period)
        
        # Create Lambda function
        lambda_result = self._create_lambda_function(instance_id, "start", schedule_data)
        if not lambda_result['success']:
            return lambda_result
        
        # Create CloudWatch rule
        rule_result = self._create_cloudwatch_rule(instance_id, "start", schedule_data)
        if not rule_result['success']:
            return rule_result
        
        # Add target to rule
        try:
            self.events_client.put_targets(
                Rule=rule_result['rule_name'],
                Targets=[{
                    'Id': '1',
                    'Arn': lambda_result['function_arn']
                }]
            )
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to add target to rule: {e.response['Error']['Message']}"
            }
        
        return {
            "success": True,
            "message": f"Successfully scheduled startup for {instance_id}",
            "instance_id": instance_id,
            "schedule": schedule_data,
            "schedule_name": schedule_name,
            "lambda_function": lambda_result['function_name'],
            "cloudwatch_rule": rule_result['rule_name']
        }
    
    def _get_instance_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current status of an EC2 instance"""
        instance_id = parameters['instance_id']
        
        try:
            response = self.ec2_client.describe_instances(
                InstanceIds=[instance_id]
            )
            
            if not response['Reservations']:
                return {
                    "success": False,
                    "error": f"Instance {instance_id} not found",
                    "instance_id": instance_id
                }
            
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                "success": True,
                "instance_id": instance_id,
                "state": instance['State']['Name'],
                "instance_type": instance['InstanceType'],
                "availability_zone": instance['Placement']['AvailabilityZone'],
                "launch_time": instance['LaunchTime'].isoformat(),
                "public_ip": instance.get('PublicIpAddress'),
                "private_ip": instance.get('PrivateIpAddress')
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS error: {e.response['Error']['Message']}",
                "instance_id": instance_id
            }
    
    def _list_instances(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List EC2 instances with optional filtering"""
        filters = []
        
        if 'state' in parameters:
            filters.append({'Name': 'instance-state-name', 'Values': [parameters['state']]})
        
        if 'instance_type' in parameters:
            filters.append({'Name': 'instance-type', 'Values': [parameters['instance_type']]})
        
        try:
            response = self.ec2_client.describe_instances(Filters=filters)
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        "instance_id": instance['InstanceId'],
                        "state": instance['State']['Name'],
                        "instance_type": instance['InstanceType'],
                        "availability_zone": instance['Placement']['AvailabilityZone'],
                        "launch_time": instance['LaunchTime'].isoformat()
                    })
            
            return {
                "success": True,
                "instances": instances,
                "count": len(instances)
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS error: {e.response['Error']['Message']}"
            }
    
    def _delete_schedule(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a scheduled action"""
        instance_id = parameters['instance_id']
        schedule_type = parameters['schedule_type']
        
        rule_name = f"foai-{instance_id}-{schedule_type}"
        function_name = f"foai-{instance_id}-{schedule_type}"
        
        try:
            # Remove targets from rule
            self.events_client.remove_targets(Rule=rule_name, Ids=['1'])
            
            # Delete rule
            self.events_client.delete_rule(Name=rule_name)
            
            # Delete Lambda function
            self.lambda_client.delete_function(FunctionName=function_name)
            
            return {
                "success": True,
                "message": f"Successfully deleted {schedule_type} schedule for {instance_id}",
                "instance_id": instance_id,
                "schedule_type": schedule_type
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to delete schedule: {e.response['Error']['Message']}",
                "instance_id": instance_id
            }
    
    def _list_schedules(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List all scheduled actions"""
        instance_id = parameters.get('instance_id')
        
        try:
            # List CloudWatch rules
            if instance_id:
                response = self.events_client.list_rules(
                    NamePrefix=f"foai-{instance_id}-"
                )
            else:
                response = self.events_client.list_rules(
                    NamePrefix="foai-"
                )
            
            schedules = []
            for rule in response['Rules']:
                if 'foai-' in rule['Name']:
                    # Extract instance ID and action from rule name
                    parts = rule['Name'].split('-')
                    if len(parts) >= 3:
                        rule_instance_id = parts[1]
                        action = parts[2]
                        
                        schedules.append({
                            "instance_id": rule_instance_id,
                            "action": action,
                            "rule_name": rule['Name'],
                            "schedule": rule.get('ScheduleExpression'),
                            "state": rule.get('State'),
                            "description": rule.get('Description')
                        })
            
            return {
                "success": True,
                "schedules": schedules,
                "count": len(schedules)
            }
            
        except ClientError as e:
            return {
                "success": False,
                "error": f"Failed to list schedules: {e.response['Error']['Message']}"
            }
