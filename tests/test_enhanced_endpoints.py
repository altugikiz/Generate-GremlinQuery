#!/usr/bin/env python3
"""
Test Script for Enhanced Graph RAG Endpoints (/ask and /filter)
Tests the exact specifications implemented for natural language and structured filter queries.
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

BASE_URL = "http://localhost:8000"

@dataclass
class TestResult:
    endpoint: str
    query_type: str
    success: bool
    response_time_ms: float
    status_code: int
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class GraphRAGEndpointTester:
    """Test suite for /ask and /filter endpoints matching exact specifications."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_ask_endpoint_basic(self) -> TestResult:
        """Test the /ask endpoint with a basic natural language query."""
        endpoint = "/api/v1/ask"
        payload = {
            "query": "What are guests saying about the staff at luxury hotels?",
            "include_gremlin_query": True,
            "include_semantic_chunks": True,
            "include_context": False
        }
        
        return self._make_request("ask_basic", endpoint, payload)
    
    def test_ask_endpoint_with_filters(self) -> TestResult:
        """Test the /ask endpoint with natural language query + filters."""
        endpoint = "/api/v1/ask"
        payload = {
            "query": "Why are guests complaining about room cleanliness?",
            "filters": {
                "language": "en",
                "source": "booking",
                "aspect": "cleanliness",
                "sentiment": "negative",
                "date_range": "last_30_days"
            },
            "include_gremlin_query": True,
            "include_semantic_chunks": True,
            "max_graph_results": 10,
            "max_semantic_results": 5,
            "use_llm_summary": True
        }
        
        return self._make_request("ask_with_filters", endpoint, payload)
    
    def test_ask_endpoint_room_specific(self) -> TestResult:
        """Test the /ask endpoint with room-specific query."""
        endpoint = "/api/v1/ask"
        payload = {
            "query": "Show me maintenance issues in room 205",
            "filters": {
                "room": "205",
                "sentiment": "negative",
                "date_range": "last_30_days"
            },
            "include_gremlin_query": True,
            "include_semantic_chunks": False,
            "include_context": True
        }
        
        return self._make_request("ask_room_specific", endpoint, payload)
    
    def test_filter_endpoint_basic(self) -> TestResult:
        """Test the /filter endpoint with structured filters only."""
        endpoint = "/api/v1/filter"
        payload = {
            "filters": {
                "language": "tr",
                "aspect": "cleanliness",
                "sentiment": "negative",
                "source": "tripadvisor",
                "date_range": "last_7_days"
            },
            "include_gremlin_query": True,
            "include_results": True,
            "use_llm_summary": True,
            "max_results": 15
        }
        
        return self._make_request("filter_basic", endpoint, payload)
    
    def test_filter_endpoint_room_maintenance(self) -> TestResult:
        """Test the /filter endpoint for room maintenance issues."""
        endpoint = "/api/v1/filter"
        payload = {
            "filters": {
                "room": "301",
                "sentiment": "negative",
                "date_range": "last_14_days",
                "aspect": "maintenance"
            },
            "include_gremlin_query": True,
            "include_results": True,
            "use_llm_summary": True,
            "max_results": 20,
            "result_format": "detailed"
        }
        
        return self._make_request("filter_room_maintenance", endpoint, payload)
    
    def test_filter_endpoint_hotel_specific(self) -> TestResult:
        """Test the /filter endpoint for hotel-specific analysis."""
        endpoint = "/api/v1/filter"
        payload = {
            "filters": {
                "hotel": "Grand Plaza Hotel",
                "guest_type": "VIP",
                "min_rating": 8.0,
                "aspect": "service"
            },
            "include_gremlin_query": True,
            "include_results": True,
            "use_llm_summary": True,
            "max_results": 10
        }
        
        return self._make_request("filter_hotel_specific", endpoint, payload)
    
    def test_filter_endpoint_rating_range(self) -> TestResult:
        """Test the /filter endpoint with rating range filters."""
        endpoint = "/api/v1/filter"
        payload = {
            "filters": {
                "min_rating": 1.0,
                "max_rating": 3.0,
                "sentiment": "negative",
                "language": "en",
                "date_range": "last_30_days"
            },
            "include_gremlin_query": True,
            "include_results": False,  # Just get the query and summary
            "use_llm_summary": True,
            "max_results": 25
        }
        
        return self._make_request("filter_rating_range", endpoint, payload)
    
    def _make_request(self, test_name: str, endpoint: str, payload: Dict[str, Any]) -> TestResult:
        """Make a request to an endpoint and return test results."""
        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            success = response.status_code < 400
            response_data = None
            
            if success:
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text[:200]}
            
            return TestResult(
                endpoint=endpoint,
                query_type=test_name,
                success=success,
                response_time_ms=response_time,
                status_code=response.status_code,
                response_data=response_data,
                error_message=None if success else response.text[:200]
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                endpoint=endpoint,
                query_type=test_name,
                success=False,
                response_time_ms=response_time,
                status_code=0,
                error_message=str(e)
            )
    
    def test_examples_endpoints(self) -> tuple[TestResult, TestResult]:
        """Test the example endpoints for both /ask and /filter."""
        ask_examples = self._make_request(
            "ask_examples", 
            "/api/v1/ask/examples", 
            {}
        )
        
        filter_examples = self._make_request(
            "filter_examples", 
            "/api/v1/filter/examples", 
            {}
        )
        
        return ask_examples, filter_examples
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("🚀 TESTING ENHANCED GRAPH RAG ENDPOINTS (/ask & /filter)")
        print("=" * 70)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all endpoint tests
        tests = [
            ("ASK Basic Query", self.test_ask_endpoint_basic),
            ("ASK with Filters", self.test_ask_endpoint_with_filters),
            ("ASK Room Specific", self.test_ask_endpoint_room_specific),
            ("FILTER Basic", self.test_filter_endpoint_basic),
            ("FILTER Room Maintenance", self.test_filter_endpoint_room_maintenance),
            ("FILTER Hotel Specific", self.test_filter_endpoint_hotel_specific),
            ("FILTER Rating Range", self.test_filter_endpoint_rating_range)
        ]
        
        results = []
        
        print(f"\\n📋 RUNNING {len(tests)} ENDPOINT TESTS")
        print("=" * 70)
        
        for test_name, test_func in tests:
            print(f"\\n🧪 Testing: {test_name}")
            result = test_func()
            results.append(result)
            
            status_emoji = "✅" if result.success else "❌"
            print(f"   {status_emoji} Status: {'PASS' if result.success else 'FAIL'}")
            print(f"   ⏱️  Response Time: {result.response_time_ms:.1f}ms")
            print(f"   📊 Status Code: {result.status_code}")
            
            if result.success and result.response_data:
                # Show key response fields
                if "query" in result.response_data:
                    print(f"   📝 Query: {result.response_data['query'][:50]}...")
                if "answer" in result.response_data:
                    print(f"   💡 Answer: {result.response_data['answer'][:80]}...")
                if "gremlin_query" in result.response_data and result.response_data["gremlin_query"]:
                    print(f"   🔍 Gremlin: {result.response_data['gremlin_query'][:60]}...")
                if "execution_time_ms" in result.response_data:
                    print(f"   ⚡ Execution: {result.response_data['execution_time_ms']:.1f}ms")
            
            if not result.success and result.error_message:
                print(f"   ❌ Error: {result.error_message}")
        
        # Test example endpoints
        print(f"\\n📚 TESTING EXAMPLE ENDPOINTS")
        print("=" * 40)
        ask_examples, filter_examples = self.test_examples_endpoints()
        results.extend([ask_examples, filter_examples])
        
        for example_result in [ask_examples, filter_examples]:
            endpoint_name = example_result.endpoint.split('/')[-1]
            status_emoji = "✅" if example_result.success else "❌"
            print(f"   {status_emoji} {endpoint_name}: {'PASS' if example_result.success else 'FAIL'}")
        
        # Generate summary
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        avg_response_time = sum(r.response_time_ms for r in results) / total_tests
        
        summary = {
            "total_tests": total_tests,
            "successful": successful_tests,
            "failed": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests) * 100,
            "average_response_time_ms": avg_response_time,
            "ask_endpoint_tests": 3,
            "filter_endpoint_tests": 4,
            "example_endpoint_tests": 2
        }
        
        # Print comprehensive summary
        print(f"\\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 70)
        
        print(f"🎯 Overall Results:")
        print(f"   • Total Tests: {summary['total_tests']}")
        print(f"   • Successful: {summary['successful']}")
        print(f"   • Failed: {summary['failed']}")
        print(f"   • Success Rate: {summary['success_rate']:.1f}%")
        print(f"   • Average Response Time: {summary['average_response_time_ms']:.1f}ms")
        
        print(f"\\n📈 Endpoint Breakdown:")
        ask_success = sum(1 for r in results[:3] if r.success)
        filter_success = sum(1 for r in results[3:7] if r.success)
        example_success = sum(1 for r in results[7:] if r.success)
        
        print(f"   📝 /ask endpoint: {ask_success}/3 ({(ask_success/3*100):.1f}%)")
        print(f"   🔍 /filter endpoint: {filter_success}/4 ({(filter_success/4*100):.1f}%)")
        print(f"   📚 Example endpoints: {example_success}/2 ({(example_success/2*100):.1f}%)")
        
        # Show failed tests
        failed_results = [r for r in results if not r.success]
        if failed_results:
            print(f"\\n❌ Failed Tests:")
            for result in failed_results:
                print(f"   • {result.query_type}: {result.error_message or f'HTTP {result.status_code}'}")
        
        # Performance analysis
        fast_tests = [r for r in results if r.response_time_ms < 1000]
        slow_tests = [r for r in results if r.response_time_ms > 3000]
        
        print(f"\\n⚡ Performance Analysis:")
        print(f"   • Fast responses (<1s): {len(fast_tests)} tests")
        print(f"   • Slow responses (>3s): {len(slow_tests)} tests")
        
        if results:
            fastest = min(results, key=lambda x: x.response_time_ms)
            slowest = max(results, key=lambda x: x.response_time_ms)
            print(f"   • Fastest: {fastest.query_type} ({fastest.response_time_ms:.1f}ms)")
            print(f"   • Slowest: {slowest.query_type} ({slowest.response_time_ms:.1f}ms)")
        
        # Overall assessment
        if summary['success_rate'] >= 95:
            print(f"\\n🎉 EXCELLENT: Both endpoints are working perfectly!")
        elif summary['success_rate'] >= 80:
            print(f"\\n✅ GOOD: Endpoints are working well with minor issues.")
        elif summary['success_rate'] >= 60:
            print(f"\\n⚠️ FAIR: Endpoints have some issues that need attention.")
        else:
            print(f"\\n🚨 POOR: Endpoints have significant issues requiring immediate attention.")
        
        print(f"\\n🏁 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return {
            "summary": summary,
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "query_type": r.query_type,
                    "success": r.success,
                    "response_time_ms": r.response_time_ms,
                    "status_code": r.status_code,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }

def check_server_availability(base_url: str) -> bool:
    """Check if the server is running and accessible."""
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        return response.status_code < 500
    except:
        return False

def main():
    """Main test execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Enhanced Graph RAG Endpoints (/ask and /filter)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_enhanced_endpoints.py
  python test_enhanced_endpoints.py --url http://localhost:8000
  python test_enhanced_endpoints.py --save-results
        """
    )
    
    parser.add_argument("--url", default=BASE_URL, help="Base URL of the API server")
    parser.add_argument("--save-results", action="store_true", help="Save test results to JSON file")
    
    args = parser.parse_args()
    
    # Check server availability
    print("🔍 Checking server availability...")
    if not check_server_availability(args.url):
        print(f"❌ Server not available at {args.url}")
        print("   Please ensure the FastAPI server is running:")
        print("   python main.py")
        return 1
    
    print(f"✅ Server is available at {args.url}")
    
    # Run tests
    tester = GraphRAGEndpointTester(args.url)
    
    try:
        results = tester.run_all_tests()
        
        # Save results if requested
        if args.save_results:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_endpoints_test_results_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\\n💾 Test results saved to: {filename}")
        
        # Exit with appropriate code
        return 0 if results["summary"]["failed"] == 0 else 1
        
    except KeyboardInterrupt:
        print("\\n\\n👋 Tests interrupted by user. Goodbye!")
        return 1
    except Exception as e:
        print(f"\\n❌ Test execution error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
