#!/usr/bin/env python3
"""
Simple test script to verify Turkish language support via API.
"""

import requests
import json
import time

def test_turkish_api():
    """Test Turkish queries via API endpoints."""
    base_url = "http://localhost:8000"
    
    # Wait for server to be ready
    print("🔗 Checking server status...")
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is ready!")
                break
        except:
            print(f"⏳ Waiting for server... ({i+1}/5)")
            time.sleep(2)
    else:
        print("❌ Server not responding")
        return False
    
    # Test Turkish query
    print("\n🇹🇷 Testing Turkish query...")
    turkish_payload = {
        "query": "Türkçe yazılmış temizlik şikayetlerini göster",
        "include_gremlin_query": True,
        "include_semantic_chunks": False,
        "use_llm_summary": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json=turkish_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Turkish query successful!")
            
            if 'gremlin_query' in data and data['gremlin_query']:
                print(f"🔍 Generated Gremlin: {data['gremlin_query']}")
                
            if 'answer' in data and data['answer']:
                print(f"💬 Answer: {data['answer'][:200]}...")
                
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_turkish_api()
    print(f"\n{'🎉 SUCCESS!' if success else '❌ FAILED'}")
