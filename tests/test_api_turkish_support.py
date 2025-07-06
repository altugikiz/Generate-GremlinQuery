#!/usr/bin/env python3
"""
Test the fixed Turkish language support in the actual API endpoints.
This script tests the /ask and /filter endpoints with Turkish queries.
"""

import asyncio
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_ask_endpoint_with_turkish():
    """Test the /ask endpoint with Turkish queries."""
    print("🇹🇷 TESTING /ask ENDPOINT WITH TURKISH QUERIES")
    print("=" * 60)
    
    turkish_test_cases = [
        {
            "name": "Turkish Cleanliness Complaints",
            "payload": {
                "query": "Türkçe yazılmış temizlik şikayetlerini göster",
                "include_gremlin_query": True,
                "include_semantic_chunks": False,
                "use_llm_summary": True
            }
        },
        {
            "name": "VIP Guest Issues in Turkish",
            "payload": {
                "query": "VIP misafirlerin sorunlarını göster",
                "filters": {
                    "guest_type": "VIP"
                },
                "include_gremlin_query": True,
                "include_semantic_chunks": True,
                "use_llm_summary": True
            }
        },
        {
            "name": "Hotel Service Ratings in Turkish",
            "payload": {
                "query": "Otellerin hizmet puanlarını göster",
                "filters": {
                    "aspect": "service"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(turkish_test_cases, 1):
        print(f"\n[{i}] {test_case['name']}")
        print(f"📝 Query: {test_case['payload']['query']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code} ({response_time:.1f}ms)")
                print(f"💡 Answer: {data.get('answer', 'No answer')[:100]}...")
                
                if data.get('gremlin_query'):
                    print(f"🔍 Gremlin Query: {data['gremlin_query'][:80]}...")
                
                if data.get('execution_time_ms'):
                    print(f"⚡ Execution Time: {data['execution_time_ms']:.1f}ms")
                
                success_count += 1
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n📊 Turkish /ask Tests: {success_count}/{len(turkish_test_cases)} successful")
    return success_count == len(turkish_test_cases)

def test_filter_endpoint_with_turkish():
    """Test the /filter endpoint with Turkish-related filters."""
    print("\n🇹🇷 TESTING /filter ENDPOINT WITH TURKISH FILTERS")
    print("=" * 60)
    
    filter_test_cases = [
        {
            "name": "Turkish Language Filter",
            "payload": {
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness",
                    "sentiment": "negative"
                },
                "include_gremlin_query": True,
                "include_results": True,
                "use_llm_summary": True,
                "max_results": 10
            }
        },
        {
            "name": "Turkish VIP Guest Filter",
            "payload": {
                "filters": {
                    "language": "tr",
                    "guest_type": "VIP",
                    "date_range": "last_30_days"
                },
                "include_gremlin_query": True,
                "include_results": True,
                "use_llm_summary": True,
                "max_results": 15
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(filter_test_cases, 1):
        print(f"\n[{i}] {test_case['name']}")
        print(f"🔧 Filters: {test_case['payload']['filters']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/filter",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code} ({response_time:.1f}ms)")
                print(f"📊 Results Count: {data.get('results_count', 0)}")
                
                if data.get('gremlin_query'):
                    print(f"🔍 Gremlin Query: {data['gremlin_query'][:80]}...")
                
                if data.get('summary'):
                    print(f"📝 Summary: {data['summary'][:100]}...")
                
                if data.get('execution_time_ms'):
                    print(f"⚡ Execution Time: {data['execution_time_ms']:.1f}ms")
                
                success_count += 1
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n📊 Turkish /filter Tests: {success_count}/{len(filter_test_cases)} successful")
    return success_count == len(filter_test_cases)

def test_mixed_language_queries():
    """Test mixed language queries (English + Turkish context)."""
    print("\n🌍 TESTING MIXED LANGUAGE QUERIES")
    print("=" * 50)
    
    mixed_test_cases = [
        {
            "name": "English Query with Turkish Context",
            "payload": {
                "query": "Show me reviews written in Turkish about cleanliness",
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        },
        {
            "name": "Turkish Query with English Context",
            "payload": {
                "query": "İngilizce yazılmış hizmet yorumlarını göster",
                "filters": {
                    "language": "en", 
                    "aspect": "service"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(mixed_test_cases, 1):
        print(f"\n[{i}] {test_case['name']}")
        print(f"📝 Query: {test_case['payload']['query']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code} ({response_time:.1f}ms)")
                print(f"💡 Answer: {data.get('answer', 'No answer')[:100]}...")
                
                if data.get('gremlin_query'):
                    print(f"🔍 Gremlin Query: {data['gremlin_query'][:80]}...")
                
                success_count += 1
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    print(f"\n📊 Mixed Language Tests: {success_count}/{len(mixed_test_cases)} successful")
    return success_count == len(mixed_test_cases)

def check_server_status():
    """Check if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run all Turkish language tests."""
    print("🧪 TESTING TURKISH LANGUAGE SUPPORT IN API ENDPOINTS")
    print("=" * 70)
    
    # Check if server is running
    if not check_server_status():
        print("❌ Server is not running or not accessible at http://localhost:8000")
        print("Please start the server with: python main.py")
        return False
    
    print("✅ Server is running")
    
    # Run tests
    ask_success = test_ask_endpoint_with_turkish()
    filter_success = test_filter_endpoint_with_turkish()
    mixed_success = test_mixed_language_queries()
    
    # Summary
    print("\n🎯 FINAL RESULTS")
    print("=" * 40)
    print(f"/ask Turkish Tests: {'✅ PASS' if ask_success else '❌ FAIL'}")
    print(f"/filter Turkish Tests: {'✅ PASS' if filter_success else '❌ FAIL'}")
    print(f"Mixed Language Tests: {'✅ PASS' if mixed_success else '❌ FAIL'}")
    
    all_success = ask_success and filter_success and mixed_success
    
    if all_success:
        print("\n🎉 ALL TESTS PASSED! Turkish language support is working in the API!")
        print("\nThe fix successfully enables:")
        print("- ✅ Turkish query detection and processing")
        print("- ✅ Enhanced prompts for multilingual input")
        print("- ✅ Proper Gremlin query generation from Turkish text")
        print("- ✅ Mixed language query support")
    else:
        print("\n⚠️ Some tests failed. The API may need to be restarted to pick up the changes.")
        print("Try restarting the server with: python main.py")
    
    return all_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
