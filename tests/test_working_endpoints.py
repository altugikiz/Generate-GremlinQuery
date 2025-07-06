#!/usr/bin/env python3
"""
Test script to verify which endpoints are working with the current server setup.
"""

import requests
import json
import sys
from typing import Dict, Any


def test_endpoint(method: str, url: str, payload: Dict[str, Any] = None) -> None:
    """Test a single endpoint and print results."""
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=payload)
        else:
            print(f"❌ Unsupported method: {method}")
            return
        
        print(f"🔍 {method.upper()} {url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    if 'answer' in data:
                        print(f"   ✅ Answer: {data['answer'][:100]}...")
                    elif 'status' in data:
                        print(f"   ✅ Status: {data['status']}")
                    elif 'models' in data:
                        print(f"   ✅ Models available: {len(data.get('models', []))}")
                    else:
                        print(f"   ✅ Response keys: {list(data.keys())}")
                else:
                    print(f"   ✅ Response type: {type(data)}")
            except:
                print(f"   ✅ Non-JSON response: {response.text[:100]}...")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
        
        print()
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        print()


def main():
    """Test various endpoints to see what's working."""
    print("🧪 TESTING WORKING ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoints (these should work)
    print("🏥 HEALTH ENDPOINTS:")
    test_endpoint("GET", f"{base_url}/api/v1/health")
    test_endpoint("GET", f"{base_url}/api/v1/health/detailed")
    
    # Test semantic endpoints (these might work in development mode)
    print("🤖 SEMANTIC ENDPOINTS:")
    
    # Test models info
    test_endpoint("GET", f"{base_url}/api/v1/semantic/models")
    
    # Test semantic ask
    semantic_payload = {
        "query": "What can you tell me about hotels?",
        "include_gremlin_query": True,
        "include_semantic_chunks": True,
        "include_context": False
    }
    test_endpoint("POST", f"{base_url}/api/v1/semantic/ask", semantic_payload)
    
    # Test gremlin translation
    gremlin_payload = {
        "prompt": "Find all hotels",
        "include_explanation": True
    }
    test_endpoint("POST", f"{base_url}/api/v1/semantic/gremlin", gremlin_payload)
    
    # Test with Turkish query
    turkish_payload = {
        "query": "VIP müşterileri göster",
        "include_gremlin_query": True,
        "include_semantic_chunks": False
    }
    test_endpoint("POST", f"{base_url}/api/v1/semantic/ask", turkish_payload)
    
    print("🎯 SUMMARY:")
    print("- Health endpoints should be working ✅")
    print("- Semantic endpoints may work in development mode ⚠️")
    print("- Graph-dependent endpoints will fail without database ❌")
    print("- LLM features should work if API keys are valid ⚠️")


if __name__ == "__main__":
    main()
