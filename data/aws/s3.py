import boto3
from typing import List, Dict, Optional
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import get_cpu_metrics
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

TARGET_REGION = "us-east-1"             
TARGET_BUCKET_NAMES = ["my-bucket-1"] 

IST = timezone(timedelta(hours=5, minutes=30))

def format_datetime_utc530(dt: datetime) -> str:
    dt_ist = dt.astimezone(IST)
    return dt_ist.strftime('%B %-d, %Y, %H:%M:%S (UTC+05:30)')

def get_boto3_client(service_name: str, region: Optional[str] = None):
    return boto3.client(service_name, region_name=region)

def get_all_buckets() -> List[Dict]:
    s3 = get_boto3_client('s3')
    response = s3.list_buckets()
    return response.get('Buckets', [])

def get_bucket_location(bucket_name: str) -> str:
    try:
        s3 = get_boto3_client('s3')
        location = s3.get_bucket_location(Bucket=bucket_name).get('LocationConstraint')
        return location or 'us-east-1'
    except Exception:
        return 'unknown'

def get_bucket_basic_info(bucket_name: str) -> Dict:
    s3 = get_boto3_client('s3')
    location = get_bucket_location(bucket_name)
    versioning = s3.get_bucket_versioning(Bucket=bucket_name).get('Status', 'Disabled')
    try:
        logging = s3.get_bucket_logging(Bucket=bucket_name).get('LoggingEnabled', {})
    except Exception:
        logging = {}

    return {
        "BucketName": bucket_name,
        "Region": location,
        "Versioning": versioning,
        "LoggingEnabled": bool(logging),
        "LoggingTarget": logging.get("TargetBucket") if logging else None
    }

def get_bucket_lifecycle_config(bucket_name: str) -> List[Dict]:
    s3 = get_boto3_client('s3')
    try:
        response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return response.get('Rules', [])
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
            return []
        raise

def get_object_stats(bucket_name: str, prefix: Optional[str] = None) -> Dict:
    s3 = get_boto3_client('s3')
    paginator = s3.get_paginator('list_objects_v2')

    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix or '')

    object_count = 0
    last_modified_map = defaultdict(lambda: datetime.min.replace(tzinfo=timezone.utc))

    for page in page_iterator:
        for obj in page.get('Contents', []):
            object_count += 1
            key = obj['Key']
            last_modified = obj['LastModified']

            group_key = key.split('/')[0] if '/' in key else key

            if last_modified > last_modified_map[group_key]:
                last_modified_map[group_key] = last_modified

    return {
        "TotalObjects": object_count,
        "LastModifiedByGroup": {
            k: format_datetime_utc530(v) for k, v in last_modified_map.items()
        }
    }


def fetch_s3_bucket_details(bucket_name: str, region: Optional[str] = None) -> Dict:
    basic_info = get_bucket_basic_info(bucket_name)
    if region and basic_info['Region'] != region:
        return {} 

    lifecycle = get_bucket_lifecycle_config(bucket_name)
    object_stats = get_object_stats(bucket_name)

    return {
        "BasicInfo": basic_info,
        "LifecyclePolicies": lifecycle,
        "ObjectStatistics": object_stats
    }


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
    all_buckets = get_all_buckets()

    results = []
    for bucket in all_buckets:
        bucket_name = bucket['Name']
        if bucket_names and bucket_name not in bucket_names:
            continue
        try:
            details = fetch_s3_bucket_details(bucket_name, region=region)
            if details:
                # Inject BucketName for clarity in list form
                details["BucketName"] = bucket_name
                results.append(details)
        except Exception as e:
            results.append({
                "BucketName": bucket_name,
                "error": str(e)
            })

    return results






