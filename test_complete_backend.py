#!/usr/bin/env python3
"""
Comprehensive Test Script for Complete FastAPI Backend

Tests both traditional analytics endpoints and semantic RAG endpoints.
"""

import requests
import json
import time
import asyncio
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"


class APITester:
    """Test client for the complete Graph RAG system."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Generic endpoint tester."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, timeout=30)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "execution_time_ms": execution_time,
                "response": response.json() if response.status_code == 200 else response.text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def test_traditional_analytics(self) -> Dict[str, Any]:
        """Test all traditional analytics endpoints."""
        print("\n🏢 TESTING TRADITIONAL ANALYTICS ENDPOINTS")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Group statistics
        print("1. Testing /average/groups...")
        results["group_stats"] = self.test_endpoint("GET", "/api/v1/average/groups")
        self._print_result("Group Statistics", results["group_stats"])
        
        # Test 2: Hotel statistics
        print("\n2. Testing /average/hotels...")
        results["hotel_stats"] = self.test_endpoint("GET", "/api/v1/average/hotels", params={"limit": 10})
        self._print_result("Hotel Statistics", results["hotel_stats"])
        
        # Test 3: Specific hotel averages
        print("\n3. Testing /average/{hotel_name}...")
        results["hotel_averages"] = self.test_endpoint("GET", "/api/v1/average/Grand Hotel")
        self._print_result("Hotel Averages", results["hotel_averages"])
        
        # Test 4: Language distribution
        print("\n4. Testing /average/{hotel_id}/languages...")
        results["language_dist"] = self.test_endpoint("GET", "/api/v1/average/hotel_001/languages")
        self._print_result("Language Distribution", results["language_dist"])
        
        # Test 5: Source distribution
        print("\n5. Testing /average/{hotel_name}/sources...")
        results["source_dist"] = self.test_endpoint("GET", "/api/v1/average/Grand Hotel/sources")
        self._print_result("Source Distribution", results["source_dist"])
        
        # Test 6: Accommodation metrics
        print("\n6. Testing /average/{hotel_name}/accommodations...")
        results["accommodation_metrics"] = self.test_endpoint("GET", "/api/v1/average/Grand Hotel/accommodations")
        self._print_result("Accommodation Metrics", results["accommodation_metrics"])
        
        # Test 7: Aspect breakdown
        print("\n7. Testing /average/{hotel_name}/aspects...")
        results["aspect_breakdown"] = self.test_endpoint("GET", "/api/v1/average/Grand Hotel/aspects")
        self._print_result("Aspect Breakdown", results["aspect_breakdown"])
        
        # Test 8: Review queries
        print("\n8. Testing /reviews with filters...")
        review_params = {
            "language": "en",
            "sentiment": "positive",
            "limit": 20
        }
        results["reviews"] = self.test_endpoint("GET", "/api/v1/reviews", params=review_params)
        self._print_result("Review Queries", results["reviews"])
        
        return results
    
    def test_semantic_rag(self) -> Dict[str, Any]:
        """Test all semantic RAG endpoints."""
        print("\n🤖 TESTING SEMANTIC RAG ENDPOINTS")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Semantic ask
        print("1. Testing /semantic/ask...")
        ask_data = {
            "query": "Why are guests complaining about room cleanliness?",
            "filters": {
                "aspect": "cleanliness",
                "sentiment": "negative"
            },
            "include_gremlin_query": True,
            "include_semantic_chunks": True
        }
        results["semantic_ask"] = self.test_endpoint("POST", "/api/v1/semantic/ask", data=ask_data)
        self._print_result("Semantic Ask", results["semantic_ask"])
        
        # Test 2: Filter conversion
        print("\n2. Testing /semantic/filter...")
        filter_data = {
            "filters": {
                "hotel_group": "Marriott",
                "aspect_score": {"cleanliness": ">= 8"},
                "sentiment": "positive"
            },
            "summarize_with_llm": True,
            "max_results": 10
        }
        results["semantic_filter"] = self.test_endpoint("POST", "/api/v1/semantic/filter", data=filter_data)
        self._print_result("Semantic Filter", results["semantic_filter"])
        
        # Test 3: Gremlin translation
        print("\n3. Testing /semantic/gremlin...")
        gremlin_data = {
            "prompt": "Find all hotels with cleanliness scores above 8",
            "include_explanation": True
        }
        results["gremlin_translation"] = self.test_endpoint("POST", "/api/v1/semantic/gremlin", data=gremlin_data)
        self._print_result("Gremlin Translation", results["gremlin_translation"])
        
        # Test 4: Vector search
        print("\n4. Testing /semantic/vector...")
        vector_data = {
            "query": "hotel room cleanliness problems",
            "top_k": 10,
            "min_score": 0.5
        }
        results["vector_search"] = self.test_endpoint("POST", "/api/v1/semantic/vector", data=vector_data)
        self._print_result("Vector Search", results["vector_search"])
        
        # Test 5: Models info
        print("\n5. Testing /semantic/models...")
        results["models_info"] = self.test_endpoint("GET", "/api/v1/semantic/models")
        self._print_result("Models Info", results["models_info"])
        
        return results
    
    def test_health_and_status(self) -> Dict[str, Any]:
        """Test health and status endpoints."""
        print("\n❤️ TESTING HEALTH AND STATUS ENDPOINTS")
        print("=" * 60)
        
        results = {}
        
        # Health check
        print("1. Testing /health...")
        results["health"] = self.test_endpoint("GET", "/api/v1/health")
        self._print_result("Health Check", results["health"])
        
        # Detailed health
        print("\n2. Testing /health/detailed...")
        results["detailed_health"] = self.test_endpoint("GET", "/api/v1/health/detailed")
        self._print_result("Detailed Health", results["detailed_health"])
        
        # Statistics
        print("\n3. Testing /statistics...")
        results["statistics"] = self.test_endpoint("GET", "/api/v1/statistics")
        self._print_result("Statistics", results["statistics"])
        
        return results
    
    def _print_result(self, test_name: str, result: Dict[str, Any]):
        """Print test result in a formatted way."""
        status = result.get("status", "unknown")
        exec_time = result.get("execution_time_ms", 0)
        
        if status == "success":
            print(f"   ✅ {test_name}: SUCCESS ({exec_time:.0f}ms)")
            
            # Print some response details
            response = result.get("response", {})
            if isinstance(response, dict):
                if "total_count" in response:
                    print(f"      📊 Total Count: {response['total_count']}")
                elif "answer" in response:
                    print(f"      💬 Answer: {response['answer'][:100]}...")
                elif "gremlin_query" in response:
                    print(f"      🔍 Query: {response['gremlin_query'][:100]}...")
                elif "results" in response and isinstance(response["results"], list):
                    print(f"      📋 Results: {len(response['results'])} items")
        else:
            print(f"   ❌ {test_name}: FAILED")
            print(f"      Error: {result.get('message', 'Unknown error')}")
    
    def run_comprehensive_test(self):
        """Run all tests and generate a comprehensive report."""
        print("🚀 COMPREHENSIVE FASTAPI BACKEND TEST SUITE")
        print("=" * 80)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        overall_start = time.time()
        
        # Test each section
        health_results = self.test_health_and_status()
        analytics_results = self.test_traditional_analytics()
        semantic_results = self.test_semantic_rag()
        
        total_time = time.time() - overall_start
        
        # Generate summary report
        self._generate_summary_report(health_results, analytics_results, semantic_results, total_time)
    
    def _generate_summary_report(self, health_results: Dict, analytics_results: Dict, semantic_results: Dict, total_time: float):
        """Generate a comprehensive summary report."""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE TEST SUMMARY REPORT")
        print("=" * 80)
        
        # Count successes and failures
        all_results = {**health_results, **analytics_results, **semantic_results}
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results.values() if r.get("status") == "success")
        
        print(f"📊 Overall Results:")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Successful: {successful_tests}")
        print(f"   • Failed: {total_tests - successful_tests}")
        print(f"   • Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        print(f"   • Total Execution Time: {total_time:.2f} seconds")
        
        # Section breakdown
        sections = [
            ("Health & Status", health_results),
            ("Traditional Analytics", analytics_results),
            ("Semantic RAG", semantic_results)
        ]
        
        print(f"\n📈 Section Breakdown:")
        for section_name, section_results in sections:
            section_total = len(section_results)
            section_success = sum(1 for r in section_results.values() if r.get("status") == "success")
            success_rate = (section_success/section_total)*100 if section_total > 0 else 0
            
            status_icon = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 50 else "❌"
            print(f"   {status_icon} {section_name}: {section_success}/{section_total} ({success_rate:.1f}%)")
        
        # Performance insights
        avg_response_time = sum(r.get("execution_time_ms", 0) for r in all_results.values()) / len(all_results)
        print(f"\n⚡ Performance Insights:")
        print(f"   • Average Response Time: {avg_response_time:.0f}ms")
        
        fastest = min(all_results.items(), key=lambda x: x[1].get("execution_time_ms", float('inf')))
        slowest = max(all_results.items(), key=lambda x: x[1].get("execution_time_ms", 0))
        
        print(f"   • Fastest Endpoint: {fastest[0]} ({fastest[1].get('execution_time_ms', 0):.0f}ms)")
        print(f"   • Slowest Endpoint: {slowest[0]} ({slowest[1].get('execution_time_ms', 0):.0f}ms)")
        
        # Recommendations
        print(f"\n🎯 Recommendations:")
        if successful_tests == total_tests:
            print("   🎉 Perfect! All endpoints are working correctly.")
            print("   • Ready for production deployment")
            print("   • Consider adding more comprehensive data for testing")
        elif successful_tests >= total_tests * 0.8:
            print("   👍 Good! Most endpoints are working.")
            print("   • Check failed endpoints for configuration issues")
            print("   • Verify database connections and API keys")
        else:
            print("   ⚠️ Attention needed! Many endpoints are failing.")
            print("   • Check server configuration and dependencies")
            print("   • Verify all environment variables are set correctly")
            print("   • Ensure graph database is accessible")
        
        print(f"\n🏁 Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


def main():
    """Run the comprehensive test suite."""
    tester = APITester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
