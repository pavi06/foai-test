
import boto3
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import os

# Global cache for pricing data
_pricing_cache = {}
DEBUG = os.getenv("DEBUG", "TRUE").lower() == "true"

def get_dynamic_ec2_pricing(instance_type: str, region: str, os_type: str = 'Linux') -> float:
    """
    Get real-time EC2 pricing from AWS Pricing API
    Returns hourly cost for the instance type in the specified region
    """
    cache_key = f"{instance_type}_{region}_{os_type}"
    
    # Check cache first
    if cache_key in _pricing_cache:
        return _pricing_cache[cache_key]
    
    try:
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        # Map region codes to AWS Pricing API region names
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'sa-east-1': 'South America (Sao Paulo)'
        }
        
        region_name = region_mapping.get(region, 'US East (N. Virginia)')
        
        if DEBUG:
            print(f"   🔍 [PRICING DEBUG] Using region name: {region_name}")
        
        # Start with basic filters and add more if needed
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os_type},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        ]
        
        if DEBUG:
            print(f"   🔍 [PRICING DEBUG] API filters: {filters}")
        
        response = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=filters,
            MaxResults=10  # Increased to get more results
        )
        
        if DEBUG:
            print(f"   🔍 [PRICING DEBUG] API response count: {len(response.get('PriceList', []))}")
        
        if response['PriceList']:
            # Try to find the best match
            for price_item in response['PriceList']:
                price_data = json.loads(price_item)
                
                # Check if this is the right instance type and OS
                product_attributes = price_data.get('product', {}).get('attributes', {})
                item_instance_type = product_attributes.get('instanceType', '')
                item_os = product_attributes.get('operatingSystem', '')
                item_tenancy = product_attributes.get('tenancy', '')
                
                if (item_instance_type == instance_type and 
                    item_os == os_type and 
                    item_tenancy == 'Shared'):
                    
                    terms = price_data.get('terms', {})
                    on_demand_terms = terms.get('OnDemand', {})
                    
                    if DEBUG:
                        print(f"   🔍 [PRICING DEBUG] Found matching product: {item_instance_type} {item_os} {item_tenancy}")
                        print(f"   🔍 [PRICING DEBUG] Found {len(on_demand_terms)} on-demand terms")
                    
                    for term_id, term_data in on_demand_terms.items():
                        price_dimensions = term_data.get('priceDimensions', {})
                        for dimension_id, dimension_data in price_dimensions.items():
                            price_per_unit = dimension_data.get('pricePerUnit', {})
                            usd_price = price_per_unit.get('USD', '0')
                            
                            if usd_price and usd_price != '0':
                                hourly_cost = float(usd_price)
                                print(f"   💰 [PRICING] {instance_type} in {region}: ${hourly_cost:.4f}/hour")
                                
                                # Cache the result
                                _pricing_cache[cache_key] = hourly_cost
                                return hourly_cost
        
        # If still no pricing found, try with fewer filters
        print(f"   ⚠️  [PRICING] No pricing found with full filters, trying simplified filters")
        
        # Simplified filters - just the essentials
        simple_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        ]
        
        if DEBUG:
            print(f"   🔍 [PRICING DEBUG] Simplified filters: {simple_filters}")
        
        simple_response = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=simple_filters,
            MaxResults=10
        )
        
        if simple_response['PriceList']:
            for price_item in simple_response['PriceList']:
                price_data = json.loads(price_item)
                product_attributes = price_data.get('product', {}).get('attributes', {})
                item_instance_type = product_attributes.get('instanceType', '')
                item_os = product_attributes.get('operatingSystem', '')
                
                # Accept Linux or any OS if Linux not found
                if (item_instance_type == instance_type and 
                    (item_os == os_type or item_os in ['Linux', 'RHEL', 'SUSE'])):
                    
                    terms = price_data.get('terms', {})
                    on_demand_terms = terms.get('OnDemand', {})
                    
                    for term_id, term_data in on_demand_terms.items():
                        price_dimensions = term_data.get('priceDimensions', {})
                        for dimension_id, dimension_data in price_dimensions.items():
                            price_per_unit = dimension_data.get('pricePerUnit', {})
                            usd_price = price_per_unit.get('USD', '0')
                            
                            if usd_price and usd_price != '0':
                                hourly_cost = float(usd_price)
                                print(f"   💰 [PRICING] {instance_type} in {region} (simplified): ${hourly_cost:.4f}/hour")
                                
                                # Cache the result
                                _pricing_cache[cache_key] = hourly_cost
                                return hourly_cost
        
        # If still no pricing found, use fallback pricing
        print(f"   ⚠️  [PRICING] No pricing found from API for {instance_type}, using fallback pricing")
        
        # Fallback pricing based on common instance types
        fallback_pricing = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664,
            't3.2xlarge': 0.3328,
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't2.large': 0.0928,
            't2.xlarge': 0.1856,
            't2.2xlarge': 0.3712,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'm5.4xlarge': 0.768,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'c5.2xlarge': 0.34,
            'c5.4xlarge': 0.68,
            'r5.large': 0.126,
            'r5.xlarge': 0.252,
            'r5.2xlarge': 0.504,
            'r5.4xlarge': 1.008,
        }
        
        if instance_type in fallback_pricing:
            fallback_cost = fallback_pricing[instance_type]
            print(f"   💰 [FALLBACK] Using fallback pricing for {instance_type}: ${fallback_cost:.4f}/hour")
            _pricing_cache[cache_key] = fallback_cost
            return fallback_cost
        else:
            # Estimate based on instance family
            if '.' in instance_type:
                family = instance_type.split('.')[0]
                size = instance_type.split('.')[1]
                
                # Simple estimation based on size
                size_multipliers = {
                    'micro': 0.25,
                    'small': 0.5,
                    'medium': 1.0,
                    'large': 2.0,
                    'xlarge': 4.0,
                    '2xlarge': 8.0,
                    '4xlarge': 16.0,
                    '8xlarge': 32.0,
                }
                
                if size in size_multipliers:
                    # Use t3.medium as base for estimation
                    base_price = 0.0416 / size_multipliers['medium']
                    estimated_price = base_price * size_multipliers.get(size, 1.0)
                    print(f"   💰 [FALLBACK] Estimated pricing for {instance_type}: ${estimated_price:.4f}/hour")
                    _pricing_cache[cache_key] = estimated_price
                    return estimated_price
        
        # Default fallback
        default_price = 0.05  # $0.05/hour = ~$36.50/month
        print(f"   💰 [FALLBACK] Using default pricing for {instance_type}: ${default_price:.4f}/hour")
        _pricing_cache[cache_key] = default_price
        return default_price
        
    except Exception as e:
        print(f"   ⚠️  [PRICING] Error fetching pricing for {instance_type}: {e}")
        if DEBUG:
            import traceback
            print(f"   🔍 [PRICING DEBUG] Full error: {traceback.format_exc()}")
        
        # Use fallback pricing on error
        fallback_pricing = {
            't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
            't3.large': 0.0832, 't3.xlarge': 0.1664, 't3.2xlarge': 0.3328,
        }
        
        if instance_type in fallback_pricing:
            fallback_cost = fallback_pricing[instance_type]
            print(f"   💰 [FALLBACK] Using fallback pricing for {instance_type}: ${fallback_cost:.4f}/hour")
            _pricing_cache[cache_key] = fallback_cost
            return fallback_cost
        
        _pricing_cache[cache_key] = 0.05
        return 0.05

