import boto3
from typing import List, Dict, Optional
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import get_cpu_metrics
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

TARGET_REGION = "us-east-1"             
TARGET_BUCKET_NAMES = [] 

IST = timezone(timedelta(hours=5, minutes=30))

def format_datetime_utc530(dt: datetime) -> str:
    dt_ist = dt.astimezone(IST)
    return dt_ist.strftime('%B %-d, %Y, %H:%M:%S (UTC+05:30)')

def get_boto3_client(service_name: str, region: Optional[str] = None):
    return boto3.client(service_name, region_name=region)

def get_all_buckets() -> List[Dict]:
    print(f"📋 [S3] Looking for your S3 buckets...")
    s3 = get_boto3_client('s3')
    response = s3.list_buckets()
    buckets = response.get('Buckets', [])
    print(f"📊 [S3] Found {len(buckets)} buckets")
    return buckets

def get_bucket_location(bucket_name: str) -> str:
    try:
        s3 = get_boto3_client('s3')
        location = s3.get_bucket_location(Bucket=bucket_name).get('LocationConstraint')
        return location or 'us-east-1'
    except Exception as e:
        print(f"⚠️  [S3] Couldn't get location for {bucket_name}: {e}")
        return 'unknown'

def get_bucket_basic_info(bucket_name: str) -> Dict:
    print(f"   📋 [S3] Checking bucket: {bucket_name}")
    s3 = get_boto3_client('s3')
    location = get_bucket_location(bucket_name)
    
    try:
        versioning = s3.get_bucket_versioning(Bucket=bucket_name).get('Status', 'Disabled')
        print(f"      🔄 Versioning: {versioning}")
    except Exception as e:
        print(f"      ⚠️  Error getting versioning: {e}")
        versioning = 'Disabled'

    try:
        logging = s3.get_bucket_logging(Bucket=bucket_name).get('LoggingEnabled', {})
        logging_enabled = bool(logging)
        logging_target = logging.get("TargetBucket") if logging else None
        print(f"      📝 Logging: {'Enabled' if logging_enabled else 'Disabled'}")
        if logging_target:
            print(f"      📝 Logging target: {logging_target}")
    except Exception as e:
        print(f"      ⚠️  Error getting logging: {e}")
        logging_enabled = False
        logging_target = None

    # Get bucket encryption
    try:
        encryption = s3.get_bucket_encryption(Bucket=bucket_name)
        encryption_enabled = True
        encryption_type = encryption.get('ServerSideEncryptionConfiguration', {}).get('Rules', [{}])[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm', 'unknown')
        print(f"      🔐 Encryption: {encryption_type}")
    except Exception as e:
        encryption_enabled = False
        encryption_type = 'None'
        print(f"      🔐 Encryption: Not configured")

    # Get bucket tags
    try:
        tags_response = s3.get_bucket_tagging(Bucket=bucket_name)
        tags = tags_response.get('TagSet', [])
        print(f"      🏷️  Tags: {len(tags)} tags found")
    except Exception as e:
        tags = []
        print(f"      🏷️  Tags: No tags found")

    return {
        "BucketName": bucket_name,
        "Region": location,
        "Versioning": versioning,
        "LoggingEnabled": logging_enabled,
        "LoggingTarget": logging_target,
        "EncryptionEnabled": encryption_enabled,
        "EncryptionType": encryption_type,
        "Tags": tags
    }

def get_bucket_lifecycle_config(bucket_name: str) -> List[Dict]:
    print(f"   🔄 [S3] Looking for lifecycle policies in: {bucket_name}")
    s3 = get_boto3_client('s3')
    try:
        response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        rules = response.get('Rules', [])
        print(f"      📋 Found {len(rules)} lifecycle rules")
        for i, rule in enumerate(rules):
            rule_id = rule.get('ID', f'Rule-{i+1}')
            status = rule.get('Status', 'Unknown')
            print(f"      📋 Rule {i+1}: {rule_id} ({status})")
        return rules
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            print(f"      ⚠️  No lifecycle configuration found")
            return []
        else:
            print(f"      ❌ Error getting lifecycle: {e}")
            raise

def get_object_stats(bucket_name: str, prefix: Optional[str] = None) -> Dict:
    print(f"   📊 [S3 ANALYSIS] Analyzing objects in bucket: {bucket_name}")
    s3 = get_boto3_client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix or '')

    object_count = 0
    total_size = 0
    last_modified_map = defaultdict(lambda: datetime.min.replace(tzinfo=timezone.utc))
    size_by_storage_class = defaultdict(int)
    objects_by_storage_class = defaultdict(int)

    print(f"      📊 Scanning objects...")
    for page in page_iterator:
        for obj in page.get('Contents', []):
            object_count += 1
            key = obj['Key']
            size = obj.get('Size', 0)
            storage_class = obj.get('StorageClass', 'STANDARD')
            last_modified = obj['LastModified']

            total_size += size
            size_by_storage_class[storage_class] += size
            objects_by_storage_class[storage_class] += 1

            group_key = key.split('/')[0] if '/' in key else key

            if last_modified > last_modified_map[group_key]:
                last_modified_map[group_key] = last_modified

    print(f"      📊 Total objects: {object_count:,}")
    print(f"      📊 Total size: {total_size / (1024**3):.2f} GB")
    print(f"      📊 Storage class breakdown:")
    for storage_class, count in objects_by_storage_class.items():
        size_gb = size_by_storage_class[storage_class] / (1024**3)
        print(f"         {storage_class}: {count:,} objects, {size_gb:.2f} GB")
    
    print(f"      📅 Last modified dates by group:")
    for group, last_modified in last_modified_map.items():
        print(f"         {group}: {format_datetime_utc530(last_modified)}")
    
    print(f"      🔍 [DEBUG] Raw object count from AWS: {object_count}")
    print(f"      🔍 [DEBUG] Raw total size from AWS: {total_size} bytes")

    return {
        "TotalObjects": object_count,
        "TotalSizeBytes": total_size,
        "TotalSizeGB": total_size / (1024**3),
        "SizeByStorageClass": dict(size_by_storage_class),
        "ObjectsByStorageClass": dict(objects_by_storage_class),
        "LastModifiedByGroup": {
            k: format_datetime_utc530(v) for k, v in last_modified_map.items()
        }
    }

