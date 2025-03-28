# api.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, List

from data.aws.ec2 import fetch_ec2_instances
from app.nodes.generate_recommendations import generate_recommendations
from rules.aws.ec2_rules import get_ec2_rules

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

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    ec2_data = fetch_ec2_instances()
    rules = get_ec2_rules()

    recommendations = generate_recommendations(ec2_data, rules)

    summary_lines = [
        f"**💻 {r['InstanceId']}** → {r['Reason']} (💰 saves ~${r['EstimatedSavings']:.2f})"
        for r in recommendations
    ]
    markdown_summary = "\n\n".join(summary_lines) if summary_lines else "_No recommendations found._"

    return {
        "response": markdown_summary,
        "raw": recommendations
    }
