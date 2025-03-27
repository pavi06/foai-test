# fo.ai/streamlit_app.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000/analyze")
st.set_page_config(page_title="fo.ai – FinOps Assistant")
st.title("fo.ai – Cloud Cost Intelligence")
query = st.text_input("Ask a cost optimization question:", placeholder="e.g. Where can I save on EC2?")
st.sidebar.markdown(f"**Version:** `{__version__}`")
if st.button("Analyze") and query:
    with st.spinner("Analyzing your AWS cost data..."):
        response = requests.post(
            API_URL,
            json={"query": query}
        )
        if response.status_code == 200:
            result = response.json()
            st.markdown("### ✅ Recommendation Summary")
            st.markdown(result["response"], unsafe_allow_html=True)
        else:
            st.error("API call failed. Check if the FastAPI server is running.")