def calculate_storage_cost(bucket_data: Dict) -> Dict:
    """Calculate estimated storage costs for different storage classes"""
    print(f"   💰 [S3 ANALYSIS] Calculating storage costs...")
    
    # AWS S3 pricing (us-east-1, per GB per month)
    pricing = {
        'STANDARD': 0.023,      # $0.023 per GB
        'STANDARD_IA': 0.0125,  # $0.0125 per GB
        'ONEZONE_IA': 0.01,     # $0.01 per GB
        'GLACIER': 0.004,       # $0.004 per GB
        'DEEP_ARCHIVE': 0.00099 # $0.00099 per GB
    }
    
    object_stats = bucket_data.get("ObjectStatistics", {})
    size_by_class = object_stats.get("SizeByStorageClass", {})
    
    current_monthly_cost = 0
    optimized_monthly_cost = 0
    
    for storage_class, size_bytes in size_by_class.items():
        size_gb = size_bytes / (1024**3)
        current_cost = size_gb * pricing.get(storage_class, pricing['STANDARD'])
        current_monthly_cost += current_cost
        
        # Calculate optimized cost (move to cheaper storage classes)
        if storage_class == 'STANDARD':
            # Move to STANDARD_IA if > 30 days old
            optimized_cost = size_gb * pricing['STANDARD_IA']
        elif storage_class == 'STANDARD_IA':
            # Move to GLACIER if > 90 days old
            optimized_cost = size_gb * pricing['GLACIER']
        else:
            optimized_cost = current_cost
            
        optimized_monthly_cost += optimized_cost
    
    potential_savings = current_monthly_cost - optimized_monthly_cost
    
    print(f"      💰 Current monthly cost: ${current_monthly_cost:.2f}")
    print(f"      💰 Optimized monthly cost: ${optimized_monthly_cost:.2f}")
    print(f"      💡 Potential savings: ${potential_savings:.2f}/month")
    
    return {
        "CurrentMonthlyCost": current_monthly_cost,
        "OptimizedMonthlyCost": optimized_monthly_cost,
        "PotentialSavings": potential_savings
    }

