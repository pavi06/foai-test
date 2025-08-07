
from typing import List, Dict
from datetime import datetime, timedelta
import json

def generate_recommendations(instances: List[Dict], rules: Dict = None) -> List[Dict]:
    # If no rules provided, get default rules
    if rules is None:
        from memory.preferences import get_user_preferences
        rules = get_user_preferences("default_user")
    
    print(f"\n🎯 [EC2 RECOMMENDATIONS] Starting EC2 cost optimization analysis...")
    print(f"📋 [EC2 RECOMMENDATIONS] Using rules: CPU threshold={rules.get('cpu_threshold', 10)}%, "
          f"Min uptime={rules.get('min_uptime_hours', 24)}h, "
          f"Min savings=${rules.get('min_savings_usd', 5)}")
    
    recommendations = []
    skipped_cpu = 0
    skipped_uptime = 0
    skipped_savings = 0
    skipped_tags = 0
    total_analyzed = 0
    total_savings_potential = 0

    for instance in instances:
        total_analyzed += 1
        instance_id = instance.get("InstanceId")
        instance_type = instance.get("InstanceType", "unknown")
        cpu = instance.get("CurrentCPU", 100)
        avg_cpu = instance.get("AverageCPU", 100)
        uptime = instance.get("UptimeHours", 0)
        monthly_cost = instance.get("estimated_monthly_cost", 0.0)
        savings = instance.get("EstimatedSavings", 0.0)
        savings_reason = instance.get("SavingsReason", "No reason provided")
        tags = instance.get("Tags", [])
        availability_zone = instance.get("AvailabilityZone", "unknown")

        print(f"\n🖥️  [EC2 RECOMMENDATIONS] Analyzing {instance_id} ({instance_type})...")
        print(f"   📊 CPU Usage: Current={cpu}%, 7-day avg={avg_cpu}%")
        print(f"   💰 Monthly Cost: ${monthly_cost:.2f}")
        print(f"   💡 Potential Savings: ${savings:.2f}/month")
        print(f"   🌍 Availability Zone: {availability_zone}")
        print(f"   ⏰ Uptime: {uptime} hours")

        if avg_cpu > rules.get("cpu_threshold", 10):
            print(f"   ❌ [SKIP] CPU threshold exceeded ({avg_cpu}% > {rules.get('cpu_threshold', 10)}%)")
            skipped_cpu += 1
            continue

        if uptime < rules.get("min_uptime_hours", 24):
            print(f"   ❌ [SKIP] Uptime threshold not met ({uptime}h < {rules.get('min_uptime_hours', 24)}h)")
            skipped_uptime += 1
            continue

        if savings < rules.get("min_savings_usd", 5):
            print(f"   ❌ [SKIP] Savings threshold not met (${savings:.2f} < ${rules.get('min_savings_usd', 5)})")
            skipped_savings += 1
            continue

        # Check excluded tags
        excluded = False
        for tag in tags:
            kv = f"{tag.get('Key')}={tag.get('Value')}"
            if kv in rules.get("excluded_tags", []):
                print(f"   ❌ [SKIP] Excluded tag match: {kv}")
                excluded = True
                skipped_tags += 1
                break

        if excluded:
            continue

        # Enhanced recommendation details
        recommendation_details = {
            "InstanceId": instance_id,
            "InstanceType": instance_type,
            "AvailabilityZone": availability_zone,
            "CurrentCPU": cpu,
            "AverageCPU": avg_cpu,
            "MonthlyCost": monthly_cost,
            "EstimatedSavings": savings,
            "SavingsReason": savings_reason,
            "UptimeHours": uptime,
            "Tags": tags,
            "Recommendation": generate_detailed_ec2_recommendation(instance),
            "Priority": "High" if savings > monthly_cost * 0.5 else "Medium" if savings > monthly_cost * 0.25 else "Low"
        }

        recommendations.append(recommendation_details)
        total_savings_potential += savings
        
        print(f"   ✅ [RECOMMENDATION] Added to optimization list")
        print(f"   💡 Priority: {recommendation_details['Priority']}")
        print(f"   📋 Action: {recommendation_details['Recommendation']['Action']}")

    print(f"\n📊 [EC2 RECOMMENDATIONS] Analysis Summary:")
    print(f"   📈 Total instances analyzed: {total_analyzed}")
    print(f"   ✅ Recommendations generated: {len(recommendations)}")
    print(f"   💰 Total savings potential: ${total_savings_potential:.2f}/month")
    print(f"   ❌ Skipped instances:")
    print(f"      - CPU threshold: {skipped_cpu}")
    print(f"      - Uptime threshold: {skipped_uptime}")
    print(f"      - Savings threshold: {skipped_savings}")
    print(f"      - Excluded tags: {skipped_tags}")
    
    return recommendations

