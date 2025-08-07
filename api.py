from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from memory.preferences import set_user_preferences
from pydantic import BaseModel
from typing import Any, List, Optional
from dotenv import load_dotenv
import os
import json
from langchain_ollama import ChatOllama
from fastapi import Request

# API prompts
from prompts.pref_explainer import build_explain_prompt

from data.aws.ec2 import fetch_ec2_instances, summarize_cost_by_region
from data.aws.s3 import fetch_s3_data
from app.nodes.generate_recommendations import generate_recommendations, get_recommendations_and_prompt, generate_s3_recommendations
from app.nodes.generate_response import stream_response


from memory.redis_memory import append_to_list, get_list
from memory.preferences import get_user_preferences

# Import settings first
from config.settings import settings

class PreferencePayload(BaseModel):
    user_id: str
    preferences: dict

DEFAULT_PREFS = settings.DEFAULT_PREFERENCES

# routers for API endpoints
from routes.aws.ec2 import router as aws_ec2_router

# Validate settings
if not settings.validate():
    print("Warning: Some required settings are missing. Application may not work correctly.")

llm = ChatOllama(model=settings.LLM_MODEL, temprature=settings.LLM_TEMPERATURE)

print("Testing the llama3 Model...")
response = llm.invoke("Tell me a joke about programmers")
print(response.content)

