"""
Agentic Service Detection for fo.ai
Uses LLM to intelligently detect AWS services and extract resources from natural language queries
"""

from typing import Dict, List, Any
import json
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

class AgenticServiceDetector:
    """
    Uses LLM to intelligently detect AWS services and extract resources from queries
    """
    
    def __init__(self):
        self.llm = ChatOllama(model=LLM_MODEL, temprature=LLM_TEMPERATURE)
        self.service_detection_prompt = self._create_service_detection_prompt()
        self.resource_extraction_prompt = self._create_resource_extraction_prompt()
    
    def _create_service_detection_prompt(self) -> PromptTemplate:
        """Create prompt for service type detection"""
        return PromptTemplate.from_template("""
You are an AWS service detection expert. Analyze the user's query and determine which AWS services they are referring to.

Available service types:
- "ec2" - For compute instances, virtual machines, servers, CPU usage, etc.
- "s3" - For storage, buckets, objects, files, lifecycle policies, etc.
- "agent_ec2" - For actions on EC2 instances (stop, start, schedule, etc.)
- "mixed" - For queries about multiple services
- "general" - For general cost optimization, billing, or unclear queries

Consider these factors:
1. **EC2 indicators**: instance, server, compute, CPU, machine, virtual, running, stopped
2. **S3 indicators**: bucket, storage, object, file, lifecycle, glacier, archive, backup
3. **Agent actions**: stop, start, shutdown, power, schedule, boot, turn on/off
4. **Context clues**: cost, optimization, savings, billing, usage

Return ONLY a JSON object with this exact structure:
{{
    "service_type": "ec2|s3|agent_ec2|mixed|general",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this service type was chosen"
}}

User Query: {query}

JSON Response:
""")
    
    def _create_resource_extraction_prompt(self) -> PromptTemplate:
        """Create prompt for resource extraction"""
        return PromptTemplate.from_template("""
            You are an AWS resource extraction expert. Extract specific resource identifiers from the user's query.

            Extract these resource types:
            1. **EC2 Instance IDs**: Format "i-xxxxxxxxxxxxxxxxx" (8-17 hex characters)
            2. **S3 Bucket Names**: Valid bucket names (3-63 characters, lowercase, hyphens, dots)

            Return ONLY a JSON object with this exact structure:
            {{
                "ec2_instances": ["i-1234567890abcdef0", "i-0987654321fedcba0"],
                "s3_buckets": ["my-bucket-name", "backup-data-2024"],
                "extraction_notes": "Any notes about the extraction process"
            }}

            Rules:
            - Only extract valid AWS resource identifiers
            - For S3 buckets, only extract if explicitly mentioned
            - Include partial matches if they look like valid resource IDs
            - Be conservative - better to miss than to extract incorrectly

            User Query: {query}

            JSON Response:
            """)
    
    def detect_service_type(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to intelligently detect the service type from a query
        """
        try:
            if DEBUG:
                print(f"[AGENTIC DETECTION] Analyzing query: '{query}'")
            
            # Get service type detection
            service_prompt = self.service_detection_prompt.format(query=query)
            service_response = self.llm.invoke(service_prompt)
            
            if DEBUG:
                print(f"[AGENTIC DETECTION] Service response: {service_response.content}")
            
            # Parse service detection response
            service_data = self._parse_json_response(service_response.content)
            
            if not service_data:
                if DEBUG:
                    print(f"[AGENTIC DETECTION] Failed to parse service response, using fallback")
                return self._fallback_service_detection(query)
            
            service_type = service_data.get("service_type", "general")
            confidence = service_data.get("confidence", 0.5)
            reasoning = service_data.get("reasoning", "No reasoning provided")
            
            if DEBUG:
                print(f"[AGENTIC DETECTION] Detected service: {service_type} (confidence: {confidence})")
                print(f"[AGENTIC DETECTION] Reasoning: {reasoning}")
            
            # Get resource extraction
            resource_prompt = self.resource_extraction_prompt.format(query=query)
            resource_response = self.llm.invoke(resource_prompt)
            
            if DEBUG:
                print(f"[AGENTIC DETECTION] Resource response: {resource_response.content}")
            
            # Parse resource extraction response
            resource_data = self._parse_json_response(resource_response.content)
            
            if not resource_data:
                if DEBUG:
                    print(f"[AGENTIC DETECTION] Failed to parse resource response, using regex fallback")
                resource_data = self._fallback_resource_extraction(query)
            
            specific_resources = {
                "ec2_instances": resource_data.get("ec2_instances", []),
                "s3_buckets": resource_data.get("s3_buckets", [])
            }
            
            is_specific_analysis = len(specific_resources["ec2_instances"]) > 0 or len(specific_resources["s3_buckets"]) > 0
            
            result = {
                "service_type": service_type,
                "specific_resources": specific_resources,
                "is_specific_analysis": is_specific_analysis,
                "confidence": confidence,
                "reasoning": reasoning,
                "method": "agentic"
            }
            
            if DEBUG:
                print(f"[AGENTIC DETECTION] Final result: {result}")
            
            return result
            
        except Exception as e:
            if DEBUG:
                print(f"[AGENTIC DETECTION] Error: {e}")
            return self._fallback_service_detection(query)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, handling various formats"""
        try:
            # Try to extract JSON from the response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            if DEBUG:
                print(f"[AGENTIC DETECTION] JSON parse error: {e}")
                print(f"[AGENTIC DETECTION] Raw response: {response}")
            return {}
    
    def _fallback_service_detection(self, query: str) -> Dict[str, Any]:
        """Fallback to keyword-based detection if LLM fails"""
        if DEBUG:
            print(f"[AGENTIC DETECTION] Using fallback keyword detection")
        
        query_lower = query.lower()
        
        # Simple keyword detection as fallback
        ec2_keywords = ["ec2", "instance", "cpu", "compute", "server", "machine", "virtual"]
        s3_keywords = ["s3", "bucket", "storage", "object", "file", "lifecycle", "glacier", "ia"]
        agent_keywords = ["stop", "start", "shutdown", "power", "schedule", "boot", "turn"]
        
        ec2_score = sum(1 for keyword in ec2_keywords if keyword in query_lower)
        s3_score = sum(1 for keyword in s3_keywords if keyword in query_lower)
        agent_score = sum(1 for keyword in agent_keywords if keyword in query_lower)
        
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
            service_type = "general"
        
        return {
            "service_type": service_type,
            "specific_resources": self._fallback_resource_extraction(query),
            "is_specific_analysis": False,
            "confidence": 0.3,
            "reasoning": "Fallback keyword detection used",
            "method": "fallback"
        }
    
    def _fallback_resource_extraction(self, query: str) -> Dict[str, List[str]]:
        """Fallback resource extraction using regex patterns"""
        ec2_instances = []
        s3_buckets = []
        
        # Extract EC2 instance IDs
        ec2_pattern = r'\bi-[a-f0-9]{8,17}\b'
        ec2_instances = re.findall(ec2_pattern, query, re.IGNORECASE)
        
        # Extract S3 bucket names (conservative approach)
        quoted_bucket_pattern = r'["\']([a-z0-9][a-z0-9.-]*[a-z0-9])["\']'
        quoted_matches = re.findall(quoted_bucket_pattern, query, re.IGNORECASE)
        s3_buckets.extend(quoted_matches)
        
        return {
            "ec2_instances": ec2_instances,
            "s3_buckets": s3_buckets
        }
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get statistics about the detection system"""
        return {
            "model": LLM_MODEL,
            "temperature": LLM_TEMPERATURE,
            "debug_enabled": DEBUG,
            "method": "agentic_with_fallback"
        }
