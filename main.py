# fo.ai/main.py
from app.graph import cost_graph

if __name__ == "__main__":
    query = "What are some cost optimization recommendations for my EC2 instances?"
    result = cost_graph.invoke({"query": query})
    print("\n--- Final Response ---\n")
    print(result["response"])
