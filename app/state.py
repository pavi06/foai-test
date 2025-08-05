from typing import TypedDict, Literal

class CostState(TypedDict, total=False):
    query: str
    query_type: Literal["general", "ec2", "s3", "region", "service"]
    ec2_data: list
    s3_data: list
    cost_data: dict
    recommendations: list
    s3_recommendations: list
    response: str
    use_mock: bool
    debug: bool
