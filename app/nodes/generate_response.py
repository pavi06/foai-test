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
You are a FinOps assistant specializing in AWS cost optimization. Provide specific, actionable recommendations based on the data provided.

For EC2 instances: Mention specific instance IDs, CPU usage, and cost savings.
For S3 buckets: Provide detailed lifecycle policy recommendations with specific bucket names, transition rules, and cost impact.

IMPORTANT: For S3 recommendations, be very specific about:
- Exact bucket names
- Specific transition periods (e.g., "30 days", "90 days")
- Target storage classes (IA, Glacier, Deep Archive)
- Current vs potential costs
- Days since last modification
- Specific lifecycle policy actions needed

CRITICAL: List ALL bucket recommendations individually. Do NOT summarize or say "X more buckets". Show each bucket recommendation separately with its specific details.

Focus on:
- Specific resource names (bucket names, instance IDs)
- Exact cost savings and current costs
- Detailed action items with specific storage classes and transition periods
- Reasoning based on actual data and user preferences
- Step-by-step implementation guidance
- Complete list of all recommendations (no summarization)

Recommendations:
{recommendations}

Provide a comprehensive summary with specific details for each recommendation. For S3, include exact lifecycle policy configurations needed. List ALL buckets individually - do not summarize or truncate the list.
""")

def generate_response(state: CostState) -> CostState:
    if DEBUG:
        print("\n[generate_response] State before response generation:")
        pprint.pprint(state)

    # Combine EC2 and S3 recommendations
    ec2_recommendations = state.get("recommendations", [])
    s3_recommendations = state.get("s3_recommendations", [])
    all_recommendations = ec2_recommendations + s3_recommendations

    if not all_recommendations:
        state["response"] = "No recommendations found. Everything looks optimized!"
        return state

    # Check if using mock data
    use_mock = state.get("use_mock", False)
    mock_data_note = ""
    if use_mock:
        mock_data_note = "\n\n⚠️ **Note**: This analysis is based on mock/test data. For real AWS data, ensure you have proper AWS credentials configured and set use_mock=False.\n"

    # Format recommendations for LLM
    formatted_recommendations = []
    
    if ec2_recommendations:
        formatted_recommendations.append("EC2 Recommendations:")
        for rec in ec2_recommendations:
            formatted_recommendations.append(f"- {rec.get('InstanceId')}: {rec.get('Reason')} (Savings: ${rec.get('EstimatedSavings', 0):.2f})")
    
    if s3_recommendations:
        formatted_recommendations.append("\nS3 Bucket Recommendations:")
        for i, rec in enumerate(s3_recommendations, 1):
            bucket_name = rec.get('BucketName', 'unknown')
            basic_info = rec.get('BasicInfo', {})
            object_stats = rec.get('ObjectStatistics', {})
            cost_analysis = rec.get('CostAnalysis', {})
            recommendation = rec.get('Recommendation', {})
            
            # Create detailed S3 recommendation with specific lifecycle policy details
            s3_detail = f"\n{i}. Bucket: '{bucket_name}'"
            s3_detail += f"\n   - Size: {object_stats.get('TotalSizeGB', 0):.2f} GB"
            s3_detail += f"\n   - Objects: {object_stats.get('TotalObjects', 0):,}"
            
            # Add storage class distribution
            storage_dist = recommendation.get('CurrentStorageClassDistribution', {})
            if storage_dist:
                s3_detail += f"\n   - Storage classes: {', '.join([f'{sc}: {count}' for sc, count in storage_dist.items()])}"
            
            # Add STANDARD object details
            standard_count = recommendation.get('StandardObjectsCount', 0)
            standard_size = recommendation.get('StandardObjectsSizeGB', 0)
            if standard_count > 0:
                s3_detail += f"\n   - STANDARD objects: {standard_count:,} ({standard_size:.2f} GB)"
            
            s3_detail += f"\n   - Current Cost: ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month"
            s3_detail += f"\n   - Potential Savings: ${cost_analysis.get('PotentialSavings', 0):.2f}/month ({recommendation.get('SavingsPercentage', 0):.1f}%)"
            s3_detail += f"\n   - Days since last modification: {recommendation.get('DaysSinceLastModified', 0)}"
            s3_detail += f"\n   - Target storage class: {recommendation.get('TargetStorageClass', 'Unknown')}"
            s3_detail += f"\n   - Transition period: {recommendation.get('TransitionDays', 0)} days"
            s3_detail += f"\n   - Impact level: {recommendation.get('Impact', 'Unknown')}"
            s3_detail += f"\n   - Action: {recommendation.get('Action', 'No action specified')}"
            s3_detail += f"\n   - Reason: {recommendation.get('Reason', 'No reason provided')}"
            
            formatted_recommendations.append(s3_detail)

    recommendations_text = "\n".join(formatted_recommendations)
    formatted = prompt.format(recommendations=recommendations_text)
    result = llm.invoke(formatted)
    
    # Add mock data note if applicable
    response_content = result.content.strip()
    if mock_data_note:
        response_content += mock_data_note
    
    state["response"] = response_content

    if DEBUG:
        print("\n[generate_response] State after response generation:")
        pprint.pprint(state)

    return state

def stream_response(prompt: str) -> Generator[str, None, None]:
    """Yields streamed LLM response token by token."""

    print(f"\n[STREAM] Generating response for prompt: {prompt}")
    message = HumanMessage(content=prompt)
    print(f"[STREAM] Sending message to LLM: {message}")
    for chunk in llm.stream([message]):
        if chunk.content:
            yield chunk.content