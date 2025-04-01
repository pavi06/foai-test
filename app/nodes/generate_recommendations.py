
from typing import List, Dict

def generate_recommendations(instances: List[Dict], rules: Dict) -> List[Dict]:
    recommendations = []

    for instance in instances:
        instance_id = instance.get("InstanceId")
        cpu = instance.get("CurrentCPU", 100)
        avg_cpu = instance.get("AverageCPU", 100)
        uptime = instance.get("UptimeHours", 0)
        cost = instance.get("EstimatedCost", 20.0)
        savings = instance.get("EstimatedSavings", 0.0)
        tags = instance.get("Tags", [])

        print(f"[CHECK] {instance_id} - CPU={cpu} Avg7d={avg_cpu} Uptime={uptime} Tags={tags} Cost={cost} Savings={savings}")

        if avg_cpu > rules.get("cpu_threshold", 10):
            print(f"[SKIP] {instance_id} due to CPU threshold ({avg_cpu} > {rules.get('cpu_threshold', 10)})")
            continue

        if uptime < rules.get("min_uptime_hours", 24):
            print(f"[SKIP] {instance_id} due to uptime threshold ({uptime} < {rules.get('min_uptime_hours', 24)})")
            continue

        if savings < rules.get("min_savings_usd", 5):
            print(f"[SKIP] {instance_id} due to savings threshold ({savings} < {rules.get('min_savings_usd', 5)})")
            continue

        excluded = False
        for tag in tags:
            kv = f"{tag.get('Key')}={tag.get('Value')}"
            if kv in rules.get("excluded_tags", []):
                print(f"[SKIP] {instance_id} due to excluded tag match: {kv}")
                excluded = True
                break

        if excluded:
            continue

        instance["Reason"] = f"7-day average CPU is low ({avg_cpu}%)"
        recommendations.append(instance)

    print(f"[RESULT] Final recommendations: {len(recommendations)}")
    return recommendations

def get_recommendations_and_prompt(instances: List[Dict], rules: Dict) -> Dict:
    recommendations = generate_recommendations(instances, rules)
    if not recommendations:
        return {"recommendations": [], "prompt": "No cost-saving recommendations at the moment."}

    lines = []
    for r in recommendations:
        line = (
            f"Instance {r['InstanceId']} (type {r.get('InstanceType')}) in "
            f"{r.get('AvailabilityZone', 'unknown zone')} has avg CPU {r.get('AverageCPU')}%, "
            f"estimated savings: ${r.get('EstimatedSavings', 0.0):.2f}."
        )
        lines.append(line)

    prompt = "\n".join(lines)
    return {"recommendations": recommendations, "prompt": prompt}
