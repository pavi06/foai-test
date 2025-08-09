
# fo.ai – Architecture & Workflow

This document provides a comprehensive overview of the fo.ai system architecture, component interactions, and operational workflow.

---

## System Architecture

### Core Application Layer
- **api.py** - FastAPI application serving as the primary backend entry point
- **foai_ui.py** - Streamlit-based web interface for user interactions
- **foai_cli.py** - Command-line interface for server management and direct queries

### Data Processing Layer
- **app/nodes/** - LangGraph workflow nodes for query analysis and response generation
  - analyze_query.py - Service type detection and query classification
  - fetch_data.py - Data retrieval from AWS services
  - generate_recommendations.py - Cost optimization analysis engine
  - generate_response.py - LLM response generation and streaming
  - route_recommendation.py - Workflow routing logic

### Agent System Layer
- **app/agents/** - Intelligent agent framework for AWS resource management
  - service_detector.py - AI-powered service type detection
  - ec2_agent.py - EC2 instance management and automation
  - agent_manager.py - Agent orchestration and coordination
  - api_endpoints.py - Agent-specific API endpoints
  - cog_integration.py - Agent integration with external systems

### Data Access Layer
- **data/aws/** - AWS service integration modules
  - ec2.py - EC2 instance data fetching and pricing analysis
  - s3.py - S3 bucket analysis and lifecycle management
  - cloudwatch.py - CloudWatch metrics and monitoring data
  - settings.py - AWS client configuration and settings
  - trusted_advisor.py - AWS Trusted Advisor integration

### Configuration & Memory
- **config/** - Application configuration management
- **memory/** - Redis-backed user preferences and session memory
- **prompts/** - LLM prompt templates and configurations

### Routing & Rules
- **routes/aws/** - Service-specific API route handlers
- **rules/aws/** - Cost optimization rules and policies

---

## Request Processing Workflow

### 1. Query Analysis
User submits a cost optimization query through the web interface or CLI. The system analyzes the query to determine the target AWS service (EC2, S3, or mixed) and extracts specific resource identifiers.

### 2. Data Retrieval
Based on the query analysis, the system fetches relevant data from AWS services:
- EC2 instances with CPU utilization metrics and pricing information
- S3 buckets with object statistics and lifecycle policies
- CloudWatch metrics for performance analysis

### 3. Cost Analysis
The recommendation engine processes the retrieved data using configurable rules:
- Identifies underutilized resources based on CPU thresholds
- Calculates potential cost savings using real-time pricing data
- Generates actionable recommendations with specific actions

### 4. Response Generation
The system formats the analysis results and generates a natural language response using the LLM. The response includes:
- Detailed cost breakdown and potential savings
- Specific action items with clear reasoning
- Risk considerations and implementation guidance

### 5. Response Delivery
The generated response is streamed back to the user interface, providing real-time feedback as the analysis completes.

---

## Key Technical Decisions

### Dynamic Pricing Integration
The system implements comprehensive dynamic pricing for EC2 instances, fetching real-time costs from the AWS Pricing API with intelligent fallback mechanisms for reliability.

### Agent-Based Resource Management
An intelligent agent system provides automated EC2 instance management capabilities, including start/stop operations and scheduled actions based on usage patterns.

### Streaming Response Architecture
Real-time response streaming enhances user experience by providing immediate feedback during analysis, particularly beneficial for large-scale cost assessments.

### Multi-Service Support
The architecture supports both EC2 and S3 cost optimization, with extensible design patterns for adding additional AWS services.

---

## Development Guidelines

### Environment Configuration
- Use environment variables for service configuration
- Toggle between live AWS data and mock data for development
- Configure Redis for session management and user preferences

### Logging and Monitoring
- Application logs are stored in logs/api.log and logs/ui.log
- Debug mode can be enabled for detailed troubleshooting
- Performance metrics are tracked for optimization

### Testing Strategy
- Unit tests for core business logic
- Integration tests for AWS service interactions
- End-to-end tests for complete workflow validation

---

## Deployment Considerations

### Prerequisites
- Python 3.8+ with required dependencies
- Redis server for session management
- Ollama with Llama3 model for LLM processing
- AWS credentials with appropriate permissions

### Performance Optimization
- Implement caching for frequently accessed pricing data
- Use connection pooling for AWS service clients
- Optimize database queries and memory usage

### Security Measures
- Secure handling of AWS credentials
- Input validation and sanitization
- Rate limiting for API endpoints
- Audit logging for sensitive operations

---

## Future Enhancements

### Planned Features
- Multi-cloud support for Azure and Google Cloud
- Advanced cost forecasting and budgeting
- Integration with CI/CD pipelines for automated optimization
- Enhanced reporting and analytics dashboard

### Architecture Evolution
- Microservices decomposition for scalability
- Event-driven architecture for real-time updates
- Advanced caching strategies for improved performance
- Machine learning integration for predictive optimization

---

## Maintenance and Support

### Regular Maintenance
- Monitor AWS service quotas and limits
- Update pricing data and optimization rules
- Review and optimize database queries
- Update dependencies and security patches

### Troubleshooting
- Check application logs for error patterns
- Verify AWS service connectivity and permissions
- Monitor system resource usage and performance
- Validate configuration settings and environment variables

---

## Contribution

- Vedanta
- Pavithra
- Aravind
- Mark Majer
