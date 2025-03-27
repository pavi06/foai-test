# This file contains the logic to fetch Trusted Advisor data from AWS
# It is not yet implemented, but will be in the future

from data.aws.settings import ENABLE_TRUSTED_ADVISOR
from data.aws.settings import DEBUG


def fetch_trusted_advisor() -> dict:
    if not ENABLE_TRUSTED_ADVISOR:
        if DEBUG:
            print("[DEBUG] Trusted Advisor is disabled via .env")
        return {}

    # Future implementation:
    print("[WARN] Trusted Advisor integration not yet implemented")
    return {}