def fetch_s3_bucket_details(bucket_name: str, region: Optional[str] = None) -> Dict:
    print(f"\n🪣 [S3 ANALYSIS] Analyzing bucket: {bucket_name}")
    
    basic_info = get_bucket_basic_info(bucket_name)
    if region and basic_info['Region'] != region:
        print(f"   ⚠️  [S3 ANALYSIS] Bucket region {basic_info['Region']} doesn't match target {region}")
        return {} 

    lifecycle = get_bucket_lifecycle_config(bucket_name)
    object_stats = get_object_stats(bucket_name)
    cost_analysis = calculate_storage_cost({"ObjectStatistics": object_stats})

    bucket_data = {
        "BasicInfo": basic_info,
        "LifecyclePolicies": lifecycle,
        "ObjectStatistics": object_stats,
        "CostAnalysis": cost_analysis
    }
    
    print(f"   ✅ [S3 ANALYSIS] Bucket {bucket_name} analysis complete")
    return bucket_data

def fetch_s3_data(
    region: Optional[str] = None,
    bucket_names: Optional[List[str]] = None
) -> List[Dict]:
    """
    Fetches S3 bucket and their Lifecycle Management policies, along with its storage details.
    Filters by bucket_names if provided.
    Uses region override if passed.
    
    Returns a list of dictionaries, one per bucket.
    """
    print(f"\n🔍 [S3 ANALYSIS] Starting S3 bucket analysis...")
    print(f"📍 [S3 ANALYSIS] Target region: {region or 'all regions'}")
    print(f"🎯 [S3 ANALYSIS] Bucket filter: {bucket_names or 'all buckets'}")
    print(f"🌐 [S3 ANALYSIS] Using REAL AWS data (not mock data)")
    
    all_buckets = get_all_buckets()

    results = []
    total_buckets = len(all_buckets)
    analyzed_buckets = 0
    total_current_cost = 0
    total_potential_savings = 0
    
    for i, bucket in enumerate(all_buckets, 1):
        bucket_name = bucket['Name']
        if bucket_names and bucket_name not in bucket_names:
            continue
            
        print(f"\n📊 [S3 ANALYSIS] Progress: {i}/{total_buckets} buckets")
        
        try:
            details = fetch_s3_bucket_details(bucket_name, region=region)
            if details:
                details["BucketName"] = bucket_name
                results.append(details)
                analyzed_buckets += 1
                
                # Accumulate cost data
                cost_analysis = details.get("CostAnalysis", {})
                total_current_cost += cost_analysis.get("CurrentMonthlyCost", 0)
                total_potential_savings += cost_analysis.get("PotentialSavings", 0)
                
        except Exception as e:
            print(f"   ❌ [S3 ANALYSIS] Error analyzing bucket {bucket_name}: {e}")
            results.append({
                "BucketName": bucket_name,
                "error": str(e)
            })

    print(f"\n📊 [S3 ANALYSIS] Summary:")
    print(f"   📈 Total buckets analyzed: {analyzed_buckets}")
    print(f"   💰 Total current monthly cost: ${total_current_cost:.2f}")
    print(f"   💡 Total potential savings: ${total_potential_savings:.2f}")
    print(f"   🎯 Buckets with optimization potential: {len([r for r in results if r.get('CostAnalysis', {}).get('PotentialSavings', 0) > 0])}")
    
    return results






