# fo.ai/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.graph import cost_graph
import os
from dotenv import load_dotenv

load_dotenv()
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"

app = FastAPI(
    title="fo.ai – FinOps AI API",
    description="API to analyze cloud cost optimization opportunities",
    version="0.1.0"
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/analyze", response_model=QueryResponse)
def analyze_query(request: QueryRequest):
    result = cost_graph.invoke({
        "query": request.query,
        "use_mock": USE_MOCK_DATA
    })
    return {"response": result["response"]}

