#!/usr/bin/env python3
"""
Test script for the Enhanced Graph RAG Pipeline.

This script demonstrates all the key features:
1. Natural language to Gremlin query translation
2. Hybrid search (graph + semantic)
3. LLM-powered response generation
4. Development mode fallbacks

Usage:
    python test_graph_rag.py
"""

import asyncio
import json
import httpx
import time
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"


class GraphRAGTester:
    """Test client for the Graph RAG system."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health(self) -> bool:
        """Test if the system is running."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                health_data = response.json()
                print("🟢 System Status:")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Development Mode: {health_data.get('development_mode', False)}")
                
                # Check component status
                components = health_data.get('components', {})
                for name, status in components.items():
                    emoji = "✅" if status == "healthy" else "❌"
                    print(f"   {emoji} {name}: {status}")
                
                return True
            return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_ask_endpoint(self, queries: List[str]) -> None:
        """Test the /ask endpoint with natural language queries."""
        print("\n🤖 Testing Natural Language Queries:")
        print("=" * 50)
        
        for i, query in enumerate(queries, 1):
            try:
                print(f"\n{i}. Query: '{query}'")
                print("-" * 40)
                
                start_time = time.time()
                
                # Make request to /ask endpoint
                response = await self.client.post(
                    f"{self.base_url}/api/v1/ask",
                    json={
                        "query": query,
                        "include_context": True,
                        "include_query_translation": True
                    }
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response ({execution_time:.2f}ms):")
                    print(f"   Answer: {data.get('answer', 'No answer')}")
                    
                    if data.get('gremlin_query'):
                        print(f"   Generated Gremlin: {data['gremlin_query']}")
                    
                    if data.get('development_mode'):
                        print("   🔧 Running in development mode")
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
            
            await asyncio.sleep(1)  # Rate limiting
    
    async def test_query_suggestions(self, base_query: str) -> None:
        """Test query suggestion feature."""
        print(f"\n💡 Testing Query Suggestions for: '{base_query}'")
        print("=" * 50)
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/ask/suggestions/{base_query}"
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get('suggestions', [])
                print(f"✅ Found {len(suggestions)} suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"   {i}. {suggestion}")
            else:
                print(f"❌ Suggestions failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Suggestions error: {e}")
    
    async def test_gremlin_explanation(self, gremlin_query: str) -> None:
        """Test Gremlin query explanation."""
        print(f"\n📖 Testing Gremlin Explanation:")
        print("=" * 50)
        print(f"Query: {gremlin_query}")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/ask/explain/{gremlin_query}"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Explanation:")
                print(f"   {data.get('explanation', 'No explanation available')}")
            else:
                print(f"❌ Explanation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Explanation error: {e}")
    
    async def test_examples(self) -> None:
        """Get and display example queries."""
        print("\n📚 Available Examples:")
        print("=" * 50)
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/ask/examples")
            
            if response.status_code == 200:
                data = response.json()
                examples = data.get('examples', {})
                
                for category, queries in examples.items():
                    print(f"\n🏷️  {category.replace('_', ' ').title()}:")
                    for query in queries:
                        print(f"   • {query}")
                
                print(f"\n💡 Tips:")
                for tip in data.get('tips', []):
                    print(f"   • {tip}")
                    
            else:
                print(f"❌ Examples request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Examples error: {e}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Run all tests."""
    print("🚀 Graph RAG Pipeline Test Suite")
    print("=" * 60)
    
    tester = GraphRAGTester()
    
    try:
        # Test system health
        healthy = await tester.test_health()
        if not healthy:
            print("❌ System appears to be down. Please start the server first.")
            return
        
        # Get available examples
        await tester.test_examples()
        
        # Test natural language queries
        test_queries = [
            "What are the best hotels in New York?",
            "Find hotels with excellent cleanliness ratings",
            "Show me reviews that mention service complaints",
            "Which hotel chains have the highest rated amenities?",
            "Find luxury hotels with poor location scores",
        ]
        
        await tester.test_ask_endpoint(test_queries)
        
        # Test query suggestions
        await tester.test_query_suggestions("hotels in Paris")
        
        # Test Gremlin explanation
        sample_gremlin = "g.V().hasLabel('Hotel').has('city', 'New York').limit(5)"
        await tester.test_gremlin_explanation(sample_gremlin)
        
        print("\n✅ Test suite completed!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
