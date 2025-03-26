# fo.ai/main.py
import os
from dotenv import load_dotenv
from app.graph import cost_graph

load_dotenv()
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() == "true"

if __name__ == "__main__":
    query = "How can I reduce my AWS waste?"
    result = cost_graph.invoke({
        "query": query,
        "use_mock": USE_MOCK_DATA,
    })
    print("\n--- Final Response ---\n")
    print(result["response"])
