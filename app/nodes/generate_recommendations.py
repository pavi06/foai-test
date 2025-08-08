
from typing import List, Dict
from datetime import datetime, timedelta
import json
from app.state import CostState
from memory.preferences import get_user_preferences

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

        # More lenient savings threshold for instances with very low CPU usage
        min_savings_threshold = rules.get("min_savings_usd", 5)
        if savings < min_savings_threshold:
            # Special case: If CPU usage is very low (< 10%) but savings are low, still recommend
            if avg_cpu < 10:
                print(f"   ⚠️  [OVERRIDE] Low savings (${savings:.2f}) but low CPU ({avg_cpu}%) - including recommendation")
            else:
                print(f"   ❌ [SKIP] Savings threshold not met (${savings:.2f} < ${min_savings_threshold})")
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
    
    # If savings is 0 but CPU is low, estimate savings as full monthly cost for stopping
    if savings == 0 and avg_cpu < 10 and monthly_cost > 0:
        savings = monthly_cost
    
    if instance_type.startswith(('t3.', 't2.')) and avg_cpu < 10:
        action = "Stop the instance during non-business hours"
        reason = f"Very low CPU usage ({avg_cpu}%) on T-series instance"
        impact = "High"
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
    
    savings_percentage = (savings / monthly_cost) * 100 if monthly_cost > 0 else 0
    
    return {
        "Action": action,
        "Reason": reason,
        "Impact": impact,
        "EstimatedSavings": savings,
        "SavingsPercentage": savings_percentage
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
        prompt += f"   - Impact: {recommendation['Impact']}\n"
        prompt += "So based on the given data, analyse everything and give  a proper recommendation details along with the reason and the instance details with id for proper understanding."
    
    print(f"📝 [EC2 PROMPT] Generated prompt with {len(recommendations)} recommendations")
    print(f"💰 [EC2 PROMPT] Total savings potential: ${total_savings:.2f}/month")
    
    return {"recommendations": recommendations, "prompt": prompt}

# S3 recommendations
def parse_custom_datetime(dt_str: str) -> datetime:
    """Parses custom datetime format: 'August 4, 2025, 15:22:37 (UTC+05:30)'"""
    try:
        # Remove timezone info and parse
        dt_part = dt_str.split(' (')[0]
        parsed_dt = datetime.strptime(dt_part, "%B %d, %Y, %H:%M:%S")
        print(f"      🔍 [PARSE] Successfully parsed '{dt_str}' -> {parsed_dt}")
        return parsed_dt
    except Exception as e:
        print(f"   ⚠️  [PARSE ERROR] Could not parse datetime '{dt_str}': {e}")
        return datetime.min

def generate_s3_recommendations_legacy(buckets_data: List[Dict], rules: Dict = None) -> List[Dict]:
    """Legacy function for API compatibility - generates S3 recommendations from bucket data and rules"""
    # If no rules provided, get default rules
    if rules is None:
        rules = get_user_preferences("default_user")
    
    print(f"\n🎯 [S3 RECOMMENDATIONS] Starting intelligent S3 cost optimization analysis...")
    print(f"📋 [S3 RECOMMENDATIONS] Using transition rules: {rules.get('transitions', [])}")
    print(f"🚫 [S3 RECOMMENDATIONS] Excluded tags: {rules.get('excluded_tags', [])}")
    
    excluded_tags = set(rules.get("excluded_tags", []))
    transition_rules = sorted(rules.get("transitions", []), key=lambda r: r["days"], reverse=True)
    now = datetime.now().date()  # Use date only for accurate day calculation

    print(f"---------Stream: Rules Final------------: {transition_rules}")
    
    recommendations = []
    total_analyzed = 0
    total_savings_potential = 0
    excluded_buckets = 0
    skipped_buckets = 0
    skipped_lifecycle_buckets = 0
    skipped_storage_class_buckets = 0

    print(f"\n📊 [S3 RECOMMENDATIONS] Analyzing {len(buckets_data)} buckets for optimization opportunities...")

    for bucket in buckets_data:
        total_analyzed += 1
        
        if "error" in bucket:
            print(f"   ❌ [S3 RECOMMENDATIONS] Skipping bucket with error: {bucket.get('error', 'Unknown error')}")
            skipped_buckets += 1
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

        # Check excluded tags first
        excluded = False
        if tags:
            tag_list = [f"{t.get('Key')}={t.get('Value')}" for t in tags]
            print(f"   🏷️  Checking tags: {tag_list}")
            for tag in tags:
                kv = f"{tag.get('Key')}={tag.get('Value')}"
                if kv in excluded_tags:
                    print(f"   ❌ [EXCLUDED] Bucket '{bucket_name}' has excluded tag: {kv}")
                    excluded = True
                    excluded_buckets += 1
                    break
            if excluded:
                continue

        # Check if lifecycle policy already exists
        if lifecycle_rules:
            print(f"   ✅ [SKIP] Bucket '{bucket_name}' already has {len(lifecycle_rules)} lifecycle policy(ies)")
            skipped_lifecycle_buckets += 1
            continue

        # Check current storage class distribution
        size_by_storage_class = object_stats.get("SizeByStorageClass", {})
        objects_by_storage_class = object_stats.get("ObjectsByStorageClass", {})
        
        print(f"   📦 [STORAGE CLASS] Current storage class distribution:")
        for storage_class, count in objects_by_storage_class.items():
            size_gb = size_by_storage_class.get(storage_class, 0) / (1024**3)
            print(f"      - {storage_class}: {count:,} objects, {size_gb:.2f} GB")
        
        # Check if objects are already in cost-optimized storage classes
        cost_optimized_classes = {'STANDARD_IA', 'ONEZONE_IA', 'GLACIER', 'DEEP_ARCHIVE', 'INTELLIGENT_TIERING'}
        has_standard_objects = size_by_storage_class.get('STANDARD', 0) > 0
        has_cost_optimized_objects = any(size_by_storage_class.get(sc, 0) > 0 for sc in cost_optimized_classes)
        
        if not has_standard_objects:
            if has_cost_optimized_objects:
                print(f"   ✅ [SKIP] Bucket '{bucket_name}' objects are already in cost-optimized storage classes")
                print(f"      - No STANDARD objects found, objects are already optimized")
                skipped_storage_class_buckets += 1
                continue
            else:
                print(f"   ⚠️  [SKIP] Bucket '{bucket_name}' has no objects or unknown storage classes")
                skipped_buckets += 1
                continue
        
        # If we have STANDARD objects, check if they're mixed with cost-optimized objects
        if has_cost_optimized_objects:
            print(f"   📊 [MIXED] Bucket '{bucket_name}' has both STANDARD and cost-optimized objects")
            print(f"      - Will recommend transitions for STANDARD objects only")
        
        print(f"   🎯 [TARGET] Focusing on STANDARD objects for lifecycle policy recommendations")

        # Analyze last modified dates to find the most recent modification
        last_modified_group = object_stats.get("LastModifiedByGroup", {})
        most_recent_modified_date = datetime.min
        
        print(f"   📅 Analyzing last modified dates...")
        for group_name, modified_str in last_modified_group.items():
            modified_dt = parse_custom_datetime(modified_str)
            if modified_dt > most_recent_modified_date:
                most_recent_modified_date = modified_dt
            print(f"      - {group_name}: {modified_str} ({modified_dt.strftime('%Y-%m-%d')})")

        if most_recent_modified_date == datetime.min:
            print(f"   ❌ [SKIP] No valid last modified timestamps found for bucket '{bucket_name}'")
            skipped_buckets += 1
            continue

        # Calculate days since last modification using date only
        most_recent_date = most_recent_modified_date.date()
        days_since_last_modified = (now - most_recent_date).days
        print(f"   📅 Days since last modification: {days_since_last_modified} (Last modified: {most_recent_date})")

        # Find the most appropriate transition rule based on last modification
        matched_rule = None
        print(f"   🎯 [RULES] Checking transition rules for {days_since_last_modified} days:")
        print(f"   🎯 [RULES] Available rules (sorted by days descending): {transition_rules}")
        
        # Find the highest tier (most cost-effective) that the bucket qualifies for
        # Rules are sorted by days descending (180, 90, 30), so we want the first match
        for rule in transition_rules:
            rule_days = rule["days"]
            rule_tier = rule["tier"]
            print(f"      - Checking rule: {rule_days} days -> {rule_tier}")
            if days_since_last_modified >= rule_days:
                matched_rule = rule
                print(f"   🎯 [MATCH] Found transition rule: {rule_days} days -> {rule_tier}")
                print(f"   🎯 [MATCH] Bucket qualifies for {rule_tier} (last modified {days_since_last_modified} days ago)")
                break  # Use the first (highest tier) rule that matches
            else:
                print(f"      - Skipped: {days_since_last_modified} < {rule_days}")
        
        # If no rule matched, use the lowest tier rule
        if not matched_rule and transition_rules:
            lowest_rule = min(transition_rules, key=lambda r: r["days"])
            print(f"   🎯 [FALLBACK] Using lowest tier rule: {lowest_rule['days']} days -> {lowest_rule['tier']}")
            matched_rule = lowest_rule

        if matched_rule:
            transition_days = matched_rule['days']
            target_storage_class = matched_rule['tier']
            
            # Get STANDARD object details for more specific recommendations
            standard_objects_count = objects_by_storage_class.get('STANDARD', 0)
            standard_objects_size_gb = size_by_storage_class.get('STANDARD', 0) / (1024**3)
            
            # Create intelligent recommendation based on actual data
            if target_storage_class == "IA":
                action = f"Add lifecycle rule to transition STANDARD objects older than {transition_days} days to Infrequent Access (IA) storage class"
                reason = f"Bucket '{bucket_name}' has {standard_objects_count:,} STANDARD objects ({standard_objects_size_gb:.2f} GB) that haven't been modified in {days_since_last_modified} days. Based on your preferences, STANDARD objects older than {transition_days} days should be moved to IA storage for cost optimization."
            elif target_storage_class == "Glacier":
                action = f"Add lifecycle rule to transition STANDARD objects older than {transition_days} days to Glacier storage class"
                reason = f"Bucket '{bucket_name}' has {standard_objects_count:,} STANDARD objects ({standard_objects_size_gb:.2f} GB) that haven't been modified in {days_since_last_modified} days. Based on your preferences, STANDARD objects older than {transition_days} days should be archived to Glacier storage for significant cost savings."
            elif target_storage_class == "Deep Archive":
                action = f"Add lifecycle rule to transition STANDARD objects older than {transition_days} days to Deep Archive storage class"
                reason = f"Bucket '{bucket_name}' has {standard_objects_count:,} STANDARD objects ({standard_objects_size_gb:.2f} GB) that haven't been modified in {days_since_last_modified} days. Based on your preferences, STANDARD objects older than {transition_days} days should be moved to Deep Archive storage for maximum cost optimization."
            else:
                action = f"Add lifecycle rule to transition STANDARD objects older than {transition_days} days to {target_storage_class} storage class"
                reason = f"Bucket '{bucket_name}' has {standard_objects_count:,} STANDARD objects ({standard_objects_size_gb:.2f} GB) that haven't been modified in {days_since_last_modified} days. Based on your preferences, STANDARD objects older than {transition_days} days should be moved to {target_storage_class} storage."
            
            # Calculate impact based on savings percentage
            current_cost = cost_analysis.get('CurrentMonthlyCost', 0)
            potential_savings = cost_analysis.get('PotentialSavings', 0)
            savings_percentage = (potential_savings / current_cost * 100) if current_cost > 0 else 0
            
            if savings_percentage > 50:
                impact = "High"
            elif savings_percentage > 25:
                impact = "Medium"
            else:
                impact = "Low"
            
            recommendation_details = {
                "BucketName": bucket_name,
                "BasicInfo": basic_info,
                "ObjectStatistics": object_stats,
                "CostAnalysis": cost_analysis,
                "Recommendation": {
                    "Reason": reason,
                    "Action": action,
                    "DaysSinceLastModified": days_since_last_modified,
                    "TargetStorageClass": target_storage_class,
                    "TransitionDays": transition_days,
                    "Impact": impact,
                    "CurrentStorageClass": "STANDARD",
                    "EstimatedMonthlySavings": potential_savings,
                    "CurrentMonthlyCost": current_cost,
                    "SavingsPercentage": savings_percentage,
                    "TotalObjects": object_stats.get('TotalObjects', 0),
                    "TotalSizeGB": object_stats.get('TotalSizeGB', 0),
                    "LastModifiedDate": most_recent_date.strftime('%Y-%m-%d'),
                    "StandardObjectsCount": standard_objects_count,
                    "StandardObjectsSizeGB": standard_objects_size_gb,
                    "CurrentStorageClassDistribution": objects_by_storage_class
                }
            }
            
            recommendations.append(recommendation_details)
            total_savings_potential += potential_savings
            
            print(f"   ✅ [RECOMMENDATION] Added bucket '{bucket_name}' to optimization list")
            print(f"   💡 Impact: {impact} (${potential_savings:.2f}/month savings, {savings_percentage:.1f}%)")
            print(f"   📋 Action: {action}")
        else:
            print(f"   ⚠️  [SKIP] Bucket '{bucket_name}' objects are too recent for transition (last modified: {days_since_last_modified} days ago)")
            if transition_rules:
                min_days = min(rule['days'] for rule in transition_rules)
                print(f"      Minimum transition period: {min_days} days")
            skipped_buckets += 1

    print(f"\n📊 [S3 RECOMMENDATIONS] Intelligent Analysis Summary:")
    print(f"   📈 Total buckets analyzed: {total_analyzed}")
    print(f"   ✅ Recommendations generated: {len(recommendations)}")
    print(f"   ❌ Excluded buckets (tags): {excluded_buckets}")
    print(f"   ⚠️  Skipped buckets:")
    print(f"      - Already have lifecycle policies: {skipped_lifecycle_buckets}")
    print(f"      - Already in cost-optimized storage: {skipped_storage_class_buckets}")
    print(f"      - Other reasons (recent/no data): {skipped_buckets}")
    print(f"   💰 Total savings potential: ${total_savings_potential:.2f}/month")
    
    # Print detailed breakdown for debugging
    print(f"\n📋 [S3 RECOMMENDATIONS] Detailed Bucket Analysis:")
    for i, rec in enumerate(recommendations, 1):
        bucket_name = rec.get("BucketName", "Unknown")
        cost_analysis = rec.get("CostAnalysis", {})
        rec_details = rec.get("Recommendation", {})
        
        print(f"   {i}. Bucket: '{bucket_name}'")
        print(f"      - Size: {rec_details.get('TotalSizeGB', 0):.2f} GB, Objects: {rec_details.get('TotalObjects', 0):,}")
        print(f"      - STANDARD objects: {rec_details.get('StandardObjectsCount', 0):,} ({rec_details.get('StandardObjectsSizeGB', 0):.2f} GB)")
        print(f"      - Current Cost: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month")
        print(f"      - Potential Savings: ${cost_analysis.get('PotentialSavings', 0):.2f}/month ({rec_details.get('SavingsPercentage', 0):.1f}%)")
        print(f"      - Days since last modification: {rec_details.get('DaysSinceLastModified', 0)}")
        print(f"      - Recommended transition: {rec_details.get('TransitionDays', 0)} days → {rec_details.get('TargetStorageClass', 'Unknown')}")
        print(f"      - Impact: {rec_details.get('Impact', 'Unknown')}")
        
        # Show storage class distribution
        storage_dist = rec_details.get('CurrentStorageClassDistribution', {})
        if storage_dist:
            print(f"      - Storage class distribution: {storage_dist}")
    
    return recommendations
