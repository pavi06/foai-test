
import boto3
from typing import List, Optional
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import get_cpu_metrics
import json

def fetch_ec2_instances(
    instance_ids: Optional[List[str]] = None,
    region: Optional[str] = None
) -> List[dict]:
    """
    Fetches EC2 instances and their CPU metrics with detailed analysis.
    Filters by instance_ids if provided.
    Uses region override if passed.
    """
    print(f"\n🔍 [EC2] Let me check your EC2 instances...")
    print(f"📍 [EC2] Looking in region: {region or 'default'}")
    print(f"🎯 [EC2] Checking: {instance_ids or 'all your running instances'}")
    
    try:
        ec2 = get_boto3_client("ec2", region=region)
        filters = [{"Name": "instance-state-name", "Values": ["running"]}]

        if instance_ids:
            print(f"📋 [EC2] Getting details for: {instance_ids}")
            response = ec2.describe_instances(InstanceIds=instance_ids)
        else:
            print(f"📋 [EC2] Finding all your running instances...")
            response = ec2.describe_instances(Filters=filters)

        instances = []
        total_instances = 0
        
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                total_instances += 1
                instance_id = instance["InstanceId"]
                instance_type = instance.get("InstanceType", "unknown")
                availability_zone = instance.get("Placement", {}).get("AvailabilityZone", "unknown")
                
                print(f"\n🖥️  [EC2] Looking at instance {instance_id}...")
                print(f"   📊 Type: {instance_type}")
                print(f"   🌍 Zone: {availability_zone}")
                
                # Get CPU metrics
                print(f"   📈 Checking CPU usage for {instance_id}...")
                metrics = get_cpu_metrics(instance_id, region=region)
                
                # Enhanced pricing map with more instance types
                pricing_map = {
                    # T3 instances
                    "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416, "t3.large": 0.0832,
                    "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
                    # T2 instances
                    "t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.0464, "t2.large": 0.0928,
                    # M5 instances
                    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384, "m5.4xlarge": 0.768,
                    "m5.12xlarge": 2.304, "m5.24xlarge": 4.608,
                    # C5 instances
                    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34, "c5.4xlarge": 0.68,
                    "c5.9xlarge": 1.53, "c5.18xlarge": 3.06,
                    # R5 instances
                    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504, "r5.4xlarge": 1.008,
                    "r5.12xlarge": 3.024, "r5.24xlarge": 6.048,
                    # I3 instances
                    "i3.large": 0.156, "i3.xlarge": 0.312, "i3.2xlarge": 0.624, "i3.4xlarge": 1.248,
                    "i3.8xlarge": 2.496, "i3.16xlarge": 4.992,
                }
                
                estimated_hourly_cost = pricing_map.get(instance_type, 0.10)  # Default fallback
                monthly_cost = estimated_hourly_cost * 730  # 730 hours per month
                
                print(f"   💰 Hourly cost: ${estimated_hourly_cost:.4f}")
                print(f"   💰 Monthly cost: ${monthly_cost:.2f}")
                
                # Calculate potential savings based on CPU utilization
                avg_cpu = metrics.get("AverageCPU", 0)
                current_cpu = metrics.get("CurrentCPU", 0)
                
                # Enhanced savings calculation
                if avg_cpu >= 0 and avg_cpu < 10:
                    # Low utilization - potential for downsizing
                    if instance_type.startswith(('t3.', 't2.')):
                        # For T instances, suggest stopping if very low usage
                        potential_savings = monthly_cost * 0.8  # 80% savings if stopped
                        savings_reason = "Very low CPU usage - consider stopping the instance"
                    else:
                        # For other instances, suggest downsizing
                        potential_savings = monthly_cost * 0.4  # 40% savings if downsized
                        savings_reason = "Low CPU usage - consider downsizing to smaller instance type"
                elif avg_cpu >= 10 and avg_cpu < 30:
                    # Medium utilization - potential for downsizing
                    potential_savings = monthly_cost * 0.25  # 25% savings if downsized
                    savings_reason = "Moderate CPU usage - consider downsizing to smaller instance type"
                else:
                    # High utilization - no immediate savings
                    potential_savings = 0.0
                    savings_reason = "High CPU usage - instance appears to be well-utilized"

                print(f"   📊 7-day average CPU: {avg_cpu}%")
                print(f"   📊 Current CPU: {current_cpu}%")
                print(f"   💡 Savings potential: ${potential_savings:.2f}/month")
                print(f"   💡 Reason: {savings_reason}")

                # Extract tags for analysis
                tags = instance.get("Tags", [])
                tag_dict = {tag.get("Key", ""): tag.get("Value", "") for tag in tags}
                
                if tags:
                    print(f"   🏷️  Tags: {json.dumps(tag_dict, indent=6)}")
                else:
                    print(f"   🏷️  No tags found")

                instance_data = {
                    "InstanceId": instance_id,
                    "InstanceType": instance_type,
                    "AvailabilityZone": availability_zone,
                    "Tags": tags,
                    "TagDict": tag_dict,
                    "AverageCPU": avg_cpu,
                    "CurrentCPU": current_cpu,
                    "EstimatedSavings": potential_savings,
                    "SavingsReason": savings_reason,
                    "UptimeHours": metrics.get("UptimeHours", 0),
                    "region": region,
                    "estimated_hourly_cost": estimated_hourly_cost,
                    "estimated_monthly_cost": monthly_cost,
                    "State": instance.get("State", {}).get("Name", "unknown"),
                    "LaunchTime": instance.get("LaunchTime", ""),
                    "Platform": instance.get("Platform", "linux"),
                    "VpcId": instance.get("VpcId", ""),
                    "SubnetId": instance.get("SubnetId", ""),
                    "PrivateIpAddress": instance.get("PrivateIpAddress", ""),
                    "PublicIpAddress": instance.get("PublicIpAddress", ""),
                }

                instances.append(instance_data)
                print(f"   ✅ Instance {instance_id} analysis complete")

        print(f"\n📊 [EC2] Here's what I found:")
        print(f"   📈 Analyzed {total_instances} instances")
        print(f"   💰 Total monthly cost: ${sum(inst.get('estimated_monthly_cost', 0) for inst in instances):.2f}")
        print(f"   💡 Potential savings: ${sum(inst.get('EstimatedSavings', 0) for inst in instances):.2f}")
        print(f"   🎯 {len([inst for inst in instances if inst.get('EstimatedSavings', 0) > 0])} instances could save you money")
        
        return instances
        
    except Exception as e:
        print(f"❌ [EC2] Oops! Something went wrong: {e}")
        return []


