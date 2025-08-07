# 🤖 fo.ai Agent Tools Guide

## Overview

fo.ai now includes a comprehensive AI agent system that allows you to manage AWS resources using natural language commands. The system is built with modularity and extensibility in mind, making it easy to add new agents and actions.

## 🏗️ Architecture

### Core Components

1. **BaseAgent** (`app/agents/base_agent.py`)
   - Abstract base class for all agents
   - Provides common functionality like logging, validation, and action history

2. **EC2Agent** (`app/agents/ec2_agent.py`)
   - Manages EC2 instances (start, stop, schedule, monitor)
   - Supports natural language time descriptions
   - Creates CloudWatch Events and Lambda functions for scheduling

3. **AgentManager** (`app/agents/agent_manager.py`)
   - Coordinates multiple agents
   - Provides natural language parsing and routing
   - Unified interface for all agent operations

4. **CogIntegration** (`app/agents/cog_integration.py`)
   - Exposes agents as Cog-compatible tools
   - Enables natural language processing
   - Provides tool schemas and validation

5. **API Endpoints** (`app/agents/api_endpoints.py`)
   - REST API for agent operations
   - Both programmatic and natural language interfaces

## 🚀 Getting Started

### 1. Setup IAM Configuration

Before using the agent tools, you need to configure AWS IAM permissions:

```bash
# Run the automated setup (recommended)
python setup_agent_iam.py

# Or check current configuration
python test_iam_configuration.py
```

### 2. Start the API Server

```bash
python foai_cli.py server start all
```

### 3. Test the Agent System

```bash
# Test IAM configuration
python test_iam_configuration.py

# Test agent functionality
python test_agent_tools.py
```

## 📋 Available Actions

### EC2 Agent Actions

| Action | Description | Parameters |
|--------|-------------|------------|
| `stop_instance` | Stop an EC2 instance immediately | `instance_id`, `force` (optional) |
| `start_instance` | Start an EC2 instance | `instance_id` |
| `schedule_shutdown` | Schedule automatic shutdown | `instance_id`, `time_period`, `schedule_name` (optional) |
| `schedule_startup` | Schedule automatic startup | `instance_id`, `time_period`, `schedule_name` (optional) |
| `get_instance_status` | Get instance details | `instance_id` |
| `list_instances` | List all instances | `state` (optional), `instance_type` (optional) |
| `delete_schedule` | Remove a schedule | `instance_id`, `schedule_type` |
| `list_schedules` | List all schedules | `instance_id` (optional) |

## 🗣️ Natural Language Examples

### Basic Commands

```bash
# Stop an instance
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Stop instance i-1234567890abcdef0"}'

# Start an instance
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Start instance i-1234567890abcdef0"}'

# Check instance status
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Check status of instance i-1234567890abcdef0"}'

# List running instances
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all running instances"}'
```

### Scheduling Commands

```bash
# Schedule shutdown during non-business hours
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Schedule shutdown for i-1234567890abcdef0 during non-business hours"}'

# Schedule startup at specific time
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Schedule startup for i-1234567890abcdef0 at 8 AM"}'

# Schedule weekend shutdown
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "Schedule shutdown for i-1234567890abcdef0 during weekend"}'
```

## 🔧 API Endpoints

### Agent Management

```bash
# Get agent status
GET /agents/status

# Get available tools
GET /agents/tools

# Execute tool
POST /agents/execute
{
  "tool_name": "ec2_stop_instance",
  "arguments": {
    "instance_id": "i-1234567890abcdef0",
    "force": false
  }
}

# Process natural language
POST /agents/natural-language
{
  "query": "Stop instance i-1234567890abcdef0"
}

# Get action history
GET /agents/history

# Validate tool call
POST /agents/validate
{
  "tool_name": "ec2_stop_instance",
  "arguments": {
    "instance_id": "i-1234567890abcdef0"
  }
}
```

### EC2-Specific Endpoints

```bash
# Stop instance
POST /agents/ec2/stop?instance_id=i-1234567890abcdef0&force=false

# Start instance
POST /agents/ec2/start?instance_id=i-1234567890abcdef0

# Schedule shutdown
POST /agents/ec2/schedule-shutdown?instance_id=i-1234567890abcdef0&time_period=non-business%20hours

# Schedule startup
POST /agents/ec2/schedule-startup?instance_id=i-1234567890abcdef0&time_period=8%20AM

# Get instance status
GET /agents/ec2/status/i-1234567890abcdef0

# List instances
GET /agents/ec2/list?state=running&instance_type=t3.micro

# List schedules
GET /agents/ec2/schedules?instance_id=i-1234567890abcdef0

# Delete schedule
DELETE /agents/ec2/schedule/i-1234567890abcdef0?schedule_type=shutdown
```

