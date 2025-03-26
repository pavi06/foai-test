# fo.ai/app/nodes/analyze_query.py
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.state import CostState

llm = ChatOllama(model="llama3")

prompt = PromptTemplate.from_template("""
You are a cloud FinOps assistant. Classify the user's query into one of the following types:
- general
- ec2
- region
- service

Query: {query}
Type:
""")

def analyze_query(state: CostState) -> CostState:
    formatted_prompt = prompt.format(query=state["query"])
    result = llm.invoke(formatted_prompt)
    
    # Extract just the type
    output = result.content.strip().lower()
    if "ec2" in output:
        state["query_type"] = "ec2"
    elif "service" in output:
        state["query_type"] = "service"
    elif "region" in output:
        state["query_type"] = "region"
    else:
        state["query_type"] = "general"
    
    return state
