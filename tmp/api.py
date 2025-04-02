from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, List
from dotenv import load_dotenv
import os
import json

from data.aws.ec2 import fetch_ec2_instances
from app.nodes.generate_recommendations import generate_recommendations, get_recommendations_and_prompt
from app.nodes.generate_response import stream_response

from memory.redis_memory import append_to_list, get_list
from memory.preferences import get_user_preferences  # ✅ new import

load_dotenv()
USERNAME = os.getenv("USERNAME", "default")

app = FastAPI(title="fo.ai API - Cloud Cost Intelligence", version="0.1.4-pre")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    query: str
    user_id: str = "demo"
    region: str = "us-west-2"

class Recommendation(BaseModel):
    InstanceId: str
    InstanceType: str
    Reason: str
    EstimatedSavings: float
    Tags: Any = None

class AnalyzeResponse(BaseModel):
    response: str
    raw: List[Recommendation]

@app.get("/status")
def status_check():
    return {"status": "ok", "message": "fo.ai API is running"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    user_id = request.user_id or "demo"
    rules = get_user_preferences(user_id)
    print(f"\n\n ******** [fo.ai] Using rules for {user_id}: {rules} **********\n\n")

    ec2_data = fetch_ec2_instances(region=request.region)

    if not ec2_data:
        return {"response": f"No EC2 instances found in region `{request.region}`.", "raw": []}

    recommendations = generate_recommendations(ec2_data, rules)

    if not recommendations:
        markdown_summary = "_No recommendations found._"
    else:
        total = len(recommendations)
        total_savings = sum(r.get("EstimatedSavings", 0.0) for r in recommendations)

        markdown_summary = (
            f"We found **{total} EC2 instance(s)** that appear underutilized "
            f"based on 7-day CPU data. Estimated savings: **${total_savings:.2f}**.\n\n"
        )

        for r in recommendations:
            az = r.get("AvailabilityZone", "unknown zone")
            instance_type = r.get("InstanceType", "unknown type")
            reason = r.get("Reason", "No reason provided")
            savings = r.get("EstimatedSavings", 0.0)

            markdown_summary += (
                f"- Instance `{r['InstanceId']}` is a **{instance_type}** in `{az}`. "
                f"{reason} Estimated savings: **${savings:.2f}**.\n"
            )

    chat_entry = {
        "query": request.query,
        "response": markdown_summary
    }
    append_to_list(f"foai:chat:{USERNAME}", json.dumps(chat_entry))

    return {
        "response": markdown_summary,
        "raw": recommendations
    }

class AnalyzeStreamRequest(BaseModel):
    user_id: str
    instance_ids: List[str] = []
    region: str = "us-west-2"

@app.post("/analyze/stream")
async def stream_analysis(req: AnalyzeStreamRequest):
    rules = get_user_preferences(req.user_id)
    ec2_data = fetch_ec2_instances(req.instance_ids, region=req.region)

    if not ec2_data:
        def empty_stream():
            yield f"No EC2 instances found in region `{req.region}`. Nothing to analyze."
        return StreamingResponse(empty_stream(), media_type="text/plain")

    result = get_recommendations_and_prompt(ec2_data, rules)
    prompt = result["prompt"]

    def stream_gen():
        yield from stream_response(prompt)

    return StreamingResponse(stream_gen(), media_type="text/plain")

@app.get("/memory", response_model=list)
def get_memory():
    key = f"foai:chat:{USERNAME}"
    raw_entries = get_list(key, limit=20)
    memory = []

    for item in raw_entries:
        try:
            memory.append(json.loads(item))
        except Exception:
            memory.append({"error": "Failed to parse item", "data": item})

    return memory
