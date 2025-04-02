
import streamlit as st
import requests
import json

st.set_page_config(page_title="fo.ai – Cloud Cost Intelligence", layout="wide")

# --- Sidebar ---
st.sidebar.title("fo.ai – Cloud Cost Intelligence")

# Chat/Analyze Mode Toggle
mode = st.sidebar.toggle("Chat Mode", value=True)
use_mock = st.sidebar.toggle("Mock Data Mode", value=False)

# Preferences Section
st.sidebar.markdown("## ⚙️ Preferences")

cpu_threshold = st.sidebar.slider("CPU Threshold (%)", min_value=1, max_value=100, value=10)
min_uptime = st.sidebar.slider("Min Uptime (hrs)", min_value=0, max_value=168, value=24)
min_savings = st.sidebar.slider("Min Savings ($)", min_value=0, max_value=100, value=5)
excluded_tags = st.sidebar.text_input("Excluded Tags (CSV)", value="env=prod,do-not-touch")

# Footer
st.sidebar.markdown("---")
st.sidebar.success("API: Live on http://localhost:8000")
st.sidebar.caption("Version: 0.1.3")

# --- Main Panel ---
if mode:
    st.header("💬 Chat with fo.ai")
    user_query = st.text_input("Ask something about your cloud usage", key="chat_query")

    if user_query:
        with st.spinner("Thinking..."):
            response = requests.post("http://localhost:8000/analyze/stream", json={
                "query": user_query,
                "user_id": "demo",
                "mock": use_mock
            }, stream=True)

            full_response = ""
            placeholder = st.empty()

            for chunk in response.iter_content(chunk_size=1):
                if chunk:
                    full_response += chunk.decode()
                    placeholder.markdown(full_response)

else:
    st.header("📊 One-Click Analyze")
    analyze_query = st.text_input("Enter a cost-saving query", value="any idle instances?", key="analyze_query")

    if st.button("Analyze"):
        with st.spinner("Fetching recommendations..."):
            result = requests.post("http://localhost:8000/analyze", json={
                "query": analyze_query,
                "user_id": "demo",
                "mock": use_mock
            })

            if result.ok:
                data = result.json()
                st.markdown(data.get("response", "No response"))
                st.json(data.get("raw", {}))
            else:
                st.error("API error")
