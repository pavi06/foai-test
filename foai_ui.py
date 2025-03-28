# foai_ui.py
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# Load environment variables
load_dotenv()
API_URL = os.getenv("FOAI_API_URL", "http://localhost:8000/analyze")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Sidebar-based navigation theme toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

theme = "dark" if st.session_state.dark_mode else "light"

# Streamlit page config
st.set_page_config(page_title="fo.ai – AWS Cost Optimizer", layout="wide")

# --- Custom Theme + Sidebar Styling ---
if theme == "dark":
    st.markdown("""
        <style>
        .main { padding: 2rem; }
        .block-container { padding-top: 1rem; }
        .st-emotion-cache-6qob1r { background-color: #111827 !important; color: #F3F4F6; }
        .st-emotion-cache-1v0mbdj, .st-emotion-cache-13ln4jf { background-color: #1f2937 !important; border-radius: 10px; }
        .stButton>button { background-color: #10b981; color: white; border-radius: 8px; padding: 0.5rem 1rem; }
        .stButton>button:hover { background-color: #059669; }
        .stTabs [data-baseweb="tab"] { font-size: 1rem; padding: 0.5rem 1rem; }
        .stTabs [aria-selected="true"] { background-color: #374151; color: white; border-radius: 6px; }
        </style>
    """, unsafe_allow_html=True)

elif theme == "light":
    st.markdown("""
        <style>
        .main { padding: 2rem; }
        .block-container { padding-top: 1rem; }
        .st-emotion-cache-6qob1r { background-color: #ffffff !important; color: #111827; }
        .st-emotion-cache-1v0mbdj, .st-emotion-cache-13ln4jf { background-color: #f9fafb !important; border-radius: 10px; }
        .stButton>button { background-color: #2563eb; color: white; border-radius: 8px; padding: 0.5rem 1rem; }
        .stButton>button:hover { background-color: #1d4ed8; }
        .stTabs [data-baseweb="tab"] { font-size: 1rem; padding: 0.5rem 1rem; }
        .stTabs [aria-selected="true"] { background-color: #e0e7ff; color: #1e3a8a; border-radius: 6px; }
        </style>
    """, unsafe_allow_html=True)

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("## 🖥️ Main Menu")
    page = st.radio("Navigation", ["Home", "EC2 Insights", "Recommendations", "Settings"], label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"Version: `{__version__}`")
    # st.session_state.dark_mode = st.toggle("🌗 Dark Mode", value=st.session_state.dark_mode)
    st.caption("fo.ai – Cloud Cost Intelligence")

# --- Title ---
st.title("fo.ai – Cloud Cost Intelligence")

# --- Main Area ---
if page == "Home":
    col1, col2 = st.columns([3, 1])

    with col1:
        st.info(f"**Mode:** {'🔁 Mock Data' if USE_MOCK_DATA else '📡 Live AWS Data'}")
        query = st.text_input("Ask a cost optimization question:",
                              placeholder="e.g. Where can I save on EC2?")

        if st.button("Analyze") and query:
            with st.spinner("Analyzing your AWS cost data..."):
                response = requests.post(API_URL, json={"query": query})
                if response.status_code == 200:
                    result = response.json()
                    st.success("Recommendations Ready ✅")
                    st.markdown(result["response"], unsafe_allow_html=True)
                else:
                    st.error("API call failed. Check if the FastAPI server is running.")

    with col2:
        st.subheader("🧪 UI Controls")
        st.markdown("_More toggles coming soon (region, service, etc.)_")

elif page == "EC2 Insights":
    st.subheader("EC2 Inventory Snapshot")
    st.markdown("_This is a mock view for now – real instance data coming soon._")
    st.dataframe([
        {"Instance ID": "i-1234", "Type": "t3.large", "CPU %": 12, "Region": "us-east-1"},
        {"Instance ID": "i-5678", "Type": "m5.xlarge", "CPU %": 4, "Region": "us-west-2"}
    ])

elif page == "Recommendations":
    st.subheader("Optimization Opportunities")
    st.markdown("_Ask a question on the Home screen to get cost-saving suggestions from fo.ai_")

elif page == "Settings":
    st.subheader("⚙️ Settings (Coming Soon)")
    st.markdown("Here you'll be able to configure services, thresholds, and preferences.")