def get_reserved_instance_pricing(instance_type: str, region: str = 'us-east-1', os_type: str = 'Linux', term: str = '1yr') -> float:
    """
    Get reserved instance pricing for better savings calculations
    Returns hourly cost in USD for reserved instances
    """
    try:
        print(f"   💰 [PRICING] Fetching reserved instance pricing for {instance_type} ({term})")
        
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'sa-east-1': 'South America (Sao Paulo)'
        }
        
        region_name = region_mapping.get(region, 'US East (N. Virginia)')
        
        # Map term to pricing API values
        term_mapping = {
            '1yr': '1yr',
            '3yr': '3yr'
        }
        
        term_value = term_mapping.get(term, '1yr')
        
        # Build filters for reserved instance pricing
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os_type},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'Reserved'},
            {'Type': 'TERM_MATCH', 'Field': 'offeringClass', 'Value': 'standard'},
            {'Type': 'TERM_MATCH', 'Field': 'purchaseOption', 'Value': 'No Upfront'},
        ]
        
        response = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=filters,
            MaxResults=10
        )
        
        if response['PriceList']:
            for price_item in response['PriceList']:
                price_data = json.loads(price_item)
                product_attributes = price_data.get('product', {}).get('attributes', {})
                item_instance_type = product_attributes.get('instanceType', '')
                item_os = product_attributes.get('operatingSystem', '')
                item_tenancy = product_attributes.get('tenancy', '')
                
                if (item_instance_type == instance_type and 
                    item_os == os_type and 
                    item_tenancy == 'Shared'):
                    
                    terms = price_data.get('terms', {})
                    reserved_terms = terms.get('Reserved', {})
                    
                    for term_id, term_data in reserved_terms.items():
                        price_dimensions = term_data.get('priceDimensions', {})
                        for dimension_id, dimension_data in price_dimensions.items():
                            price_per_unit = dimension_data.get('pricePerUnit', {})
                            usd_price = price_per_unit.get('USD', '0')
                            
                            if usd_price and usd_price != '0':
                                hourly_cost = float(usd_price)
                                print(f"   💰 [RESERVED PRICING] {instance_type} in {region}: ${hourly_cost:.4f}/hour")
                                return hourly_cost
        
        # If no reserved pricing found, use fallback pricing
        print(f"   ⚠️  [PRICING] No reserved pricing found for {instance_type}, using fallback pricing")
        
        # Fallback reserved pricing (approximately 33% savings)
        fallback_reserved_pricing = {
            't3.micro': 0.007,
            't3.small': 0.014,
            't3.medium': 0.028,
            't3.large': 0.056,
            't3.xlarge': 0.112,
            't3.2xlarge': 0.224,
            't2.micro': 0.0078,
            't2.small': 0.0154,
            't2.medium': 0.0311,
            't2.large': 0.0622,
            't2.xlarge': 0.1244,
            't2.2xlarge': 0.2488,
            'm5.large': 0.064,
            'm5.xlarge': 0.128,
            'm5.2xlarge': 0.256,
            'm5.4xlarge': 0.512,
            'c5.large': 0.057,
            'c5.xlarge': 0.114,
            'c5.2xlarge': 0.228,
            'c5.4xlarge': 0.456,
            'r5.large': 0.084,
            'r5.xlarge': 0.168,
            'r5.2xlarge': 0.336,
            'r5.4xlarge': 0.672,
        }
        
        if instance_type in fallback_reserved_pricing:
            fallback_cost = fallback_reserved_pricing[instance_type]
            print(f"   💰 [FALLBACK] Using fallback reserved pricing for {instance_type}: ${fallback_cost:.4f}/hour")
            return fallback_cost
        else:
            # Estimate based on instance family (33% savings from on-demand)
            ondemand_cost = get_dynamic_ec2_pricing(instance_type, region, os_type)
            estimated_reserved_cost = ondemand_cost * 0.67  # 33% savings
            print(f"   💰 [FALLBACK] Estimated reserved pricing for {instance_type}: ${estimated_reserved_cost:.4f}/hour")
            return estimated_reserved_cost
        
    except Exception as e:
        print(f"   ⚠️  [PRICING] Error fetching reserved pricing for {instance_type}: {e}")
        
        # Use fallback pricing on error
        fallback_reserved_pricing = {
            't3.micro': 0.007, 't3.small': 0.014, 't3.medium': 0.028,
            't3.large': 0.056, 't3.xlarge': 0.112, 't3.2xlarge': 0.224,
        }
        
        if instance_type in fallback_reserved_pricing:
            fallback_cost = fallback_reserved_pricing[instance_type]
            print(f"   💰 [FALLBACK] Using fallback reserved pricing for {instance_type}: ${fallback_cost:.4f}/hour")
            return fallback_cost
        
        # Default fallback (33% savings from default on-demand)
        return 0.033  # $0.033/hour = ~$24.09/month


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
                
                # Get dynamic pricing based on instance type and region
                print(f"   💰 [PRICING] Fetching pricing for {instance_type} in {region}")
                estimated_hourly_cost = get_dynamic_ec2_pricing(instance_type, region)
                monthly_cost = estimated_hourly_cost * 730  # 730 hours per month
                
                print(f"   💰 Hourly cost: ${estimated_hourly_cost:.4f}")
                print(f"   💰 Monthly cost: ${monthly_cost:.2f}")
                
                # Calculate potential savings based on CPU utilization
                avg_cpu = metrics.get("AverageCPU", 0)
                current_cpu = metrics.get("CurrentCPU", 0)
                
                # Get reserved instance pricing for better savings calculation
                reserved_hourly_cost = get_reserved_instance_pricing(instance_type, region)
                reserved_monthly_cost = reserved_hourly_cost * 730
                
                # Enhanced savings calculation with real pricing (no hardcoded multipliers)
                savings_options = []
                
                # Option 1: Reserved Instance savings (real pricing)
                reserved_savings = monthly_cost - reserved_monthly_cost
                if reserved_savings > 0:
                    savings_options.append({
                        "type": "Reserved Instance",
                        "savings": reserved_savings,
                        "reason": f"Switch to 1-year reserved instance (saves ${reserved_savings:.2f}/month)"
                    })
                
                # Option 2: Shutdown savings (for low CPU usage instances)
                if avg_cpu >= 0 and avg_cpu < 10:
                    # Calculate shutdown savings (full monthly cost when stopping)
                    shutdown_result = calculate_stop_instance_savings(instance_type, region)
                    if shutdown_result["savings"] > 0:
                        savings_options.append({
                            "type": "Shutdown Instance",
                            "savings": shutdown_result["savings"],
                            "reason": shutdown_result["reason"]
                        })
                
                # Select the best savings option
                if savings_options:
                    best_option = max(savings_options, key=lambda x: x["savings"])
                    potential_savings = best_option["savings"]
                    savings_reason = best_option["reason"]
                else:
                    potential_savings = 0.0
                    savings_reason = "High CPU usage - instance appears to be well-utilized"

                print(f"   📊 7-day average CPU: {avg_cpu}%")
                print(f"   📊 Current CPU: {current_cpu}%")
                print(f"   💰 On-demand cost: ${monthly_cost:.2f}/month")
                print(f"   💰 Reserved cost: ${reserved_monthly_cost:.2f}/month")
                print(f"   💡 Best savings option: {savings_reason}")
                print(f"   💡 Potential savings: ${potential_savings:.2f}/month")

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

