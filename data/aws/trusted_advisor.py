from data.aws.settings import ENABLE_TRUSTED_ADVISOR

def fetch_trusted_advisor() -> dict:
    if not ENABLE_TRUSTED_ADVISOR:
        print("[DEBUG] Trusted Advisor is disabled via .env")
        return {}

    print("[DEBUG] Trusted Advisor integration enabled — returning stub data")

    return {
        "Underutilized EC2 Instances": {
            "count": 2,
            "estimated_monthly_savings": 47.12,
            "recommendation": "Review EC2 usage — some are idle or underused."
        },
        "Unattached EBS Volumes": {
            "count": 4,
            "estimated_monthly_savings": 16.89,
            "recommendation": "Delete unused EBS volumes to reduce storage costs."
        }
    }
