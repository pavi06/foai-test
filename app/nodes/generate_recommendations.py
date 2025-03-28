from typing import List

def generate_recommendations(ec2_data: List[dict], rules: dict) -> List[dict]:
    recommendations = []

    for instance in ec2_data:
        instance_id = instance.get("InstanceId")
        instance_type = instance.get("InstanceType")
        cpu = instance.get("CPU", 100)
        avg_cpu = instance.get("CPU7dAvg", 100)
        uptime = instance.get("UptimeHours", 0)
        cost = instance.get("MonthlyCost", 0)
        tags = instance.get("Tags", [])

        if uptime < rules["min_uptime_hours"]:
            continue

        if any(
            f"{tag.get('Key', '').lower()}={tag.get('Value', '').lower()}"
            in [ex.lower() for ex in rules.get("excluded_tags", [])]
            for tag in tags
        ):
            continue

        if avg_cpu <= rules["idle_7day_cpu_threshold"]:
            estimated_savings = round(cost * 0.5, 2)
            if estimated_savings >= rules["min_savings_usd"]:
                recommendations.append({
                    "InstanceId": instance_id,
                    "InstanceType": instance_type,
                    "Reason": f"7-day average CPU is low ({avg_cpu}%)",
                    "EstimatedSavings": estimated_savings,
                    "Tags": tags
                })
            continue

        if cpu <= rules["cpu_threshold"]:
            estimated_savings = round(cost * 0.4, 2)
            if estimated_savings >= rules["min_savings_usd"]:
                recommendations.append({
                    "InstanceId": instance_id,
                    "InstanceType": instance_type,
                    "Reason": f"Low point-in-time CPU utilization ({cpu}%)",
                    "EstimatedSavings": estimated_savings,
                    "Tags": tags,
                })

    return recommendations
