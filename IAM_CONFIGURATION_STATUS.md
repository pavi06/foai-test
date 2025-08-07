# 🔐 IAM Configuration Status for fo.ai Agent Tools

## Current Status

The fo.ai agent tools require specific AWS IAM permissions to function properly. Here's what needs to be configured:

## ✅ What's Already Configured

### 1. **Agent Code Structure**
- ✅ EC2 Agent with comprehensive functionality
- ✅ Lambda function creation for scheduling
- ✅ CloudWatch Events integration
- ✅ Natural language processing
- ✅ API endpoints for all operations

### 2. **Required IAM Role Reference**
- ✅ Code references: `arn:aws:iam::{account}:role/foai-lambda-ec2-role`
- ✅ Lambda execution role for scheduled actions
- ✅ Proper trust policy for Lambda service

## ❌ What Needs to be Configured

### 1. **Lambda Execution Role**
**Role Name:** `foai-lambda-ec2-role`

**Required Permissions:**
```json
{
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
```

**Trust Policy:**
```json
{
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
```

### 2. **Agent User Policy**
**Policy Name:** `foai-agent-policy`

**Required Permissions:**
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
      "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/foai-lambda-ec2-role"
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
```

## 🔧 Setup Options

### Option 1: Automated Setup (Recommended)
```bash
python setup_agent_iam.py
```

This script will:
- ✅ Check your current permissions
- ✅ Create the Lambda execution role
- ✅ Create the agent policy
- ✅ Test the configuration
- ✅ Provide detailed feedback

### Option 2: Manual Setup via AWS Console

#### Step 1: Create Lambda Execution Role
1. Go to IAM Console > Roles > Create Role
2. Trusted entity: Lambda
3. Role name: `foai-lambda-ec2-role`
4. Attach policies:
   - `AWSLambdaBasicExecutionRole`
   - Create custom policy with EC2 permissions

#### Step 2: Create Agent Policy
1. Go to IAM Console > Policies > Create Policy
2. Policy name: `foai-agent-policy`
3. Use the policy document above
4. Replace `YOUR_ACCOUNT_ID` with your actual account ID

#### Step 3: Attach Policy to User/Role
1. Go to IAM Console > Users/Roles
2. Select your user/role
3. Attach the `foai-agent-policy`

### Option 3: AWS CLI Setup
```bash
# Create Lambda execution role
aws iam create-role \
  --role-name foai-lambda-ec2-role \
  --assume-role-policy-document file://trust-policy.json

# Attach basic Lambda execution policy
aws iam attach-role-policy \
  --role-name foai-lambda-ec2-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create agent policy
aws iam create-policy \
  --policy-name foai-agent-policy \
  --policy-document file://agent-policy.json

# Attach to your user/role
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/foai-agent-policy
```

## 🧪 Testing Configuration

### Test IAM Setup
```bash
python test_iam_configuration.py
```

This will test:
- ✅ AWS credentials
- ✅ Lambda execution role
- ✅ Agent policy
- ✅ EC2 permissions
- ✅ CloudWatch Events permissions
- ✅ Lambda permissions
- ✅ Agent functionality
- ✅ Scheduling functionality

### Test Agent Tools
```bash
# Start the API server
python foai_cli.py server start all

# Test natural language
curl -X POST "http://localhost:8000/agents/natural-language" \
  -H "Content-Type: application/json" \
  -d '{"query": "List all running instances"}'
```

## 🚨 Common Issues

### 1. **Role Not Found Error**
```
ValidationException: Value 'arn:aws:iam::YOUR_ACCOUNT:role/foai-lambda-ec2-role' at 'role' failed to satisfy constraint
```
**Solution:** Run `python setup_agent_iam.py` to create the role

### 2. **Access Denied Error**
```
AccessDenied: User is not authorized to perform: lambda:CreateFunction
```
**Solution:** Attach the `foai-agent-policy` to your user/role

### 3. **No Credentials Error**
```
NoCredentialsError: Unable to locate credentials
```
**Solution:** Configure AWS credentials using `aws configure` or environment variables

### 4. **Insufficient Permissions**
```
UnauthorizedOperation: You are not authorized to perform this operation
```
**Solution:** Ensure your user has the required IAM permissions to create roles and policies

## 📋 Required Permissions Summary

### For Setup (One-time):
- `iam:CreateRole`
- `iam:CreatePolicy`
- `iam:AttachRolePolicy`
- `iam:PutRolePolicy`

### For Operation (Ongoing):
- `ec2:DescribeInstances`, `ec2:StartInstances`, `ec2:StopInstances`
- `events:PutRule`, `events:PutTargets`, `events:RemoveTargets`, `events:DeleteRule`, `events:ListRules`
- `lambda:CreateFunction`, `lambda:DeleteFunction`, `lambda:InvokeFunction`
- `iam:PassRole` (for the Lambda execution role)
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

## 🎯 Next Steps

1. **Run the setup script:**
   ```bash
   python setup_agent_iam.py
   ```

2. **Test the configuration:**
   ```bash
   python test_iam_configuration.py
   ```

3. **Start using the agent tools:**
   ```bash
   python foai_cli.py server start all
   ```

4. **Test with natural language:**
   ```bash
   curl -X POST "http://localhost:8000/agents/natural-language" \
     -H "Content-Type: application/json" \
     -d '{"query": "Stop instance i-1234567890abcdef0"}'
   ```

## 🔒 Security Notes

- The Lambda execution role has minimal permissions (only EC2 start/stop)
- The agent policy follows the principle of least privilege
- All operations are logged for audit purposes
- Consider using resource-level permissions for production environments
- Regularly review and rotate access keys

---

**Once configured, your agent tools will be fully functional and ready for production use! 🚀**
