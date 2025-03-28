# app/nodes/generate_recommendations.py

from typing import List

def generate_recommendations(ec2_data: List[dict], rules: dict) -> List[dict]:
    recommendations = []

    for instance in ec2_data:
        instance_id = instance.get("InstanceId")
        instance_type = instance.get("InstanceType")
        cpu = instance.get("CPU", 100)
        uptime = instance.get("UptimeHours", 0)
        cost = instance.get("MonthlyCost", 0)
        tags = instance.get("Tags", [])

        # Rule conditions
        if cpu > rules["cpu_threshold"]:
            continue
        if uptime < rules["min_uptime_hours"]:
            continue

        # Check tag exclusions
        excluded = False
        for tag in tags:
            tag_key = tag.get("Key", "").lower()
            tag_val = tag.get("Value", "").lower()
            if any(ex.lower() in f"{tag_key}={tag_val}" for ex in rules.get("excluded_tags", [])):
                excluded = True
                break
        if excluded:
            continue

        # Estimate savings (mock)
        estimated_savings = round(cost * 0.5, 2)  # 50% savings assumed
        if estimated_savings < rules.get("min_savings_usd", 1):
            continue

        recommendations.append({
            "InstanceId": instance_id,
            "InstanceType": instance_type,
            "Reason": f"Low CPU utilization ({cpu}%) and uptime > {uptime:.1f}h",
            "EstimatedSavings": estimated_savings,
            "Tags": tags,
        })

    return recommendations
