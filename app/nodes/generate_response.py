# fo.ai/app/nodes/generate_response.py
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.state import CostState

llm = ChatOllama(model="llama3")

prompt = PromptTemplate.from_template("""
You are a FinOps assistant. Summarize the following cost optimization recommendations in plain language.
Be concise but helpful. Mention instance IDs, services, or cost values as needed.

Recommendations:
{recommendations}

Summary:
""")

def generate_response(state: CostState) -> CostState:
    if not state.get("recommendations"):
        state["response"] = "No recommendations found. Everything looks optimized!"
        return state

    formatted = prompt.format(recommendations=state["recommendations"])
    result = llm.invoke(formatted)
    state["response"] = result.content.strip()
    return state
