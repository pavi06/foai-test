# fo.ai/api.py
from fastapi import FastAPI
from pydantic import BaseModel
from app.graph import cost_graph

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/analyze", response_model=QueryResponse)
def analyze_query(request: QueryRequest):
    result = cost_graph.invoke({"query": request.query})
    return {"response": result["response"]}
