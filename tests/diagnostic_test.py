#!/usr/bin/env python3
"""
Simple Diagnostic Test for Graph RAG System

This script tests individual components to identify what's working and what's not.
"""
import requests
import json
from typing import Dict, Any
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint and return results."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"success": False, "error": f"Unsupported method: {method}"}
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
            "error": None if response.status_code == 200 else f"HTTP {response.status_code}"
        }
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection refused - server not running"}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    """Run diagnostic tests."""
    print("🔍 GRAPH RAG SYSTEM DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test 1: Health endpoints
    print("\n1️⃣ HEALTH ENDPOINTS")
    print("-" * 30)
    
    health_tests = [
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/health/detailed"),
    ]
    
    for method, endpoint in health_tests:
        result = test_endpoint(method, endpoint)
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} {method} {endpoint}")
        if not result["success"]:
            print(f"      Error: {result['error']}")
        else:
            print(f"      Response: {str(result['response'])[:100]}...")
    
    # Test 2: Simple semantic endpoints
    print("\n2️⃣ SEMANTIC ENDPOINTS")
    print("-" * 30)
    
    semantic_tests = [
        ("POST", "/api/v1/semantic/gremlin", {"prompt": "Find all hotels"}),
        ("GET", "/api/v1/semantic/models", None),
        ("POST", "/api/v1/semantic/vector", {"query": "hotels", "limit": 5}),
    ]
    
    for method, endpoint, data in semantic_tests:
        result = test_endpoint(method, endpoint, data)
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {status} {method} {endpoint}")
        if not result["success"]:
            print(f"      Error: {result['error']}")
        else:
            print(f"      Response: {str(result['response'])[:100]}...")
    
    # Test 3: Simple analytics (might fail due to no database)
    print("\n3️⃣ ANALYTICS ENDPOINTS (Expected to fail without database)")
    print("-" * 30)
    
    analytics_tests = [
        ("GET", "/api/v1/statistics", None),
        ("GET", "/api/v1/average/hotels", None),
    ]
    
    for method, endpoint, data in analytics_tests:
        result = test_endpoint(method, endpoint)
        status = "✅ PASS" if result["success"] else "❌ FAIL (Expected)"
        print(f"   {status} {method} {endpoint}")
        if not result["success"]:
            print(f"      Error: {result['error']}")
        else:
            print(f"      Response: {str(result['response'])[:100]}...")
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC COMPLETE")
    print("\nKey findings:")
    print("• Health endpoints should work")
    print("• LLM endpoints may fail if not properly initialized")
    print("• Database endpoints will fail without graph database connection")
    print("• Vector search may work but return empty results")

if __name__ == "__main__":
    main()
