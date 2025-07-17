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
            print("\nPreferences loaded:", overrides)
            print("\nDefault rules:", default_rules)
            print("\nMerged rules:", {**default_rules, **overrides})
            return {**default_rules, **overrides}
    except Exception as e:
        print(f"[fo.ai] Preference error for {user_id}: {e}")

    return default_rules.copy()

def set_user_preferences(user_id: str, preferences: dict) -> None:
    """
    Save user preferences to Redis in the expected format:
    Key:   user:{user_id}:prefs
    Value: JSON string like {"cpu_threshold": 10, "min_uptime_hours": 0, "min_savings_usd": 0}
    """
    key = f"user:{user_id}:prefs"
    value = json.dumps(preferences)
    r.set(key, value)