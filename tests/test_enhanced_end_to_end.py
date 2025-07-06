#!/usr/bin/env python3
"""
Enhanced End-to-End Test with Direct Execution

This enhanced test script includes testing the direct Gremlin execution endpoint
for a more comprehensive end-to-end validation.
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EnhancedTestResult:
    """Enhanced test result with direct execution."""
    query_name: str
    natural_language: str
    gremlin_query: Optional[str]
    gremlin_generated: bool
    gremlin_executed: bool
    direct_results_count: int
    filter_results_count: int
    ask_answer: Optional[str]
    execution_time_ms: float
    errors: List[str]
    success: bool


class EnhancedGraphRAGTester:
    """Enhanced tester with direct Gremlin execution capabilities."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[EnhancedTestResult] = []
        
        # Quick test queries for the enhanced test
        self.test_queries = [
            {
                "name": "hotel_count_test",
                "query": "Count all hotels",
                "language": "en",
                "expected_gremlin": "g.V().hasLabel('Hotel').count()"
            },
            {
                "name": "vip_guest_search",
                "query": "Find VIP guests", 
                "language": "en",
                "expected_gremlin": "g.V().hasLabel('Guest').has('type', 'VIP')"
            },
            {
                "name": "recent_reviews_turkish",
                "query": "Son yorumları göster",
                "language": "tr", 
                "expected_gremlin": "g.V().hasLabel('Review')"
            },
            {
                "name": "hotel_cleanliness_issues",
                "query": "Show hotels with cleanliness complaints",
                "language": "en",
                "expected_gremlin": "g.V().hasLabel('Hotel')"
            }
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_direct_gremlin_execution(self, gremlin_query: str) -> Tuple[bool, int, List[str]]:
        """Test the direct Gremlin execution endpoint."""
        try:
            payload = {"query": gremlin_query}
            
            async with self.session.post(
                f"{self.base_url}/api/v1/semantic/execute",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    count = len(results) if isinstance(results, list) else 1
                    return True, count, []
                else:
                    error_text = await response.text()
                    return False, 0, [f"Direct execution failed: HTTP {response.status}: {error_text}"]
                    
        except Exception as e:
            return False, 0, [f"Exception in direct execution: {str(e)}"]
    
    async def run_enhanced_test(self, test_query: Dict[str, Any]) -> EnhancedTestResult:
        """Run an enhanced end-to-end test."""
        start_time = time.time()
        errors = []
        
        print(f"\n🧪 Testing: {test_query['name']}")
        print(f"   📝 Query: '{test_query['query']}' ({test_query['language']})")
        
        # Step 1: Generate Gremlin query
        gremlin_query = None
        gremlin_generated = False
        
        try:
            payload = {"prompt": test_query['query'], "include_explanation": True}
            async with self.session.post(f"{self.base_url}/api/v1/semantic/gremlin", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    gremlin_query = data.get("gremlin_query", "")
                    gremlin_generated = bool(gremlin_query and gremlin_query.startswith("g."))
                    print(f"   ✅ Generated: {gremlin_query}")
                else:
                    errors.append(f"Gremlin generation failed: {response.status}")
                    print(f"   ❌ Gremlin generation failed")
        except Exception as e:
            errors.append(f"Gremlin generation error: {str(e)}")
            print(f"   ❌ Gremlin generation crashed: {e}")
        
        # Step 2: Execute Gremlin query directly (if generated)
        direct_success = False
        direct_count = 0
        
        if gremlin_query and gremlin_generated:
            print(f"   🔄 Executing Gremlin query directly...")
            direct_success, direct_count, direct_errors = await self.test_direct_gremlin_execution(gremlin_query)
            errors.extend(direct_errors)
            
            if direct_success:
                print(f"   ✅ Direct execution: {direct_count} results")
            else:
                print(f"   ❌ Direct execution failed")
        
        # Step 3: Test filter execution (simplified)
        filter_count = 0
        if test_query['language'] == 'en':
            try:
                filter_payload = {
                    "filters": {"sentiment": "positive"},
                    "max_results": 5,
                    "summarize_with_llm": False
                }
                async with self.session.post(f"{self.base_url}/api/v1/semantic/filter", json=filter_payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        filter_count = len(data.get("results", []))
                        print(f"   ✅ Filter test: {filter_count} results")
                    else:
                        print(f"   ⚠️  Filter test skipped (status {response.status})")
            except Exception as e:
                print(f"   ⚠️  Filter test error: {e}")
        
        # Step 4: Test ask pipeline
        ask_answer = None
        ask_success = False
        
        try:
            ask_payload = {
                "query": test_query['query'],
                "include_gremlin_query": True,
                "max_graph_results": 3
            }
            async with self.session.post(f"{self.base_url}/api/v1/ask", json=ask_payload) as response:
                if response.status == 200:
                    data = await response.json()
                    ask_answer = data.get("answer", "")
                    ask_success = bool(ask_answer and len(ask_answer.strip()) > 0)
                    if ask_success:
                        print(f"   ✅ Ask pipeline: Generated answer ({len(ask_answer)} chars)")
                    else:
                        print(f"   ❌ Ask pipeline: Empty answer")
                else:
                    errors.append(f"Ask pipeline failed: {response.status}")
                    print(f"   ❌ Ask pipeline failed")
        except Exception as e:
            errors.append(f"Ask pipeline error: {str(e)}")
            print(f"   ❌ Ask pipeline crashed: {e}")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Determine success
        success = gremlin_generated and (direct_success or ask_success)
        
        result = EnhancedTestResult(
            query_name=test_query['name'],
            natural_language=test_query['query'],
            gremlin_query=gremlin_query,
            gremlin_generated=gremlin_generated,
            gremlin_executed=direct_success,
            direct_results_count=direct_count,
            filter_results_count=filter_count,
            ask_answer=ask_answer,
            execution_time_ms=execution_time,
            errors=errors,
            success=success
        )
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} ({execution_time:.1f}ms)")
        
        return result
    
    async def run_enhanced_tests(self):
        """Run all enhanced tests."""
        print("🎯 ENHANCED END-TO-END GRAPH RAG TESTING")
        print("=" * 50)
        
        # Health check
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    print("✅ Server health check passed")
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return
        
        # Run tests
        for test_query in self.test_queries:
            try:
                result = await self.run_enhanced_test(test_query)
                self.results.append(result)
            except Exception as e:
                print(f"   💥 Test crashed: {e}")
                self.results.append(EnhancedTestResult(
                    query_name=test_query['name'],
                    natural_language=test_query['query'],
                    gremlin_query=None,
                    gremlin_generated=False,
                    gremlin_executed=False,
                    direct_results_count=0,
                    filter_results_count=0,
                    ask_answer=None,
                    execution_time_ms=0,
                    errors=[f"Test crashed: {str(e)}"],
                    success=False
                ))
    
    def print_enhanced_summary(self):
        """Print enhanced test summary."""
        print("\n" + "=" * 50)
        print("📊 ENHANCED TEST SUMMARY")
        print("=" * 50)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        
        print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Component breakdown
        gremlin_gen = sum(1 for r in self.results if r.gremlin_generated)
        gremlin_exec = sum(1 for r in self.results if r.gremlin_executed)
        ask_success = sum(1 for r in self.results if r.ask_answer)
        
        print(f"\n🔧 Component Success:")
        print(f"   🎯 Gremlin Generation: {gremlin_gen}/{total} ({gremlin_gen/total*100:.1f}%)")
        print(f"   ⚡ Direct Execution: {gremlin_exec}/{total} ({gremlin_exec/total*100:.1f}%)")
        print(f"   💬 Ask Pipeline: {ask_success}/{total} ({ask_success/total*100:.1f}%)")
        
        # Results preview
        print(f"\n📋 Sample Results:")
        for result in self.results[:3]:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.query_name}: '{result.natural_language}'")
            if result.gremlin_query:
                print(f"      🎯 Gremlin: {result.gremlin_query[:80]}...")
            if result.direct_results_count > 0:
                print(f"      📊 Direct results: {result.direct_results_count}")
            if result.ask_answer:
                answer_preview = result.ask_answer[:60] + "..." if len(result.ask_answer) > 60 else result.ask_answer
                print(f"      💬 Answer: {answer_preview}")
        
        # Performance
        total_time = sum(r.execution_time_ms for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        print(f"\n⚡ Performance: {total_time:.1f}ms total, {avg_time:.1f}ms average")
        
        # Failed tests
        failed = [r for r in self.results if not r.success]
        if failed:
            print(f"\n❌ Failed Tests:")
            for result in failed:
                print(f"   • {result.query_name}: {'; '.join(result.errors[:2])}")


async def main():
    """Main enhanced test function."""
    print("🚀 Starting Enhanced End-to-End Graph RAG Testing...")
    
    try:
        async with EnhancedGraphRAGTester() as tester:
            await tester.run_enhanced_tests()
            tester.print_enhanced_summary()
            
            # Save results
            results_data = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(tester.results),
                "passed_tests": sum(1 for r in tester.results if r.success),
                "results": [
                    {
                        "name": r.query_name,
                        "query": r.natural_language,
                        "gremlin_generated": r.gremlin_generated,
                        "gremlin_executed": r.gremlin_executed,
                        "direct_results": r.direct_results_count,
                        "success": r.success,
                        "errors": r.errors
                    }
                    for r in tester.results
                ]
            }
            
            with open("enhanced_test_results.json", "w", encoding="utf-8") as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results saved to: enhanced_test_results.json")
            
            # Exit code
            failed_count = sum(1 for r in tester.results if not r.success)
            if failed_count > 0:
                print(f"\n⚠️  {failed_count} tests failed")
                sys.exit(1)
            else:
                print(f"\n🎉 All tests passed!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
