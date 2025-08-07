#!/usr/bin/env python3
"""
Comprehensive test script for the fo.ai EC2 and S3 analysis system
"""

import requests
import json
import sys
import time

# Configuration
API_BASE_URL = "http://localhost:8000"
USER_ID = "test_user"
REGION = "us-east-1"

def test_endpoint(endpoint, method="GET", data=None, params=None, expected_status=200):
    """Test an API endpoint and return the result"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, params=params)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        else:
            print(f"Unsupported method: {method}")
            return None
            
        if response.status_code == expected_status:
            print(f"{method} {endpoint} - Success")
            return response.json() if response.content else None
        else:
            print(f"{method} {endpoint} - Failed ({response.status_code})")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"{method} {endpoint} - Exception: {e}")
        return None

def test_preferences():
    """Test user preferences functionality"""
    print("\n🧪 Testing User Preferences...")
    
    # Test loading default preferences
    prefs = test_endpoint("/preferences/load", params={"user_id": USER_ID})
    if prefs:
        print(f"   Default preferences loaded: {len(prefs.get('preferences', {}))} settings")
    
    # Test saving custom preferences
    custom_prefs = {
        "cpu_threshold": 15,
        "min_uptime_hours": 48,
        "min_savings_usd": 10,
        "s3_standard_to_ia_days": 45,
        "s3_ia_to_glacier_days": 120
    }
    
    save_result = test_endpoint("/preferences/save", method="POST", data={
        "user_id": USER_ID,
        "preferences": custom_prefs
    })
    
    if save_result:
        print("   Custom preferences saved successfully")
    
    # Test preference explanation
    explain_result = test_endpoint("/preferences/explain", params={
        "user_id": USER_ID,
        "persona": "engineer"
    })
    
    if explain_result:
        print("   Preference explanation generated")

def test_ec2_analysis():
    """Test EC2 analysis functionality"""
    print("\n🧪 Testing EC2 Analysis...")
    
    # Test EC2-specific query
    ec2_query = "Find underutilized EC2 instances with low CPU usage"
    result = test_endpoint("/analyze", method="POST", data={
        "query": ec2_query,
        "user_id": USER_ID,
        "region": REGION
    })
    
    if result:
        print(f"   EC2 analysis completed: {result.get('service_type', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Raw results: {len(result.get('raw', []))} items")

def test_s3_analysis():
    """Test S3 analysis functionality"""
    print("\n🧪 Testing S3 Analysis...")
    
    # Test S3-specific query
    s3_query = "Analyze my S3 buckets for cost optimization opportunities"
    result = test_endpoint("/analyze", method="POST", data={
        "query": s3_query,
        "user_id": USER_ID,
        "region": REGION
    })
    
    if result:
        print(f"   S3 analysis completed: {result.get('service_type', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Raw results: {len(result.get('raw', []))} items")

def test_mixed_analysis():
    """Test mixed EC2/S3 analysis"""
    print("\n🧪 Testing Mixed Analysis...")
    
    # Test general query that should trigger both services
    mixed_query = "What are my biggest cost optimization opportunities across all services?"
    result = test_endpoint("/analyze", method="POST", data={
        "query": mixed_query,
        "user_id": USER_ID,
        "region": REGION
    })
    
    if result:
        print(f"   Mixed analysis completed: {result.get('service_type', 'unknown')}")
        print(f"   Response length: {len(result.get('response', ''))} chars")
        print(f"   Raw results: {len(result.get('raw', []))} items")

def test_streaming():
    """Test streaming analysis"""
    print("\n🧪 Testing Streaming Analysis...")
    
    # Test streaming with EC2 query
    stream_result = test_endpoint("/analyze/stream", method="POST", data={
        "user_id": USER_ID,
        "query": "Find expensive EC2 instances",
        "region": REGION
    })
    
    if stream_result is not None:  # Streaming returns None for success
        print("   Streaming analysis completed")

def test_memory_management():
    """Test memory management"""
    print("\n🧪 Testing Memory Management...")
    
    # Test getting memory
    memory = test_endpoint("/memory")
    if memory is not None:
        print(f"   Memory retrieved: {len(memory)} entries")
    
    # Test clearing memory
    clear_result = test_endpoint("/memory", method="DELETE", params={"user_id": USER_ID})
    if clear_result:
        print("   Memory cleared successfully")

def test_service_detection():
    """Test service type detection with various queries"""
    print("\n🧪 Testing Service Detection...")
    
    test_queries = [
        ("Find EC2 instances with low CPU", "ec2"),
        ("Analyze S3 buckets for lifecycle policies", "s3"),
        ("Which buckets need optimization", "s3"),
        ("Show me all cost optimization opportunities", "mixed"),
        ("What are my biggest savings opportunities", "mixed")
    ]
    
    for query, expected_type in test_queries:
        result = test_endpoint("/analyze", method="POST", data={
            "query": query,
            "user_id": USER_ID,
            "region": REGION
        })
        
        if result:
            detected_type = result.get('service_type', 'unknown')
            status = "PASS" if detected_type == expected_type else "FAIL"
            print(f"   {status} Query: '{query[:30]}...' -> {detected_type} (expected: {expected_type})")

def main():
    print("Comprehensive fo.ai System Test")
    print("=" * 60)
    
    # Test basic connectivity
    print("\n1. Testing basic connectivity...")
    status = test_endpoint("/status")
    if not status:
        print("Cannot connect to API. Make sure the server is running.")
        print("   Run: uvicorn api:app --reload")
        return
    
    # Run all tests
    test_preferences()
    test_ec2_analysis()
    test_s3_analysis()
    test_mixed_analysis()
    test_streaming()
    test_memory_management()
    test_service_detection()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("\nNext Steps:")
    print("1. Start the UI: streamlit run foai_ui.py")
    print("2. Open http://localhost:8501 in your browser")
    print("3. Set your preferences in the sidebar")
    print("4. Start asking questions about your AWS resources!")
    print("\nExample queries:")
    print("   - 'Find underutilized EC2 instances'")
    print("   - 'Analyze my S3 buckets for cost optimization'")
    print("   - 'What are my biggest cost savings opportunities?'")

if __name__ == "__main__":
    main() 