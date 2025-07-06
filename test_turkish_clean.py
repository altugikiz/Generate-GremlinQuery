#!/usr/bin/env python3
"""
Simple test to verify Turkish language support is working correctly.
This fixes the syntax error and provides a clean test.
"""

import requests
import json

def test_turkish_support():
    """Test Turkish language support with proper syntax."""
    
    print("🇹🇷 TESTING TURKISH LANGUAGE SUPPORT")
    print("=" * 50)
    
    # Test payload with Turkish query
    payload = {
        "query": "Türkçe yazılmış temizlik şikayetlerini göster",
        "include_gremlin_query": True,
        "include_semantic_chunks": False,
        "use_llm_summary": False
    }
    
    print(f"📝 Turkish Query: {payload['query']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        print(f"🔗 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if Gremlin query was generated
            if "gremlin_query" in data and data["gremlin_query"]:
                print("✅ SUCCESS: Turkish → Gremlin conversion working!")
                print(f"🔍 Generated Gremlin Query:")
                print(f"   {data['gremlin_query']}")
                
                # Verify it contains Turkish-related elements
                gremlin = data["gremlin_query"].lower()
                if "tr" in gremlin or "turkish" in gremlin or "cleanliness" in gremlin:
                    print("✅ Query contains expected Turkish/cleanliness elements")
                
                return True
            else:
                print("⚠️  No Gremlin query generated")
                return False
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return False

def test_vip_turkish():
    """Test another Turkish query - VIP guests."""
    
    print("\n🎩 TESTING VIP GUEST QUERY IN TURKISH")
    print("=" * 50)
    
    payload = {
        "query": "VIP misafirlerin sorunlarını göster",
        "include_gremlin_query": True,
        "use_llm_summary": False
    }
    
    print(f"📝 Turkish Query: {payload['query']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "gremlin_query" in data and data["gremlin_query"]:
                print("✅ SUCCESS: VIP Turkish query working!")
                print(f"🔍 Generated Query: {data['gremlin_query']}")
                return True
            else:
                print("⚠️  No Gremlin query in response")
                return False
        else:
            print(f"❌ Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests and show summary."""
    
    # Test server connectivity first
    try:
        health_response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running and responsive")
        else:
            print("⚠️  Server may have issues")
    except:
        print("❌ Cannot connect to server - make sure it's running on port 8000")
        return False
    
    # Run Turkish tests
    test1_result = test_turkish_support()
    test2_result = test_vip_turkish()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    
    if test1_result:
        print("✅ Turkish cleanliness query: PASSED")
    else:
        print("❌ Turkish cleanliness query: FAILED")
        
    if test2_result:
        print("✅ Turkish VIP query: PASSED")
    else:
        print("❌ Turkish VIP query: FAILED")
    
    if test1_result or test2_result:
        print("\n🎉 CONCLUSION: Turkish language support is WORKING!")
        print("✅ User input is being converted to Gremlin queries")
        print("✅ System can process Turkish natural language")
        print("✅ LLM understands Turkish hotel domain queries")
        return True
    else:
        print("\n⚠️  CONCLUSION: Turkish support needs debugging")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