def clear_pricing_cache():
    """Clear the pricing cache"""
    global _pricing_cache
    _pricing_cache.clear()
    print("💰 [PRICING] Cache cleared")

def get_pricing_cache_stats():
    """Get pricing cache statistics"""
    global _pricing_cache
    return {
        "cache_size": len(_pricing_cache),
        "cached_instances": list(_pricing_cache.keys())
    }

def print_pricing_cache_stats():
    """Print pricing cache statistics"""
    stats = get_pricing_cache_stats()
    print(f"💰 [PRICING] Cache stats: {stats['cache_size']} cached prices")
    if stats['cached_instances']:
        print(f"💰 [PRICING] Cached instances: {', '.join(stats['cached_instances'][:5])}{'...' if len(stats['cached_instances']) > 5 else ''}")

def get_downsized_instance_type(current_instance_type: str) -> str:
    """
    Get the next smaller instance type for downsizing recommendations
    Returns the smaller instance type or empty string if no smaller type available
    """
    # Instance type hierarchy (smaller to larger)
    instance_hierarchy = {
        # T3 family
        't3.2xlarge': 't3.xlarge', 't3.xlarge': 't3.large', 't3.large': 't3.medium',
        't3.medium': 't3.small', 't3.small': 't3.micro',
        # T2 family
        't2.2xlarge': 't2.xlarge', 't2.xlarge': 't2.large', 't2.large': 't2.medium',
        't2.medium': 't2.small', 't2.small': 't2.micro',
        # M5 family
        'm5.24xlarge': 'm5.12xlarge', 'm5.12xlarge': 'm5.4xlarge', 'm5.4xlarge': 'm5.2xlarge',
        'm5.2xlarge': 'm5.xlarge', 'm5.xlarge': 'm5.large',
        # C5 family
        'c5.18xlarge': 'c5.9xlarge', 'c5.9xlarge': 'c5.4xlarge', 'c5.4xlarge': 'c5.2xlarge',
        'c5.2xlarge': 'c5.xlarge', 'c5.xlarge': 'c5.large',
        # R5 family
        'r5.24xlarge': 'r5.12xlarge', 'r5.12xlarge': 'r5.4xlarge', 'r5.4xlarge': 'r5.2xlarge',
        'r5.2xlarge': 'r5.xlarge', 'r5.xlarge': 'r5.large',
    }
    
    return instance_hierarchy.get(current_instance_type, '')

