# rules/aws/ec2_rules.py

def get_ec2_rules():
    return {
        "cpu_threshold": 10,
        "min_uptime_hours": 24,
        "excluded_tags": ["env=prod", "do-not-touch"],
        "min_savings_usd": 5
    }
