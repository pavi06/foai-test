from typing import TypedDict, Literal

class CostState(TypedDict, total=False):
    query: str
    query_type: Literal["general", "ec2", "region", "service"]
    ec2_data: list
    cost_data: dict
    recommendations: list
    response: str
