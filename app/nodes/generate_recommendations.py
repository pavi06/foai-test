
from typing import List, Dict
from datetime import datetime, timedelta
import json
from app.state import CostState
from memory.preferences import get_user_preferences

def generate_recommendations(instances: List[Dict], rules: Dict = None) -> List[Dict]:
    """Generate EC2 cost optimization recommendations"""
    if rules is None:
        rules = get_user_preferences("default_user")
    
    print(f"[EC2] Starting cost optimization analysis...")
    print(f"[EC2] Rules: CPU threshold={rules.get('cpu_threshold', 10)}%, "
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

        print(f"[EC2] Analyzing {instance_id} ({instance_type})...")
        print(f"  [CPU] Current: {cpu}%, 7-day avg: {avg_cpu}%")
        print(f"  [COST] Monthly: ${monthly_cost:.2f}")
        print(f"  [SAVINGS] Potential: ${savings:.2f}/month")
        print(f"  [ZONE] {availability_zone}, Uptime: {uptime}h")

        # Check CPU threshold
        if avg_cpu > rules.get("cpu_threshold", 10):
            print(f"  [SKIP] CPU threshold exceeded ({avg_cpu}% > {rules.get('cpu_threshold', 10)}%)")
            skipped_cpu += 1
            continue

        # Check uptime threshold
        if uptime < rules.get("min_uptime_hours", 24):
            print(f"  [SKIP] Uptime threshold not met ({uptime}h < {rules.get('min_uptime_hours', 24)}h)")
            skipped_uptime += 1
            continue

        # Check savings threshold
        min_savings_threshold = rules.get("min_savings_usd", 5)
        if savings < min_savings_threshold:
            if avg_cpu < 10:
                print(f"  [OVERRIDE] Low savings (${savings:.2f}) but low CPU ({avg_cpu}%) - including recommendation")
            else:
                print(f"  [SKIP] Savings threshold not met (${savings:.2f} < ${min_savings_threshold})")
                skipped_savings += 1
                continue

        # Check excluded tags
        excluded = False
        for tag in tags:
            kv = f"{tag.get('Key')}={tag.get('Value')}"
            if kv in rules.get("excluded_tags", []):
                print(f"  [SKIP] Excluded tag match: {kv}")
                excluded = True
                skipped_tags += 1
                break

        if excluded:
            continue

        # Create recommendation details
        recommendation_details = {
            "InstanceId": instance_id,
            "InstanceType": instance_type,
            "AvailabilityZone": availability_zone,
            "CurrentCPU": cpu,
            "AverageCPU": avg_cpu,
            "estimated_monthly_cost": monthly_cost,
            "EstimatedSavings": savings,
            "SavingsReason": savings_reason,
            "UptimeHours": uptime,
            "Tags": tags,
            "Recommendation": generate_detailed_ec2_recommendation(instance),
            "Priority": "High" if savings > monthly_cost * 0.5 else "Medium" if savings > monthly_cost * 0.25 else "Low"
        }

        recommendations.append(recommendation_details)
        total_savings_potential += savings
        
        print(f"  [RECOMMENDATION] Added to optimization list")
        print(f"  [PRIORITY] {recommendation_details['Priority']}")
        print(f"  [ACTION] {recommendation_details['Recommendation']['Action']}")

    # Sort and limit to top 5 recommendations
    recommendations.sort(key=lambda x: x.get("EstimatedSavings", 0), reverse=True)
    recommendations = recommendations[:5]
    
    print(f"\n[EC2] Analysis Summary:")
    print(f"  [INFO] Total instances analyzed: {total_analyzed}")
    print(f"  [SUCCESS] Top {len(recommendations)} recommendations generated")
    print(f"  [SAVINGS] Total potential: ${total_savings_potential:.2f}/month")
    print(f"  [SKIPPED] CPU threshold: {skipped_cpu}, Uptime: {skipped_uptime}, Savings: {skipped_savings}, Tags: {skipped_tags}")
    
    return recommendations

def generate_detailed_ec2_recommendation(instance: Dict) -> Dict:
    """Generate detailed recommendation based on instance characteristics"""
    instance_type = instance.get("InstanceType", "")
    avg_cpu = instance.get("AverageCPU", 0)
    monthly_cost = instance.get("estimated_monthly_cost", 0)
    savings = instance.get("EstimatedSavings", 0)
    
    # Estimate savings for very low CPU instances
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
    """Generate recommendations and format them for LLM prompt"""
    if rules is None:
        rules = get_user_preferences("default_user")
    
    print(f"[EC2] Generating detailed recommendation prompt...")
    
    recommendations = generate_recommendations(instances, rules)
    if not recommendations:
        return {"recommendations": [], "prompt": "No cost-saving recommendations found for EC2 instances at the moment."}

    # Calculate total savings
    total_savings = sum(r.get('EstimatedSavings', 0) for r in recommendations)
    
    # Create detailed prompt in key points format
    prompt_lines = []
    prompt_lines.append(f"## **EC2 Cost Optimization Analysis - Top {len(recommendations)} Recommendations**")
    prompt_lines.append(f"")
    prompt_lines.append(f"**Total Potential Monthly Savings: ${total_savings:.2f}**")
    prompt_lines.append(f"")
    prompt_lines.append(f"**Key Points:**")
    prompt_lines.append(f"")
    
    # Add key points for each instance
    for i, r in enumerate(recommendations, 1):
        instance_id = r['InstanceId']
        instance_type = r['InstanceType']
        availability_zone = r.get('AvailabilityZone', 'unknown')
        avg_cpu = r['AverageCPU']
        current_cpu = r['CurrentCPU']
        monthly_cost = r['estimated_monthly_cost']
        savings = r['EstimatedSavings']
        uptime_hours = r.get('UptimeHours', 0)
        recommendation = r['Recommendation']
        priority = r.get('Priority', 'Medium')
        instance_type_details = r.get('InstanceTypeDetails', {})
        
        prompt_lines.append(f"• **Instance {instance_id}** ({instance_type}) in {availability_zone}:")
        if instance_type_details:
            prompt_lines.append(f"  - **Instance Type Details:** {instance_type_details.get('Family', 'Unknown')} Family - {instance_type_details.get('Description', 'Unknown')}")
            prompt_lines.append(f"  - **Specifications:** {instance_type_details.get('vCPU', 'Unknown')} vCPU, {instance_type_details.get('Memory', 'Unknown')} RAM, {instance_type_details.get('Network', 'Unknown')} Network")
        prompt_lines.append(f"  - Current CPU: {current_cpu}%, 7-day average: {avg_cpu}%")
        prompt_lines.append(f"  - Monthly cost: ${monthly_cost:.2f}, Potential savings: ${savings:.2f}")
        prompt_lines.append(f"  - Uptime: {uptime_hours} hours, Priority: {priority}")
        prompt_lines.append(f"  - **Action:** {recommendation['Action']}")
        prompt_lines.append(f"  - **Reason:** {recommendation['Reason']}")
        prompt_lines.append(f"  - **Impact:** {recommendation['Impact']}")
        
        # Add tags if available
        tags = r.get('Tags', [])
        if tags:
            tag_str = ", ".join([f"{tag.get('Key')}={tag.get('Value')}" for tag in tags])
            prompt_lines.append(f"  - **Tags:** {tag_str}")
        prompt_lines.append(f"")
    
    prompt = "\n".join(prompt_lines)
    
    print(f"[EC2] Generated detailed prompt with {len(recommendations)} recommendations")
    print(f"[EC2] Total savings potential: ${total_savings:.2f}/month")
    
    return {"recommendations": recommendations, "prompt": prompt}

def parse_custom_datetime(dt_str: str) -> datetime:
    """Parse custom datetime format: 'August 4, 2025, 15:22:37 (UTC+05:30)'"""
    try:
        dt_part = dt_str.split(' (')[0]
        parsed_dt = datetime.strptime(dt_part, "%B %d, %Y, %H:%M:%S")
        print(f"  [PARSE] Successfully parsed '{dt_str}' -> {parsed_dt}")
        return parsed_dt
    except Exception as e:
        print(f"  [PARSE ERROR] Could not parse datetime '{dt_str}': {e}")
        return datetime.min

def generate_s3_recommendations_legacy(buckets_data: List[Dict], rules: Dict = None) -> List[Dict]:
    """Generate S3 recommendations from bucket data and rules"""
    if rules is None:
        rules = get_user_preferences("default_user")
    
    print(f"[S3] Starting cost optimization analysis...")
    print(f"[S3] Transition rules: {rules.get('transitions', [])}")
    print(f"[S3] Excluded tags: {rules.get('excluded_tags', [])}")
    
    excluded_tags = set(rules.get("excluded_tags", []))
    transition_rules = sorted(rules.get("transitions", []), key=lambda r: r["days"], reverse=True)
    now = datetime.now().date()

    recommendations = []
    total_analyzed = 0
    total_savings_potential = 0
    excluded_buckets = 0
    skipped_buckets = 0
    skipped_lifecycle_buckets = 0
    skipped_storage_class_buckets = 0

    print(f"[S3] Analyzing {len(buckets_data)} buckets for optimization opportunities...")

    for bucket in buckets_data:
        total_analyzed += 1
        
        if "error" in bucket:
            print(f"  [SKIP] Bucket with error: {bucket.get('error', 'Unknown error')}")
            skipped_buckets += 1
            continue 

        bucket_name = bucket.get("BucketName")
        basic_info = bucket.get("BasicInfo", {})
        lifecycle_rules = bucket.get("LifecyclePolicies", [])
        object_stats = bucket.get("ObjectStatistics", {})
        cost_analysis = bucket.get("CostAnalysis", {})
        tags = basic_info.get("Tags", [])

        print(f"[S3] Analyzing bucket: {bucket_name}")
        print(f"  [INFO] Objects: {object_stats.get('TotalObjects', 0):,}, Size: {object_stats.get('TotalSizeGB', 0):.2f} GB")
        print(f"  [COST] Current: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month")
        print(f"  [SAVINGS] Potential: ${cost_analysis.get('PotentialSavings', 0):.2f}/month")

        # Check excluded tags
        excluded = False
        if tags:
            for tag in tags:
                kv = f"{tag.get('Key')}={tag.get('Value')}"
                if kv in excluded_tags:
                    print(f"  [EXCLUDED] Bucket has excluded tag: {kv}")
                    excluded = True
                    excluded_buckets += 1
                    break
            if excluded:
                continue

        # Check if lifecycle policy already exists
        if lifecycle_rules:
            print(f"  [SKIP] Bucket already has {len(lifecycle_rules)} lifecycle policy(ies)")
            skipped_lifecycle_buckets += 1
            continue

        # Check current storage class distribution
        size_by_storage_class = object_stats.get("SizeByStorageClass", {})
        objects_by_storage_class = object_stats.get("ObjectsByStorageClass", {})
        
        print(f"  [STORAGE] Current storage class distribution:")
        for storage_class, count in objects_by_storage_class.items():
            size_gb = size_by_storage_class.get(storage_class, 0) / (1024**3)
            print(f"    - {storage_class}: {count:,} objects, {size_gb:.2f} GB")
        
        # Check if objects are already in cost-optimized storage classes
        cost_optimized_classes = {'STANDARD_IA', 'ONEZONE_IA', 'GLACIER', 'DEEP_ARCHIVE', 'INTELLIGENT_TIERING'}
        has_standard_objects = size_by_storage_class.get('STANDARD', 0) > 0
        has_cost_optimized_objects = any(size_by_storage_class.get(sc, 0) > 0 for sc in cost_optimized_classes)
        
        if not has_standard_objects:
            if has_cost_optimized_objects:
                print(f"  [SKIP] Objects already in cost-optimized storage classes")
                skipped_storage_class_buckets += 1
                continue
            else:
                print(f"  [SKIP] No objects or unknown storage classes")
                skipped_buckets += 1
                continue
        
        if has_cost_optimized_objects:
            print(f"  [MIXED] Bucket has both STANDARD and cost-optimized objects")
        
        print(f"  [TARGET] Focusing on STANDARD objects for lifecycle policy recommendations")

        # Analyze last modified dates
        last_modified_group = object_stats.get("LastModifiedByGroup", {})
        most_recent_modified_date = datetime.min
        
        print(f"  [DATE] Analyzing last modified dates...")
        for group_name, modified_str in last_modified_group.items():
            modified_dt = parse_custom_datetime(modified_str)
            if modified_dt > most_recent_modified_date:
                most_recent_modified_date = modified_dt
            print(f"    - {group_name}: {modified_str} ({modified_dt.strftime('%Y-%m-%d')})")

        if most_recent_modified_date == datetime.min:
            print(f"  [SKIP] No valid last modified timestamps found")
            skipped_buckets += 1
            continue

        # Calculate days since last modification
        most_recent_date = most_recent_modified_date.date()
        days_since_last_modified = (now - most_recent_date).days
        print(f"  [DATE] Days since last modification: {days_since_last_modified} (Last modified: {most_recent_date})")

        # Find the most appropriate transition rule
        matched_rule = None
        print(f"  [RULES] Checking transition rules for {days_since_last_modified} days:")
        
        for rule in transition_rules:
            rule_days = rule["days"]
            rule_tier = rule["tier"]
            print(f"    - Checking rule: {rule_days} days -> {rule_tier}")
            if days_since_last_modified >= rule_days:
                matched_rule = rule
                print(f"  [MATCH] Found transition rule: {rule_days} days -> {rule_tier}")
                break
            else:
                print(f"    - Skipped: {days_since_last_modified} < {rule_days}")
        
        # Use lowest tier rule if no match
        if not matched_rule and transition_rules:
            lowest_rule = min(transition_rules, key=lambda r: r["days"])
            print(f"  [FALLBACK] Using lowest tier rule: {lowest_rule['days']} days -> {lowest_rule['tier']}")
            matched_rule = lowest_rule

        if matched_rule:
            transition_days = matched_rule['days']
            target_storage_class = matched_rule['tier']
            
            # Get STANDARD object details
            standard_objects_count = objects_by_storage_class.get('STANDARD', 0)
            standard_objects_size_gb = size_by_storage_class.get('STANDARD', 0) / (1024**3)
            
            # Create recommendation based on target storage class
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
            
            print(f"  [RECOMMENDATION] Added bucket to optimization list")
            print(f"  [IMPACT] {impact} (${potential_savings:.2f}/month savings, {savings_percentage:.1f}%)")
            print(f"  [ACTION] {action}")
        else:
            print(f"  [SKIP] Objects too recent for transition (last modified: {days_since_last_modified} days ago)")
            if transition_rules:
                min_days = min(rule['days'] for rule in transition_rules)
                print(f"    Minimum transition period: {min_days} days")
            skipped_buckets += 1

    print(f"\n[S3] Analysis Summary:")
    print(f"  [INFO] Total buckets analyzed: {total_analyzed}")
    print(f"  [SUCCESS] Recommendations generated: {len(recommendations)}")
    print(f"  [EXCLUDED] Buckets (tags): {excluded_buckets}")
    print(f"  [SKIPPED] Lifecycle policies: {skipped_lifecycle_buckets}, Cost-optimized: {skipped_storage_class_buckets}, Other: {skipped_buckets}")
    print(f"  [SAVINGS] Total potential: ${total_savings_potential:.2f}/month")
    
    return recommendations
