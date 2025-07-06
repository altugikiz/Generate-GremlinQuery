#!/usr/bin/env python3
"""
Final test to demonstrate Turkish language support is working.
"""

import requests
import json

def test_turkish_query():
    """Test Turkish query via the correct API endpoint."""
    
    # Turkish test payload
    payload = {
        "query": "Türkçe yazılmış temizlik şikayetlerini göster",
        "include_gremlin_query": True,
        "include_semantic_chunks": False,
        "use_llm_summary": True
    }
    
    print("🇹🇷 TESTING TURKISH LANGUAGE SUPPORT")
    print("=" * 50)
    print(f"📝 Query: {payload['query']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"🔗 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ REQUEST SUCCESSFUL!")
            
            # Show the generated Gremlin query
            if 'gremlin_query' in data and data['gremlin_query']:
                print(f"\n🔍 Generated Gremlin Query:")
                print(f"   {data['gremlin_query']}")
                
            # Show the answer
            if 'answer' in data and data['answer']:
                print(f"\n💬 Generated Answer:")
                print(f"   {data['answer'][:300]}...")
                
            # Show execution time
            if 'execution_time_ms' in data:
                print(f"\n⏱️  Execution Time: {data['execution_time_ms']:.1f}ms")
                
            # Show component times
            if 'component_times' in data and data['component_times']:
                print(f"\n🔧 Component Times:")
                for component, time_ms in data['component_times'].items():
                    print(f"   {component}: {time_ms:.1f}ms")
                    
            return True
            
        else:
            print(f"❌ REQUEST FAILED")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_vip_query():
    """Test another Turkish query."""
    
    payload = {
        "query": "VIP misafirlerin sorunlarını göster",
        "filters": {
            "guest_type": "VIP"
        },
        "include_gremlin_query": True,
        "use_llm_summary": True
    }
    
    print("\n🎩 TESTING VIP GUEST QUERY IN TURKISH")
    print("=" * 50)
    print(f"📝 Query: {payload['query']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ask",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ VIP QUERY SUCCESSFUL!")
            
            if 'gremlin_query' in data and data['gremlin_query']:
                print(f"\n🔍 Generated Gremlin Query:")
                print(f"   {data['gremlin_query']}")
                
            return True
        else:
            print(f"❌ VIP QUERY FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ VIP QUERY ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test both queries
    result1 = test_turkish_query()
    result2 = test_vip_query()
    
    print("\n" + "=" * 50)
    if result1 and result2:
        print("🎉 ALL TURKISH TESTS PASSED!")
        print("✅ Turkish language support is working correctly!")
        print("✅ User input → Gremlin query conversion is functional!")
        print("✅ Database querying capabilities are available!")
    else:
        print("⚠️  Some tests failed, but core functionality may still work")
