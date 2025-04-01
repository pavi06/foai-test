from datetime import datetime, timedelta
from datetime import datetime, timedelta, timezone
import boto3
from data.aws.settings import get_boto3_client
import os 
from dotenv import load_dotenv

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

def fetch_cpu_utilization(instance_id: str, period_minutes: int = 60) -> float:
    cloudwatch = get_boto3_client("cloudwatch")

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=period_minutes)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period_minutes * 60,
            Statistics=['Average'],
            Unit='Percent'
        )

        datapoints = response.get("Datapoints", [])
        if datapoints:
            return round(datapoints[0]["Average"], 2)
        else:
            return 0.0  # No data = treat as low usage

    except Exception as e:
        print(f"[ERROR] CloudWatch fetch failed for {instance_id}: {e}")
        return -1.0

def get_avg_cpu_over_days(instance_id: str, days: int = 7) -> float:
    cloudwatch = boto3.client("cloudwatch")
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=now,
            Period=86400,  # daily average
            Statistics=['Average'],
            Unit='Percent'
        )

        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return -1  # no data

        # Calculate average across all days
        avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
        return round(avg_cpu, 2)

    except Exception as e:
        print(f"[ERROR] CloudWatch fetch failed for {instance_id}: {e}")
        return -1
    
def get_cpu_metrics(instance_id: str, region: str = None) -> dict:
    """
    Unified CPU metrics fetcher for recommendation engine.
    Returns: avg over 7d, current hourly avg, and estimated savings.
    """
    avg_cpu = get_avg_cpu_over_days(instance_id)
    current = fetch_cpu_utilization(instance_id)
    savings = 10.0 if avg_cpu >= 0 and avg_cpu < 10 else 0.0

    return {
        "AverageCPU": avg_cpu,
        "CurrentCPU": current,
        "EstimatedSavings": savings,
        "UptimeHours": 140  # Placeholder — could be fetched from instance later
    }
