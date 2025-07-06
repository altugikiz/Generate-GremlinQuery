#!/usr/bin/env python3
"""Test Turkish queries with the test server"""

import requests
import json

def test_queries():
    base_url = "http://localhost:8001"
    
    test_cases = [
        {
            "query": "Temizlik puanı düşük olan otelleri göster",
            "description": "Turkish: Show hotels with low cleanliness ratings",
            "expected_language": "Turkish"
        },
        {
            "query": "Show me hotels with excellent service",
            "description": "English: Show excellent service hotels",
            "expected_language": "English"
        },
        {
            "query": "En iyi otel önerilerini listele",
            "description": "Turkish: List best hotel recommendations",
            "expected_language": "Turkish"
        }
    ]
    
    print("🧪 Testing Turkish Query Support")
    print("=" * 50)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"Query: {test_case['query']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/ask",
                json={"query": test_case["query"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ Status: Success")
                print(f"Generated Gremlin: {result.get('gremlin_query', 'None')}")
                print(f"Answer: {result.get('answer', 'None')[:100]}...")
                print(f"Execution time: {result.get('execution_time_ms', 'N/A')} ms")
                
                results.append({
                    "test": test_case["description"],
                    "query": test_case["query"],
                    "success": True,
                    "gremlin_generated": bool(result.get('gremlin_query')),
                    "response_time": result.get('execution_time_ms', 0)
                })
            else:
                print(f"❌ Status: Failed ({response.status_code})")
                print(f"Error: {response.text}")
                results.append({
                    "test": test_case["description"],
                    "query": test_case["query"],
                    "success": False,
                    "error": response.text
                })
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                "test": test_case["description"],
                "query": test_case["query"],
                "success": False,
                "error": str(e)
            })
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    print(f"Tests passed: {successful_tests}/{total_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Turkish query support is working.")
    else:
        print("⚠️ Some tests failed.")
    
    return results

if __name__ == "__main__":
    results = test_queries()
