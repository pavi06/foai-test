# 🤖 **fo.ai Agent Integration Guide**

## 🔍 **How It Works - Complete Flow**

The agent integration seamlessly connects the Streamlit UI with the agent tools. Here's the complete flow:

### **1. User Input in Streamlit**
```
User types: "Stop instance i-1234567890abcdef0"
```

### **2. Streamlit UI Processing**
```python
# foai_ui.py sends request to /analyze endpoint
requests.post(f"{API_URL}/analyze", json={
    "query": "Stop instance i-1234567890abcdef0",
    "user_id": USER_ID,
    "region": AWS_REGION
})
```

### **3. API Detection & Routing**
```python
# api.py detect_service_type() function
def detect_service_type(query: str) -> dict:
    # Detects agent action keywords: "stop", "start", "schedule", etc.
    agent_action_keywords = [
        "stop", "start", "shutdown", "power off", "power on", 
        "schedule", "schedule shutdown", "schedule startup"
    ]
    
    # If agent keywords found + EC2 keywords → service_type = "agent_ec2"
    if agent_score > 0 and (ec2_score > 0 or "instance" in query_lower):
        service_type = "agent_ec2"
```

### **4. Agent Processing**
```python
# api.py analyze_fallback() function
if service_type == "agent_ec2":
    # Initialize agent integration
    cog_integration = CogIntegration(region=request.region)
    
    # Process natural language request
    agent_result = cog_integration.process_natural_language(request.query)
    
    # Execute the action
    # Returns: {"success": True, "message": "Successfully stopped instance..."}
```

### **5. Response Formatting**
```python
# Format response for Streamlit display
formatted_response = f"## 🤖 **Agent Action Completed**\n\n"
formatted_response += f"**Query:** {request.query}\n\n"
formatted_response += f"**Result:** {message}\n\n"
formatted_response += f"**Instance:** `{instance_id}`\n\n"
```

### **6. Streamlit Display**
```
🤖 Agent Action Completed

Query: Stop instance i-1234567890abcdef0

Result: Successfully initiated stop for instance i-1234567890abcdef0

Instance: i-1234567890abcdef0

Action Type: stop_instance
```

## 🔧 **Technical Implementation**

### **Query Detection Logic**

The system uses **keyword-based detection** to identify agent actions:

```python
# Agent action keywords
agent_action_keywords = [
    "stop", "start", "shutdown", "power off", "power on", "boot", 
    "turn off", "turn on", "schedule", "schedule shutdown", 
    "schedule startup", "auto shutdown", "auto start",
    "delete schedule", "remove schedule", "cancel schedule", 
    "list schedules"
]

# EC2 keywords
ec2_keywords = ["ec2", "instance", "cpu", "compute", "server", "machine", "virtual"]

# Detection logic
if agent_score > 0 and (ec2_score > 0 or "instance" in query_lower):
    service_type = "agent_ec2"
```

### **Service Type Classification**

| Query Type | Keywords Detected | Service Type | Action |
|------------|-------------------|--------------|---------|
| Agent Action | "stop" + "instance" | `agent_ec2` | Execute agent action |
| Cost Analysis | "wasting money" + "instance" | `ec2` | Generate recommendations |
| S3 Analysis | "bucket" + "lifecycle" | `s3` | Generate S3 recommendations |
| Mixed | Both EC2 and S3 keywords | `mixed` | Analyze both services |

### **Agent Integration Points**

#### **1. Main Analysis Endpoint (`/analyze`)**
```python
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    # Tries state graph first, falls back to direct calls
    try:
        result = cost_graph.invoke(graph_state)
        # ... state graph processing
    except Exception as e:
        return analyze_fallback(request, user_id, rules)  # ← Agent processing here
```

#### **2. Fallback Analysis Function**
```python
def analyze_fallback(request: AnalyzeRequest, user_id: str, rules: dict):
    service_type_info = detect_service_type(request.query)
    service_type = service_type_info["service_type"]
    
    if service_type == "agent_ec2":
        # ← Agent processing logic
        cog_integration = CogIntegration(region=request.region)
        agent_result = cog_integration.process_natural_language(request.query)
        # ... format and return response
```

#### **3. Streaming Analysis (`/analyze/stream`)**
```python
@app.post("/analyze/stream")
async def stream_analysis(req: AnalyzeStreamRequest):
    service_type_info = detect_service_type(req.query)
    service_type = service_type_info["service_type"]
    
    if service_type == "agent_ec2":
        # ← Agent processing for streaming
        cog_integration = CogIntegration(region=req.region)
        agent_result = cog_integration.process_natural_language(req.query)
        prompt = f"🤖 Agent Action Completed: {message}"
```

## 📋 **Available Agent Actions**

### **Immediate Actions**
| Action | Query Examples | Description |
|--------|---------------|-------------|
| `stop_instance` | "Stop instance i-1234567890abcdef0" | Immediately stop an EC2 instance |
| `start_instance` | "Start instance i-1234567890abcdef0" | Start a stopped EC2 instance |
| `get_instance_status` | "Check status of i-1234567890abcdef0" | Get detailed instance information |
| `list_instances` | "List all running instances" | List instances with filtering |

### **Scheduling Actions**
| Action | Query Examples | Description |
|--------|---------------|-------------|
| `schedule_shutdown` | "Schedule shutdown for i-1234567890abcdef0 during non-business hours" | Create automated shutdown schedule |
| `schedule_startup` | "Schedule startup for i-1234567890abcdef0 at 8 AM" | Create automated startup schedule |
| `delete_schedule` | "Delete shutdown schedule for i-1234567890abcdef0" | Remove existing schedule |
| `list_schedules` | "List all schedules" | View all scheduled actions |

