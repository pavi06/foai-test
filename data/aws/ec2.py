import os 
from dotenv import load_dotenv
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import fetch_cpu_utilization


DEBUG = os.getenv("DEBUG", "False").lower() == "true"


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

                cpu = fetch_cpu_utilization(instance_id)

                instances.append({
                    "InstanceId": instance_id,
                    "InstanceType": instance_type,
                    "State": state,
                    "AvailabilityZone": az,
                    "CPUUtilization": cpu
                })
                if DEBUG:
                    print(f"[DEBUG] {instance_id} → {cpu}% CPU")

        return instances

    except Exception as e:
        
        print(f"[ERROR] Failed to fetch EC2 instances: {e}")
        return []
