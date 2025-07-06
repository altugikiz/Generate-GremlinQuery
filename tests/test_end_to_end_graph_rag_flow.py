#!/usr/bin/env python3
"""
End-to-End Graph RAG Flow Test

Comprehensive test script that validates the complete LLM-to-Gremlin-to-Graph workflow:
1. Send natural language queries to `/semantic/gremlin`
2. Parse and validate the generated Gremlin queries
3. Execute queries via `/semantic/filter` endpoint (structured execution)
4. Test the complete `/ask` pipeline (natural language to answer)
5. Validate results for both English and Turkish queries
6. Test error handling and edge cases

This script provides full end-to-end validation of the Graph RAG system.
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class TestQuery:
    """Test query configuration."""
    name: str
    query: str
    language: str
    expected_type: str  # "hotels", "reviews", "guests", "issues", etc.
    include_filters: Optional[Dict[str, Any]] = None
    should_succeed: bool = True


@dataclass
class TestResult:
    """Test result tracking."""
    query_name: str
    natural_language: str
    gremlin_generated: bool
    gremlin_query: Optional[str]
    gremlin_valid: bool
    filter_executed: bool
    filter_results_count: int
    ask_pipeline_success: bool
    ask_answer: Optional[str]
    execution_time_ms: float
    errors: List[str]
    success: bool


class EndToEndGraphRAGTester:
    """
    Comprehensive end-to-end tester for the Graph RAG system.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
        # Test queries covering different scenarios
        self.test_queries = [
            # English queries - Basic hotel searches
            TestQuery(
                name="hotels_basic_english",
                query="Show me all hotels",
                language="en",
                expected_type="hotels"
            ),
            TestQuery(
                name="vip_guests_english", 
                query="Find VIP guests",
                language="en",
                expected_type="guests"
            ),
            TestQuery(
                name="luxury_hotels_english",
                query="Find luxury hotels with high ratings",
                language="en",
                expected_type="hotels"
            ),
            TestQuery(
                name="staff_complaints_english",
                query="Show me guest complaints about staff service",
                language="en",
                expected_type="reviews",
                include_filters={"aspect": "staff", "sentiment": "negative"}
            ),
            TestQuery(
                name="cleanliness_issues_english",
                query="Find hotels with cleanliness complaints in the last month",
                language="en", 
                expected_type="reviews",
                include_filters={"aspect": "cleanliness", "sentiment": "negative", "date_range": "last_30_days"}
            ),
            
            # Turkish queries - Multilingual support
            TestQuery(
                name="hotels_basic_turkish",
                query="Tüm otelleri göster",
                language="tr",
                expected_type="hotels"
            ),
            TestQuery(
                name="cleaning_complaints_turkish",
                query="Temizlik şikayetlerini göster",
                language="tr",
                expected_type="reviews",
                include_filters={"aspect": "cleanliness", "sentiment": "negative"}
            ),
            TestQuery(
                name="location_reviews_turkish", 
                query="Konum hakkında Türkçe yorumları bul",
                language="tr",
                expected_type="reviews",
                include_filters={"aspect": "location", "language": "tr"}
            ),
            TestQuery(
                name="high_rating_hotels_turkish",
                query="Yüksek puanlı otelleri listele",
                language="tr",
                expected_type="hotels"
            ),
            
            # Complex analytical queries
            TestQuery(
                name="maintenance_issues_complex_english",
                query="Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
                language="en",
                expected_type="issues",
                include_filters={"guest_type": "VIP", "date_range": "last_14_days"}
            ),
            TestQuery(
                name="booking_source_analysis_english",
                query="Find hotels with recent guest complaints from Booking.com",
                language="en",
                expected_type="reviews",
                include_filters={"source": "booking", "sentiment": "negative", "date_range": "last_7_days"}
            ),
            
            # Edge cases and error scenarios
            TestQuery(
                name="empty_query",
                query="",
                language="en",
                expected_type="error",
                should_succeed=False
            ),
            TestQuery(
                name="very_long_query",
                query="This is a very long query that goes on and on and should test the limits of the system to see how it handles extremely verbose natural language input that might exceed normal parameters or cause processing issues" * 3,
                language="en", 
                expected_type="error",
                should_succeed=False
            ),
            TestQuery(
                name="nonsense_query",
                query="purple elephants flying backwards through quantum dimensions",
                language="en",
                expected_type="unclear",
                should_succeed=True  # Should generate something, even if unclear
            )
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def check_server_health(self) -> bool:
        """Check if the FastAPI server is running and healthy."""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Server health check passed: {health_data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ Server health check failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False
    
    async def test_gremlin_generation(self, test_query: TestQuery) -> Tuple[bool, Optional[str], List[str]]:
        """
        Test the /semantic/gremlin endpoint for natural language to Gremlin translation.
        
        Returns:
            Tuple of (success, gremlin_query, errors)
        """
        try:
            payload = {
                "prompt": test_query.query,
                "include_explanation": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/semantic/gremlin",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    gremlin_query = data.get("gremlin_query", "")
                    
                    # Validate the Gremlin query
                    if gremlin_query and gremlin_query.startswith("g."):
                        return True, gremlin_query, []
                    else:
                        return False, gremlin_query, [f"Invalid Gremlin query format: {gremlin_query}"]
                else:
                    error_text = await response.text()
                    return False, None, [f"HTTP {response.status}: {error_text}"]
                    
        except Exception as e:
            return False, None, [f"Exception in gremlin generation: {str(e)}"]
    
    async def test_filter_execution(self, test_query: TestQuery) -> Tuple[bool, int, List[str]]:
        """
        Test the /semantic/filter endpoint for structured query execution.
        
        Returns:
            Tuple of (success, results_count, errors)  
        """
        if not test_query.include_filters:
            # Skip filter test if no filters provided
            return True, 0, ["No filters provided - skipping filter execution test"]
        
        try:
            payload = {
                "filters": test_query.include_filters,
                "max_results": 10,
                "summarize_with_llm": False,
                "include_gremlin_query": True,
                "include_results": True
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/semantic/filter",
                json=payload  
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results_count = len(data.get("results", []))
                    return True, results_count, []
                else:
                    error_text = await response.text()
                    return False, 0, [f"Filter execution failed: HTTP {response.status}: {error_text}"]
                    
        except Exception as e:
            return False, 0, [f"Exception in filter execution: {str(e)}"]
    
    async def test_ask_pipeline(self, test_query: TestQuery) -> Tuple[bool, Optional[str], List[str]]:
        """
        Test the complete /ask pipeline for natural language question answering.
        
        Returns:
            Tuple of (success, answer, errors)
        """
        try:
            payload = {
                "query": test_query.query,
                "include_gremlin_query": True,
                "include_semantic_chunks": True,
                "max_graph_results": 5,
                "max_semantic_results": 3
            }
            
            # Add filters if provided
            if test_query.include_filters:
                payload["filters"] = test_query.include_filters
            
            async with self.session.post(
                f"{self.base_url}/api/v1/ask",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    answer = data.get("answer", "")
                    
                    if answer and len(answer.strip()) > 0:
                        return True, answer, []
                    else:
                        return False, answer, ["Empty or missing answer"]
                else:
                    error_text = await response.text()
                    return False, None, [f"Ask pipeline failed: HTTP {response.status}: {error_text}"]
                    
        except Exception as e:
            return False, None, [f"Exception in ask pipeline: {str(e)}"]
    
    async def run_single_test(self, test_query: TestQuery) -> TestResult:
        """Run a complete end-to-end test for a single query."""
        start_time = time.time()
        errors = []
        
        print(f"\n🧪 Testing: {test_query.name}")
        print(f"   📝 Query: '{test_query.query}' ({test_query.language})")
        
        # Step 1: Test Gremlin generation
        print("   🔄 Step 1: Generating Gremlin query...")
        gremlin_success, gremlin_query, gremlin_errors = await self.test_gremlin_generation(test_query)
        errors.extend(gremlin_errors)
        
        if gremlin_success and gremlin_query:
            print(f"   ✅ Gremlin generated: {gremlin_query[:100]}...")
        else:
            print(f"   ❌ Gremlin generation failed: {'; '.join(gremlin_errors)}")
        
        # Step 2: Test filter execution (if filters provided)
        print("   🔄 Step 2: Testing filter execution...")
        filter_success, filter_count, filter_errors = await self.test_filter_execution(test_query)
        errors.extend(filter_errors)
        
        if filter_success:
            print(f"   ✅ Filter execution: {filter_count} results")
        else:
            print(f"   ❌ Filter execution failed: {'; '.join(filter_errors)}")
        
        # Step 3: Test complete ask pipeline
        print("   🔄 Step 3: Testing complete ask pipeline...")
        ask_success, ask_answer, ask_errors = await self.test_ask_pipeline(test_query)
        errors.extend(ask_errors)
        
        if ask_success and ask_answer:
            print(f"   ✅ Ask pipeline: Generated answer ({len(ask_answer)} chars)")
            print(f"   💬 Answer preview: {ask_answer[:150]}...")
        else:
            print(f"   ❌ Ask pipeline failed: {'; '.join(ask_errors)}")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Determine overall success
        if test_query.should_succeed:
            success = gremlin_success and (filter_success or not test_query.include_filters) and ask_success
        else:
            # For queries that should fail, success means they failed gracefully
            success = not gremlin_success or not ask_success
        
        result = TestResult(
            query_name=test_query.name,
            natural_language=test_query.query,
            gremlin_generated=gremlin_success,
            gremlin_query=gremlin_query,
            gremlin_valid=gremlin_success and bool(gremlin_query and gremlin_query.startswith("g.")),
            filter_executed=filter_success,
            filter_results_count=filter_count,
            ask_pipeline_success=ask_success,
            ask_answer=ask_answer,
            execution_time_ms=execution_time,
            errors=errors,
            success=success
        )
        
        status_icon = "✅" if success else "❌"
        print(f"   {status_icon} Test result: {'PASS' if success else 'FAIL'} ({execution_time:.1f}ms)")
        
        return result
    
    async def run_all_tests(self) -> None:
        """Run all end-to-end tests."""
        print("🎯 END-TO-END GRAPH RAG FLOW TESTING")
        print("=" * 60)
        
        # Check server health first
        print("\n🔍 Checking server health...")
        if not await self.check_server_health():
            print("❌ Server health check failed. Please ensure the FastAPI server is running.")
            return
        
        # Run tests
        print(f"\n🧪 Running {len(self.test_queries)} end-to-end tests...")
        
        for test_query in self.test_queries:
            try:
                result = await self.run_single_test(test_query)
                self.results.append(result)
            except Exception as e:
                print(f"   💥 Test crashed: {e}")
                # Add a failed result for tracking
                self.results.append(TestResult(
                    query_name=test_query.name,
                    natural_language=test_query.query,
                    gremlin_generated=False,
                    gremlin_query=None,
                    gremlin_valid=False,
                    filter_executed=False,
                    filter_results_count=0,
                    ask_pipeline_success=False,
                    ask_answer=None,
                    execution_time_ms=0,
                    errors=[f"Test crashed: {str(e)}"],
                    success=False
                ))
    
    def print_summary_report(self) -> None:
        """Print a comprehensive summary report."""
        print("\n" + "=" * 60)
        print("📊 END-TO-END TEST SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 Overall Results:")
        print(f"   ✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"   ❌ Failed: {failed_tests}/{total_tests} ({failed_tests/total_tests*100:.1f}%)")
        
        # Component success rates
        gremlin_success = sum(1 for r in self.results if r.gremlin_generated)
        filter_success = sum(1 for r in self.results if r.filter_executed)
        ask_success = sum(1 for r in self.results if r.ask_pipeline_success)
        
        print(f"\n🔧 Component Success Rates:")
        print(f"   🎯 Gremlin Generation: {gremlin_success}/{total_tests} ({gremlin_success/total_tests*100:.1f}%)")
        print(f"   🔍 Filter Execution: {filter_success}/{total_tests} ({filter_success/total_tests*100:.1f}%)")
        print(f"   💬 Ask Pipeline: {ask_success}/{total_tests} ({ask_success/total_tests*100:.1f}%)")
        
        # Performance metrics
        total_time = sum(r.execution_time_ms for r in self.results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        print(f"\n⚡ Performance Metrics:")
        print(f"   📊 Total execution time: {total_time:.1f}ms")
        print(f"   📊 Average per test: {avg_time:.1f}ms")
        print(f"   📊 Fastest test: {min(r.execution_time_ms for r in self.results):.1f}ms")
        print(f"   📊 Slowest test: {max(r.execution_time_ms for r in self.results):.1f}ms")
        
        # Language breakdown
        english_tests = [r for r in self.results if "english" in r.query_name]
        turkish_tests = [r for r in self.results if "turkish" in r.query_name]
        
        if english_tests:
            english_passed = sum(1 for r in english_tests if r.success)
            print(f"\n🇺🇸 English Query Results: {english_passed}/{len(english_tests)} passed")
        
        if turkish_tests:
            turkish_passed = sum(1 for r in turkish_tests if r.success)
            print(f"🇹🇷 Turkish Query Results: {turkish_passed}/{len(turkish_tests)} passed")
        
        # Failed test details
        failed_results = [r for r in self.results if not r.success]
        if failed_results:
            print(f"\n❌ Failed Test Details:")
            for result in failed_results:
                print(f"   • {result.query_name}: {'; '.join(result.errors[:2])}")
        
        # Sample successful results
        successful_results = [r for r in self.results if r.success and r.ask_answer]
        if successful_results:
            print(f"\n✅ Sample Successful Results:")
            for result in successful_results[:3]:
                answer_preview = result.ask_answer[:100] + "..." if len(result.ask_answer) > 100 else result.ask_answer
                print(f"   • {result.query_name}: '{result.natural_language}' → '{answer_preview}'")
        
        print(f"\n🎉 Test completion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def save_detailed_report(self, filename: str = "end_to_end_test_report.json") -> None:
        """Save detailed test results to JSON file."""
        report_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.results),
                "passed_tests": sum(1 for r in self.results if r.success),
                "failed_tests": sum(1 for r in self.results if not r.success),
                "total_execution_time_ms": sum(r.execution_time_ms for r in self.results)
            },
            "test_results": [
                {
                    "query_name": r.query_name,
                    "natural_language": r.natural_language,
                    "gremlin_generated": r.gremlin_generated,
                    "gremlin_query": r.gremlin_query,
                    "gremlin_valid": r.gremlin_valid,
                    "filter_executed": r.filter_executed,
                    "filter_results_count": r.filter_results_count,
                    "ask_pipeline_success": r.ask_pipeline_success,
                    "ask_answer": r.ask_answer,
                    "execution_time_ms": r.execution_time_ms,
                    "errors": r.errors,
                    "success": r.success
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed report saved to: {filename}")


async def main():
    """Main function to run the end-to-end tests."""
    print("🚀 Starting End-to-End Graph RAG Flow Testing...")
    
    try:
        async with EndToEndGraphRAGTester() as tester:
            await tester.run_all_tests()
            tester.print_summary_report()
            tester.save_detailed_report("end_to_end_test_report.json")
            
            # Return exit code based on results
            failed_tests = sum(1 for r in tester.results if not r.success)
            if failed_tests > 0:
                print(f"\n⚠️  {failed_tests} tests failed. Check the report for details.")
                sys.exit(1)
            else:
                print(f"\n🎉 All tests passed successfully!")
                sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
