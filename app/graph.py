# fo.ai/app/graph.py
from langgraph.graph import StateGraph
from app.state import CostState
from app.nodes.analyze_query import analyze_query
from app.nodes.fetch_data import fetch_data
from app.nodes.generate_recommendations import generate_recommendations
from app.nodes.generate_response import generate_response

# Step 1: Initialize the graph
builder = StateGraph(CostState)

# Step 2: Add nodes
builder.add_node("analyze_query", analyze_query)
builder.add_node("fetch_mock_data", fetch_data)
builder.add_node("generate_recommendations", generate_recommendations)
builder.add_node("generate_response", generate_response)

# Step 3: Set entry point and flow
builder.set_entry_point("analyze_query")

builder.add_edge("analyze_query", "fetch_mock_data")
builder.add_edge("fetch_mock_data", "generate_recommendations")
builder.add_edge("generate_recommendations", "generate_response")

# Step 4: Set finish
builder.set_finish_point("generate_response")

# Step 5: Compile
cost_graph = builder.compile()
