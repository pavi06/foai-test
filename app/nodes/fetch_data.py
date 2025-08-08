# this is a router that fetches data from the various cloud cost APIs or can be toggled to use mock data.
import json
from app.state import CostState
from data.aws.settings import ENABLE_TRUSTED_ADVISOR

def fetch_data(state: CostState) -> CostState:
    query_type = state.get("query_type", "general")
    use_mock = state.get("use_mock", False)  # Changed default to False to use real AWS data
    debug = state.get("debug", False)
    region = state.get("region", "us-east-1")
    user_id = state.get("user_id", "default_user")

    if debug:
        print(f"[DEBUG] fetch_data → use_mock={use_mock}, query_type={query_type}, region={region}")

    try:
        if use_mock:
            print(f"🔧 [FETCH_DATA] Using MOCK data for testing")
            if query_type == "ec2":
                with open("data/ec2_instances.json") as f:
                    state["ec2_data"] = json.load(f)
            elif query_type == "s3":
                # Create mock S3 data for testing
                state["s3_data"] = create_mock_s3_data()
            elif query_type == "service":
                with open("data/cost_explorer.json") as f:
                    state["cost_data"] = json.load(f)
            elif query_type == "general":
                # For general queries, fetch both EC2 and S3 data
                with open("data/ec2_instances.json") as f:
                    state["ec2_data"] = json.load(f)
                state["s3_data"] = create_mock_s3_data()
        else:
            print(f"🌐 [FETCH_DATA] Using REAL AWS data")
            # Real AWS API fetch logic (service-specific)
            if query_type == "ec2":
                from data.aws.ec2 import fetch_ec2_instances
                state["ec2_data"] = fetch_ec2_instances(region=region)
            elif query_type == "s3":
                from data.aws.s3 import fetch_s3_data
                state["s3_data"] = fetch_s3_data(region=region)
            elif query_type == "general":
                # For general queries, fetch both EC2 and S3 data
                from data.aws.ec2 import fetch_ec2_instances
                from data.aws.s3 import fetch_s3_data
                state["ec2_data"] = fetch_ec2_instances(region=region)
                state["s3_data"] = fetch_s3_data(region=region)
            else:
                state["response"] = f"No AWS integration implemented for query_type: {query_type}"
    except Exception as e:
        if debug:
            print(f"[ERROR] fetch_data failed: {e}")
        state["response"] = f"Failed to fetch data: {str(e)}"
        
    return state

def create_mock_s3_data():
    """Create mock S3 data for testing S3 recommendations"""
    from datetime import datetime, timedelta
    
    # Create mock data that would trigger S3 recommendations
    now = datetime.now()
    old_date = now - timedelta(days=45)  # Objects not modified in 45 days
    very_old_date = now - timedelta(days=120)  # Objects not modified in 120 days
    
    return [
        {
            "BucketName": "pavi-test-bucket",
            "BasicInfo": {
                "Region": "us-east-1",
                "Versioning": "Enabled",
                "LoggingEnabled": False,
                "EncryptionType": "AES256",
                "Tags": []
            },
            "LifecyclePolicies": [],  # No lifecycle policy - should trigger recommendation
            "ObjectStatistics": {
                "TotalObjects": 1250,
                "TotalSizeGB": 45.7,
                "LastModifiedByGroup": {
                    "recent": str(now - timedelta(days=5)),
                    "old": str(old_date)
                }
            },
            "CostAnalysis": {
                "CurrentMonthlyCost": 12.50,
                "PotentialSavings": 8.75
            }
        },
        {
            "BucketName": "my-storage-bucket",
            "BasicInfo": {
                "Region": "us-east-1",
                "Versioning": "Disabled",
                "LoggingEnabled": True,
                "EncryptionType": "AES256",
                "Tags": []
            },
            "LifecyclePolicies": [],  # No lifecycle policy - should trigger recommendation
            "ObjectStatistics": {
                "TotalObjects": 3200,
                "TotalSizeGB": 89.3,
                "LastModifiedByGroup": {
                    "very_old": str(very_old_date)
                }
            },
            "CostAnalysis": {
                "CurrentMonthlyCost": 24.80,
                "PotentialSavings": 18.60
            }
        },
        {
            "BucketName": "backup-archive-bucket",
            "BasicInfo": {
                "Region": "us-east-1",
                "Versioning": "Enabled",
                "LoggingEnabled": False,
                "EncryptionType": "AES256",
                "Tags": []
            },
            "LifecyclePolicies": [],  # No lifecycle policy - should trigger recommendation
            "ObjectStatistics": {
                "TotalObjects": 8500,
                "TotalSizeGB": 156.2,
                "LastModifiedByGroup": {
                    "very_old": str(very_old_date)
                }
            },
            "CostAnalysis": {
                "CurrentMonthlyCost": 43.20,
                "PotentialSavings": 32.40
            }
        },
        {
            "BucketName": "sow-poc-bucket",
            "BasicInfo": {
                "Region": "us-east-1",
                "Versioning": "Disabled",
                "LoggingEnabled": False,
                "EncryptionType": "AES256",
                "Tags": []
            },
            "LifecyclePolicies": [],  # No lifecycle policy - should trigger recommendation
            "ObjectStatistics": {
                "TotalObjects": 4,  # Actual count from S3 console
                "TotalSizeGB": 0.000371,  # ~371 KB total (142.1 + 83.8 + 145.3 KB)
                "LastModifiedByGroup": {
                    "recent": str(now - timedelta(days=1)),  # Recent modification (June 6, 2025)
                    "very_recent": str(now - timedelta(hours=2))
                }
            },
            "CostAnalysis": {
                "CurrentMonthlyCost": 0.0001,  # Very small cost due to small size
                "PotentialSavings": 0.00005   # Very small savings due to small size
            }
        }
    ]