### **Supported Time Periods**
- **"non-business hours"** → 6 PM - 8 AM weekdays
- **"business hours"** → 8 AM - 6 PM weekdays
- **"weekend"** → Friday 6 PM - Monday 8 AM
- **"overnight"** → 10 PM - 6 AM daily
- **"6 PM"** or **"18:00"** → Specific time
- **"8 AM"** or **"08:00"** → Specific time

## 🎯 **User Experience Flow**

### **1. User Types Query**
```
User: "Stop instance i-1234567890abcdef0"
```

### **2. System Detection**
```
🔍 [SERVICE DETECTION] Query: 'Stop instance i-1234567890abcdef0'
   📊 Service type: agent_ec2
   🖥️  EC2 instances found: ['i-1234567890abcdef0']
```

### **3. Agent Processing**
```
🤖 [AGENT] Detected agent action request: Stop instance i-1234567890abcdef0
✅ [AGENT] Action executed successfully
```

### **4. Response Display**
```
🤖 Agent Action Completed

Query: Stop instance i-1234567890abcdef0

Result: Successfully initiated stop for instance i-1234567890abcdef0

Instance: i-1234567890abcdef0

Action Type: stop_instance
```

## 🔄 **Integration Points**

### **1. Streamlit UI (`foai_ui.py`)**
- ✅ **Same input field** for both analysis and agent actions
- ✅ **Example queries** include agent actions
- ✅ **Chat mode** supports agent actions
- ✅ **Non-chat mode** supports agent actions

### **2. API Layer (`api.py`)**
- ✅ **Unified endpoint** (`/analyze`) handles both analysis and actions
- ✅ **Automatic detection** of agent vs analysis queries
- ✅ **Streaming support** for agent actions
- ✅ **Error handling** for invalid agent queries

### **3. Agent System (`app/agents/`)**
- ✅ **Natural language processing** for query understanding
- ✅ **AWS integration** for actual EC2 operations
- ✅ **Scheduling system** using CloudWatch Events and Lambda
- ✅ **Action history** and logging

## 🧪 **Testing the Integration**

### **1. Test Query Detection**
```bash
python test_agent_integration.py
```

### **2. Test Specific Scenarios**
```bash
# Test agent detection
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "Stop instance i-1234567890abcdef0", "user_id": "test", "region": "us-east-1"}'

# Test regular analysis (should not trigger agent)
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "Which instances are wasting money?", "user_id": "test", "region": "us-east-1"}'
```

### **3. Test in Streamlit UI**
1. Start the application: `python foai_cli.py server start all`
2. Open Streamlit: `streamlit run foai_ui.py`
3. Try agent queries in the input field

## 🚨 **Error Handling**

### **1. Invalid Instance ID**
```
❌ Agent Action Failed

Query: Stop instance invalid-id

Error: Invalid parameters for action: stop_instance

Suggestions:
- Stop instance i-1234567890abcdef0
- Start instance i-1234567890abcdef0
```

### **2. Missing Permissions**
```
❌ Agent Processing Error

Query: Stop instance i-1234567890abcdef0

Error: User is not authorized to perform: ec2:StopInstances

Please ensure the agent system is properly configured.
```

### **3. Instance Not Found**
```
❌ Agent Action Failed

Query: Stop instance i-1234567890abcdef0

Error: AWS error: The instance ID 'i-1234567890abcdef0' does not exist
```

## 🔒 **Security Considerations**

### **1. Permission Validation**
- ✅ **Parameter validation** before execution
- ✅ **Instance ID format** validation
- ✅ **AWS permission** checks
- ✅ **Action history** logging

### **2. Safe Defaults**
- ✅ **Force stop** requires explicit parameter
- ✅ **Scheduling** requires valid time periods
- ✅ **Error messages** don't expose sensitive information

### **3. Audit Trail**
- ✅ **All actions** logged to chat history
- ✅ **Agent results** stored for review
- ✅ **User identification** for accountability

## 📈 **Performance Characteristics**

### **Response Times**
- **Query Detection**: < 100ms
- **Agent Processing**: 1-3 seconds
- **AWS API Calls**: 2-5 seconds
- **Total Response**: 3-8 seconds

### **Scalability**
- ✅ **Stateless design** for horizontal scaling
- ✅ **Connection pooling** for AWS clients
- ✅ **Async processing** for streaming responses
- ✅ **Caching** for repeated queries

## 🔄 **Future Enhancements**

### **1. Additional Agents**
- **S3 Agent**: Bucket management, lifecycle policies
- **RDS Agent**: Database start/stop, backup management
- **Lambda Agent**: Function management, environment variables

### **2. Advanced Features**
- **Approval workflows** for destructive actions
- **Multi-region support** for cross-region operations
- **Webhook integration** for external notifications
- **Cost estimation** before actions

### **3. UI Enhancements**
- **Action confirmation** dialogs
- **Real-time status** updates
- **Scheduled actions** dashboard
- **Action history** visualization

---

## 🎯 **Summary**

The agent integration provides a **seamless experience** where users can:

1. **Use the same input field** for both cost analysis and agent actions
2. **Speak naturally** without learning specific commands
3. **Get immediate feedback** on action success or failure
4. **View detailed results** with proper formatting
5. **Access all functionality** through the familiar Streamlit interface

**The system automatically detects the user's intent and routes to the appropriate handler, making it feel like one unified system rather than separate tools! 🚀**
