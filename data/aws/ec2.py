from data.aws.settings import get_boto3_client

def fetch_ec2_instances() -> list[dict]:
    ec2 = get_boto3_client("ec2")

    try:
        response = ec2.describe_instances()
        instances = []

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instances.append({
                    "InstanceId": instance.get("InstanceId"),
                    "InstanceType": instance.get("InstanceType"),
                    "State": instance.get("State", {}).get("Name"),
                    "AvailabilityZone": instance.get("Placement", {}).get("AvailabilityZone")
                })

        return instances

    except Exception as e:
        print(f"[ERROR] Failed to fetch EC2 instances: {e}")
        return []