def generate_detailed_ec2_recommendation(instance: Dict) -> Dict:
    """Generate detailed recommendation based on instance characteristics"""
    instance_type = instance.get("InstanceType", "")
    avg_cpu = instance.get("AverageCPU", 0)
    monthly_cost = instance.get("estimated_monthly_cost", 0)
    savings = instance.get("EstimatedSavings", 0)
    
    if instance_type.startswith(('t3.', 't2.')) and avg_cpu < 5:
        action = "Stop the instance during non-business hours"
        reason = f"Very low CPU usage ({avg_cpu}%) on T-series instance"
        savings_percentage = (savings / monthly_cost) * 100 if monthly_cost > 0 else 0
        impact = "High" if savings_percentage > 50 else "Medium"
    elif avg_cpu < 15:
        action = "Downsize to smaller instance type"
        reason = f"Low CPU usage ({avg_cpu}%) indicates over-provisioning"
        impact = "High"
    elif avg_cpu < 30:
        action = "Consider downsizing to smaller instance type"
        reason = f"Moderate CPU usage ({avg_cpu}%) - potential for optimization"
        impact = "Medium"
    else:
        action = "Monitor usage patterns"
        reason = f"CPU usage ({avg_cpu}%) is within normal range"
        impact = "Low"
    
    return {
        "Action": action,
        "Reason": reason,
        "Impact": impact,
        "EstimatedSavings": savings,
        "SavingsPercentage": (savings / monthly_cost) * 100 if monthly_cost > 0 else 0
    }

def get_recommendations_and_prompt(instances: List[Dict], rules: Dict = None) -> Dict:
    # If no rules provided, get default rules
    if rules is None:
        from memory.preferences import get_user_preferences
        rules = get_user_preferences("default_user")
    
    print(f"\n📝 [EC2 PROMPT] Generating recommendation prompt...")
    
    recommendations = generate_recommendations(instances, rules)
    if not recommendations:
        return {"recommendations": [], "prompt": "No cost-saving recommendations found for EC2 instances at the moment."}

    lines = []
    total_savings = 0
    
    for r in recommendations:
        instance_id = r['InstanceId']
        instance_type = r['InstanceType']
        avg_cpu = r['AverageCPU']
        monthly_cost = r['MonthlyCost']
        savings = r['EstimatedSavings']
        recommendation = r['Recommendation']
        
        total_savings += savings
        
        line = (
            f"Instance {instance_id} ({instance_type}) in {r.get('AvailabilityZone', 'unknown zone')} "
            f"has {avg_cpu}% average CPU usage and costs ${monthly_cost:.2f}/month. "
            f"Recommendation: {recommendation['Action']}. "
            f"Potential savings: ${savings:.2f}/month ({recommendation['SavingsPercentage']:.1f}% reduction)."
        )
        lines.append(line)

    prompt = "\n".join(lines)
    prompt += f"\n\nTotal potential savings across all recommended instances: ${total_savings:.2f}/month."
    
    # Add detailed breakdown for LLM
    prompt += "\n\n**Detailed Breakdown:**\n"
    for i, r in enumerate(recommendations, 1):
        instance_id = r['InstanceId']
        instance_type = r['InstanceType']
        avg_cpu = r['AverageCPU']
        monthly_cost = r['MonthlyCost']
        savings = r['EstimatedSavings']
        recommendation = r['Recommendation']
        
        prompt += f"\n{i}. **Instance {instance_id}** ({instance_type}):\n"
        prompt += f"   - CPU Usage: {avg_cpu}% (7-day average)\n"
        prompt += f"   - Monthly Cost: ${monthly_cost:.2f}\n"
        prompt += f"   - Potential Savings: ${savings:.2f}/month\n"
        prompt += f"   - Recommendation: {recommendation['Action']}\n"
        prompt += f"   - Reason: {recommendation['Reason']}\n"
    
    print(f"📝 [EC2 PROMPT] Generated prompt with {len(recommendations)} recommendations")
    print(f"💰 [EC2 PROMPT] Total savings potential: ${total_savings:.2f}/month")
    
    return {"recommendations": recommendations, "prompt": prompt}

# S3 recommendations
def parse_custom_datetime(dt_str: str) -> datetime:
    """Parses custom datetime format: 'August 4, 2025, 15:22:37 (UTC+05:30)'"""
    try:
        return datetime.strptime(dt_str.split(' (')[0], "%B %d, %Y, %H:%M:%S")
    except Exception:
        return datetime.min