def calculate_downsizing_savings(current_instance_type: str, target_instance_type: str, region: str, os_type: str = 'Linux') -> dict:
    """
    Calculate savings from downsizing to a smaller instance type
    Returns dict with actual savings from downsizing
    """
    try:
        # Get pricing for both instance types
        current_hourly_cost = get_dynamic_ec2_pricing(current_instance_type, region, os_type)
        target_hourly_cost = get_dynamic_ec2_pricing(target_instance_type, region, os_type)
        
        current_monthly_cost = current_hourly_cost * 730
        target_monthly_cost = target_hourly_cost * 730
        
        # If no pricing available, no savings possible
        if current_monthly_cost == 0 or target_monthly_cost == 0:
            return {
                "savings": 0.0,
                "reason": f"No pricing available for downsizing {current_instance_type} to {target_instance_type}"
            }
        
        savings = current_monthly_cost - target_monthly_cost
        
        return {
            "savings": savings,
            "reason": f"Downsize from {current_instance_type} to {target_instance_type} (saves ${savings:.2f}/month)"
        }
        
    except Exception as e:
        print(f"   ⚠️  [DOWNSIZE] Error calculating downsizing savings: {e}")
        return {
            "savings": 0.0,
            "reason": f"Error calculating downsizing savings for {current_instance_type}"
        }