# data/aws/ec2.py

from collections import defaultdict
from typing import List, Dict

def summarize_cost_by_region(instances: List[dict]) -> List[dict]:
    """
    Groups EC2 instances by region and calculates total estimated cost per region.

    Returns a sorted list of:
    {
        "region": str,
        "instance_count": int,
        "estimated_hourly_cost": float
    }
    """
    print(f"\n🌍 [EC2] Breaking down costs by region...")
    
    region_summary = defaultdict(lambda: {"instance_count": 0, "estimated_hourly_cost": 0.0, "estimated_monthly_cost": 0.0})

    for inst in instances:
        region = inst.get("region", "unknown")
        hourly_cost = inst.get("estimated_hourly_cost", 0.0)
        monthly_cost = inst.get("estimated_monthly_cost", 0.0)

        region_summary[region]["instance_count"] += 1
        region_summary[region]["estimated_hourly_cost"] += hourly_cost
        region_summary[region]["estimated_monthly_cost"] += monthly_cost

    # Convert to list and sort by cost descending
    result = sorted(
        [{"region": r, **summary} for r, summary in region_summary.items()],
        key=lambda x: x["estimated_monthly_cost"],
        reverse=True
    )
    
    print(f"📊 [EC2] Regional breakdown:")
    for region_data in result:
        print(f"   🌍 {region_data['region']}: {region_data['instance_count']} instances, "
              f"${region_data['estimated_monthly_cost']:.2f}/month")
    
    return result
