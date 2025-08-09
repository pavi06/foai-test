
# fo.ai – Cloud Cost Intelligence Platform

**Version:** `v0.1.3`  
**Built by:** A team that got tired of surprise AWS bills

---

## What's This All About?

Hey there! 👋 We built `fo.ai` because we were spending way too much time staring at AWS bills and wondering where all our money went. You know that feeling when you get that monthly invoice and think "wait, what's this $200 charge for?" Yeah, we've been there too.

`fo.ai` is our attempt to make cloud cost optimization less painful. It's like having a smart friend who actually understands AWS pricing and can tell you exactly which instances are just sitting there burning money.

---

## What Can It Do For You?

### Intelligent Resource Analysis
- **EC2 Cost Optimization**: Identifies underutilized instances and provides specific cost-saving recommendations
- **S3 Lifecycle Management**: Analyzes bucket policies and object storage patterns for optimization opportunities
- **Real-time Pricing**: Dynamic cost calculations using current AWS pricing data
- **Performance Metrics**: CloudWatch integration for comprehensive resource utilization analysis

### AI-Powered Insights
- **Natural Language Processing**: Conversational interface for complex cost analysis queries
- **Intelligent Recommendations**: Context-aware suggestions with specific action items
- **Streaming Responses**: Real-time analysis results as they're generated
- **Memory Integration**: Remembers user preferences and analysis history

### Flexible Interface Options
- **Web Application**: Streamlit-based interface for interactive analysis
- **Command Line Interface**: Powerful CLI for automation and scripting
- **REST API**: Programmatic access for integration with existing tools
- **Agent System**: Automated resource management capabilities

---

## Quick Start Guide

### Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher
- AWS credentials with appropriate permissions
- Redis server for session management
- Ollama with Llama3 model for AI processing

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/fo.ai.git
   cd fo.ai
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create a `.env` file in the project root:
   ```env
   FOAI_API_URL=http://localhost:8000
   USE_MOCK_DATA=false
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-east-1
   ```

3. **Start the Application**
   ```bash
   python foai_cli.py server start all
   ```

4. **Access the Interface**
   Open your browser to [http://localhost:8501](http://localhost:8501) to begin using the web interface.

---

## Usage Examples

### Web Interface

The web interface provides an intuitive way to interact with the platform. Simply type your questions in natural language:

- "Which EC2 instances are underutilized and costing money?"
- "Analyze instance i-1234567890abcdef0 for optimization opportunities"
- "Check my S3 bucket 'production-logs' for lifecycle policy recommendations"
- "Show me the top 5 cost optimization opportunities across all services"

### Command Line Interface

For power users and automation scenarios, the CLI provides comprehensive functionality:

```bash
# Quick cost analysis
python foai_cli.py ask "How can I reduce my EC2 costs?"

# Streaming analysis with real-time updates
python foai_cli.py ask "Show me underutilized instances" --stream

# System status check
python foai_cli.py status

# Server management
python foai_cli.py server start all
python foai_cli.py server stop all

# View application logs
python foai_cli.py logs api
python foai_cli.py logs ui
```

### Global CLI Access

For convenience, add the CLI to your system PATH:

```bash
# Add to your shell configuration (~/.zshrc or ~/.bashrc)
alias foai="python /full/path/to/foai_cli.py"

# Then use from anywhere
foai ask "What's driving up my AWS costs?"
foai server start all
```

---

## Platform Architecture

### Core Components

- **FastAPI Backend**: High-performance API server handling analysis requests
- **Streamlit Frontend**: Interactive web interface for user interactions
- **LangGraph Workflow**: Orchestrated data processing and analysis pipeline
- **Agent System**: Intelligent automation for resource management
- **Redis Memory**: Persistent storage for user preferences and session data

### Data Processing Pipeline

1. **Query Analysis**: Natural language processing to understand user intent
2. **Data Retrieval**: AWS API integration for real-time resource data
3. **Cost Analysis**: Dynamic pricing calculations and optimization algorithms
4. **Recommendation Generation**: AI-powered insights with specific actions
5. **Response Delivery**: Streaming results with detailed explanations

### Technology Stack

- **Backend Framework**: FastAPI for high-performance API development
- **Frontend Framework**: Streamlit for rapid web application development
- **AI Framework**: LangChain with Ollama for local LLM processing
- **Data Storage**: Redis for session management and caching
- **AWS Integration**: boto3 for comprehensive AWS service access
- **Monitoring**: CloudWatch for performance metrics and resource utilization

---

## Current Capabilities

### Completed Features
- **EC2 Cost Analysis**: Comprehensive instance utilization analysis with dynamic pricing
- **S3 Optimization**: Bucket lifecycle policy analysis and storage class recommendations
- **Single Resource Analysis**: Detailed analysis of specific instances or buckets
- **Real-time Streaming**: Live response generation for immediate feedback
- **Multi-region Support**: Analysis across multiple AWS regions
- **Agent Automation**: Automated EC2 instance management capabilities

### In Development
- **Multi-cloud Support**: Extending beyond AWS to Azure and Google Cloud
- **Advanced Forecasting**: Predictive cost modeling and budget planning
- **Integration APIs**: Slack, Teams, and email notification systems
- **Custom Rule Engine**: User-defined optimization criteria and thresholds
- **Cost Allocation**: Detailed cost breakdown by project, team, or application

---

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FOAI_API_URL` | Backend API endpoint | `http://localhost:8000` |
| `USE_MOCK_DATA` | Enable mock data for testing | `false` |
| `AWS_ACCESS_KEY_ID` | AWS access key for API calls | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for API calls | Required |
| `AWS_DEFAULT_REGION` | Default AWS region | `us-east-1` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `DEBUG` | Enable debug logging | `false` |

### Analysis Parameters

The platform supports configurable thresholds and parameters for cost optimization:

- **CPU Utilization Threshold**: Minimum CPU usage for cost optimization (default: 10%)
- **Minimum Uptime**: Minimum instance uptime for analysis (default: 24 hours)
- **Cost Savings Threshold**: Minimum monthly savings for recommendations (default: $5)
- **Analysis Depth**: Number of recommendations to generate (default: 5 for EC2, 10 for S3)

---

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   ```bash
   # Start Redis service (macOS)
   brew services start redis
   
   # Check Redis status
   redis-cli ping
   ```

2. **AWS Credentials Issues**
   - Verify AWS credentials are properly configured
   - Ensure IAM permissions include EC2, S3, and CloudWatch access
   - Check AWS region configuration

3. **Application Startup Problems**
   - Verify all dependencies are installed: `pip install -r requirements.txt`
   - Check port availability (8000 for API, 8501 for UI)
   - Review application logs for specific error messages

### Log Analysis

Application logs provide detailed information for troubleshooting:

```bash
# View API server logs
python foai_cli.py logs api

# View web interface logs
python foai_cli.py logs ui

# Check system status
python foai_cli.py status
```

### Performance Optimization

For production deployments, consider:

- **Caching**: Enable Redis caching for frequently accessed data
- **Connection Pooling**: Configure AWS client connection pooling
- **Resource Limits**: Set appropriate memory and CPU limits
- **Monitoring**: Implement application performance monitoring

---

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/fo.ai.git
cd fo.ai

# Install development dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/
```

---


## Acknowledgments

Having trouble? Here are some things to check:

1. **Make sure Redis is running**: `brew services start redis` (on Mac)
2. **Check your AWS credentials**: Make sure you have access to the resources you're trying to analyze
3. **Look at the logs**: `python foai_cli.py logs api` or `python foai_cli.py logs ui`

Still stuck? Open an issue and we'll help you out!

---