## ⏰ Supported Time Periods

The scheduling system supports natural language time descriptions:

### Predefined Periods

- **Non-business hours**: 6 PM - 8 AM weekdays
- **Business hours**: 8 AM - 6 PM weekdays  
- **Weekend**: Friday 6 PM - Monday 8 AM
- **Overnight**: 10 PM - 6 AM daily

### Specific Times

- **"6 PM"** or **"18:00"**: Specific time
- **"8 AM"** or **"08:00"**: Specific time
- **"midnight"**: 12:00 AM
- **"noon"**: 12:00 PM

### Custom Periods

- **"during non-business hours"**
- **"at 6 PM"**
- **"from 6 PM to 8 AM"**
- **"weekend"**
- **"overnight"**

## 🔐 AWS Permissions Required

The EC2 Agent requires the following AWS permissions:

### EC2 Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:DescribeInstanceStatus"
      ],
      "Resource": "*"
    }
  ]
}
```

### CloudWatch Events Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:DeleteRule",
        "events:ListRules"
      ],
      "Resource": "*"
    }
  ]
}
```

### Lambda Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
}
```

### IAM Role for Lambda
The Lambda functions need an execution role with EC2 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🧪 Testing

### Run the Test Suite

```bash
python test_agent_tools.py
```

### Manual Testing

```bash
# Test agent status
curl http://localhost:8000/agents/status

# Test natural language
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all running instances"}'

# Test tool execution
curl -X POST "http://localhost:8000/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "ec2_list_instances",
    "arguments": {"state": "running"}
  }'
```

## 🔧 Extending the System

### Adding a New Agent

1. Create a new agent class inheriting from `BaseAgent`:

```python
from app.agents.base_agent import BaseAgent

class S3Agent(BaseAgent):
    def __init__(self, region: str = "us-east-1"):
        super().__init__(
            name="S3Agent",
            description="AI agent for managing S3 buckets"
        )
        self.region = region
    
    def get_available_actions(self):
        return [
            {
                "name": "delete_bucket",
                "description": "Delete an S3 bucket",
                "parameters": {
                    "bucket_name": {"type": "string", "required": True}
                }
            }
        ]
    
    def execute_action(self, action_name: str, parameters: Dict[str, Any]):
        # Implementation here
        pass
    
    def validate_action(self, action_name: str, parameters: Dict[str, Any]):
        # Validation logic here
        pass
```

2. Register the agent in `AgentManager`:

```python
# In app/agents/agent_manager.py
from .s3_agent import S3Agent

def _initialize_agents(self):
    self.agents['ec2'] = EC2Agent(region=self.region)
    self.agents['s3'] = S3Agent(region=self.region)  # Add this line
```

### Adding New Actions

1. Add the action to the agent's `get_available_actions()` method
2. Implement the action in `execute_action()`
3. Add validation in `validate_action()`
4. Update natural language parsing in `AgentManager.parse_natural_language_request()`

## 🐛 Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   - Ensure AWS credentials are configured
   - Check `~/.aws/credentials` or environment variables

2. **Permission Denied**
   - Verify IAM permissions are correct
   - Check if the Lambda execution role exists

3. **Instance Not Found**
   - Verify the instance ID is correct
   - Check if the instance is in the specified region

4. **Scheduling Not Working**
   - Check CloudWatch Events rules
   - Verify Lambda functions are created
   - Check Lambda execution logs

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Agent Status

```bash
curl http://localhost:8000/agents/status
```

## 📈 Monitoring

### Action History

```bash
# Get all action history
curl http://localhost:8000/agents/history

# Get specific agent history
curl http://localhost:8000/agents/history?agent_name=ec2
```

### CloudWatch Monitoring

The system creates CloudWatch Events rules and Lambda functions. Monitor:

- CloudWatch Events rule execution
- Lambda function invocations and errors
- EC2 instance state changes

## 🔄 Future Enhancements

### Planned Features

1. **S3 Agent**: Bucket management, lifecycle policies
2. **RDS Agent**: Database start/stop, backup management
3. **Cost Optimization**: Automatic cost-saving recommendations
4. **Multi-region Support**: Manage resources across regions
5. **Webhook Integration**: Notify external systems of actions
6. **Approval Workflows**: Require approval for destructive actions

### Contributing

To add new features:

1. Create a feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review the test suite output
3. Check AWS CloudWatch logs
4. Open an issue on the repository

---

**Happy automating! 🚀**
