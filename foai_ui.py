
import streamlit as st
import requests
import os
from dotenv import load_dotenv
from version import __version__

# Load environment
from config.settings import settings

API_URL = settings.FOAI_API_URL
USER_ID = settings.USERNAME
AWS_REGION = settings.AWS_REGION

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
    
    .session-info-card {
        background: transparent;
        border-radius: 10px;
        padding: 15px 20px;
        margin: 10px 0;
        border: 2px solid;
        border-image: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #f5576c) 1;
        position: relative;
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
    }
    
    .session-info-card::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #f5576c);
        border-radius: 12px;
        z-index: -1;
        opacity: 0.3;
    }
    
    .session-info-text {
        color: #e0e0e0;
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
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
    <h1 class="gradient-title typewriter ">fo.ai – Your Cloud Cost Companion</h1>
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
        st.warning(f"Could not load preferences: {e}")
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
        st.toast("Preferences saved", icon="💾")
    except Exception as e:
        st.error(f"Error saving preferences: {e}")

# Sidebar preferences UI
with st.sidebar:
    # st.title("fo.ai")
    st.markdown(""" <div class="subtitle1 ">fo.ai</div> """, unsafe_allow_html=True)
    # st.markdown("### ⚙️ Preferences")
    st.markdown(""" <div class="subtitle ">Your Settings</div> """, unsafe_allow_html=True)

    with st.form("preferences_form"):
        with st.expander("EC2 Settings", expanded=False):
            st.session_state.preferences["cpu_threshold"] = st.slider(
                "CPU Threshold (%)", 1, 100, st.session_state.preferences.get("cpu_threshold", 10)
            )
            st.session_state.preferences["min_uptime_hours"] = st.slider(
                "Min Uptime (hrs)", 0, 168, st.session_state.preferences.get("min_uptime_hours", 24)
            )
            st.session_state.preferences["min_savings_usd"] = st.slider(
                "Min Savings ($)", 0, 100, st.session_state.preferences.get("min_savings_usd", 5)
            )

        with st.expander("S3 Storage Settings", expanded=False):
            st.markdown("**Storage Class Transition Days:**")
            st.session_state.preferences["s3_standard_to_ia_days"] = st.slider(
                "Standard → IA (days)", 30, 365, st.session_state.preferences.get("s3_standard_to_ia_days", 30)
            )
            st.session_state.preferences["s3_ia_to_glacier_days"] = st.slider(
                "IA → Glacier (days)", 90, 2555, st.session_state.preferences.get("s3_ia_to_glacier_days", 90)
            )
            st.session_state.preferences["s3_glacier_to_deep_archive_days"] = st.slider(
                "Glacier → Deep Archive (days)", 180, 2555, st.session_state.preferences.get("s3_glacier_to_deep_archive_days", 180)
            )
            st.session_state.preferences["s3_expiration_days"] = st.slider(
                "Object Expiration (days)", 365, 3650, st.session_state.preferences.get("s3_expiration_days", 2555)
            )
            
            st.markdown("**Lifecycle Policy Settings:**")
            s3_excluded_tags = st.text_input(
                "S3 Excluded Tags (CSV)",
                value=", ".join(st.session_state.preferences.get("s3_excluded_tags", []))
            )
            st.session_state.preferences["s3_excluded_tags"] = [tag.strip() for tag in s3_excluded_tags.split(",") if tag.strip()]
            
            st.session_state.preferences["s3_include_previous_versions"] = st.checkbox(
                "Include Previous Versions", value=st.session_state.preferences.get("s3_include_previous_versions", False)
            )
            st.session_state.preferences["s3_include_delete_markers"] = st.checkbox(
                "Include Delete Markers", value=st.session_state.preferences.get("s3_include_delete_markers", False)
            )
            
            st.markdown("**Analysis Settings:**")
            st.session_state.preferences["s3_analyze_versioning"] = st.checkbox(
                "Analyze Versioning", value=st.session_state.preferences.get("s3_analyze_versioning", True)
            )
            st.session_state.preferences["s3_analyze_logging"] = st.checkbox(
                "Analyze Logging", value=st.session_state.preferences.get("s3_analyze_logging", True)
            )
            st.session_state.preferences["s3_analyze_encryption"] = st.checkbox(
                "Analyze Encryption", value=st.session_state.preferences.get("s3_analyze_encryption", True)
            )
            
            # Update transitions based on user preferences
            st.session_state.preferences["transitions"] = [
                {"days": st.session_state.preferences.get("s3_standard_to_ia_days", 30), "tier": "IA"},
                {"days": st.session_state.preferences.get("s3_ia_to_glacier_days", 90), "tier": "Glacier"},
                {"days": st.session_state.preferences.get("s3_glacier_to_deep_archive_days", 180), "tier": "Deep Archive"}
            ]

        with st.expander("Advanced Settings"):
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
    # Session Management
    st.markdown("---")
    st.markdown(""" <div class="subtitle ">Session Info</div> """, unsafe_allow_html=True)
    
    # Session info with gradient borders
    st.markdown(f"""
        <div class="session-info-card">
            <p class="session-info-text"><strong>User:</strong> {USER_ID}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="session-info-card">
            <p class="session-info-text"><strong>Region:</strong> {AWS_REGION}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Chat toggle
    use_chat = st.sidebar.toggle("💬 Chat Mode", value=True)
    
    # API Status
    st.markdown("---")
    try:
        status = requests.get(f"{API_URL}/status").json()
        st.success(f"🟢 {status['message']}")
    except Exception:
        st.error("🔴 API offline")
    
    # Memory Management
    if st.sidebar.button("Clear Chat History", use_container_width=True):
        try:
            # Clear chat history from Redis
            res = requests.delete(f"{API_URL}/memory", params={"user_id": USER_ID})
            res.raise_for_status()
            st.sidebar.success("Chat history cleared!")
            # Clear session state chat history
            if "chat_history" in st.session_state:
                st.session_state.chat_history = []
        except Exception as e:
            st.sidebar.error("Failed to clear history")
    

    
    st.caption(f"Version: `{__version__}`")


# === Analyze Section ===
if not use_chat:
    st.markdown("### What's Costing You Money?")
    
    # Example queries for non-chat mode
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        **Cost Analysis:**
        - "Which instances are wasting money?"
        - "Find underutilized EC2 instances"
        - "What's costing me money in S3?"
        
        ** Agent Actions **
        - "Stop instance i-1234567890abcdef0"
        - "Start instance i-1234567890abcdef0"
        - "Schedule shutdown for i-1234567890abcdef0 during non-business hours"
        - "Check status of instance i-1234567890abcdef0"
        - "List all running instances"
        """)
    
    query = st.text_input("Ask me anything about your cloud costs...")

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
                    st.success("Here's what I found:")
                    st.markdown(result.get("response", "No response"))

                    if "raw" in result and result["raw"]:
                        st.markdown("---")
                        st.subheader("The Details")
                        
                        # Show if this was a specific resource analysis
                        if result.get("is_specific_analysis"):
                            specific_resources = result.get("specific_resources", {})
                            ec2_instances = specific_resources.get("ec2_instances", [])
                            s3_buckets = specific_resources.get("s3_buckets", [])
                            
                            if ec2_instances:
                                st.info(f"**Specific Analysis**: Analyzing {len(ec2_instances)} EC2 instance(s): {', '.join(ec2_instances)}")
                            if s3_buckets:
                                st.info(f"**Specific Analysis**: Analyzing {len(s3_buckets)} S3 bucket(s): {', '.join(s3_buckets)}")
                        
                        # Check if it's EC2 or S3 data and display accordingly
                        if result.get("service_type") == "ec2" or any("InstanceId" in rec for rec in result["raw"]):
                            # EC2 recommendations
                            st.markdown("### **Your EC2 Instances**")
                            
                            # Summary metrics
                            total_savings = sum(rec.get("EstimatedSavings", 0) for rec in result["raw"])
                            total_cost = sum(rec.get("MonthlyCost", 0) for rec in result["raw"])
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Instances", len(result["raw"]))
                            with col2:
                                st.metric("Total Monthly Cost", f"${total_cost:.2f}")
                            with col3:
                                st.metric("Potential Savings", f"${total_savings:.2f}")
                            
                            # Detailed instance breakdown
                            for i, rec in enumerate(result["raw"], 1):
                                instance_id = rec.get("InstanceId", "Unknown")
                                instance_type = rec.get("InstanceType", "Unknown")
                                avg_cpu = rec.get("AverageCPU", 0)
                                monthly_cost = rec.get("MonthlyCost", 0)
                                savings = rec.get("EstimatedSavings", 0)
                                availability_zone = rec.get("AvailabilityZone", "Unknown")
                                priority = rec.get("Priority", "Unknown")
                                
                                # Color code based on priority
                                if priority == "High":
                                    expander_title = f"🔴 {i}. {instance_id} ({instance_type}) - High Priority"
                                elif priority == "Medium":
                                    expander_title = f"🟡 {i}. {instance_id} ({instance_type}) - Medium Priority"
                                else:
                                    expander_title = f"🟢 {i}. {instance_id} ({instance_type}) - Low Priority"
                                
                                with st.expander(expander_title, expanded=True):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown(f"**Instance ID:** `{instance_id}`")
                                        st.markdown(f"**Instance Type:** {instance_type}")
                                        st.markdown(f"**Availability Zone:** {availability_zone}")
                                        st.markdown(f"**Priority:** {priority}")
                                        
                                        # CPU usage with color coding
                                        if avg_cpu < 10:
                                            st.markdown(f"**CPU Usage:** 🟢 {avg_cpu}% (Very Low)")
                                        elif avg_cpu < 30:
                                            st.markdown(f"**CPU Usage:** 🟡 {avg_cpu}% (Low)")
                                        else:
                                            st.markdown(f"**CPU Usage:** 🔴 {avg_cpu}% (Moderate)")
                                    
                                    with col2:
                                        st.metric("Monthly Cost", f"${monthly_cost:.2f}")
                                        st.metric("Potential Savings", f"${savings:.2f}")
                                        st.metric("Savings %", f"{(savings/monthly_cost*100):.1f}%" if monthly_cost > 0 else "0%")
                                    
                                                            # Recommendation details
                        if "Recommendation" in rec:
                            rec_details = rec["Recommendation"]
                            st.markdown("---")
                            st.markdown(f"**Recommended Action:** {rec_details.get('Action', 'No action specified')}")
                            st.markdown(f"**Reason:** {rec_details.get('Reason', 'No reason provided')}")
                            st.markdown(f"**Impact:** {rec_details.get('Impact', 'Unknown')}")
                        

                        
                        # Tags
                        if tags := rec.get("Tags"):
                            st.markdown("---")
                            st.markdown("**Tags:**")
                            tag_text = ", ".join([f"`{t['Key']}={t['Value']}`" for t in tags])
                            st.markdown(tag_text)
                        
                        elif result.get("service_type") == "s3" or any("BucketName" in rec for rec in result["raw"]):
                            # S3 recommendations
                            st.markdown("### **S3 Bucket Details**")
                            
                            # Summary metrics
                            total_savings = sum(rec.get("CostAnalysis", {}).get("PotentialSavings", 0) for rec in result["raw"])
                            total_cost = sum(rec.get("CostAnalysis", {}).get("CurrentMonthlyCost", 0) for rec in result["raw"])
                            total_size = sum(rec.get("ObjectStatistics", {}).get("TotalSizeGB", 0) for rec in result["raw"])
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Buckets", len(result["raw"]))
                            with col2:
                                st.metric("Total Size", f"{total_size:.2f} GB")
                            with col3:
                                st.metric("Monthly Cost", f"${total_cost:.2f}")
                            with col4:
                                st.metric("Potential Savings", f"${total_savings:.2f}")
                            
                            # Detailed bucket breakdown
                            for i, rec in enumerate(result["raw"], 1):
                                bucket_name = rec.get("BucketName", "Unknown")
                                basic_info = rec.get("BasicInfo", {})
                                object_stats = rec.get("ObjectStatistics", {})
                                cost_analysis = rec.get("CostAnalysis", {})
                                rec_details = rec.get("Recommendation", {})
                                
                                # Determine priority based on savings
                                savings = cost_analysis.get("PotentialSavings", 0)
                                if savings > 10:
                                    priority = "High"
                                    expander_title = f"🔴 {i}. {bucket_name} - High Priority"
                                elif savings > 5:
                                    priority = "Medium"
                                    expander_title = f"🟡 {i}. {bucket_name} - Medium Priority"
                                else:
                                    priority = "Low"
                                    expander_title = f"🟢 {i}. {bucket_name} - Low Priority"
                                
                                with st.expander(expander_title, expanded=True):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.markdown(f"**Bucket Name:** `{bucket_name}`")
                                        st.markdown(f"**Region:** {basic_info.get('Region', 'Unknown')}")
                                        st.markdown(f"**Priority:** {priority}")
                                        st.markdown(f"**Versioning:** {basic_info.get('Versioning', 'Unknown')}")
                                        st.markdown(f"**Logging:** {'Enabled' if basic_info.get('LoggingEnabled') else 'Disabled'}")
                                        st.markdown(f"**Encryption:** {basic_info.get('EncryptionType', 'None')}")
                                    
                                    with col2:
                                        st.metric("Objects", f"{object_stats.get('TotalObjects', 0):,}")
                                        st.metric("Size", f"{object_stats.get('TotalSizeGB', 0):.2f} GB")
                                        st.metric("Monthly Cost", f"${cost_analysis.get('CurrentMonthlyCost', 0):.2f}")
                                        st.metric("Potential Savings", f"${savings:.2f}")
                                    
                                    # Recommendation details
                                    if rec_details:
                                        st.markdown("---")
                                        st.markdown(f"**Recommended Action:** {rec_details.get('Action', 'No action specified')}")
                                        st.markdown(f"**Reason:** {rec_details.get('Reason', 'No reason provided')}")
                                        st.markdown(f"**Days Since Last Modified:** {rec_details.get('DaysSinceLastModified', 0)}")
                                        st.markdown(f"**Target Storage Class:** {rec_details.get('TargetStorageClass', 'Unknown')}")
                                        st.markdown(f"**Impact:** {rec_details.get('Impact', 'Unknown')}")
                                    
                                    # Tags
                                    if tags := basic_info.get("Tags"):
                                        st.markdown("---")
                                        st.markdown("**Tags:**")
                                        tag_text = ", ".join([f"`{t['Key']}={t['Value']}`" for t in tags])
                                        st.markdown(tag_text)
                        
                        else:
                            # Generic display for mixed or unknown data
                            for rec in result["raw"]:
                                with st.expander(f"Recommendation {result['raw'].index(rec) + 1}"):
                                    st.json(rec)
            except Exception as e:
                st.error(f"API call failed: {e}")
    
else:
    st.markdown("### Let's Chat About Your Cloud Costs")
    
    # Example queries
    with st.expander("Example Queries", expanded=False):
        st.markdown("""
        **Ask about EC2:**
        - "Which instances are wasting money?"
        - "Find underutilized EC2 instances"
        - "What's wrong with instance i-1234567890abcdef0?"
        - "Should I keep instance i-0fbcfd48d33cb9245 running?"
        - "Which instances can I stop to save money?"

        
        **Ask about S3:**
        - "Which buckets need lifecycle policies?"
        - "What's costing me money in S3?"
        - "Check bucket 'pavi-test-bucket' for optimization"
        - "Which buckets have old data that could be archived?"
        - "How can I save money on storage?"
        
        **Enforce Actions:**
        - "Stop instance i-1234567890abcdef0"
        - "Start instance i-1234567890abcdef0"
        - "Schedule shutdown for i-1234567890abcdef0 during non-business hours"
        - "Schedule startup for i-1234567890abcdef0 at 8 AM"
        - "Check status of instance i-1234567890abcdef0"
        - "List all running instances"
        - "Delete shutdown schedule for i-1234567890abcdef0"
        
        **General questions:**
        - "What are my biggest cost optimization opportunities?"
        - "Where can I save cost on compute resources?"
        - "What's costing me the most money?"
        - "Give me a cost analysis of my resources"
        """)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for entry in st.session_state.chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    user_input = st.chat_input("What would you like to know about your cloud costs?")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("_Let me check your AWS resources..._")
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
