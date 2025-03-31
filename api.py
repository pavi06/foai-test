# api.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List

from data.aws.ec2 import fetch_ec2_instances
from app.nodes.generate_recommendations import generate_recommendations
from rules.aws.ec2_rules import get_ec2_rules


import json
import os
from memory.redis_memory import append_to_list, get_list
from dotenv import load_dotenv

load_dotenv()
USERNAME= os.getenv("USERNAME", "default")

app = FastAPI(title="fo.ai API", version="0.1.0")

# Allow UI or external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input schema
class AnalyzeRequest(BaseModel):
    query: str

# Output schema
class Recommendation(BaseModel):
    InstanceId: str
    InstanceType: str
    Reason: str
    EstimatedSavings: float
    Tags: Any = None  # optional

class AnalyzeResponse(BaseModel):
    response: str
    raw: List[Recommendation]

@app.get("/status")
def status_check():
    return {"status": "ok", "message": "fo.ai API is running"}

from memory.redis_memory import append_to_list
import json
import os
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("USERNAME", "default")

    
@app.get("/memory", response_model=list)
def get_memory():
    USERNAME = os.getenv("USERNAME", "default")
    key = f"foai:chat:{USERNAME}"
    raw_entries = get_list(key, limit=20)

    # Parse JSON entries from Redis
    memory = []
    for item in raw_entries:
        try:
            memory.append(json.loads(item))
        except Exception as e:
            memory.append({"error": "Failed to parse item", "data": item})

    return memory

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    ec2_data = fetch_ec2_instances()
    rules = get_ec2_rules()

    recommendations = generate_recommendations(ec2_data, rules)

    if not recommendations:
        markdown_summary = "_No recommendations found._"
    else:
        markdown_summary = f"Based on your AWS cost data, {len(recommendations)} EC2 instance(s) appear underutilized.\n\n"
        for r in recommendations:
            az = r.get("AvailabilityZone", "unknown zone")
            instance_type = r.get("InstanceType", "unknown type")
            cpu = r.get("CPUUtilization", 0.0)
            reason = r.get("Reason", "No reason provided")
            savings = r.get("EstimatedSavings", 0.0)

            markdown_summary += (
                f"- Instance `{r['InstanceId']}` is a **{instance_type}** in `{az}` "
                f"with a 7-day average CPU of **{cpu:.2f}%**. {reason} "
                f"This could save approximately **${savings:.2f}**.\n"
            )

    # Log query + response to memory (after summary is ready)
    chat_entry = {
        "query": request.query,
        "response": markdown_summary
    }
    append_to_list(f"foai:chat:{USERNAME}", json.dumps(chat_entry))

    return {
        "response": markdown_summary,
        "raw": recommendations
    }
