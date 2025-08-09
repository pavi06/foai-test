# fo.ai/app/nodes/generate_response.py
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from app.state import CostState
import pprint
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from typing import Generator


load_dotenv()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.5"))

llm = ChatOllama(model=LLM_MODEL, temprature=LLM_TEMPERATURE)

prompt = PromptTemplate.from_template("""
You are a FinOps assistant specializing in AWS cost optimization. Provide responses in KEY POINTS format for easy reading and quick understanding.

For EC2 instances: 
- Use bullet points (•) for each key point
- Mention specific instance IDs, types, and availability zones
- Include CPU usage metrics (current and 7-day average)
- Provide exact cost savings and current costs
- Give specific, actionable recommendations with clear reasoning
- Include priority levels and impact assessments

For S3 buckets: 
- Use bullet points (•) for each key point
- Provide specific bucket names and lifecycle policy recommendations
- Include transition rules and cost impact
- Mention object counts, sizes, and last modified dates

IMPORTANT: Format your response as KEY POINTS:
• Start each recommendation with a bullet point (•)
• Use clear, concise language
• Focus on actionable items
• Include specific resource names (instance IDs, bucket names)
• Provide exact cost savings and current costs
• Give specific actions needed with clear reasoning

CRITICAL: List ALL recommendations individually as key points. Do NOT summarize or say "X more instances/buckets". Show each recommendation separately with its specific details.

Focus on:
• Specific resource names (instance IDs, bucket names)
• Exact cost savings and current costs
• Detailed action items with specific recommendations
• Clear reasoning for each recommendation
• Step-by-step implementation guidance
• Complete list of all recommendations (no summarization)
• Professional, easy-to-read key points format

Recommendations:
{recommendations}

Provide a comprehensive response in KEY POINTS format. Use bullet points (•) for each recommendation and keep the language clear, concise, and actionable.
""")

def format_data_for_llm(ec2_data: list, s3_data: list, service_type: str) -> str:
    """
    Format EC2 and S3 data for LLM consumption
    Returns a formatted string with all recommendations
    """
    formatted_recommendations = []
    
    # Format EC2 recommendations
    if ec2_data and service_type in ['ec2', 'general']:
        formatted_recommendations.append("## **EC2 Cost Optimization Recommendations**")
        formatted_recommendations.append("")
        
        for i, rec in enumerate(ec2_data, 1):
            instance_id = rec.get('InstanceId', 'unknown')
            instance_type = rec.get('InstanceType', 'unknown')
            availability_zone = rec.get('AvailabilityZone', 'unknown')
            avg_cpu = rec.get('AverageCPU', 0)
            current_cpu = rec.get('CurrentCPU', 0)
            monthly_cost = rec.get('estimated_monthly_cost', 0)
            savings = rec.get('EstimatedSavings', 0)
            uptime_hours = rec.get('UptimeHours', 0)
            recommendation = rec.get('Recommendation', {})
            priority = rec.get('Priority', 'Medium')
            instance_type_details = rec.get('InstanceTypeDetails', {})
            
            formatted_recommendations.append(f"• **Instance {instance_id}** ({instance_type}) in {availability_zone}:")
            if instance_type_details:
                formatted_recommendations.append(f"  - **Instance Type Details:** {instance_type_details.get('Family', 'Unknown')} Family - {instance_type_details.get('Description', 'Unknown')}")
                formatted_recommendations.append(f"  - **Specifications:** {instance_type_details.get('vCPU', 'Unknown')} vCPU, {instance_type_details.get('Memory', 'Unknown')} RAM, {instance_type_details.get('Network', 'Unknown')} Network")
            formatted_recommendations.append(f"  - Current CPU: {current_cpu}%, 7-day average: {avg_cpu}%")
            formatted_recommendations.append(f"  - Monthly cost: ${monthly_cost:.2f}, Potential savings: ${savings:.2f}")
            formatted_recommendations.append(f"  - Uptime: {uptime_hours} hours, Priority: {priority}")
            formatted_recommendations.append(f"  - **Action:** {recommendation.get('Action', 'No action specified')}")
            formatted_recommendations.append(f"  - **Reason:** {recommendation.get('Reason', 'No reason provided')}")
            formatted_recommendations.append(f"  - **Impact:** {recommendation.get('Impact', 'Unknown')}")
            
            tags = rec.get('Tags', [])
            if tags:
                tag_str = ", ".join([f"{tag.get('Key')}={tag.get('Value')}" for tag in tags])
                formatted_recommendations.append(f"  - **Tags:** {tag_str}")
            formatted_recommendations.append("")
    
    # Format S3 recommendations
    if s3_data and service_type in ['s3', 'general']:
        formatted_recommendations.append("## **S3 Cost Optimization Recommendations**")
        formatted_recommendations.append("")
        
        for i, rec in enumerate(s3_data, 1):
            bucket_name = rec.get("BucketName", "")
            basic_info = rec.get("BasicInfo", {})
            object_stats = rec.get("ObjectStatistics", {})
            cost_analysis = rec.get("CostAnalysis", {})
            rec_details = rec.get("Recommendation", {})
            
            formatted_recommendations.append(f"• **Bucket {bucket_name}** ({basic_info.get('Region', 'unknown')}):")
            formatted_recommendations.append(f"  - Objects: {object_stats.get('TotalObjects', 0):,}, Size: {object_stats.get('TotalSizeGB', 0):.2f} GB")
            formatted_recommendations.append(f"  - Current cost: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month")
            formatted_recommendations.append(f"  - Potential savings: ${cost_analysis.get('PotentialSavings', 0):.2f}/month")
            formatted_recommendations.append(f"  - Last modified: {rec_details.get('DaysSinceLastModified', 0)} days ago")
            formatted_recommendations.append(f"  - **Target storage:** {rec_details.get('TargetStorageClass', 'Unknown')}")
            formatted_recommendations.append(f"  - **Action:** {rec_details.get('Action', 'No action specified')}")
            formatted_recommendations.append(f"  - **Reason:** {rec_details.get('Reason', 'No reason provided')}")
            formatted_recommendations.append("")
    
    # If no recommendations, provide a message
    if not formatted_recommendations:
        if service_type == 'ec2':
            formatted_recommendations.append("No EC2 optimization recommendations found at this time.")
        elif service_type == 's3':
            formatted_recommendations.append("No S3 optimization recommendations found at this time.")
        else:
            formatted_recommendations.append("No optimization recommendations found at this time.")
    
    return "\n".join(formatted_recommendations)

def generate_response(state: CostState) -> CostState:
    """Generate a natural language response using the LLM"""
    query = state.get("query", "")
    ec2_data = state.get("ec2_data", [])
    s3_data = state.get("s3_data", [])
    service_type = state.get("service_type", "general")
    
    try:
        # Format the data for the LLM
        formatted_data = format_data_for_llm(ec2_data, s3_data, service_type)
        
        # Generate the response using the LLM
        response = llm.invoke(prompt.format(recommendations=formatted_data))
        
        # Update the state with the response
        state["response"] = response.content
        return state
        
    except Exception as e:
        state["response"] = f"Error generating response: {str(e)}"
        return state

def stream_response(prompt: str) -> Generator[str, None, None]:
    """Yields streamed LLM response token by token."""

    print(f"\n[STREAM] Generating response for prompt: {prompt}")
    message = HumanMessage(content=prompt)
    print(f"[STREAM] Sending message to LLM: {message}")
    for chunk in llm.stream([message]):
        if chunk.content:
            yield chunk.content