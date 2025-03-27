import os
import boto3
from dotenv import load_dotenv

load_dotenv()  # Load from .env or .envrc

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def get_boto3_client(service: str):
    try:
        # Create session with explicit credentials if provided
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION
            )
        else:
            # Fallback to environment/profile/default credential chain
            session = boto3.Session(region_name=AWS_REGION)

        # Validate by calling STS
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        print(f"[AWS] Authenticated as: {identity['Arn']}")

        return session.client(service)

    except Exception as e:
        raise RuntimeError(f"[AWS Error] Could not create {service} client: {e}")
