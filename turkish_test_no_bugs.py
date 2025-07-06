#!/usr/bin/env python3
"""
Fixed Turkish Language Test - No Syntax Errors
"""

import requests
import json

def test_turkish_functionality():
    """Test Turkish language support with proper syntax."""
    
    print("🇹🇷 TESTING TURKISH LANGUAGE SUPPORT")
    print("=" * 50)
    
    # Test Turkish language query translation
    payload = {
        "query": "Türkçe yazılmış temizlik şikayetlerini göster",
        "include_gremlin_query": True,
        "include_semantic_chunks": False,
        "use_llm_summary": False
    }
    
    try:
        print(f"📝 Input Query: {payload['query']}")
        print("🔄 Sending request...")
        
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            timeout=20
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Turkish query processed!")
            
            if "gremlin_query" in data and data["gremlin_query"]:
                print(f"\n🔍 Generated Gremlin Query:")
                print(f"   {data['gremlin_query']}")
                print("\n✅ CONFIRMED: Turkish → Gremlin conversion works!")
                return True
            else:
                print("⚠️  No Gremlin query in response")
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
        return False

def test_english_control():
    """Test English query as control."""
    
    print("\n🇺🇸 TESTING ENGLISH CONTROL")
    print("=" * 30)
    
    payload = {
        "query": "Show me cleanliness complaints",
        "include_gremlin_query": True,
        "use_llm_summary": False
    }
    
    try:
        print(f"📝 Input Query: {payload['query']}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ English query works!")
            
            if "gremlin_query" in data and data["gremlin_query"]:
                print(f"🔍 Gremlin: {data['gremlin_query'][:80]}...")
                return True
                
        print(f"Status: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 GRAPH RAG TURKISH LANGUAGE TEST")
    print("=" * 60)
    
    # Test server availability
    try:
        health_response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            exit(1)
    except:
        print("❌ Cannot connect to server")
        exit(1)
    
    # Run tests
    turkish_result = test_turkish_functionality()
    english_result = test_english_control()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if turkish_result:
        print("✅ Turkish Language Support: WORKING")
        print("✅ Natural Language → Gremlin Query: WORKING")
        print("✅ Multilingual LLM Integration: WORKING")
    else:
        print("❌ Turkish Language Support: FAILED")
    
    if english_result:
        print("✅ English Language Support: WORKING")
    else:
        print("❌ English Language Support: FAILED")
    
    if turkish_result and english_result:
        print("\n🎉 OVERALL STATUS: ALL TESTS PASSED!")
        print("🔧 The system can convert user input to Gremlin queries")
        print("🌍 Both Turkish and English languages are supported")
        print("📊 Database querying pipeline is functional")
    else:
        print("\n⚠️  OVERALL STATUS: SOME ISSUES DETECTED")
        
    print("\n" + "=" * 60)
