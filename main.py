# fo.ai/main.py
import os
from dotenv import load_dotenv
from app.graph import cost_graph

load_dotenv()
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"

if __name__ == "__main__":
    query = "Are my EC2 instances optimized?"
    result = cost_graph.invoke({
        "query": query,
        "use_mock": USE_MOCK_DATA,
    })
    print("\n--- Final Response START ---\n")
    print(result["response"])
    print("\n--- Final Response END ---\n")