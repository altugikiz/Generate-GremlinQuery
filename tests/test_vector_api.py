#!/usr/bin/env python3
"""
Test Vector Search API Endpoint

This script tests the vector search endpoint to see if it's working correctly.
"""

import asyncio
import json
import aiohttp
import sys
import time
from typing import Dict, Any

# Test data
TEST_QUERIES = [
    {
        "query": "otel temizliği hakkında yorum",
        "description": "Turkish query about hotel cleanliness",
        "top_k": 5,
        "min_score": 0.0
    },
    {
        "query": "hotel cleanliness reviews",
        "description": "English query about hotel cleanliness", 
        "top_k": 5,
        "min_score": 0.0
    },
    {
        "query": "personel hizmeti nasıl",
        "description": "Turkish query about staff service",
        "top_k": 3,
        "min_score": 0.0
    }
]

async def test_vector_search_endpoint(base_url: str = "http://localhost:8000"):
    """Test the vector search endpoint."""
    
    print("🧪 Testing Vector Search API Endpoint")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check if the service is running
        try:
            async with session.get(f"{base_url}/api/v1/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Service is running: {health_data}")
                else:
                    print(f"❌ Service health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to service: {e}")
            print("💡 Make sure the FastAPI server is running with: python main.py")
            return False
        
        # Test 2: Test vector search endpoint
        for i, test_query in enumerate(TEST_QUERIES, 1):
            print(f"\n🔍 Test {i}: {test_query['description']}")
            print(f"📝 Query: '{test_query['query']}'")
            
            payload = {
                "query": test_query["query"],
                "top_k": test_query["top_k"],
                "min_score": test_query["min_score"],
                "include_embeddings": False
            }
            
            try:
                start_time = time.time()
                async with session.post(
                    f"{base_url}/api/v1/semantic/vector",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        result_data = await response.json()
                        
                        print(f"✅ Request successful ({execution_time:.2f}ms)")
                        print(f"📊 Results: {len(result_data.get('results', []))} documents found")
                        print(f"📊 Total documents in index: {result_data.get('total_documents', 'unknown')}")
                        print(f"⏱️  Execution time: {result_data.get('execution_time_ms', 'unknown'):.2f}ms")
                        
                        # Display top results
                        results = result_data.get('results', [])
                        if results:
                            print(f"🎯 Top {min(3, len(results))} results:")
                            for j, result in enumerate(results[:3], 1):
                                score = result.get('score', 0)
                                content = result.get('content', '')[:60] + "..." if len(result.get('content', '')) > 60 else result.get('content', '')
                                metadata = result.get('metadata', {})
                                aspect = metadata.get('aspect', 'unknown')
                                print(f"   {j}. Score: {score:.4f} | Aspect: {aspect} | Content: {content}")
                        else:
                            print("⚠️  No results returned")
                            
                    else:
                        error_text = await response.text()
                        print(f"❌ Request failed: {response.status}")
                        print(f"❌ Error: {error_text}")
                        
            except Exception as e:
                print(f"❌ Request error: {e}")
        
        # Test 3: Test with different min_score thresholds
        print(f"\n🎯 Testing score thresholds with Turkish query...")
        test_query = "otel temizliği hakkında yorum"
        
        for min_score in [0.0, 0.3, 0.5, 0.7]:
            payload = {
                "query": test_query,
                "top_k": 5,
                "min_score": min_score,
                "include_embeddings": False
            }
            
            try:
                async with session.post(
                    f"{base_url}/api/v1/semantic/vector",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        result_data = await response.json()
                        results_count = len(result_data.get('results', []))
                        print(f"📊 min_score={min_score}: {results_count} results")
                        
                        if results_count > 0:
                            top_score = result_data['results'][0].get('score', 0)
                            print(f"   Top result score: {top_score:.4f}")
                    else:
                        print(f"❌ min_score={min_score}: Request failed ({response.status})")
                        
            except Exception as e:
                print(f"❌ min_score={min_score}: Error {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Vector search endpoint testing completed!")
    return True

async def main():
    """Main test function."""
    success = await test_vector_search_endpoint()
    return success

if __name__ == "__main__":
    asyncio.run(main())
