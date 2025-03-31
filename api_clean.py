from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List
from dotenv import load_dotenv
import os
import json

from data.aws.ec2 import fetch_ec2_instances
from app.nodes.generate_recommendations import generate_recommendations
from rules.aws.ec2_rules import get_ec2_rules
from memory.redis_memory import append_to_list, get_list

load_dotenv()
USERNAME = os.getenv("USERNAME", "default")

app = FastAPI(title="fo.ai API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    query: str

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
    ec2_data = fetch_ec2_instances()
    rules = get_ec2_rules()
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
