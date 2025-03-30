# foai_ui.py

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# Load environment variables
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Page config
st.set_page_config(page_title="fo.ai – Cloud Cost Intelligence", layout="wide")

# Set light theme always
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .block-container { padding-top: 1rem; }
    .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; padding: 0.5rem 1rem; }
    .stButton>button:hover { background-color: #1d4ed8; }
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
        st.error("🔴 API offline or unreachable")

# --- Main Area ---
st.title("Cloud Cost Intelligence")

st.info(f"**Mode:** {'🔁 Mock Data' if USE_MOCK_DATA else '📡 Live AWS Data'}")

query = st.text_input("Ask a cost optimization question:")
if st.button("Analyze") and query:
    with st.spinner("Analyzing your AWS cost data..."):
        try:
            response = requests.post(f"{API_URL}/analyze", json={"query": query})
            response.raise_for_status()
            result = response.json()

            st.success("Recommendations Ready ✅")
            st.markdown(result["response"], unsafe_allow_html=True)

            if "raw" in result and result["raw"]:
                st.markdown("---")
                st.subheader("🔍 Detailed Recommendations")

                for rec in result["raw"]:
                    with st.expander(f"💻 {rec.get('InstanceId')} – {rec.get('InstanceType')}"):
                        st.markdown(f"**Recommended because:** {rec.get('Reason', 'No explanation available')}")
                        st.markdown(f"**Estimated Monthly Savings:** `${rec.get('EstimatedSavings', 0):.2f}`")
                        if tags := rec.get("Tags"):
                            tag_str = ", ".join([f"{tag['Key']}={tag['Value']}" for tag in tags])
                            st.markdown(f"**Tags:** `{tag_str}`")
            else:
                st.warning("No recommendations found.")

        except Exception as e:
            st.error(f"API call failed: {e}")
