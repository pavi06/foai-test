
# foai_ui.py – v0.1.3 Streaming Fix

import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# === Configurable Theme ===
SIDEBAR_BG = "#000000"     
PANEL_BG = "#F2EFE7"       
TEXT_COLOR = "#006A71"     

# Load .env
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Page setup
st.set_page_config(page_title="fo.ai – Cloud Cost Intelligence", layout="wide")

# === Inject Custom CSS ===
st.markdown(f"""
<style>
html, body, .main {{
    background-color: {PANEL_BG};
    color: {TEXT_COLOR};
}}
.block-container {{ padding-top: 2rem; }}
.stSidebar {{ background-color: {SIDEBAR_BG}; }}
.stButton>button {{
    background-color: #f0f0f0;
    color: #111;
    border: 1px solid #ddd;
    padding: 0.5rem 1rem;
    border-radius: 8px;
}}
.stButton>button:hover {{
    background-color: #e5e5e5;
}}
.stExpanderHeader {{ font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# === Sidebar ===
with st.sidebar:
    st.title("fo.ai")
    use_chat = st.toggle("💬 Chat Mode", value=True)
    use_live_data = st.toggle("📡 Live Data", value=not USE_MOCK_DATA)
    # Preferences Section
    st.sidebar.markdown("## ⚙️ Preferences")
    cpu_threshold = st.sidebar.slider("CPU Threshold (%)", min_value=1, max_value=100, value=10)
    min_uptime = st.sidebar.slider("Min Uptime (hrs)", min_value=0, max_value=168, value=24)
    min_savings = st.sidebar.slider("Min Savings ($)", min_value=0, max_value=100, value=5)
    excluded_tags = st.sidebar.text_input("Excluded Tags (CSV)", value="env=prod,do-not-touch")
    st.markdown("---")
    try:
        status = requests.get(f"{API_URL}/status").json()
        st.success(f"🟢 {status['message']}")
    except Exception:
        st.error("🔴 API offline")
    st.caption(f"Version: `{__version__}`")

# === Main Area ===
st.title("Cloud Cost Intelligence")

if not use_chat:
    st.info(f"**Mode:** {'Live AWS Data' if use_live_data else 'Mock Data'}")
    query = st.text_input("Ask a question about your AWS costs:")

    if st.button("Analyze") and query:
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

# === Chat UI Mode ===
else:
    st.info("💬 Chat mode streams live insights from the AI assistant.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    user_input = st.chat_input("Type a cost question...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Thinking..._")
            full_response = ""
            buffer = ""
            update_every = 5

            try:
                with requests.post(
                    f"{API_URL}/analyze/stream",
                    json={"user_id": "demo", "instance_ids": []},
                    stream=True,
                ) as r:
                    r.raise_for_status()
                    for i, chunk in enumerate(r.iter_content(chunk_size=1, decode_unicode=True)):
                        if chunk:
                            buffer += chunk
                            full_response += chunk
                            if i % update_every == 0:
                                placeholder.markdown(full_response)

                placeholder.markdown(full_response.strip())
                st.session_state.chat_history.append({"role": "assistant", "content": full_response.strip()})
            except Exception as e:
                placeholder.error(f"Streaming failed: {e}")
