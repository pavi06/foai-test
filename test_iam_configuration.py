#!/usr/bin/env python3
"""
IAM Configuration Test for fo.ai Agent Tools
Verifies that all necessary IAM roles and permissions are properly configured
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError

def test_aws_credentials():
    """Test if AWS credentials are properly configured"""
    print("Testing AWS Credentials...")
    
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"AWS credentials configured")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        
        return True, identity
    except NoCredentialsError:
        print("AWS credentials not found")
        print("   Please configure your AWS credentials using:")
        print("   - AWS CLI: aws configure")
        print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("   - IAM role (if running on EC2)")
        return False, None
    except Exception as e:
        print(f"AWS credentials test failed: {e}")
        return False, None

def test_lambda_execution_role(account_id: str):
    """Test if the Lambda execution role exists and has correct permissions"""
    print("\n🔧 Testing Lambda Execution Role...")
    
    role_name = "foai-lambda-ec2-role"
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    
    try:
        iam_client = boto3.client('iam')
        
        # Check if role exists
        response = iam_client.get_role(RoleName=role_name)
        print(f"Role exists: {role_name}")
        
        # Check trust policy
        trust_policy = response['Role']['AssumeRolePolicyDocument']
        if 'lambda.amazonaws.com' in str(trust_policy):
            print("Trust policy allows Lambda")
        else:
            print("Trust policy does not allow Lambda")
            return False
        
        # Check attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        policy_names = [p['PolicyName'] for p in attached_policies['AttachedPolicies']]
        
        if 'AWSLambdaBasicExecutionRole' in policy_names:
            print("Basic Lambda execution policy attached")
        else:
            print("Basic Lambda execution policy not attached")
            return False
        
        # Check inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        if inline_policies['PolicyNames']:
            print("Inline policies found")
        else:
            print("No inline policies found (may be using attached policies)")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"Role {role_name} does not exist")
            print("   Run: python setup_agent_iam.py")
            return False
        else:
            print(f"Error checking role: {e.response['Error']['Message']}")
            return False

def test_agent_policy(account_id: str):
    """Test if the agent policy exists"""
    print("\nTesting Agent Policy...")
    
    policy_name = "foai-agent-policy"
    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
    
    try:
        iam_client = boto3.client('iam')
        
        # Check if policy exists
        response = iam_client.get_policy(PolicyArn=policy_arn)
        print(f"Policy exists: {policy_name}")
        
        # Get policy version
        policy_version = iam_client.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=response['Policy']['DefaultVersionId']
        )
        
        policy_document = policy_version['PolicyVersion']['Document']
        statements = policy_document['Statement']
        
        # Check for required permissions
        required_actions = [
            "ec2:DescribeInstances",
            "ec2:StartInstances", 
            "ec2:StopInstances",
            "events:PutRule",
            "events:PutTargets",
            "lambda:CreateFunction",
            "lambda:DeleteFunction"
        ]
        
        found_actions = []
        for statement in statements:
            if 'Action' in statement:
                actions = statement['Action']
                if isinstance(actions, str):
                    actions = [actions]
                found_actions.extend(actions)
        
        missing_actions = [action for action in required_actions if action not in found_actions]
        
        if missing_actions:
            print(f"Missing required actions: {missing_actions}")
            return False
        else:
            print("All required actions found in policy")
            return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"Policy {policy_name} does not exist")
            print("   Run: python setup_agent_iam.py")
            return False
        else:
            print(f"Error checking policy: {e.response['Error']['Message']}")
            return False

def test_ec2_permissions():
    """Test EC2 permissions"""
    print("\nTesting EC2 Permissions...")
    
    try:
        ec2_client = boto3.client('ec2')
        
        # Test describe instances
        response = ec2_client.describe_instances(MaxResults=5)
        instance_count = sum(len(reservation['Instances']) for reservation in response['Reservations'])
        print(f"Can describe instances (found {instance_count} instances)")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print(f"EC2 permissions denied: {e.response['Error']['Message']}")
            return False
        else:
            print(f"EC2 test failed: {e.response['Error']['Message']}")
            return False

def test_cloudwatch_events_permissions():
    """Test CloudWatch Events permissions"""
    print("\n⏰ Testing CloudWatch Events Permissions...")
    
    try:
        events_client = boto3.client('events')
        
        # Test list rules
        response = events_client.list_rules(Limit=5)
        rule_count = len(response['Rules'])
        print(f"Can list CloudWatch Events rules (found {rule_count} rules)")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print(f"CloudWatch Events permissions denied: {e.response['Error']['Message']}")
            return False
        else:
            print(f"CloudWatch Events test failed: {e.response['Error']['Message']}")
            return False

def test_lambda_permissions():
    """Test Lambda permissions"""
    print("\n🔧 Testing Lambda Permissions...")
    
    try:
        lambda_client = boto3.client('lambda')
        
        # Test list functions
        response = lambda_client.list_functions(MaxItems=5)
        function_count = len(response['Functions'])
        print(f"✅ Can list Lambda functions (found {function_count} functions)")
        
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] in ['AccessDenied', 'UnauthorizedOperation']:
            print(f"❌ Lambda permissions denied: {e.response['Error']['Message']}")
            return False
        else:
            print(f"⚠️  Lambda test failed: {e.response['Error']['Message']}")
            return False

def test_agent_functionality():
    """Test if the agent can be initialized and perform basic operations"""
    print("\n🤖 Testing Agent Functionality...")
    
    try:
        from app.agents.ec2_agent import EC2Agent
        
        # Initialize agent
        agent = EC2Agent()
        print("✅ EC2 Agent initialized successfully")
        
        # Test available actions
        actions = agent.get_available_actions()
        if len(actions) > 0:
            print(f"✅ Agent has {len(actions)} available actions")
            
            # List some actions
            for action in actions[:3]:
                print(f"   - {action['name']}: {action['description']}")
        else:
            print("❌ Agent has no available actions")
            return False
        
        # Test action validation
        valid_params = {"instance_id": "i-1234567890abcdef0"}
        invalid_params = {"instance_id": "invalid-id"}
        
        if agent.validate_action("stop_instance", valid_params):
            print("✅ Action validation works for valid parameters")
        else:
            print("❌ Action validation failed for valid parameters")
            return False
        
        if not agent.validate_action("stop_instance", invalid_params):
            print("✅ Action validation correctly rejects invalid parameters")
        else:
            print("❌ Action validation should reject invalid parameters")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import EC2 Agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Agent functionality test failed: {e}")
        return False

def test_scheduling_functionality():
    """Test scheduling functionality"""
    print("\n🕐 Testing Scheduling Functionality...")
    
    try:
        from app.agents.ec2_agent import EC2Agent
        
        agent = EC2Agent()
        
        # Test time period parsing
        test_cases = [
            ("non-business hours", "daily"),
            ("business hours", "daily"), 
            ("weekend", "weekly"),
            ("6 PM", "specific"),
            ("18:00", "specific")
        ]
        
        for time_text, expected_type in test_cases:
            schedule_data = agent._parse_time_period(time_text)
            if schedule_data['type'] == expected_type:
                print(f"✅ Time parsing works for '{time_text}'")
            else:
                print(f"❌ Time parsing failed for '{time_text}'")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduling functionality test failed: {e}")
        return False

def main():
    """Run all IAM configuration tests"""
    print("🔍 fo.ai Agent IAM Configuration Test")
    print("=" * 50)
    
    # Test AWS credentials
    credentials_ok, identity = test_aws_credentials()
    if not credentials_ok:
        sys.exit(1)
    
    account_id = identity['Account']
    
    # Run all tests
    tests = [
        ("Lambda Execution Role", lambda: test_lambda_execution_role(account_id)),
        ("Agent Policy", lambda: test_agent_policy(account_id)),
        ("EC2 Permissions", test_ec2_permissions),
        ("CloudWatch Events Permissions", test_cloudwatch_events_permissions),
        ("Lambda Permissions", test_lambda_permissions),
        ("Agent Functionality", test_agent_functionality),
        ("Scheduling Functionality", test_scheduling_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All IAM configuration tests passed!")
        print("✅ Your agent tools are properly configured and ready to use.")
        print("\n🚀 Next steps:")
        print("1. Start the API server: python foai_cli.py server start all")
        print("2. Test with natural language: curl -X POST 'http://localhost:8000/agents/natural-language' -H 'Content-Type: application/json' -d '{\"query\": \"List all running instances\"}'")
    else:
        print("⚠️  Some tests failed. Please run the setup script:")
        print("   python setup_agent_iam.py")
        print("\nOr manually configure the missing components.")

if __name__ == "__main__":
    main()
