#!/usr/bin/env python3
"""
Quick test for individual analytics endpoints to debug specific issues.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_single_endpoint(method: str, endpoint: str, data: dict = None, params: dict = None) -> None:
    """Test a single endpoint and print detailed results."""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"🧪 Testing: {method} {endpoint}")
    print(f"🔗 URL: {url}")
    if params:
        print(f"📋 Params: {params}")
    if data:
        print(f"📄 Data: {json.dumps(data, indent=2)}")
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return
        
        execution_time = (time.time() - start_time) * 1000
        
        print(f"⏱️ Execution time: {execution_time:.0f}ms")
        print(f"🏷️ Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"📊 Response JSON:")
            print(json.dumps(response_json, indent=2))
        except ValueError:
            print(f"📄 Raw response:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Test analytics endpoints that are failing
    print("🚀 TESTING INDIVIDUAL ANALYTICS ENDPOINTS")
    print("=" * 50)
    
    endpoints_to_test = [
        ("GET", "/api/v1/average/Grand Hotel"),
        ("GET", "/api/v1/average/hotel-123/languages"),
        ("GET", "/api/v1/average/Grand Hotel/sources"),
        ("GET", "/api/v1/average/Grand Hotel/accommodations"),
        ("GET", "/api/v1/average/Grand Hotel/aspects"),
        ("GET", "/api/v1/reviews", {"limit": 5}),
        ("GET", "/api/v1/statistics"),
        ("POST", "/api/v1/semantic/filter", {
            "filters": {
                "hotel_group": "Marriott",
                "aspect_score": {"cleanliness": ">= 8"}
            }
        })
    ]
    
    for i, (method, endpoint, *args) in enumerate(endpoints_to_test, 1):
        print(f"\n{i}. " + "="*40)
        
        if len(args) > 0:
            if method == "GET":
                test_single_endpoint(method, endpoint, params=args[0])
            else:
                test_single_endpoint(method, endpoint, data=args[0])
        else:
            test_single_endpoint(method, endpoint)
        
        print()
