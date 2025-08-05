# fo.ai/app/nodes/generate_response.py
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.state import CostState
import pprint
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from typing import Generator


load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.5"))

llm = ChatOllama(model=LLM_MODEL, temprature=LLM_TEMPERATURE)

prompt = PromptTemplate.from_template("""
You are a FinOps assistant. Summarize the following cost optimization recommendations in plain language.
Be concise but helpful. Mention instance IDs, services, or cost values as needed for ec2 instances. 
And for s3 buckets, mention bucket details and provide recommended lifecycle policies. 

Recommendations:
{recommendations}

Summary:
""")

def generate_response(state: CostState) -> CostState:
    if DEBUG:
        print("\n[generate_response] State before response generation:")
        pprint.pprint(state)

    if not state.get("recommendations"):
        state["response"] = "No recommendations found. Everything looks optimized!"
        return state

    formatted = prompt.format(recommendations=state["recommendations"])
    result = llm.invoke(formatted)
    state["response"] = result.content.strip()

    if DEBUG:
        print("\n[generate_response] State after response generation:")
        pprint.pprint(state)

    return state

def stream_response(prompt: str) -> Generator[str, None, None]:
    """Yields streamed LLM response token by token."""

    print(f"\n[STREAM] Generating response for prompt: {prompt}")
    message = HumanMessage(content=prompt)
    print(f"[STREAM] Sending message to LLM: {message}")
    for chunk in llm.stream([message]):
        if chunk.content:
            yield chunk.content