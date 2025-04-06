
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# Load environment
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000")
USER_ID = os.getenv("USERNAME", "default_user")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

st.set_page_config(page_title="fo.ai – Cloud Cost Intelligence", layout="wide")
st.title("fo.ai – Cloud Cost Intelligence")

# Load preferences from Redis (once)
@st.cache_data(show_spinner=False)
def load_preferences_from_api():
    try:
        res = requests.get(f"{API_URL}/preferences/load", params={"user_id": USER_ID})
        res.raise_for_status()
        return res.json().get("preferences", {})
    except Exception as e:
        st.warning(f"⚠️ Could not load preferences: {e}")
        return {}

# Initialize session state
if "preferences" not in st.session_state:
    st.session_state.preferences = load_preferences_from_api()

def save_preferences():
    try:
        r = requests.post(f"{API_URL}/preferences/save", json={
            "user_id": USER_ID,
            "preferences": st.session_state.preferences
        })
        r.raise_for_status()
        st.toast("✅ Preferences saved", icon="💾")
    except Exception as e:
        st.error(f"❌ Error saving preferences: {e}")

# Sidebar preferences UI
with st.sidebar:
    st.title("fo.ai")
    st.markdown("## ⚙️ Preferences")

    with st.form("preferences_form"):
        with st.expander("User Preferences", expanded=True):
            st.session_state.preferences["cpu_threshold"] = st.slider(
                "CPU Threshold (%)", 1, 100, st.session_state.preferences.get("cpu_threshold", 10)
            )
            st.session_state.preferences["min_uptime_hours"] = st.slider(
                "Min Uptime (hrs)", 0, 168, st.session_state.preferences.get("min_uptime_hours", 24)
            )
            st.session_state.preferences["min_savings_usd"] = st.slider(
                "Min Savings ($)", 0, 100, st.session_state.preferences.get("min_savings_usd", 5)
            )

        with st.expander("Advanced Preferences"):
            tags = st.text_input(
                "Excluded Tags (CSV)",
                value=", ".join(st.session_state.preferences.get("excluded_tags", []))
            )
            st.session_state.preferences["excluded_tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]

            st.session_state.preferences["idle_7day_cpu_threshold"] = st.slider(
                "Idle 7-day CPU (%)", 1, 100, st.session_state.preferences.get("idle_7day_cpu_threshold", 5)
            )

        submitted = st.form_submit_button("Apply Changes")
        if submitted:
            save_preferences()

# Chat toggle
use_chat = st.sidebar.toggle("💬 Chat Mode", value=True)

# === Analyze Section ===
if not use_chat:
    st.markdown("## 🔍 Analyze Your Cloud Spend")
    query = st.text_input("Ask a cost-related question")

    if st.button("Analyze"):
        if not query:
            st.warning("Enter a query first.")
        else:
            try:
                with st.spinner("Analyzing..."):
                    res = requests.post(f"{API_URL}/analyze", json={
                        "query": query,
                        "user_id": USER_ID,
                        "region": AWS_REGION,
                        "preferences": st.session_state.preferences
                    })
                    res.raise_for_status()
                    result = res.json()
                    st.success("✅ Result:")
                    st.markdown(result.get("response", "No response"))

                    if "raw" in result and result["raw"]:
                        st.markdown("---")
                        st.subheader("📊 Detailed Optimization Findings")
                        for rec in result["raw"]:
                            with st.expander(f"💻 {rec.get('InstanceId')} – {rec.get('InstanceType')}"):
                                st.markdown(f"**Reason:** {rec.get('Reason')}")
                                # st.markdown(f"**Savings:** `${{rec.get('EstimatedSavings', 0):.2f}}`")
                                savings = rec.get("EstimatedSavings", 0)
                                st.markdown(f"**Savings:** `${savings:.2f}`")
                                if tags := rec.get("Tags"):
                                    st.markdown("**Tags:** `" + ", ".join([f"{t['Key']}={t['Value']}" for t in tags]) + "`")
            except Exception as e:
                st.error(f"API call failed: {e}")
else:
    st.markdown("## 💬 Chat Mode")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    user_input = st.chat_input("Ask a cloud savings question...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Thinking..._")
            full_response = ""

            try:
                with requests.post(
                    f"{API_URL}/analyze/stream",
                    json={
                        "user_id": USER_ID,
                        "region": AWS_REGION,
                        "query": user_input,
                        "preferences": st.session_state.preferences
                    },
                    stream=True,
                ) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=1, decode_unicode=True):
                        if chunk:
                            full_response += chunk
                            placeholder.markdown(full_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_response.strip()})
            except Exception as e:
                placeholder.error(f"Streaming failed: {e}")
