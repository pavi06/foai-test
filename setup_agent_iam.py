#!/usr/bin/env python3
"""
IAM Setup Script for fo.ai Agent Tools
Configures all necessary AWS permissions and roles for the agent system
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError

class AgentIAMSetup:
    """Setup IAM roles and policies for fo.ai agent tools"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.iam_client = None
        self.sts_client = None
        self.account_id = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AWS clients"""
        try:
            self.iam_client = boto3.client('iam')
            self.sts_client = boto3.client('sts')
            
            # Get account ID
            identity = self.sts_client.get_caller_identity()
            self.account_id = identity['Account']
            
            print(f"AWS clients initialized for account: {self.account_id}")
            print(f"   Region: {self.region}")
            print(f"   User: {identity['Arn']}")
            
        except NoCredentialsError:
            print("AWS credentials not found. Please configure your AWS credentials.")
            sys.exit(1)
        except Exception as e:
            print(f"Failed to initialize AWS clients: {e}")
            sys.exit(1)
    
    def check_existing_role(self, role_name: str) -> bool:
        """Check if a role already exists"""
        try:
            self.iam_client.get_role(RoleName=role_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return False
            else:
                raise
    
    def create_lambda_execution_role(self) -> str:
        """Create IAM role for Lambda execution"""
        role_name = "foai-lambda-ec2-role"
        
        if self.check_existing_role(role_name):
            print(f"Role {role_name} already exists")
            return f"arn:aws:iam::{self.account_id}:role/{role_name}"
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Permission policy for EC2 operations
        permission_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:StartInstances",
                        "ec2:StopInstances",
                        "ec2:DescribeInstances",
                        "ec2:DescribeInstanceStatus"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        try:
            # Create the role
            print(f"🔧 Creating role: {role_name}")
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="fo.ai Lambda execution role for EC2 agent operations"
            )
            
            # Attach the permission policy
            policy_name = f"{role_name}-policy"
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permission_policy)
            )
            
            # Attach basic Lambda execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            
            print(f"Successfully created role: {role_name}")
            return response['Role']['Arn']
            
        except ClientError as e:
            print(f"Failed to create role {role_name}: {e.response['Error']['Message']}")
            return None
    
    def create_agent_user_policy(self) -> str:
        """Create IAM policy for the agent user/application"""
        policy_name = "foai-agent-policy"
        
        # Check if policy exists
        try:
            self.iam_client.get_policy(PolicyArn=f"arn:aws:iam::{self.account_id}:policy/{policy_name}")
            print(f"Policy {policy_name} already exists")
            return f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
        except ClientError:
            pass
        
        # Permission policy for agent operations
        policy_document = {
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
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "events:PutRule",
                        "events:PutTargets",
                        "events:RemoveTargets",
                        "events:DeleteRule",
                        "events:ListRules",
                        "events:DescribeRule"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:CreateFunction",
                        "lambda:DeleteFunction",
                        "lambda:InvokeFunction",
                        "lambda:GetFunction",
                        "lambda:UpdateFunctionCode"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "iam:PassRole"
                    ],
                    "Resource": f"arn:aws:iam::{self.account_id}:role/foai-lambda-ec2-role"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:GetLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            print(f"🔧 Creating policy: {policy_name}")
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="fo.ai agent tools policy for EC2 and scheduling operations"
            )
            
            print(f"Successfully created policy: {policy_name}")
            return response['Policy']['Arn']
            
        except ClientError as e:
            print(f"Failed to create policy {policy_name}: {e.response['Error']['Message']}")
            return None
    
    def check_user_permissions(self) -> bool:
        """Check if current user has necessary permissions"""
        print("Checking current user permissions...")
        
        required_permissions = [
            "iam:CreateRole",
            "iam:CreatePolicy",
            "iam:AttachRolePolicy",
            "iam:PutRolePolicy",
            "ec2:DescribeInstances",
            "events:PutRule",
            "lambda:CreateFunction"
        ]
        
        missing_permissions = []
        
        for permission in required_permissions:
            try:
                # Test each permission with a simple operation
                if permission.startswith("iam:"):
                    if "CreateRole" in permission:
                        # Test by trying to describe a non-existent role
                        self.iam_client.get_role(RoleName="test-permission-check")
                    elif "CreatePolicy" in permission:
                        # Test by trying to describe a non-existent policy
                        self.iam_client.get_policy(PolicyArn="arn:aws:iam::123456789012:policy/test")
                elif permission.startswith("ec2:"):
                    # Test EC2 permissions
                    ec2_client = boto3.client('ec2', region_name=self.region)
                    ec2_client.describe_instances(MaxResults=1)
                elif permission.startswith("events:"):
                    # Test CloudWatch Events permissions
                    events_client = boto3.client('events', region_name=self.region)
                    events_client.list_rules(Limit=1)
                elif permission.startswith("lambda:"):
                    # Test Lambda permissions
                    lambda_client = boto3.client('lambda', region_name=self.region)
                    lambda_client.list_functions(MaxItems=1)
                    
            except ClientError as e:
                if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
                    missing_permissions.append(permission)
                # Other errors (like NoSuchEntity) are expected and don't indicate missing permissions
        
        if missing_permissions:
            print(f"Missing permissions: {missing_permissions}")
            return False
        else:
            print("All required permissions are available")
            return True
    
    def test_agent_functionality(self) -> bool:
        """Test if the agent can perform basic operations"""
        print("🧪 Testing agent functionality...")
        
        try:
            from app.agents.ec2_agent import EC2Agent
            
            # Initialize agent
            agent = EC2Agent(region=self.region)
            print("EC2 Agent initialized successfully")
            
            # Test listing instances
            result = agent.execute_action("list_instances", {})
            if result.get("success"):
                print("EC2 Agent can list instances")
            else:
                print(f"EC2 Agent list instances failed: {result.get('error')}")
            
            # Test getting available actions
            actions = agent.get_available_actions()
            if len(actions) > 0:
                print(f"EC2 Agent has {len(actions)} available actions")
            else:
                print("EC2 Agent has no available actions")
            
            return True
            
        except Exception as e:
            print(f"Agent functionality test failed: {e}")
            return False
    
    def generate_setup_instructions(self):
        """Generate setup instructions for manual configuration"""
        print("\nManual Setup Instructions")
        print("=" * 50)
        
        print("\n1. Create Lambda Execution Role:")
        print("   - Go to IAM Console > Roles > Create Role")
        print("   - Trusted entity: Lambda")
        print("   - Role name: foai-lambda-ec2-role")
        print("   - Attach policies:")
        print("     * AWSLambdaBasicExecutionRole")
        print("     * Custom policy for EC2 operations")
        
        print("\n2. Create Agent Policy:")
        print("   - Go to IAM Console > Policies > Create Policy")
        print("   - Policy name: foai-agent-policy")
        print("   - Use the policy document from AGENT_TOOLS_GUIDE.md")
        
        print("\n3. Attach Policy to User/Role:")
        print("   - Go to IAM Console > Users/Roles")
        print("   - Select your user/role")
        print("   - Attach the foai-agent-policy")
        
        print("\n4. Required Permissions Summary:")
        print("   - EC2: DescribeInstances, StartInstances, StopInstances")
        print("   - CloudWatch Events: PutRule, PutTargets, RemoveTargets, DeleteRule, ListRules")
        print("   - Lambda: CreateFunction, DeleteFunction, InvokeFunction")
        print("   - IAM: PassRole (for the Lambda execution role)")
        print("   - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents")
    
    def run_full_setup(self) -> bool:
        """Run complete IAM setup"""
        print("Starting fo.ai Agent IAM Setup")
        print("=" * 50)
        
        # Check permissions first
        if not self.check_user_permissions():
            print("\nInsufficient permissions. Please ensure your AWS user/role has the required permissions.")
            self.generate_setup_instructions()
            return False
        
        # Create Lambda execution role
        lambda_role_arn = self.create_lambda_execution_role()
        if not lambda_role_arn:
            print("Failed to create Lambda execution role")
            return False
        
        # Create agent policy
        agent_policy_arn = self.create_agent_user_policy()
        if not agent_policy_arn:
            print("Failed to create agent policy")
            return False
        
        # Test agent functionality
        if not self.test_agent_functionality():
            print("Agent functionality test failed")
            return False
        
        print("\n" + "=" * 50)
        print("IAM Setup Complete!")
        print(f"   Lambda Role: {lambda_role_arn}")
        print(f"   Agent Policy: {agent_policy_arn}")
        
        print("\nNext Steps:")
        print("1. Attach the agent policy to your AWS user/role")
        print("2. Test the agent tools with: python test_agent_tools.py")
        print("3. Start using natural language commands!")
        
        return True

def main():
    """Main setup function"""
    setup = AgentIAMSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        # Only check permissions
        setup.check_user_permissions()
        setup.test_agent_functionality()
    else:
        # Run full setup
        setup.run_full_setup()

if __name__ == "__main__":
    main()
