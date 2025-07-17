import os
import boto3
from dotenv import load_dotenv

load_dotenv()  # Load from .env or .envrc

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
ENABLE_TRUSTED_ADVISOR = os.getenv("ENABLE_TRUSTED_ADVISOR", "false").lower() == "true"


def get_boto3_client(service: str, region: str = None):
    """
    Returns a boto3 client for the given AWS service.
    Supports override region (e.g., 'us-west-2').
    """
    try:
        selected_region = region or AWS_REGION
        
        if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN]):
            session = boto3.Session(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                aws_session_token=AWS_SESSION_TOKEN,
                region_name=selected_region
            )
        else:
            session = boto3.Session(region_name=selected_region)

        # Validate credentials
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        if DEBUG:
            print(f"[AWS] Authenticated as: {identity['Arn']}")

        return session.client(service)

    except Exception as e:
        raise RuntimeError(f"[AWS Error] Could not create {service} client: {e}")

