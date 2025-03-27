from datetime import datetime, timedelta
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
