import json
from memory.redis_memory import r
from rules.aws.ec2_rules import get_ec2_rules

def get_user_preferences(user_id: str) -> dict:
    """
    Fetch user-specific rule overrides from Redis and merge with EC2 rule defaults.
    Redis key: user:{user_id}:prefs
    """
    key = f"user:{user_id}:prefs"
    default_rules = get_ec2_rules()

    try:
        raw = r.get(key)
        if raw:
            overrides = json.loads(raw)
            return {**default_rules, **overrides}
    except Exception as e:
        print(f"[fo.ai] Preference error for {user_id}: {e}")

    return default_rules.copy()
