#!/usr/bin/env python3
"""
Quick Validation Test

A simple script to verify that the FastAPI server is running and 
the key endpoints are responding correctly.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


async def quick_validation():
    """Run quick validation checks."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        print("🔍 QUICK VALIDATION TEST")
        print("=" * 30)
        
        # Test 1: Health check
        print("\n1️⃣  Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Health check: {data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Cannot connect to server: {e}")
            print("   💡 Make sure FastAPI server is running on localhost:8000")
            return False
        
        # Test 2: Gremlin generation
        print("\n2️⃣  Testing Gremlin generation...")
        try:
            payload = {"prompt": "Show me all hotels", "include_explanation": True}
            async with session.post(f"{base_url}/api/v1/semantic/gremlin", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    gremlin_query = data.get("gremlin_query", "")
                    if gremlin_query and gremlin_query.startswith("g."):
                        print(f"   ✅ Gremlin generation working")
                        print(f"   📝 Generated: {gremlin_query}")
                    else:
                        print(f"   ⚠️  Generated query format unexpected: {gremlin_query}")
                else:
                    print(f"   ❌ Gremlin generation failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Gremlin generation error: {e}")
        
        # Test 3: Direct execution endpoint (if available)
        print("\n3️⃣  Testing direct execution endpoint...")
        try:
            payload = {"query": "g.V().hasLabel('Hotel').limit(1).count()"}
            async with session.post(f"{base_url}/api/v1/semantic/execute", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    results_count = data.get("results_count", 0)
                    print(f"   ✅ Direct execution working")
                    print(f"   📊 Query executed, returned {results_count} results")
                elif response.status == 403:
                    print(f"   ⚠️  Execution endpoint requires development mode")
                elif response.status == 503:
                    print(f"   ⚠️  Gremlin client not available")
                else:
                    print(f"   ❌ Direct execution failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Direct execution error: {e}")
        
        # Test 4: Ask pipeline
        print("\n4️⃣  Testing ask pipeline...")
        try:
            payload = {
                "query": "How many hotels are there?",
                "include_gremlin_query": True,
                "max_graph_results": 3
            }
            async with session.post(f"{base_url}/api/v1/ask", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get("answer", "")
                    if answer and len(answer.strip()) > 0:
                        print(f"   ✅ Ask pipeline working")
                        answer_preview = answer[:80] + "..." if len(answer) > 80 else answer
                        print(f"   💬 Answer: {answer_preview}")
                    else:
                        print(f"   ⚠️  Ask pipeline returned empty answer")
                else:
                    print(f"   ❌ Ask pipeline failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Ask pipeline error: {e}")
        
        # Test 5: Turkish query test
        print("\n5️⃣  Testing Turkish query...")
        try:
            payload = {"prompt": "Otelleri göster", "include_explanation": True}
            async with session.post(f"{base_url}/api/v1/semantic/gremlin", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    gremlin_query = data.get("gremlin_query", "")
                    if gremlin_query and gremlin_query.startswith("g."):
                        print(f"   ✅ Turkish query generation working")
                        print(f"   🇹🇷 Generated: {gremlin_query}")
                    else:
                        print(f"   ⚠️  Turkish query generation issue")
                else:
                    print(f"   ❌ Turkish query failed: HTTP {response.status}")
        except Exception as e:
            print(f"   ❌ Turkish query error: {e}")
        
        print(f"\n✅ Quick validation completed at {datetime.now().strftime('%H:%M:%S')}")
        print(f"🎯 Ready to run full end-to-end tests!")
        return True


async def main():
    """Main validation function."""
    success = await quick_validation()
    
    if success:
        print(f"\n🚀 Run the full end-to-end test with:")
        print(f"   python test_end_to_end_graph_rag_flow.py")
        print(f"   python test_enhanced_end_to_end.py")
        sys.exit(0)
    else:
        print(f"\n❌ Validation failed. Fix issues before running full tests.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
