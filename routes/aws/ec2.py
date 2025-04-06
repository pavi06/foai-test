# src/routes/aws/ec2.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from fastapi.responses import JSONResponse

from data.aws.ec2 import fetch_ec2_instances, summarize_cost_by_region

router = APIRouter()

class RegionSummaryRequest(BaseModel):
    region: str

class RegionSummaryItem(BaseModel):
    region: str
    instance_count: int
    estimated_hourly_cost: float

class RegionSummaryResponse(BaseModel):
    summary: List[RegionSummaryItem]

@router.post("/summary", response_model=RegionSummaryResponse)
def ec2_region_summary(request: RegionSummaryRequest):
    """
    Summarize EC2 cost concentration by region.
    """
    try:
        ec2_data = fetch_ec2_instances(region=request.region)
        if not ec2_data:
            return JSONResponse(status_code=404, content={"message": "No EC2 instances found."})
        else:
            print(ec2_data)
        summary = summarize_cost_by_region(ec2_data)
        return {"summary": summary}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})