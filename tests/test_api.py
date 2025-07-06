#!/usr/bin/env python3
"""
Test script for Graph RAG Pipeline API endpoints.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed - Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Health check failed - Status: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Connection failed - Is the server running?")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_simple_search():
    """Test the simple search endpoint."""
    print("🔍 Testing simple search endpoint...")
    try:
        params = {
            "q": "hotel",
            "search_type": "hybrid",
            "max_results": 5
        }
        response = requests.get(f"{BASE_URL}/api/v1/search/simple", params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simple search passed - Found {len(data.get('semantic_results', []))} semantic results")
            return True
        else:
            print(f"❌ Simple search failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Simple search error: {e}")
        return False

def test_hybrid_search():
    """Test the hybrid search endpoint."""
    print("🔍 Testing hybrid search endpoint...")
    try:
        payload = {
            "query": "best hotels with good service",
            "search_type": "hybrid",
            "max_results": 10,
            "include_embeddings": False
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            graph_count = data.get('graph_results', {}).get('total_count', 0)
            semantic_count = len(data.get('semantic_results', []))
            print(f"✅ Hybrid search passed - Graph: {graph_count}, Semantic: {semantic_count}")
            return True
        else:
            print(f"❌ Hybrid search failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Hybrid search error: {e}")
        return False

def test_statistics():
    """Test the statistics endpoint."""
    print("🔍 Testing statistics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/statistics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistics endpoint passed")
            return True
        else:
            print(f"❌ Statistics failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Statistics error: {e}")
        return False

def run_tests():
    """Run all tests."""
    print("🏁 Graph RAG Pipeline API Tests")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    max_retries = 30
    for i in range(max_retries):
        if test_health_endpoint():
            break
        if i < max_retries - 1:
            print(f"Retrying in 1 second... ({i+1}/{max_retries})")
            time.sleep(1)
    else:
        print("❌ Server is not responding. Please start the server first.")
        sys.exit(1)
    
    print("\n🧪 Running API tests...")
    print("-" * 30)
    
    # Run tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Simple Search", test_simple_search),
        ("Hybrid Search", test_hybrid_search),
        ("Statistics", test_statistics),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Test: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"Details: Check server logs for more information")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