def get_ebs_pricing(region: str = 'us-east-1') -> float:
    """
    Get EBS pricing for the specified region
    Returns monthly cost per GB
    """
    try:
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'Europe (Ireland)',
            'eu-central-1': 'Europe (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'sa-east-1': 'South America (Sao Paulo)'
        }
        
        region_name = region_mapping.get(region, 'US East (N. Virginia)')
        
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'volumeType', 'Value': 'General Purpose'},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        ]
        
        response = pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=filters,
            MaxResults=1
        )
        
        if response['PriceList']:
            price_data = json.loads(response['PriceList'][0])
            terms = price_data.get('terms', {})
            on_demand_terms = terms.get('OnDemand', {})
            
            for term_id, term_data in on_demand_terms.items():
                price_dimensions = term_data.get('priceDimensions', {})
                for dimension_id, dimension_data in price_dimensions.items():
                    price_per_unit = dimension_data.get('pricePerUnit', {})
                    usd_price = price_per_unit.get('USD', '0')
                    
                    if usd_price and usd_price != '0':
                        # Convert hourly price to monthly (730 hours)
                        hourly_price = float(usd_price)
                        monthly_price = hourly_price * 730
                        print(f"   💰 [EBS PRICING] EBS cost for {region}: ${monthly_price:.4f}/GB/month")
                        return monthly_price
        
        # If no pricing found, return 0 (no savings possible)
        print(f"   ⚠️  [EBS PRICING] No EBS pricing found for {region}")
        return 0.0
        
    except Exception as e:
        print(f"   ⚠️  [EBS PRICING] Error fetching EBS pricing: {e}")
        return 0.0

def calculate_stop_instance_savings(instance_type: str, region: str, os_type: str = 'Linux') -> dict:
    """
    Calculate savings from stopping an instance (for instances with very low usage)
    Returns dict with actual savings from stopping - savings is the full monthly cost
    """
    try:
        # Get current instance pricing
        current_hourly_cost = get_dynamic_ec2_pricing(instance_type, region, os_type)
        current_monthly_cost = current_hourly_cost * 730
        
        # If no pricing available, no savings possible
        if current_monthly_cost == 0:
            return {
                "savings": 0.0,
                "reason": f"No pricing available for {instance_type} in {region}"
            }
        
        # When stopping an instance, the savings is the full monthly cost
        # (you only pay for EBS storage which is minimal)
        savings = current_monthly_cost
        
        return {
            "savings": savings,
            "reason": f"Stop instance (saves ${savings:.2f}/month - full compute cost)"
        }
        
    except Exception as e:
        print(f"   ⚠️  [STOP] Error calculating stop savings: {e}")
        return {
            "savings": 0.0,
            "reason": f"Error calculating stop savings for {instance_type}"
        }