app = FastAPI(title="fo.ai API - Cloud Cost Intelligence", version="0.1.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    region: str = "us-east-1"

class Recommendation(BaseModel):
    InstanceId: str
    InstanceType: str
    Reason: str
    EstimatedSavings: float
    Tags: Any = None

class AnalyzeResponse(BaseModel):
    response: str
    raw: List[Recommendation]
    service_type: str = "ec2"  # "ec2", "s3", or "mixed"

def detect_service_type(query: str) -> dict:
    """Detect if the query is about EC2, S3, agent actions, or both, and extract specific resource identifiers"""
    query_lower = query.lower()
    
    ec2_keywords = ["ec2", "instance", "cpu", "compute", "server", "machine", "virtual"]
    s3_keywords = ["s3", "bucket", "storage", "object", "file", "lifecycle", "glacier", "ia", "recommendation", "recommendations", "optimization", "optimize", "cost", "savings"]
    
    # Agent action keywords
    agent_action_keywords = [
        "stop", "start", "shutdown", "power off", "power on", "boot", "turn off", "turn on",
        "schedule", "schedule shutdown", "schedule startup", "auto shutdown", "auto start",
        "delete schedule", "remove schedule", "cancel schedule", "list schedules"
    ]
    
    ec2_score = sum(1 for keyword in ec2_keywords if keyword in query_lower)
    s3_score = sum(1 for keyword in s3_keywords if keyword in query_lower)
    agent_score = sum(1 for keyword in agent_action_keywords if keyword in query_lower)
    
    # Extract specific resource identifiers
    specific_resources = {
        "ec2_instances": [],
        "s3_buckets": []
    }
    
    # Extract EC2 instance IDs (format: i-xxxxxxxxxxxxxxxxx)
    import re
    ec2_instance_pattern = r'\bi-[a-f0-9]{8,17}\b'
    ec2_instances = re.findall(ec2_instance_pattern, query, re.IGNORECASE)
    specific_resources["ec2_instances"] = ec2_instances
    
    # Extract S3 bucket names - ONLY when explicitly specified
    bucket_matches = []
    
    # Pattern 1: Quoted bucket names (most reliable)
    # Examples: "my-bucket", 'pavi-test-bucket'
    quoted_bucket_pattern = r'["\']([a-z0-9][a-z0-9.-]*[a-z0-9])["\']'
    quoted_matches = re.findall(quoted_bucket_pattern, query, re.IGNORECASE)
    bucket_matches.extend(quoted_matches)
    
    # Pattern 2: "bucket name" format (very specific)
    # Examples: bucket "my-bucket", s3 "my-bucket"
    bucket_name_pattern = r'\b(?:bucket|s3)\s+["\']([a-z0-9][a-z0-9.-]*[a-z0-9])["\']'
    bucket_name_matches = re.findall(bucket_name_pattern, query, re.IGNORECASE)
    bucket_matches.extend(bucket_name_matches)
    
    # Pattern 3: "name bucket" format (very specific)
    # Examples: "my-bucket" bucket, "my-bucket" s3
    name_bucket_pattern = r'["\']([a-z0-9][a-z0-9.-]*[a-z0-9])["\']\s+(?:bucket|s3)\b'
    name_bucket_matches = re.findall(name_bucket_pattern, query, re.IGNORECASE)
    bucket_matches.extend(name_bucket_matches)
    
    # Pattern 4: Very specific unquoted patterns (avoid common words)
    # Only match if it looks like a real bucket name (not common words)
    # Examples: bucket my-app-logs, s3 backup-data
    # But NOT: bucket the, s3 all, bucket this, etc.
    common_words = r'\b(?:the|all|this|that|these|those|my|your|our|their|some|any|each|every|both|either|neither|few|many|several|various|different|same|similar|other|another|next|last|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|give|get|show|list|check|analyze|analyse|find|search|look|see|view|display|print|output|result|data|info|information|details|summary|report|analysis|recommendation|recommendations|optimization|optimize|cost|savings|money|storage|object|file|lifecycle|glacier|ia|standard|intelligent|archive|deep|archive|onezone|reduced|redundancy|rr|zr|szr|glacier|instant|retrieval|flexible|retrieval|expedited|bulk|standard|ia|glacier|deep|archive|onezone|reduced|redundancy|rr|zr|szr|glacier|instant|retrieval|flexible|retrieval|expedited|bulk)\b'
    
    # Look for bucket name followed by "bucket" or "s3" but exclude common words
    specific_bucket_pattern = r'\b([a-z0-9][a-z0-9.-]{2,}[a-z0-9])\s+(?:bucket|s3)\b'
    specific_matches = re.findall(specific_bucket_pattern, query, re.IGNORECASE)
    
    # Filter out common words
    filtered_matches = []
    for match in specific_matches:
        if not re.match(common_words, match, re.IGNORECASE):
            filtered_matches.append(match)
    
    bucket_matches.extend(filtered_matches)
    
    # Remove duplicates and store
    specific_resources["s3_buckets"] = list(set(bucket_matches))
    
    # Determine service type
    if agent_score > 0 and (ec2_score > 0 or "instance" in query_lower):
        service_type = "agent_ec2"
    elif ec2_score > 0 and s3_score > 0:
        service_type = "mixed"
    elif s3_score > 0:
        service_type = "s3"
    elif ec2_score > 0:
        service_type = "ec2"
    else:
        # Default to EC2 if no clear service type detected
        service_type = "ec2"
    
    print(f"[SERVICE DETECTION] Query: '{query}'")
    print(f"   Service type: {service_type}")
    print(f"   EC2 instances found: {specific_resources['ec2_instances']}")
    print(f"   S3 buckets found: {specific_resources['s3_buckets']}")
    
    return {
        "service_type": service_type,
        "specific_resources": specific_resources,
        "is_specific_analysis": len(specific_resources["ec2_instances"]) > 0 or len(specific_resources["s3_buckets"]) > 0
    }

def analyze_ec2_resources(user_id: str, region: str, rules: dict, specific_instance_ids: list = None) -> dict:
    """Analyze EC2 resources and return detailed recommendations"""
    print(f"\n[API] Starting EC2 resource analysis for user {user_id} in region {region}")
    
    if specific_instance_ids:
        print(f"[API] Analyzing specific instances: {specific_instance_ids}")
        ec2_data = fetch_ec2_instances(instance_ids=specific_instance_ids, region=region)
        analysis_type = "specific instances"
    else:
        print(f"[API] Analyzing all running instances")
        ec2_data = fetch_ec2_instances(region=region)
        analysis_type = "all instances"
    
    if not ec2_data:
        if specific_instance_ids:
            return {
                "response": f"**No EC2 instances found** with the specified IDs: {specific_instance_ids}. The instances may be stopped, terminated, or not accessible in region `{region}`.",
                "raw": [],
                "total_savings": 0.0
            }
        else:
            return {
                "response": f"**No EC2 instances found** in region `{region}`. All instances may be stopped or the region may be empty.",
                "raw": [],
                "total_savings": 0.0
            }

    print(f"[API] Found {len(ec2_data)} EC2 instances, generating recommendations...")
    recommendations = generate_recommendations(ec2_data, rules)
    
    if not recommendations:
        if specific_instance_ids:
            return {
                "response": f"**No optimization opportunities found** for the specified instances: {specific_instance_ids}. These instances appear to be well-utilized based on your current preferences.",
                "raw": [],
                "total_savings": 0.0
            }
        else:
            return {
                "response": f"**No EC2 optimization opportunities found** in region `{region}`. All instances appear to be well-utilized based on your current preferences.",
                "raw": [],
                "total_savings": 0.0
            }
    
    total_savings = sum(r.get("EstimatedSavings", 0.0) for r in recommendations)
    total_monthly_cost = sum(r.get("MonthlyCost", 0.0) for r in recommendations)
    
    # Generate detailed markdown response with specific resource details
    markdown_summary = f"## **EC2 Cost Optimization Analysis**\n\n"
    markdown_summary += f"**Region:** `{region}`  \n"
    markdown_summary += f"**Analysis Type:** {analysis_type}  \n"
    markdown_summary += f"**Total Instances Analyzed:** {len(ec2_data)}  \n"
    markdown_summary += f"**Optimization Opportunities:** {len(recommendations)}  \n"
    markdown_summary += f"**Total Monthly Cost:** ${total_monthly_cost:.2f}  \n"
    markdown_summary += f"**Potential Monthly Savings:** ${total_savings:.2f}  \n\n"
    
    # Add specific resource summary
    markdown_summary += f"### **Specific Resources to Target**\n\n"
    if specific_instance_ids:
        markdown_summary += f"**{len(recommendations)} of {len(specific_instance_ids)} requested instances** have been identified for optimization:\n\n"
    else:
        markdown_summary += f"**{len(recommendations)} instances** have been identified for optimization:\n\n"
    
    # List all instances with key details
    for i, r in enumerate(recommendations, 1):
        instance_id = r.get("InstanceId")
        instance_type = r.get("InstanceType")
        avg_cpu = r.get("AverageCPU", 0)
        monthly_cost = r.get("MonthlyCost", 0)
        savings = r.get("EstimatedSavings", 0)
        availability_zone = r.get("AvailabilityZone", "")
        
        markdown_summary += f"**{i}. Instance `{instance_id}`**  \n"
        markdown_summary += f"   - **Type:** {instance_type}  \n"
        markdown_summary += f"   - **Zone:** {availability_zone}  \n"
        markdown_summary += f"   - **CPU Usage:** {avg_cpu}% (7-day average)  \n"
        markdown_summary += f"   - **Monthly Cost:** ${monthly_cost:.2f}  \n"
        markdown_summary += f"   - **Potential Savings:** ${savings:.2f}/month  \n\n"
    
    markdown_summary += "### **Detailed Recommendations**\n\n"
    
    # Group by priority
    high_priority = [r for r in recommendations if r.get("Priority") == "High"]
    medium_priority = [r for r in recommendations if r.get("Priority") == "Medium"]
    low_priority = [r for r in recommendations if r.get("Priority") == "Low"]
    
    if high_priority:
        markdown_summary += "#### **High Priority Actions**\n\n"
        for r in high_priority:
            markdown_summary += generate_ec2_recommendation_markdown(r)
    
    if medium_priority:
        markdown_summary += "#### **Medium Priority Actions**\n\n"
        for r in medium_priority:
            markdown_summary += generate_ec2_recommendation_markdown(r)
    
    if low_priority:
        markdown_summary += "#### **Low Priority Actions**\n\n"
        for r in low_priority:
            markdown_summary += generate_ec2_recommendation_markdown(r)
    
    markdown_summary += f"\n### **Summary**\n\n"
    markdown_summary += f"By implementing these recommendations, you could save **${total_savings:.2f} per month** "
    markdown_summary += f"({(total_savings/total_monthly_cost*100):.1f}% reduction) on your EC2 costs.\n\n"
    
    markdown_summary += "**Next Steps:**\n"
    markdown_summary += "1. Review each recommendation carefully\n"
    markdown_summary += "2. Test changes in a non-production environment first\n"
    markdown_summary += "3. Monitor performance after implementing changes\n"
    markdown_summary += "4. Consider using AWS Cost Explorer for detailed cost analysis\n"
    
    print(f"[API] EC2 analysis complete. Generated {len(recommendations)} recommendations with ${total_savings:.2f} potential savings")
    
    return {
        "response": markdown_summary,
        "raw": recommendations,
        "total_savings": total_savings
    }

def generate_ec2_recommendation_markdown(recommendation: dict) -> str:
    """Generate detailed markdown for a single EC2 recommendation"""
    instance_id = recommendation.get("InstanceId", "")
    instance_type = recommendation.get("InstanceType", "")
    availability_zone = recommendation.get("AvailabilityZone", "")
    avg_cpu = recommendation.get("AverageCPU", 0)
    monthly_cost = recommendation.get("MonthlyCost", 0)
    savings = recommendation.get("EstimatedSavings", 0)
    rec_details = recommendation.get("Recommendation", {})
    
    markdown = f"**Instance:** `{instance_id}`  \n"
    markdown += f"**Type:** {instance_type}  \n"
    markdown += f"**Zone:** {availability_zone}  \n"
    markdown += f"**Current CPU Usage:** {avg_cpu}% (7-day average)  \n"
    markdown += f"**Monthly Cost:** ${monthly_cost:.2f}  \n"
    markdown += f"**Potential Savings:** ${savings:.2f}/month  \n"
    markdown += f"**Recommendation:** {rec_details.get('Action', 'No action specified')}  \n"
    markdown += f"**Reason:** {rec_details.get('Reason', 'No reason provided')}  \n"
    
    # Add tags if available
    tags = recommendation.get("Tags", [])
    if tags:
        tag_str = ", ".join([f"{tag.get('Key')}={tag.get('Value')}" for tag in tags])
        markdown += f"**Tags:** {tag_str}  \n"
    
    markdown += f"**Impact:** {rec_details.get('Impact', 'Unknown')}  \n\n"
    
    return markdown

def analyze_s3_resources(user_id: str, region: str, rules: dict, specific_bucket_names: list = None) -> dict:
    """Analyze S3 resources and return detailed recommendations"""
    print(f"\n[API] Starting S3 resource analysis for user {user_id} in region {region}")
    
    if specific_bucket_names:
        print(f"[API] Analyzing specific buckets: {specific_bucket_names}")
        s3_data = fetch_s3_data(region=region, bucket_names=specific_bucket_names)
        analysis_type = "specific buckets"
    else:
        print(f"[API] Analyzing all buckets")
        s3_data = fetch_s3_data(region=region)
        analysis_type = "all buckets"
    
    if not s3_data:
        if specific_bucket_names:
            return {
                "response": f"**No S3 buckets found** with the specified names: {specific_bucket_names}. The buckets may not exist or you may not have access to them.",
                "raw": [],
                "total_savings": 0.0
            }
        else:
            return {
                "response": f"**No S3 buckets found** in region `{region}` or no access to bucket information.",
                "raw": [],
                "total_savings": 0.0
            }

    # Filter out buckets with errors
    valid_buckets = [bucket for bucket in s3_data if "error" not in bucket]
    
    if not valid_buckets:
        if specific_bucket_names:
            return {
                "response": f"**No valid S3 buckets found** for analysis with the specified names: {specific_bucket_names}.",
                "raw": [],
                "total_savings": 0.0
            }
        else:
            return {
                "response": f"**No valid S3 buckets found** for analysis in region `{region}`.",
                "raw": [],
                "total_savings": 0.0
            }

    print(f"[API] Found {len(valid_buckets)} valid S3 buckets, generating recommendations...")
    recommendations = generate_s3_recommendations(valid_buckets, rules)
    
    if not recommendations:
        if specific_bucket_names:
            return {
                "response": f"**No S3 optimization opportunities found** for the specified buckets: {specific_bucket_names}. These buckets appear to be properly configured.",
                "raw": [],
                "total_savings": 0.0
            }
        else:
            return {
                "response": f"**No S3 optimization opportunities found** in region `{region}`. All buckets appear to be properly configured.",
                "raw": [],
                "total_savings": 0.0
            }
    
    total_savings = sum(r.get("CostAnalysis", {}).get("PotentialSavings", 0.0) for r in recommendations)
    total_current_cost = sum(r.get("CostAnalysis", {}).get("CurrentMonthlyCost", 0.0) for r in recommendations)
    
    # Generate detailed markdown response with specific bucket details
    markdown_summary = f"## **S3 Cost Optimization Analysis**\n\n"
    markdown_summary += f"**Region:** `{region}`  \n"
    markdown_summary += f"**Analysis Type:** {analysis_type}  \n"
    markdown_summary += f"**Total Buckets Analyzed:** {len(valid_buckets)}  \n"
    markdown_summary += f"**Optimization Opportunities:** {len(recommendations)}  \n"
    markdown_summary += f"**Total Monthly Cost:** ${total_current_cost:.2f}  \n"
    markdown_summary += f"**Potential Monthly Savings:** ${total_savings:.2f}  \n\n"
    
    # Add specific resource summary
    markdown_summary += f"### **Specific Buckets to Configure**\n\n"
    if specific_bucket_names:
        markdown_summary += f"**{len(recommendations)} of {len(specific_bucket_names)} requested buckets** need lifecycle policy configuration:\n\n"
    else:
        markdown_summary += f"**{len(recommendations)} buckets** need lifecycle policy configuration:\n\n"
    
    # List all buckets with key details
    for i, r in enumerate(recommendations, 1):
        bucket_name = r.get("BucketName", "")
        basic_info = r.get("BasicInfo", {})
        object_stats = r.get("ObjectStatistics", {})
        cost_analysis = r.get("CostAnalysis", {})
        rec_details = r.get("Recommendation", {})
        
        markdown_summary += f"**{i}. Bucket `{bucket_name}`**  \n"
        markdown_summary += f"   - **Region:** {basic_info.get('Region', 'unknown')}  \n"
        markdown_summary += f"   - **Objects:** {object_stats.get('TotalObjects', 0):,}  \n"
        markdown_summary += f"   - **Size:** {object_stats.get('TotalSizeGB', 0):.2f} GB  \n"
        markdown_summary += f"   - **Current Cost:** ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}/month  \n"
        markdown_summary += f"   - **Potential Savings:** ${cost_analysis.get('PotentialSavings', 0):.2f}/month  \n"
        markdown_summary += f"   - **Last Modified:** {rec_details.get('DaysSinceLastModified', 0)} days ago  \n"
        markdown_summary += f"   - **Target Storage:** {rec_details.get('TargetStorageClass', 'Unknown')}  \n\n"
    
    markdown_summary += "### **Detailed Recommendations**\n\n"
    
    for r in recommendations:
        markdown_summary += generate_s3_recommendation_markdown(r)
    
    markdown_summary += f"\n### **Summary**\n\n"
    markdown_summary += f"By implementing these lifecycle policies, you could save **${total_savings:.2f} per month** "
    if total_current_cost > 0:
        markdown_summary += f"({(total_savings/total_current_cost*100):.1f}% reduction) on your S3 storage costs.\n\n"
    else:
        markdown_summary += "on your S3 storage costs.\n\n"
    
    markdown_summary += "**Next Steps:**\n"
    markdown_summary += "1. Review each bucket's current configuration\n"
    markdown_summary += "2. Implement lifecycle policies gradually\n"
    markdown_summary += "3. Monitor access patterns before transitioning to cheaper storage\n"
    markdown_summary += "4. Consider using S3 Intelligent Tiering for automatic optimization\n"
    
    print(f"[API] S3 analysis complete. Generated {len(recommendations)} recommendations with ${total_savings:.2f} potential savings")
    
    return {
        "response": markdown_summary,
        "raw": recommendations,
        "total_savings": total_savings
    }

def generate_s3_recommendation_markdown(recommendation: dict) -> str:
    """Generate detailed markdown for a single S3 recommendation"""
    bucket_name = recommendation.get("BucketName", "")
    basic_info = recommendation.get("BasicInfo", {})
    object_stats = recommendation.get("ObjectStatistics", {})
    cost_analysis = recommendation.get("CostAnalysis", {})
    rec_details = recommendation.get("Recommendation", {})
    
    markdown = f"**Bucket:** `{bucket_name}`  \n"
    markdown += f"**Region:** {basic_info.get('Region', 'unknown')}  \n"
    markdown += f"**Total Objects:** {object_stats.get('TotalObjects', 0):,}  \n"
    markdown += f"**Total Size:** {object_stats.get('TotalSizeGB', 0):.2f} GB  \n"
    markdown += f"**Current Monthly Cost:** ${cost_analysis.get('CurrentMonthlyCost', 0):.2f}  \n"
    markdown += f"**Potential Savings:** ${cost_analysis.get('PotentialSavings', 0):.2f}/month  \n"
    markdown += f"**Recommendation:** {rec_details.get('Action', 'No action specified')}  \n"
    markdown += f"**Reason:** {rec_details.get('Reason', 'No reason provided')}  \n"
    markdown += f"**Days Since Last Modified:** {rec_details.get('DaysSinceLastModified', 0)}  \n"
    markdown += f"**Target Storage Class:** {rec_details.get('TargetStorageClass', 'Unknown')}  \n"
    markdown += f"**Impact:** {rec_details.get('Impact', 'Unknown')}  \n"
    
    # Add configuration details
    markdown += f"**Versioning:** {basic_info.get('Versioning', 'Unknown')}  \n"
    markdown += f"**Logging:** {'Enabled' if basic_info.get('LoggingEnabled') else 'Disabled'}  \n"
    markdown += f"**Encryption:** {basic_info.get('EncryptionType', 'None')}  \n"
    
    # Add tags if available
    tags = basic_info.get("Tags", [])
    if tags:
        tag_str = ", ".join([f"{tag.get('Key')}={tag.get('Value')}" for tag in tags])
        markdown += f"**Tags:** {tag_str}  \n"
    
    markdown += "\n"
    
    return markdown

def enhance_response_with_llm(query: str, ec2_result: dict, s3_result: dict, service_type: str) -> str:
    """Use LLM to enhance the response based on user query"""
    
    print(f"\n[LLM] Enhancing response for query: '{query}'")
    print(f"[LLM] Service type: {service_type}")
    
    # Prepare detailed context for LLM
    context_parts = []
    
    if service_type in ["ec2", "mixed"] and ec2_result.get("raw"):
        ec2_recommendations = ec2_result['raw']
        ec2_savings = ec2_result.get('total_savings', 0)
        ec2_count = len(ec2_recommendations)
        
        ec2_summary = f"EC2 Analysis: Found {ec2_count} optimization opportunities with ${ec2_savings:.2f} potential monthly savings. "
        
        # Add specific details about high-priority recommendations
        high_priority = [r for r in ec2_recommendations if r.get("Priority") == "High"]
        if high_priority:
            ec2_summary += f"High priority actions: {len(high_priority)} instances need immediate attention. "
        
        context_parts.append(ec2_summary)
        print(f"[LLM] EC2 context: {ec2_count} recommendations, ${ec2_savings:.2f} savings")
    
    if service_type in ["s3", "mixed"] and s3_result.get("raw"):
        s3_recommendations = s3_result['raw']
        s3_savings = s3_result.get('total_savings', 0)
        s3_count = len(s3_recommendations)
        
        s3_summary = f"S3 Analysis: Found {s3_count} buckets needing lifecycle policies with ${s3_savings:.2f} potential monthly savings. "
        
        # Add details about storage optimization
        total_size = sum(r.get("ObjectStatistics", {}).get("TotalSizeGB", 0) for r in s3_recommendations)
        s3_summary += f"Total storage to optimize: {total_size:.2f} GB. "
        
        context_parts.append(s3_summary)
        print(f"[LLM] S3 context: {s3_count} recommendations, ${s3_savings:.2f} savings")
    
    if not context_parts:
        print(f"[LLM] No optimization opportunities found")
        return "**No optimization opportunities found** based on your current preferences and resources. All your AWS resources appear to be well-utilized and properly configured."
    
    context = " ".join(context_parts)
    total_savings = (ec2_result.get('total_savings', 0) + s3_result.get('total_savings', 0))
    
    # Create enhanced LLM prompt with specific resource details
    prompt = f"""
    You are a professional AWS cost optimization expert. A user has requested cost-saving recommendations for their AWS infrastructure.

    User Query: "{query}"

    Analysis Results:
    {context}

    Total Potential Monthly Savings: ${total_savings:.2f}

    IMPORTANT: The user wants to see SPECIFIC resource details, not just generic summaries. Include:
    - Specific instance IDs and bucket names
    - Individual CPU utilization percentages
    - Exact savings amounts for each resource
    - Specific recommendations for each resource

    Please provide a comprehensive, professional response that includes:

    1. **Executive Summary**: Brief overview of findings and total savings potential
    2. **Specific Resources Identified**: List the exact resources (instance IDs, bucket names) with their individual metrics
    3. **Key Insights**: Most important optimization opportunities with specific details
    4. **Actionable Recommendations**: Specific next steps for each resource with priority levels
    5. **Risk Considerations**: Important factors to consider before implementing changes
    6. **Monitoring Suggestions**: How to track the impact of optimizations

    Format your response in clear, professional markdown with appropriate headers and bullet points.
    Be VERY specific about individual resource details - mention instance IDs, bucket names, exact CPU percentages, and specific savings amounts.
    Use a confident but cautious tone, emphasizing the importance of testing changes in non-production environments first.

    Response:
    """
    
    try:
        print(f"[LLM] Sending prompt to Llama3 model...")
        llm_response = llm.invoke(prompt)
        enhanced_response = llm_response.content
        
        print(f"[LLM] Successfully generated enhanced response")
        return enhanced_response
        
    except Exception as e:
        print(f"[LLM] Enhancement failed: {e}")
        print(f"[LLM] Falling back to basic response")
        
        # Fallback to detailed basic response
        if service_type == "mixed":
            return f"# **AWS Cost Optimization Analysis**\n\n{ec2_result.get('response', '')}\n\n{s3_result.get('response', '')}\n\n## **Total Potential Savings**\n\nBy implementing all recommendations, you could save **${total_savings:.2f} per month** across your AWS infrastructure."
        elif service_type == "s3":
            return s3_result.get('response', 'No S3 optimization recommendations found.')
        else:
            return ec2_result.get('response', 'No EC2 optimization recommendations found.')

@app.get("/status")
def status_check():
    return {"status": "ok", "message": "fo.ai API is running"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    user_id = request.user_id or os.getenv("USERNAME", "default_user")
    rules = get_user_preferences(user_id)
    print(f"\n\n ******** [fo.ai] Using rules for {user_id}: {rules} **********\n\n")

    # Try to use state graph first, fallback to direct calls
    try:
        from app.graph import cost_graph
        
        # Prepare state for graph
        graph_state = {
            "query": request.query,
            "use_mock": settings.USE_MOCK_DATA,
            "user_id": user_id,
            "region": request.region,
            "debug": settings.DEBUG
        }
        
        # Invoke state graph
        result = cost_graph.invoke(graph_state)
        
        # Extract results from state graph
        enhanced_response = result.get("response", "No response generated")
        combined_raw = result.get("recommendations", []) + result.get("s3_recommendations", [])
        service_type = result.get("query_type", "general")
        
        # Save to chat history
        chat_entry = {
            "query": request.query,
            "response": enhanced_response,
            "service_type": service_type,
            "method": "state_graph"
        }
        append_to_list(f"foai:chat:{settings.USERNAME}", json.dumps(chat_entry))
        
        return {
            "response": enhanced_response,
            "raw": combined_raw,
            "service_type": service_type
        }
        
    except Exception as e:
        print(f"State graph failed, using fallback: {e}")
        return analyze_fallback(request, user_id, rules)

def analyze_fallback(request: AnalyzeRequest, user_id: str, rules: dict):
    """Fallback analysis using direct function calls"""
    # Detect service type and specific resources from query
    service_type_info = detect_service_type(request.query)
    service_type = service_type_info["service_type"]
    specific_resources = service_type_info["specific_resources"]
    is_specific_analysis = service_type_info["is_specific_analysis"]
    
    print(f"Fallback: Detected service type: {service_type}")
    print(f"Fallback: Specific analysis: {is_specific_analysis}")
    print(f"Fallback: Specific resources: {specific_resources}")

    # Check if this is an agent action request
    if service_type == "agent_ec2":
        print(f"[AGENT] Detected agent action request: {request.query}")
        try:
            # Initialize agent integration
            cog_integration = CogIntegration(region=request.region)
            
            # Process the natural language request
            agent_result = cog_integration.process_natural_language(request.query)
            print(f"[AGENT] Agent result: {agent_result}")
            
            if agent_result.get("success"):
                print(f"[AGENT] Action executed successfully")
                
                # Format the response for Streamlit
                response_data = agent_result.get("result", {})
                message = response_data.get("message", "Action completed successfully")
                
                # Create a clean, user-friendly response
                action_type = agent_result.get('parsed_request', {}).get('action', 'Unknown')
                instance_id = response_data.get('instance_id', '')
                
                # Create action-specific messages
                if action_type == "stop_instance":
                    formatted_response = f"## **Instance Stopped Successfully**\n\n"
                    formatted_response += f"**Instance:** `{instance_id}`\n\n"
                    formatted_response += f"**Status:** Stopped as per your request\n\n"
                    formatted_response += f"**Action:** The instance has been initiated for shutdown and will stop shortly.\n\n"
                    
                elif action_type == "start_instance":
                    formatted_response = f"## **Instance Started Successfully**\n\n"
                    formatted_response += f"**Instance:** `{instance_id}`\n\n"
                    formatted_response += f"**Status:** Started as per your request\n\n"
                    formatted_response += f"**Action:** The instance is now booting up and will be available shortly.\n\n"
                    
                elif action_type == "get_instance_status":
                    formatted_response = f"## **Instance Status**\n\n"
                    formatted_response += f"**Instance:** `{instance_id}`\n\n"
                    formatted_response += f"**Status:** {message}\n\n"
                    
                elif action_type == "list_instances":
                    formatted_response = f"## **Instance List**\n\n"
                    formatted_response += f"{message}\n\n"
                    
                elif action_type.startswith("schedule"):
                    formatted_response = f"## **Schedule Created Successfully**\n\n"
                    formatted_response += f"**Instance:** `{instance_id}`\n\n"
                    formatted_response += f"**Schedule:** {message}\n\n"
                    if "schedule" in response_data:
                        formatted_response += f"**Details:** {response_data['schedule']['description']}\n\n"
                    
                else:
                    # Generic success response
                    formatted_response = f"## **Action Completed Successfully**\n\n"
                    formatted_response += f"**Result:** {message}\n\n"
                    if instance_id:
                        formatted_response += f"**Instance:** `{instance_id}`\n\n"
                
                # Save to chat history
                chat_entry = {
                    "query": request.query,
                    "response": formatted_response,
                    "service_type": "agent_ec2",
                    "agent_result": agent_result,
                    "method": "agent_action"
                }
                append_to_list(f"foai:chat:{settings.USERNAME}", json.dumps(chat_entry))
                
                return {
                    "response": formatted_response,
                    "raw": [],  # No raw recommendations for agent actions
                    "service_type": "agent_ec2",
                    "is_specific_analysis": True,
                    "specific_resources": specific_resources,
                    "agent_result": agent_result
                }
            else:
                print(f"[AGENT] Action failed: {agent_result.get('error')}")
                error_response = f"## **Action Failed**\n\n"
                error_response += f"**Issue:** {agent_result.get('error', 'Unknown error')}\n\n"
                
                # Add helpful suggestions
                error_response += f"**What you can try:**\n"
                error_response += f"- Check if the instance ID is correct\n"
                error_response += f"- Verify the instance is in the correct region\n"
                error_response += f"- Ensure you have the necessary permissions\n"
                error_response += f"- Try a different action (start, check status, list instances)\n\n"
                
                # Add specific suggestions if available
                suggestions = agent_result.get("result", {}).get("suggestions", [])
                if suggestions:
                    error_response += f"**Specific suggestions:**\n"
                    for suggestion in suggestions:
                        error_response += f"- {suggestion}\n"
                    error_response += "\n"
                
                return {
                    "response": error_response,
                    "raw": [],
                    "service_type": "agent_ec2",
                    "is_specific_analysis": True,
                    "specific_resources": specific_resources,
                    "agent_result": agent_result
                }
                
        except Exception as e:
            print(f"[AGENT] Exception during agent processing: {e}")
            error_response = f"## **Agent Processing Error**\n\n"
            error_response += f"**Query:** {request.query}\n\n"
            error_response += f"**Error:** {str(e)}\n\n"
            error_response += f"Please ensure the agent system is properly configured."
            
            return {
                "response": error_response,
                "raw": [],
                "service_type": "agent_ec2",
                "is_specific_analysis": True,
                "specific_resources": specific_resources
            }

    # Initialize results for regular analysis
    ec2_result = {"response": "", "raw": [], "total_savings": 0.0}
    s3_result = {"response": "", "raw": [], "total_savings": 0.0}

    # Analyze based on service type and specific resources
    if service_type in ["ec2", "mixed"]:
        specific_instance_ids = specific_resources.get("ec2_instances", [])
        ec2_result = analyze_ec2_resources(user_id, request.region, rules, specific_instance_ids)
    
    if service_type in ["s3", "mixed"]:
        specific_bucket_names = specific_resources.get("s3_buckets", [])
        s3_result = analyze_s3_resources(user_id, request.region, rules, specific_bucket_names)

    # Enhance response with LLM
    enhanced_response = enhance_response_with_llm(request.query, ec2_result, s3_result, service_type)

    # Combine raw results for backward compatibility
    combined_raw = ec2_result.get("raw", []) + s3_result.get("raw", [])

    # Save to chat history
    chat_entry = {
        "query": request.query,
        "response": enhanced_response,
        "service_type": service_type,
        "ec2_savings": ec2_result.get("total_savings", 0.0),
        "s3_savings": s3_result.get("total_savings", 0.0),
        "is_specific_analysis": is_specific_analysis,
        "specific_resources": specific_resources
    }
    append_to_list(f"foai:chat:{settings.USERNAME}", json.dumps(chat_entry))

    return {
        "response": enhanced_response,
        "raw": combined_raw,
        "service_type": service_type,
        "is_specific_analysis": is_specific_analysis,
        "specific_resources": specific_resources
    }

class AnalyzeStreamRequest(BaseModel):
    user_id: str
    query: str
    region: str = "us-east-1"

@app.post("/analyze/stream")
async def stream_analysis(req: AnalyzeStreamRequest):
    print("\n-----------------------------------------\nRequest received:", req)
    rules = get_user_preferences(req.user_id)
    print("Rules : ", rules)
    
    # Detect service type and specific resources
    service_type_info = detect_service_type(req.query)
    service_type = service_type_info["service_type"]
    specific_resources = service_type_info["specific_resources"]
    is_specific_analysis = service_type_info["is_specific_analysis"]
    
    print(f"Stream: Service type: {service_type}")
    print(f"Stream: Specific analysis: {is_specific_analysis}")
    print(f"Stream: Specific resources: {specific_resources}")
    
    # Check if this is an agent action request
    if service_type == "agent_ec2":
        print(f"[AGENT STREAM] Detected agent action request: {req.query}")
        try:
            # Initialize agent integration
            cog_integration = CogIntegration(region=req.region)
            
            # Process the natural language request
            agent_result = cog_integration.process_natural_language(req.query)
            
            if agent_result.get("success"):
                print(f"[AGENT STREAM] Action executed successfully")
                response_data = agent_result.get("result", {})
                action_type = agent_result.get('parsed_request', {}).get('action', 'Unknown')
                instance_id = response_data.get('instance_id', '')
                
                # Create user-friendly streaming response
                if action_type == "stop_instance":
                    prompt = f"Instance `{instance_id}` stopped successfully as per your request. The instance has been initiated for shutdown and will stop shortly."
                elif action_type == "start_instance":
                    prompt = f"Instance `{instance_id}` started successfully as per your request. The instance is now booting up and will be available shortly."
                elif action_type == "get_instance_status":
                    prompt = f"Instance `{instance_id}` status: {response_data.get('message', 'Status retrieved')}"
                elif action_type == "list_instances":
                    prompt = f"{response_data.get('message', 'Instance list retrieved')}"
                elif action_type.startswith("schedule"):
                    prompt = f"Schedule created successfully for instance `{instance_id}`: {response_data.get('message', 'Schedule created')}"
                else:
                    prompt = f"Action completed successfully: {response_data.get('message', 'Action completed')}"
            else:
                print(f"[AGENT STREAM] Action failed: {agent_result.get('error')}")
                prompt = f"Action failed: {agent_result.get('error', 'Unknown error')}. Please check the instance ID and try again."
                
        except Exception as e:
            print(f"[AGENT STREAM] Exception during agent processing: {e}")
            prompt = f"Agent Processing Error: {str(e)}"
    
    # Get recommendations based on service type and specific resources
    elif service_type in ["ec2", "mixed"]:
        specific_instance_ids = specific_resources.get("ec2_instances", [])
        if specific_instance_ids:
            print(f"Stream: Analyzing specific EC2 instances: {specific_instance_ids}")
            ec2_data = fetch_ec2_instances(instance_ids=specific_instance_ids, region=req.region)
        else:
            print(f"Stream: Analyzing all EC2 instances")
            ec2_data = fetch_ec2_instances(region=req.region)
            
        if ec2_data:
            result = get_recommendations_and_prompt(ec2_data, rules)
            prompt = result["prompt"]
        else:
            if specific_instance_ids:
                prompt = f"No EC2 instances found with the specified IDs: {specific_instance_ids}."
            else:
                prompt = f"No EC2 instances found in region `{req.region}`."
    elif service_type == "s3":
        specific_bucket_names = specific_resources.get("s3_buckets", [])
        if specific_bucket_names:
            print(f"Stream: Analyzing specific S3 buckets: {specific_bucket_names}")
            s3_data = fetch_s3_data(region=req.region, bucket_names=specific_bucket_names)
        else:
            print(f"Stream: Analyzing all S3 buckets")
            s3_data = fetch_s3_data(region=req.region)
            
        if s3_data:
            recommendations = generate_s3_recommendations(s3_data, rules)
            if recommendations:
                if specific_bucket_names:
                    prompt = f"Found {len(recommendations)} of {len(specific_bucket_names)} specified S3 buckets that need lifecycle policies."
                else:
                    prompt = f"Found {len(recommendations)} S3 buckets that need lifecycle policies."
            else:
                if specific_bucket_names:
                    prompt = f"No S3 optimization recommendations found for the specified buckets: {specific_bucket_names}."
                else:
                    prompt = "No S3 optimization recommendations found."
        else:
            if specific_bucket_names:
                prompt = f"No S3 buckets found with the specified names: {specific_bucket_names}."
            else:
                prompt = f"No S3 buckets found in region `{req.region}`."
    else:
        prompt = "No resources found to analyze."

    def stream_gen():
        yield from stream_response(prompt)

    return StreamingResponse(stream_gen(), media_type="text/plain")

@app.get("/memory", response_model=list,tags=["Memory"])
def get_memory():
    key = f"foai:chat:{settings.USERNAME}"
    raw_entries = get_list(key, limit=20)
    memory = []

    for item in raw_entries:
        try:
            memory.append(json.loads(item))
        except Exception:
            memory.append({"error": "Failed to parse item", "data": item})

    return memory

@app.delete("/memory", tags=["Memory"])
def clear_memory(user_id: str = None):
    """Clear chat memory for a user"""
    try:
        target_user = user_id or settings.USERNAME
        key = f"foai:chat:{target_user}"
        from memory.redis_memory import r
        r.delete(key)
        return {"message": f"Chat memory cleared for user {target_user}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# User preferences endpoints

@app.get("/preferences/explain", tags=["Preferences"])
async def explain_preferences(request: Request, user_id: str):
    """
    Generate a natural language explanation of the user's preferences using the LLM.
    """
    try:
        # Get user preferences from Redis
        prefs = get_user_preferences(user_id)
        # Retrieve 'persona' from query parameters, default to 'engineer' if not provided
        persona = request.query_params.get("persona", "engineer")
        # Build the prompt for LLM based on preferences and persona
        prompt = build_explain_prompt(prefs, persona=persona)
        print("Prompt for LLM:", prompt)
        # Invoke LLM for the explanation
        explanation = llm.invoke(prompt)
        print("LLM Explanation:", explanation)

        return {
            "user_id": user_id,
            "preferences": prefs,
            "explanation": explanation,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/preferences/load", tags=["Preferences"])
def load_preferences(user_id: str):
    try:
        prefs = get_user_preferences(user_id)
        return {"user_id": user_id, "preferences": prefs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/preferences/save", tags=["Preferences"])
def save_preferences(payload: PreferencePayload):
    try:
        set_user_preferences(payload.user_id, payload.preferences)
        return {"message": "Preferences saved", "user_id": payload.user_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/preferences/reset", tags=["Preferences"])
def reset_preferences(payload: dict, user_id: str = "user_id"):
    user_id = payload.get("user_id", user_id)
    if not user_id:
        return JSONResponse(status_code=400, content={"error": "Missing user_id"})
    try:
        set_user_preferences(user_id, DEFAULT_PREFS)
        return {"message": "Preferences reset to default", "user_id": user_id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Cloud service routers
app.include_router(aws_ec2_router, prefix="/aws/ec2", tags=["AWS EC2"])

# AI Agent routers
from app.agents.api_endpoints import router as agent_router
app.include_router(agent_router)

# Import agent integration
from app.agents.cog_integration import CogIntegration

