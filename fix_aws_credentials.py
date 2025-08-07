#!/usr/bin/env python3
"""
Fix AWS Credentials Script
Uncomments AWS credentials in .env file
"""

import re
import os

def fix_aws_credentials():
    """Uncomment AWS credentials in .env file"""
    
    # Read the .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    # Uncomment AWS credentials
    fixed_content = re.sub(r'^# (AWS_ACCESS_KEY_ID=)', r'\1', content, flags=re.MULTILINE)
    fixed_content = re.sub(r'^# (AWS_SECRET_ACCESS_KEY=)', r'\1', fixed_content, flags=re.MULTILINE)
    fixed_content = re.sub(r'^# (AWS_SESSION_TOKEN=)', r'\1', fixed_content, flags=re.MULTILINE)
    
    # Write back to .env file
    with open('.env', 'w') as f:
        f.write(fixed_content)
    
    print("✅ AWS credentials have been uncommented in .env file")
    print("🔍 Verifying the fix...")
    
    # Show the fixed lines
    with open('.env', 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip().startswith('AWS_ACCESS_KEY_ID=') or \
               line.strip().startswith('AWS_SECRET_ACCESS_KEY=') or \
               line.strip().startswith('AWS_SESSION_TOKEN='):
                print(f"   {line.strip()}")

if __name__ == "__main__":
    print("🔧 Fixing AWS Credentials...")
    fix_aws_credentials()
    print("\n🚀 Next steps:")
    print("1. Run: python3 setup_agent_iam.py")
    print("2. Run: python3 test_iam_configuration.py")
    print("3. Test your agent action again!")
