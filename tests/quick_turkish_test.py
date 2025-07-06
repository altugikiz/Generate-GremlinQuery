#!/usr/bin/env python3
"""Quick test of Turkish query processing"""

import requests
import json

def test_turkish_query():
    url = "http://localhost:8000/api/v1/ask"
    
    # Turkish query
    payload = {
        "query": "Temizlik puanı düşük olan otelleri göster"
    }
    
    try:
        print("🧪 Testing Turkish query processing...")
        print(f"Query: {payload['query']}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Response received:")
            print(f"Query: {result.get('query', 'N/A')}")
            print(f"Generated Gremlin: {result.get('gremlin_query', 'N/A')}")
            print(f"Answer length: {len(result.get('answer', ''))} characters")
            print(f"Execution time: {result.get('execution_time_ms', 'N/A')} ms")
            print(f"Development mode: {result.get('development_mode', 'N/A')}")
            
            if result.get('gremlin_query'):
                print(f"\n🎯 Success: Turkish query converted to Gremlin!")
                return True
            else:
                print(f"\n❌ No Gremlin query generated")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_turkish_query()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
