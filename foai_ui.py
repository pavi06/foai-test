
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

#css
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&display=swap');

    .gradient-title {
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 500;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
    }

    .typewriter {
        overflow: hidden;
        border-right: 4px solid #667eea;
        padding-right: 0.3rem;
        padding-bottom: 0rem;
        white-space: nowrap;
        margin: 0 auto;
        animation: typing 3s steps(40, end), blink-caret 0.75s step-end infinite;
        max-width: fit-content;
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }

    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #667eea }
    }

    .subtitle {
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
            
    .subtitle1 {
        text-align: center;
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        margin-bottom: 1rem;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
                
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .user-message {
        border-left: 2px solid #2196f3;
        box-shadow: 0 2px 4px 0 #2196f3;
    }
    .assistant-message {
        border-left: 2px solid #9c27b0;
        box-shadow: 0 2px 4px 0 #9c27b0;
    }
    .sidebar .element-container {
        margin-bottom: 1rem;
        background: white;
    }
                
     /* Remove default Streamlit slider styling */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        height: 10px !important;
        border-radius: 3px !important;
    }
    
    /* Slider track (background) */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 3px !important;
    }
    
    /* Slider thumb hover effect */
    .stSlider > div > div > div > div > div:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5) !important;
        transform: scale(1.1) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Remove red color on focus/active */
    .stSlider > div > div > div > div:focus,
    .stSlider > div > div > div > div:active {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Slider labels */
    .stSlider > label {
        color:  white  !important;
        font-weight: 500 !important;
    }
                
    .centertext{
        text-align: center;
        padding: 0.5rem;
        text-transform: uppercase;
        font-weight: 600;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-family: 'Poppins', sans-serif;
    }
                
    .glassmorphic-container {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 1rem !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.2) !important;
    }
                
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 1rem !important;
        box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.2) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 1rem !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.2) !important;
    }
                
    [data-testid="stChatInputSubmitButton"] {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
                
    .stExpander {
        border: 1px solid #667eea !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 1px 2px rgba(102, 126, 234, 0.2) !important;  
    }
    
    summary:hover{
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
                
    summary div p{
        font-weight: 600;
        font-size: 1.2rem;
        font-family: 'Poppins', sans-serif;
        text-align: center;
    }
                
    summary:hover svg{
        fill: #6136cd !important; 
    }
    
    [data-testid="stSliderThumbValue"] {
        color: white !important;
    }
            
    button[data-testid="stBaseButton-headerNoPadding"] > span > span{
        fill: #6136cd !important; 
    }
            
    .st-emotion-cache-ujm5ma{
        fill: #6136cd !important;  
    }
                
    button[data-testid="stBaseButton-secondaryFormSubmit"]{
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%) !important;
        opacity: 0.8 !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        font-family: 'Poppins', sans-serif !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .stForm{
        display: flex;
        justify-content: center;
        align-items: center;
    }

    button[data-testid="stBaseButton-secondaryFormSubmit"]:hover {
        background: none !important;
        color: white !important;
        border: 1px solid #6136cd !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        font-family: 'Poppins', sans-serif !important;
    }
                
    [data-testid="stTextInputRootElement"]:focus{
        background: white !important;
        border: 1px solid pink !important;
    }
            
    label > div.toggle{
        background: #6136cd !important;    
    }
                
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="container">
    <h1 class="gradient-title typewriter ">fo.ai – Cloud Cost Intelligence</h1>
</div>
""", unsafe_allow_html=True)

# st.title("fo.ai – Cloud Cost Intelligence")

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
    # st.title("fo.ai")
    st.markdown(""" <div class="subtitle1 ">🤖 fo.ai</div> """, unsafe_allow_html=True)
    # st.markdown("### ⚙️ Preferences")
    st.markdown(""" <div class="subtitle ">Preferences</div> """, unsafe_allow_html=True)

    with st.form("preferences_form"):
        with st.expander("User Preferences", expanded=False):
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

        submitted = st.form_submit_button("Save Preferences")
        if submitted:
            save_preferences()
    # Chat toggle
    use_chat = st.sidebar.toggle("💬 Chat Mode", value=True)
    st.markdown("---")
    try:
        status = requests.get(f"{API_URL}/status").json()
        st.success(f"🟢 {status['message']}")
    except Exception:
        st.error("🔴 API offline")
    st.caption(f"Version: `{__version__}`")


# === Analyze Section ===
if not use_chat:
    st.markdown("### Analyze Your Cloud Spend")
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
    st.markdown("### Chat Mode")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    user_input = st.chat_input("Ask a cloud savings question...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

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
