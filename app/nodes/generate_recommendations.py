
from typing import List, Dict
from datetime import datetime, timedelta

def generate_recommendations(instances: List[Dict], rules: Dict) -> List[Dict]:
    recommendations = []
    skipped_cpu = 0
    skipped_uptime = 0
    skipped_savings = 0
    skipped_tags = 0

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
            skipped_cpu += 1
            continue

        if uptime < rules.get("min_uptime_hours", 24):
            print(f"[SKIP] {instance_id} due to uptime threshold ({uptime} < {rules.get('min_uptime_hours', 24)})")
            skipped_uptime += 1
            continue

        if savings < rules.get("min_savings_usd", 5):
            print(f"[SKIP] {instance_id} due to savings threshold ({savings} < {rules.get('min_savings_usd', 5)})")
            skipped_savings += 1
            continue

        excluded = False
        for tag in tags:
            kv = f"{tag.get('Key')}={tag.get('Value')}"
            if kv in rules.get("excluded_tags", []):
                print(f"[SKIP] {instance_id} due to excluded tag match: {kv}")
                excluded = True
                skipped_tags += 1
                break

        if excluded:
            continue

        instance["Reason"] = f"7-day average CPU is low ({avg_cpu}%)"
        print("Instance Details : ",instance)
        recommendations.append(instance)

    print(f"[RESULT] Final recommendations: {len(recommendations)}")
    print(f"[SUMMARY] Skipped by rules — CPU: {skipped_cpu}, Uptime: {skipped_uptime}, Savings: {skipped_savings}, Tags: {skipped_tags}")
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
    print("--------------------------------------------")
    print(f"[PROMPT] Generated prompt: {prompt}")
    print(f"Recommendations:", recommendations)
    return {"recommendations": recommendations, "prompt": prompt}




#s3 recommendations
def parse_custom_datetime(dt_str: str) -> datetime:
    """Parses custom datetime format: 'August 4, 2025, 15:22:37 (UTC+05:30)'"""
    try:
        return datetime.strptime(dt_str.split(' (')[0], "%B %d, %Y, %H:%M:%S")
    except Exception:
        return datetime.min
    

#give recommendation for adding lifecycle policies to S3 buckets
def generate_s3_recommendations(
    buckets_data: List[Dict],
    rules: Dict
) -> List[Dict]:
    """
    Enriches each bucket dict with recommendation and reason if:
    - Lifecycle policy is missing
    - Last modified exceeds a threshold from rules
    - Tags do not match exclusion list
    """
    excluded_tags = set(rules.get("excluded_tags", []))
    transition_rules = sorted(rules.get("transitions", []), key=lambda r: r["days"], reverse=True)
    now = datetime.now()

    for bucket in buckets_data:
        if "error" in bucket:
            continue 

        bucket_name = bucket.get("BucketName")
        lifecycle_rules = bucket.get("LifecyclePolicies", [])
        last_modified_group = bucket.get("ObjectStatistics", {}).get("LastModifiedByGroup", {})
        tags = bucket.get("BasicInfo", {}).get("Tags", [])

        if tags:
            for tag in tags:
                kv = f"{tag.get('Key')}={tag.get('Value')}"
                if kv in excluded_tags:
                    print(f"[SKIP] {bucket_name} due to excluded tag {kv}")
                    break
            else:
                pass 
        else:
            tags = []

        if lifecycle_rules:
            print(f"[SKIP] {bucket_name} already has lifecycle policy.")
            continue

        max_modified_date = datetime.min
        for _, modified_str in last_modified_group.items():
            modified_dt = parse_custom_datetime(modified_str)
            if modified_dt > max_modified_date:
                max_modified_date = modified_dt

        if max_modified_date == datetime.min:
            print(f"[SKIP] {bucket_name} has no valid last modified timestamps.")
            continue

        days_since_modified = (now - max_modified_date).days

        # Match transition rule
        matched_rule = next(
            (rule for rule in transition_rules if days_since_modified >= rule["days"]),
            None
        )

        if matched_rule:
            bucket["Recommendation"] = {
                "Reason": (
                    f"No lifecycle policy and objects not modified in {days_since_modified} days"
                ),
                "Action": (
                    f"Add a lifecycle rule to transition objects older than {matched_rule['days']} days "
                    f"to {matched_rule['tier']} storage class."
                ),
                "DaysSinceLastModified": days_since_modified
            }

    return [bucket for bucket in buckets_data if "Recommendation" in bucket]
