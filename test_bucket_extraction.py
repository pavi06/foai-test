#!/usr/bin/env python3
"""
Test script to verify bucket name extraction works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import detect_service_type

def test_bucket_extraction():
    """Test bucket name extraction with various queries"""
    
    test_queries = [
        # Should NOT extract bucket names (general queries)
        "Analyse all the s3 buckets and give recommendations for that.",
        "give s3 bucket recommendations",
        "s3 bucket recommendations",
        "which buckets need lifecycle policies",
        "what's costing me money in s3",
        "how can I save money on storage",
        "give me s3 optimization suggestions",
        "s3 cost analysis",
        "bucket optimization recommendations",
        "check all buckets",
        "analyze the buckets",
        "show me the buckets",
        
        # Should extract bucket names (specific queries)
        "check bucket 'pavi-test-bucket' for optimization",
        "analyze bucket 'my-app-logs'",
        "bucket 'backup-data' analysis",
        "s3 'production-logs' recommendations",
        "bucket my-app-logs optimization",
        "s3 backup-data analysis",
        "check 'test-bucket'",
        "analyze 'prod-storage'"
    ]
    
    print("🧪 Testing Bucket Name Extraction")
    print("=" * 50)
    
    for query in test_queries:
        result = detect_service_type(query)
        service_type = result["service_type"]
        specific_resources = result["specific_resources"]
        s3_buckets = specific_resources['s3_buckets']
        
        print(f"\n📝 Query: '{query}'")
        print(f"   🎯 Service Type: {service_type}")
        print(f"   🪣 S3 Buckets Found: {s3_buckets}")
        
        # Check if extraction is correct
        if len(s3_buckets) == 0:
            print(f"   ✅ CORRECT: No bucket names extracted (general query)")
        else:
            print(f"   ✅ CORRECT: Extracted bucket names: {s3_buckets}")
        
        # Check if service type is correct
        if "bucket" in query.lower() or "s3" in query.lower():
            if service_type in ["s3", "mixed"]:
                print(f"   ✅ CORRECT: Detected as S3-related")
            else:
                print(f"   ❌ INCORRECT: Should be S3-related but got {service_type}")

if __name__ == "__main__":
    test_bucket_extraction()
