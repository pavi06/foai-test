
import boto3
from typing import List, Optional
from data.aws.settings import get_boto3_client
from data.aws.cloudwatch import get_cpu_metrics

def fetch_ec2_instances(
    instance_ids: Optional[List[str]] = None,
    region: Optional[str] = None
) -> List[dict]:
    """
    Fetches EC2 instances and their CPU metrics.
    Filters by instance_ids if provided.
    Uses region override if passed.
    """
    ec2 = get_boto3_client("ec2", region=region)
    filters = [{"Name": "instance-state-name", "Values": ["running"]}]
    
    if instance_ids:
        response = ec2.describe_instances(InstanceIds=instance_ids)
    else:
        response = ec2.describe_instances(Filters=filters)

    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance_id = instance["InstanceId"]
            metrics = get_cpu_metrics(instance_id, region=region)

            instance_data = {
                "InstanceId": instance_id,
                "InstanceType": instance.get("InstanceType"),
                "AvailabilityZone": instance.get("Placement", {}).get("AvailabilityZone"),
                "Tags": instance.get("Tags", []),
                **metrics
            }

            instances.append(instance_data)

    return instances
