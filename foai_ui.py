# foai_ui.py – Clean UI for fo.ai

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# Load .env and base settings
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Page setup
st.set_page_config(page_title="fo.ai – Cloud Cost Intelligence", layout="wide")

# Inject custom minimalist theme
st.markdown("""
    <style>
    html, body, .main {
        background-color: #ffffff;
        color: #333333;
    }
    .block-container { padding-top: 2rem; }
    .stButton>button {
        background-color: #f0f0f0;
        color: #111;
        border: 1px solid #ddd;
        padding: 0.5rem 1rem;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #e5e5e5;
    }
    .stSidebar { background-color: #f9f9f9; }
    .stExpanderHeader { font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("fo.ai")
    st.caption("Cloud Cost Intelligence")
    st.caption(f"Version: `{__version__}`")

    # Health check
    try:
        status = requests.get(f"{API_URL}/status").json()
        st.success(f"🟢 {status['message']}")
    except Exception:
        st.error("🔴 API offline")

    st.markdown("---")
    mode = st.radio("Choose Mode", ["Analyze", "Chat (Stream)"], index=0)

# --- Main Content ---
st.title("Cloud Cost Optimization Assistant")
st.info(f"**Mode:** {'Mock Data' if USE_MOCK_DATA else 'Live AWS'}")

query = st.text_input("Ask a question about your AWS costs:")

if mode == "Analyze":
    if st.button("Run Analysis") and query:
        with st.spinner("Analyzing your cost data..."):
            try:
                response = requests.post(f"{API_URL}/analyze", json={"query": query})
                response.raise_for_status()
                result = response.json()

                st.success("✅ Recommendations Ready")
                st.markdown(result["response"], unsafe_allow_html=True)

                if "raw" in result and result["raw"]:
                    st.markdown("---")
                    st.subheader("📊 Detailed Optimization Findings")
                    for rec in result["raw"]:
                        with st.expander(f"💻 {rec.get('InstanceId')} – {rec.get('InstanceType')}"):
                            st.markdown(f"**Reason:** {rec.get('Reason')}")
                            st.markdown(f"**Savings:** `${rec.get('EstimatedSavings', 0):.2f}`")
                            if tags := rec.get("Tags"):
                                st.markdown("**Tags:** `" + ", ".join([f"{t['Key']}={t['Value']}" for t in tags]) + "`")
                else:
                    st.warning("No optimizations found.")
            except Exception as e:
                st.error(f"API call failed: {e}")

elif mode == "Chat (Stream)":
    if st.button("Stream Summary") and query:
        with st.spinner("Streaming summary..."):
            try:
                with requests.post(
                    f"{API_URL}/analyze/stream",
                    json={"user_id": "demo", "instance_ids": []},
                    stream=True,
                ) as r:
                    r.raise_for_status()
                    streamed = st.empty()
                    summary = ""
                    for chunk in r.iter_content(chunk_size=256, decode_unicode=True):
                        summary += chunk
                        streamed.markdown(summary)
                st.success("✅ Stream complete")
            except Exception as e:
                st.error(f"Streaming failed: {e}")
