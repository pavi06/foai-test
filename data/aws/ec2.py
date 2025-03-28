import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import fetch_cpu_utilization, get_avg_cpu_over_days



load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

def estimate_monthly_cost(instance_type: str) -> float:
    pricing = {
        "t3.micro": 8.50,
        "t3.small": 12.00,
        "t3.large": 22.50,
        "m5.large": 30.00,
        "m5.xlarge": 60.00
    }
    return pricing.get(instance_type, 20.00)

def calculate_uptime_hours(launch_time: datetime) -> float:
    now = datetime.now(timezone.utc)
    delta = now - launch_time
    return round(delta.total_seconds() / 3600, 2)

def fetch_ec2_instances() -> list[dict]:
    ec2 = get_boto3_client("ec2")

    try:
        response = ec2.describe_instances()
        instances = []

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance.get("InstanceId")
                instance_type = instance.get("InstanceType")
                state = instance.get("State", {}).get("Name")
                az = instance.get("Placement", {}).get("AvailabilityZone")
                tags = instance.get("Tags", [])
                launch_time = instance.get("LaunchTime")

                cpu = fetch_cpu_utilization(instance_id)
                avg_cpu_7d = get_avg_cpu_over_days(instance_id)
                uptime_hours = calculate_uptime_hours(launch_time)
                monthly_cost = estimate_monthly_cost(instance_type)

                instances.append({
                    "InstanceId": instance_id,
                    "InstanceType": instance_type,
                    "AvailabilityZone": az,
                    "State": state,
                    "CPU": cpu,
                    "CPU7dAvg": avg_cpu_7d,
                    "UptimeHours": uptime_hours,
                    "MonthlyCost": monthly_cost,
                    "Tags": tags
                })

                if DEBUG:
                    print(f"[DEBUG] {instance_id}: CPU={cpu}%, Avg7d={avg_cpu_7d}%, Uptime={uptime_hours}h, Cost=${monthly_cost:.2f}")

        return instances

    except Exception as e:
        print(f"[ERROR] Failed to fetch EC2 instances: {e}")
        return []
