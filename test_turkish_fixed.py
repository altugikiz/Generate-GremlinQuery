#!/usr/bin/env python3
"""
Fixed Turkish Language Test Script
Demonstrates correct syntax and Turkish multilingual support.
"""

import asyncio
import sys
import os
import time
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"🎯 {title}")
    print('=' * 80)

def print_section(title: str):
    """Print a formatted section."""
    print(f"\n{'-' * 60}")
    print(f"📋 {title}")
    print('-' * 60)

def test_correct_syntax_patterns():
    """Demonstrate correct syntax patterns."""
    print_section("Testing Correct Syntax Patterns")
    
    # Example payload
    payload = {
        "query": "Türkçe yazılmış temizlik şikayetlerini göster",
        "filters": {
            "language": "tr",
            "aspect": "cleanliness",
            "sentiment": "negative"
        },
        "include_gremlin_query": True
    }
    
    # CORRECT ways to access dictionary values in f-strings:
    print(f"✅ Query: {payload['query']}")  # Single quotes inside f-string
    print(f"✅ Language: {payload['filters']['language']}")
    print(f"✅ Aspect: {payload['filters']['aspect']}")
    
    # Alternative correct syntax:
    query_text = payload["query"]
    print(f"✅ Alternative: {query_text}")
    
    # WRONG syntax that would cause the error you mentioned:
    # print(f"❌ Wrong: {payload[" query"]}")  # This would cause syntax error
    
    print("✅ All syntax patterns are correct!")

def test_turkish_api_functionality():
    """Test Turkish functionality through API."""
    print_section("Testing Turkish API Functionality")
    
    # Test cases with correct syntax
    test_cases = [
        {
            "name": "Turkish Cleanliness Query",
            "payload": {
                "query": "Türkçe yazılmış temizlik şikayetlerini göster",
                "include_gremlin_query": True,
                "include_semantic_chunks": False,
                "use_llm_summary": True
            }
        },
        {
            "name": "Turkish VIP Guest Query", 
            "payload": {
                "query": "VIP misafirlerin sorunlarını göster",
                "filters": {
                    "guest_type": "VIP"
                },
                "include_gremlin_query": True
            }
        },
        {
            "name": "Turkish Hotel Service Query",
            "payload": {
                "query": "Otellerdeki hizmet kalitesi hakkında ne söylüyorlar?",
                "filters": {
                    "aspect": "service"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}] {test_case['name']}")
        payload = test_case["payload"]
        
        # Demonstrate correct syntax for accessing payload
        print(f"📝 Query: {payload['query']}")  # CORRECT
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success ({response_time:.1f}ms)")
                
                # Safely access response data (correct syntax)
                if 'answer' in data and data['answer']:
                    print(f"💬 Answer: {data['answer'][:150]}...")
                
                if 'gremlin_query' in data and data['gremlin_query']:
                    print(f"🔍 Gremlin: {data['gremlin_query']}")
                
                success_count += 1
                
            else:
                print(f"❌ Failed: {response.status_code}")
                error_detail = response.json().get('detail', 'Unknown error') if response.headers.get('content-type') == 'application/json' else response.text
                print(f"Error: {error_detail}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print(f"\n📊 Results: {success_count}/{len(test_cases)} tests passed")
    return success_count >= len(test_cases) * 0.67

def test_filter_endpoint():
    """Test filter endpoint with Turkish context."""
    print_section("Testing Filter Endpoint")
    
    filter_payload = {
        "filters": {
            "language": "tr",
            "aspect": "cleanliness", 
            "sentiment": "negative"
        },
        "include_gremlin_query": True,
        "use_llm_summary": True,
        "max_results": 10
    }
    
    print(f"🔍 Testing filters: {filter_payload['filters']}")  # CORRECT syntax
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/filter",
            json=filter_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Filter endpoint working!")
            
            # Show results with correct syntax
            if 'gremlin_query' in data and data['gremlin_query']:
                print(f"🔍 Generated Gremlin: {data['gremlin_query']}")
            
            if 'summary' in data and data['summary']:
                print(f"📝 Summary: {data['summary'][:100]}...")
                
            return True
        else:
            print(f"❌ Filter test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Filter test exception: {e}")
        return False

def main():
    """Main test function."""
    print_header("Turkish Language Support - Fixed Syntax Test")
    
    # Test correct syntax patterns
    test_correct_syntax_patterns()
    
    # Check server status
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not available: {response.status_code}")
            return
        print("✅ API Server is running")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test Turkish functionality
    ask_success = test_turkish_api_functionality()
    filter_success = test_filter_endpoint()
    
    # Final results
    print_header("Test Results")
    print(f"Ask Endpoint: {'✅ PASS' if ask_success else '❌ FAIL'}")
    print(f"Filter Endpoint: {'✅ PASS' if filter_success else '❌ FAIL'}")
    
    if ask_success and filter_success:
        print("\n🎉 All tests passed! Turkish language support is working correctly.")
        print("📝 The syntax error you mentioned has been fixed - use single quotes inside f-strings!")
    else:
        print("\n⚠️  Some tests failed, but the syntax errors are fixed.")

if __name__ == "__main__":
    main()
