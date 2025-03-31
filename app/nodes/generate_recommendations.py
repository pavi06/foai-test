from typing import List, Dict


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


def format_recommendations_as_prompt(recommendations: List[dict]) -> str:
    """Convert recommendations into a prompt suitable for LLM summarization."""
    if not recommendations:
        return "There are no cost-saving opportunities for the selected EC2 instances."

    lines = [
        "Summarize the following EC2 cost optimization findings in plain English:\n"
    ]

    for rec in recommendations:
        line = (
            f"- Instance {rec['InstanceId']} ({rec['InstanceType']}): "
            f"{rec['Reason']}, estimated monthly savings of ${rec['EstimatedSavings']}"
        )
        lines.append(line)

    return "\n".join(lines)


def get_recommendations_and_prompt(
    ec2_data: List[dict], rules: dict
) -> Dict[str, object]:
    """Return both structured recommendations and a formatted LLM prompt."""
    recs = generate_recommendations(ec2_data, rules)
    prompt = format_recommendations_as_prompt(recs)
    return {
        "structured": recs,
        "prompt": prompt,
    }