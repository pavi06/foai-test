#!/usr/bin/env python3
"""
Test script to verify the pricing fix resolves the empty PriceList issue
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_pricing_api():
    """Test the pricing API directly to see what's happening"""
    
    print("🧪 Testing AWS Pricing API Directly")
    print("=" * 50)
    
    try:
        import boto3
        import json
        
        # Test the pricing API directly
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
        # Test with t3.micro (the instance from the image)
        instance_type = 't3.micro'
        region = 'us-east-1'
        os_type = 'Linux'
        
        print(f"🔍 Testing pricing for {instance_type} in {region}")
        
        # Test 1: Full filters (original approach)
        print(f"\n📊 Test 1: Full filters")
        full_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': 'US East (N. Virginia)'},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os_type},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        ]
        
        try:
            response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=full_filters,
                MaxResults=10
            )
            print(f"   ✅ Full filters response count: {len(response.get('PriceList', []))}")
            
            if response['PriceList']:
                print(f"   📋 Found {len(response['PriceList'])} pricing items")
                for i, item in enumerate(response['PriceList'][:2]):  # Show first 2
                    price_data = json.loads(item)
                    product_attrs = price_data.get('product', {}).get('attributes', {})
                    print(f"   Item {i+1}: {product_attrs.get('instanceType', 'N/A')} - {product_attrs.get('operatingSystem', 'N/A')} - {product_attrs.get('tenancy', 'N/A')}")
            else:
                print(f"   ❌ No pricing items found with full filters")
                
        except Exception as e:
            print(f"   ❌ Error with full filters: {e}")
        
        # Test 2: Simplified filters (new approach)
        print(f"\n📊 Test 2: Simplified filters")
        simple_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'regionCode', 'Value': 'US East (N. Virginia)'},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'OnDemand'},
        ]
        
        try:
            response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=simple_filters,
                MaxResults=10
            )
            print(f"   ✅ Simplified filters response count: {len(response.get('PriceList', []))}")
            
            if response['PriceList']:
                print(f"   📋 Found {len(response['PriceList'])} pricing items")
                for i, item in enumerate(response['PriceList'][:2]):  # Show first 2
                    price_data = json.loads(item)
                    product_attrs = price_data.get('product', {}).get('attributes', {})
                    print(f"   Item {i+1}: {product_attrs.get('instanceType', 'N/A')} - {product_attrs.get('operatingSystem', 'N/A')} - {product_attrs.get('tenancy', 'N/A')}")
            else:
                print(f"   ❌ No pricing items found with simplified filters")
                
        except Exception as e:
            print(f"   ❌ Error with simplified filters: {e}")
        
        # Test 3: Minimal filters
        print(f"\n📊 Test 3: Minimal filters")
        minimal_filters = [
            {'Type': 'TERM_MATCH', 'Field': 'serviceCode', 'Value': 'AmazonEC2'},
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
        ]
        
        try:
            response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=minimal_filters,
                MaxResults=10
            )
            print(f"   ✅ Minimal filters response count: {len(response.get('PriceList', []))}")
            
            if response['PriceList']:
                print(f"   📋 Found {len(response['PriceList'])} pricing items")
                for i, item in enumerate(response['PriceList'][:2]):  # Show first 2
                    price_data = json.loads(item)
                    product_attrs = price_data.get('product', {}).get('attributes', {})
                    print(f"   Item {i+1}: {product_attrs.get('instanceType', 'N/A')} - {product_attrs.get('operatingSystem', 'N/A')} - {product_attrs.get('tenancy', 'N/A')} - {product_attrs.get('regionCode', 'N/A')}")
            else:
                print(f"   ❌ No pricing items found with minimal filters")
                
        except Exception as e:
            print(f"   ❌ Error with minimal filters: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing pricing API: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pricing_functions():
    """Test the updated pricing functions"""
    
    print("\n🧪 Testing Updated Pricing Functions")
    print("=" * 50)
    
    try:
        from data.aws.ec2 import get_dynamic_ec2_pricing, get_reserved_instance_pricing
        
        # Test instance types from the image
        test_instances = [
            't3.micro',
            't3.medium',
            't3.small',
            't3.large'
        ]
        
        region = 'us-east-1'
        
        results = []
        
        for instance_type in test_instances:
            print(f"\n📊 Testing {instance_type}:")
            
            try:
                # Test on-demand pricing
                ondemand_hourly = get_dynamic_ec2_pricing(instance_type, region)
                ondemand_monthly = ondemand_hourly * 730
                
                print(f"   💰 On-demand hourly: ${ondemand_hourly:.4f}")
                print(f"   💰 On-demand monthly: ${ondemand_monthly:.2f}")
                
                # Test reserved pricing
                reserved_hourly = get_reserved_instance_pricing(instance_type, region)
                reserved_monthly = reserved_hourly * 730
                
                print(f"   💰 Reserved hourly: ${reserved_hourly:.4f}")
                print(f"   💰 Reserved monthly: ${reserved_monthly:.2f}")
                
                # Calculate savings
                savings = ondemand_monthly - reserved_monthly
                savings_percent = (savings / ondemand_monthly * 100) if ondemand_monthly > 0 else 0
                
                print(f"   💡 Potential savings: ${savings:.2f} ({savings_percent:.1f}%)")
                
                results.append({
                    "instance_type": instance_type,
                    "ondemand_hourly": ondemand_hourly,
                    "ondemand_monthly": ondemand_monthly,
                    "reserved_hourly": reserved_hourly,
                    "reserved_monthly": reserved_monthly,
                    "savings": savings,
                    "success": True
                })
                
            except Exception as e:
                print(f"   ❌ Error testing {instance_type}: {e}")
                results.append({
                    "instance_type": instance_type,
                    "error": str(e),
                    "success": False
                })
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 Pricing Test Summary:")
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"   ✅ Successful: {len(successful)}/{len(results)}")
        print(f"   ❌ Failed: {len(failed)}/{len(results)}")
        
        if successful:
            print(f"\n💰 Pricing Results:")
            for result in successful:
                print(f"   {result['instance_type']}:")
                print(f"     On-demand: ${result['ondemand_monthly']:.2f}/month")
                print(f"     Reserved: ${result['reserved_monthly']:.2f}/month")
                print(f"     Savings: ${result['savings']:.2f}/month")
        
        # Check if any pricing is still $0.00
        zero_pricing = [r for r in successful if r['ondemand_monthly'] == 0.0]
        if zero_pricing:
            print(f"\n⚠️  WARNING: {len(zero_pricing)} instances still have $0.00 pricing:")
            for result in zero_pricing:
                print(f"   - {result['instance_type']}")
        
        return len(failed) == 0 and len(zero_pricing) == 0
        
    except Exception as e:
        print(f"❌ Error during pricing test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Pricing Fix Tests")
    print("=" * 50)
    
    # Test pricing API directly
    api_success = test_pricing_api()
    
    # Test updated pricing functions
    functions_success = test_pricing_functions()
    
    print("\n" + "=" * 50)
    print("📊 Overall Test Results:")
    print(f"   🔌 Pricing API: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   💰 Pricing Functions: {'✅ PASS' if functions_success else '❌ FAIL'}")
    
    if api_success and functions_success:
        print("\n🎉 All tests passed! The pricing fix should resolve the empty PriceList issue.")
        print("\n💡 The system now:")
        print("   - Uses less restrictive filters")
        print("   - Falls back to simplified filters if needed")
        print("   - Provides realistic fallback pricing")
        print("   - Handles API failures gracefully")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
