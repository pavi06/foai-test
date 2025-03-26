# fo.ai/main.py
from app.graph import cost_graph

if __name__ == "__main__":
    query = "Which EC2 instance is most optimized?"
    result = cost_graph.invoke({"query": query})
    print("\n--- Final Response ---\n")
    print(result["response"])