def generate_s3_recommendations(
    buckets_data: List[Dict],
    rules: Dict = None
) -> List[Dict]:
    # If no rules provided, get default rules
    if rules is None:
        from memory.preferences import get_user_preferences
        rules = get_user_preferences("default_user")
    
    print(f"\n🎯 [S3 RECOMMENDATIONS] Starting S3 cost optimization analysis...")
    print(f"📋 [S3 RECOMMENDATIONS] Using rules: Transition days={rules.get('transitions', [])}")
    
    excluded_tags = set(rules.get("excluded_tags", []))
    transition_rules = sorted(rules.get("transitions", []), key=lambda r: r["days"], reverse=True)
    now = datetime.now()
    
    recommendations = []
    total_analyzed = 0
    total_savings_potential = 0

    for bucket in buckets_data:
        total_analyzed += 1
        
        if "error" in bucket:
            print(f"   ❌ [S3 RECOMMENDATIONS] Skipping bucket with error: {bucket.get('error', 'Unknown error')}")
            continue 

        bucket_name = bucket.get("BucketName")
        basic_info = bucket.get("BasicInfo", {})
        lifecycle_rules = bucket.get("LifecyclePolicies", [])
        object_stats = bucket.get("ObjectStatistics", {})
        cost_analysis = bucket.get("CostAnalysis", {})
        tags = basic_info.get("Tags", [])

        print(f"\n🪣 [S3 RECOMMENDATIONS] Analyzing bucket: {bucket_name}")
        print(f"   📊 Total objects: {object_stats.get('TotalObjects', 0):,}")
        print(f"   📊 Total size: {object_stats.get('TotalSizeGB', 0):.2f} GB")
        print(f"   💰 Current monthly cost: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}")
        print(f"   💡 Potential savings: ${cost_analysis.get('PotentialSavings', 0):.2f}/month")

        # Check excluded tags
        excluded = False
        if tags:
            for tag in tags:
                kv = f"{tag.get('Key')}={tag.get('Value')}"
                if kv in excluded_tags:
                    print(f"   ❌ [SKIP] Excluded tag match: {kv}")
                    excluded = True
                    break
            if excluded:
                continue

        # Check if lifecycle policy exists
        if lifecycle_rules:
            print(f"   ✅ [SKIP] Already has {len(lifecycle_rules)} lifecycle policy(ies)")
            continue

        # Analyze last modified dates
        last_modified_group = object_stats.get("LastModifiedByGroup", {})
        max_modified_date = datetime.min
        
        for _, modified_str in last_modified_group.items():
            modified_dt = parse_custom_datetime(modified_str)
            if modified_dt > max_modified_date:
                max_modified_date = modified_dt

        if max_modified_date == datetime.min:
            print(f"   ❌ [SKIP] No valid last modified timestamps found")
            continue

        days_since_modified = (now - max_modified_date).days
        print(f"   📅 Days since last modification: {days_since_modified}")

        # Match transition rule
        matched_rule = next(
            (rule for rule in transition_rules if days_since_modified >= rule["days"]),
            None
        )

        if matched_rule:
            recommendation_details = {
                "BucketName": bucket_name,
                "BasicInfo": basic_info,
                "ObjectStatistics": object_stats,
                "CostAnalysis": cost_analysis,
                "Recommendation": {
                    "Reason": f"No lifecycle policy and objects not modified in {days_since_modified} days",
                    "Action": f"Add lifecycle rule to transition objects older than {matched_rule['days']} days to {matched_rule['tier']} storage class",
                    "DaysSinceLastModified": days_since_modified,
                    "TargetStorageClass": matched_rule['tier'],
                    "TransitionDays": matched_rule['days'],
                    "Impact": "High" if cost_analysis.get('PotentialSavings', 0) > 10 else "Medium"
                }
            }
            
            recommendations.append(recommendation_details)
            total_savings_potential += cost_analysis.get('PotentialSavings', 0)
            
            print(f"   ✅ [RECOMMENDATION] Added to optimization list")
            print(f"   💡 Impact: {recommendation_details['Recommendation']['Impact']}")
            print(f"   📋 Action: {recommendation_details['Recommendation']['Action']}")
        else:
            print(f"   ⚠️  [SKIP] No matching transition rule for {days_since_modified} days")

    print(f"\n📊 [S3 RECOMMENDATIONS] Analysis Summary:")
    print(f"   📈 Total buckets analyzed: {total_analyzed}")
    print(f"   ✅ Recommendations generated: {len(recommendations)}")
    print(f"   💰 Total savings potential: ${total_savings_potential:.2f}/month")
    
    # Print detailed breakdown for debugging
    print(f"\n📋 [S3 RECOMMENDATIONS] Detailed Breakdown:")
    for i, rec in enumerate(recommendations, 1):
        bucket_name = rec.get("BucketName", "Unknown")
        cost_analysis = rec.get("CostAnalysis", {})
        rec_details = rec.get("Recommendation", {})
        
        print(f"   {i}. {bucket_name}:")
        print(f"      - Current Cost: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month")
        print(f"      - Potential Savings: ${cost_analysis.get('PotentialSavings', 0):.2f}/month")
        print(f"      - Action: {rec_details.get('Action', 'No action')}")
        print(f"      - Days Since Modified: {rec_details.get('DaysSinceLastModified', 0)}")
    
    return recommendations
