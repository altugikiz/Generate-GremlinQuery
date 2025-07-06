#!/usr/bin/env python3
"""
Final Production Verification Test Suite
========================================

Comprehensive validation script for the Graph RAG system in production mode.
This script performs end-to-end testing with real data to verify all components
are working correctly before deployment.

Test Coverage:
1. Health endpoint validation (all components healthy)
2. Gremlin translation (Turkish & English queries)
3. Gremlin execution with real graph data
4. Semantic endpoints (/ask, /gremlin, /vector)
5. Analytics endpoints (hotel-specific data)
6. Error handling and edge cases

Usage:
    python final_production_verification.py

Requirements:
    - FastAPI server running on http://localhost:8000
    - Production mode enabled (DEVELOPMENT_MODE=false)
    - All services operational (Gremlin, LLM, Vector store)
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0
MAX_RETRIES = 3

class TestStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"
    SKIP = "⏭️ SKIP"

@dataclass
class TestResult:
    name: str
    status: TestStatus
    execution_time_ms: float
    details: str = ""
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class TestSuite:
    name: str
    results: List[TestResult]
    total_time_ms: float = 0.0
    
    @property
    def passed(self) -> int:
        return len([r for r in self.results if r.status == TestStatus.PASS])
    
    @property
    def failed(self) -> int:
        return len([r for r in self.results if r.status == TestStatus.FAIL])
    
    @property
    def warnings(self) -> int:
        return len([r for r in self.results if r.status == TestStatus.WARN])
    
    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return (self.passed / len(self.results)) * 100

class ProductionVerificationTester:
    """Comprehensive production verification test suite."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.test_suites: List[TestSuite] = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def print_header(self, title: str, level: int = 1):
        """Print formatted header."""
        if level == 1:
            print(f"\n{'='*80}")
            print(f"🎯 {title}")
            print('='*80)
        else:
            print(f"\n{'-'*60}")
            print(f"📋 {title}")
            print('-'*60)
    
    def print_result(self, result: TestResult):
        """Print individual test result."""
        status_icon = result.status.value
        time_str = f"{result.execution_time_ms:.1f}ms"
        print(f"{status_icon} {result.name} ({time_str})")
        
        if result.details:
            print(f"   📝 {result.details}")
        
        if result.error:
            print(f"   🚨 Error: {result.error}")
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any], float]:
        """Make HTTP request with timing and error handling."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                execution_time = (time.time() - start_time) * 1000
                
                try:
                    response_data = await response.json()
                except:
                    response_data = {"text": await response.text()}
                
                return response.status, response_data, execution_time
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return 0, {"error": str(e)}, execution_time
    
    async def test_health_endpoints(self) -> TestSuite:
        """Test health and status endpoints."""
        self.print_header("HEALTH & STATUS VERIFICATION", 2)
        results = []
        
        # Test 1: Basic health endpoint
        status, data, exec_time = await self.make_request("GET", "/api/v1/health")
        
        if status == 200:
            health_status = data.get("status", "unknown")
            components = data.get("components", {})
            
            # Check if all components are healthy
            unhealthy_components = [
                comp for comp, state in components.items() 
                if state not in ["healthy", "operational"]
            ]
            
            if health_status == "healthy" and not unhealthy_components:
                result = TestResult(
                    name="System Health Check",
                    status=TestStatus.PASS,
                    execution_time_ms=exec_time,
                    details=f"All components healthy: {list(components.keys())}",
                    response_data=data
                )
            elif unhealthy_components:
                result = TestResult(
                    name="System Health Check",
                    status=TestStatus.FAIL,
                    execution_time_ms=exec_time,
                    details=f"Unhealthy components: {unhealthy_components}",
                    error=f"System status: {health_status}",
                    response_data=data
                )
            else:
                result = TestResult(
                    name="System Health Check",
                    status=TestStatus.WARN,
                    execution_time_ms=exec_time,
                    details=f"Status: {health_status}",
                    response_data=data
                )
        else:
            result = TestResult(
                name="System Health Check",
                status=TestStatus.FAIL,
                execution_time_ms=exec_time,
                error=f"HTTP {status}: {data.get('error', 'Unknown error')}",
                response_data=data
            )
        
        results.append(result)
        self.print_result(result)
        
        # Test 2: Detailed health endpoint (if available)
        status, data, exec_time = await self.make_request("GET", "/api/v1/health/detailed")
        
        if status == 200:
            result = TestResult(
                name="Detailed Health Check",
                status=TestStatus.PASS,
                execution_time_ms=exec_time,
                details="Detailed health information available",
                response_data=data
            )
        elif status == 404:
            result = TestResult(
                name="Detailed Health Check",
                status=TestStatus.SKIP,
                execution_time_ms=exec_time,
                details="Detailed health endpoint not available"
            )
        else:
            result = TestResult(
                name="Detailed Health Check",
                status=TestStatus.WARN,
                execution_time_ms=exec_time,
                details=f"HTTP {status}",
                response_data=data
            )
        
        results.append(result)
        self.print_result(result)
        
        return TestSuite("Health & Status", results)
    
    async def test_gremlin_translation(self) -> TestSuite:
        """Test natural language to Gremlin translation."""
        self.print_header("GREMLIN TRANSLATION VERIFICATION", 2)
        results = []
        
        # Test cases with both Turkish and English
        test_cases = [
            {
                "name": "Turkish Hotel Query",
                "query": "Türkiye otellerinin isimlerini göster",
                "expected_elements": ["hasLabel", "Hotel", "valueMap", "hotel_name"]
            },
            {
                "name": "English Cleanliness Query", 
                "query": "Show me hotels with cleanliness complaints",
                "expected_elements": ["hasLabel", "Review", "has", "cleanliness"]
            },
            {
                "name": "Turkish VIP Guest Query",
                "query": "VIP misafirlerin sorunlarını göster",
                "expected_elements": ["hasLabel", "Guest", "VIP", "out"]
            },
            {
                "name": "English Rating Query",
                "query": "Find hotels with rating above 4.5",
                "expected_elements": ["hasLabel", "Hotel", "has", "rating", "gt"]
            },
            {
                "name": "Turkish Complex Query",
                "query": "Son bir ayda yazılmış olumsuz yorumları göster",
                "expected_elements": ["hasLabel", "Review", "has", "sentiment"]
            }
        ]
        
        for test_case in test_cases:
            payload = {
                "prompt": test_case["query"],
                "include_explanation": True
            }
            
            status, data, exec_time = await self.make_request(
                "POST", "/api/v1/semantic/gremlin", payload
            )
            
            if status == 200:
                gremlin_query = data.get("gremlin_query", "")
                
                if gremlin_query and gremlin_query.startswith("g."):
                    # Check if expected elements are in the query
                    missing_elements = [
                        elem for elem in test_case["expected_elements"]
                        if elem not in gremlin_query
                    ]
                    
                    if len(missing_elements) <= 1:  # Allow one missing element
                        result = TestResult(
                            name=test_case["name"],
                            status=TestStatus.PASS,
                            execution_time_ms=exec_time,
                            details=f"Generated valid Gremlin query: {gremlin_query[:100]}...",
                            response_data=data
                        )
                    else:
                        result = TestResult(
                            name=test_case["name"],
                            status=TestStatus.WARN,
                            execution_time_ms=exec_time,
                            details=f"Query missing elements: {missing_elements}",
                            response_data=data
                        )
                else:
                    result = TestResult(
                        name=test_case["name"],
                        status=TestStatus.FAIL,
                        execution_time_ms=exec_time,
                        error="Invalid or empty Gremlin query generated",
                        response_data=data
                    )
            else:
                result = TestResult(
                    name=test_case["name"],
                    status=TestStatus.FAIL,
                    execution_time_ms=exec_time,
                    error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                    response_data=data
                )
            
            results.append(result)
            self.print_result(result)
        
        return TestSuite("Gremlin Translation", results)
    
    async def test_gremlin_execution(self) -> TestSuite:
        """Test direct Gremlin query execution with real data."""
        self.print_header("GREMLIN EXECUTION VERIFICATION", 2)
        results = []
        
        # Test cases with actual Gremlin queries
        test_queries = [
            {
                "name": "Hotel Count Query",
                "query": "g.V().hasLabel('Hotel').count()",
                "expected_min_results": 1
            },
            {
                "name": "Hotel Names Query",
                "query": "g.V().hasLabel('Hotel').limit(5).valueMap('hotel_name')",
                "expected_min_results": 1
            },
            {
                "name": "Review Count Query",
                "query": "g.V().hasLabel('Review').count()",
                "expected_min_results": 1
            },
            {
                "name": "Edge Labels Query",
                "query": "g.E().label().dedup().limit(10)",
                "expected_min_results": 1
            },
            {
                "name": "Hotel-Review Relationship",
                "query": "g.V().hasLabel('Hotel').limit(1).out().hasLabel('Review').limit(3).valueMap()",
                "expected_min_results": 0  # May not have data, that's okay
            }
        ]
        
        for test_query in test_queries:
            payload = {"query": test_query["query"]}
            
            status, data, exec_time = await self.make_request(
                "POST", "/api/v1/semantic/execute", payload
            )
            
            if status == 200:
                results_data = data.get("results", [])
                results_count = data.get("results_count", 0)
                
                if results_count >= test_query["expected_min_results"]:
                    result = TestResult(
                        name=test_query["name"],
                        status=TestStatus.PASS,
                        execution_time_ms=exec_time,
                        details=f"Returned {results_count} results",
                        response_data=data
                    )
                elif test_query["expected_min_results"] == 0:
                    result = TestResult(
                        name=test_query["name"],
                        status=TestStatus.PASS,
                        execution_time_ms=exec_time,
                        details=f"Query executed successfully (no data required)",
                        response_data=data
                    )
                else:
                    result = TestResult(
                        name=test_query["name"],
                        status=TestStatus.WARN,
                        execution_time_ms=exec_time,
                        details=f"Expected ≥{test_query['expected_min_results']} results, got {results_count}",
                        response_data=data
                    )
            else:
                result = TestResult(
                    name=test_query["name"],
                    status=TestStatus.FAIL,
                    execution_time_ms=exec_time,
                    error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                    response_data=data
                )
            
            results.append(result)
            self.print_result(result)
        
        return TestSuite("Gremlin Execution", results)
    
    async def test_semantic_endpoints(self) -> TestSuite:
        """Test semantic RAG endpoints."""
        self.print_header("SEMANTIC RAG ENDPOINTS VERIFICATION", 2)
        results = []
        
        # Test 1: Semantic Ask endpoint
        ask_payload = {
            "query": "What are the most common complaints about hotel cleanliness?",
            "max_results": 5,
            "include_gremlin_query": True
        }
        
        status, data, exec_time = await self.make_request(
            "POST", "/api/v1/semantic/ask", ask_payload
        )
        
        if status == 200:
            answer = data.get("answer", "")
            gremlin_query = data.get("gremlin_query", "")
            
            if answer and len(answer) > 50:  # Reasonable answer length
                result = TestResult(
                    name="Semantic Ask Endpoint",
                    status=TestStatus.PASS,
                    execution_time_ms=exec_time,
                    details=f"Generated answer ({len(answer)} chars) with Gremlin query",
                    response_data=data
                )
            else:
                result = TestResult(
                    name="Semantic Ask Endpoint",
                    status=TestStatus.WARN,
                    execution_time_ms=exec_time,
                    details=f"Short answer generated: {answer[:100]}...",
                    response_data=data
                )
        else:
            result = TestResult(
                name="Semantic Ask Endpoint",
                status=TestStatus.FAIL,
                execution_time_ms=exec_time,
                error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                response_data=data
            )
        
        results.append(result)
        self.print_result(result)
        
        # Test 2: Vector Search endpoint
        vector_payload = {
            "query": "hotel service quality",
            "max_results": 5
        }
        
        status, data, exec_time = await self.make_request(
            "POST", "/api/v1/semantic/vector", vector_payload
        )
        
        if status == 200:
            documents = data.get("documents", [])
            
            if documents:
                result = TestResult(
                    name="Vector Search Endpoint",
                    status=TestStatus.PASS,
                    execution_time_ms=exec_time,
                    details=f"Found {len(documents)} semantic matches",
                    response_data=data
                )
            else:
                result = TestResult(
                    name="Vector Search Endpoint",
                    status=TestStatus.WARN,
                    execution_time_ms=exec_time,
                    details="No vector search results (may need indexed data)",
                    response_data=data
                )
        else:
            result = TestResult(
                name="Vector Search Endpoint",
                status=TestStatus.FAIL,
                execution_time_ms=exec_time,
                error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                response_data=data
            )
        
        results.append(result)
        self.print_result(result)
        
        # Test 3: Filter endpoint
        filter_payload = {
            "filters": {
                "vertex_label": "Hotel",
                "properties": {"rating": {"gte": 4.0}}
            },
            "max_results": 10
        }
        
        status, data, exec_time = await self.make_request(
            "POST", "/api/v1/semantic/filter", filter_payload
        )
        
        if status == 200:
            results_data = data.get("results", [])
            gremlin_query = data.get("gremlin_query", "")
            
            result = TestResult(
                name="Semantic Filter Endpoint",
                status=TestStatus.PASS,
                execution_time_ms=exec_time,
                details=f"Executed filter query, got {len(results_data)} results",
                response_data=data
            )
        else:
            result = TestResult(
                name="Semantic Filter Endpoint",
                status=TestStatus.FAIL,
                execution_time_ms=exec_time,
                error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                response_data=data
            )
        
        results.append(result)
        self.print_result(result)
        
        return TestSuite("Semantic RAG Endpoints", results)
    
    async def test_analytics_endpoints(self) -> TestSuite:
        """Test analytics endpoints with real hotel data."""
        self.print_header("ANALYTICS ENDPOINTS VERIFICATION", 2)
        results = []
        
        # First, try to get a real hotel name from the data
        hotel_name = "AKKA CLAROS"  # Default from our test data
        
        # Try to get actual hotel names
        status, data, _ = await self.make_request(
            "POST", "/api/v1/semantic/execute", 
            {"query": "g.V().hasLabel('Hotel').limit(1).valueMap('hotel_name')"}
        )
        
        if status == 200 and data.get("results"):
            try:
                first_hotel = data["results"][0]
                if "hotel_name" in first_hotel:
                    hotel_name = first_hotel["hotel_name"][0]
                    print(f"   🏨 Using real hotel name: {hotel_name}")
            except:
                pass
        
        # Test analytics endpoints
        analytics_tests = [
            {
                "name": "Hotel Average Ratings",
                "endpoint": f"/api/v1/average/{hotel_name}",
                "method": "GET"
            },
            {
                "name": "Group Statistics",
                "endpoint": "/api/v1/average/groups",
                "method": "GET"
            },
            {
                "name": "Source Statistics",
                "endpoint": "/api/v1/average/hotels",
                "method": "GET"
            }
        ]
        
        for test in analytics_tests:
            status, data, exec_time = await self.make_request(
                test["method"], test["endpoint"]
            )
            
            if status == 200:
                if isinstance(data, list) and data:
                    result = TestResult(
                        name=test["name"],
                        status=TestStatus.PASS,
                        execution_time_ms=exec_time,
                        details=f"Returned {len(data)} analytics records",
                        response_data=data
                    )
                elif isinstance(data, dict) and data:
                    result = TestResult(
                        name=test["name"],
                        status=TestStatus.PASS,
                        execution_time_ms=exec_time,
                        details="Returned analytics data",
                        response_data=data
                    )
                else:
                    result = TestResult(
                        name=test["name"],
                        status=TestStatus.WARN,
                        execution_time_ms=exec_time,
                        details="Empty analytics response (may need more data)",
                        response_data=data
                    )
            elif status == 404:
                result = TestResult(
                    name=test["name"],
                    status=TestStatus.WARN,
                    execution_time_ms=exec_time,
                    details=f"Endpoint not found (may not be implemented)",
                    response_data=data
                )
            elif status == 503:
                result = TestResult(
                    name=test["name"],
                    status=TestStatus.FAIL,
                    execution_time_ms=exec_time,
                    error="Service unavailable - check Gremlin connectivity",
                    response_data=data
                )
            else:
                result = TestResult(
                    name=test["name"],
                    status=TestStatus.FAIL,
                    execution_time_ms=exec_time,
                    error=f"HTTP {status}: {data.get('detail', 'Unknown error')}",
                    response_data=data
                )
            
            results.append(result)
            self.print_result(result)
        
        return TestSuite("Analytics Endpoints", results)
    
    async def test_error_handling(self) -> TestSuite:
        """Test error handling and edge cases."""
        self.print_header("ERROR HANDLING VERIFICATION", 2)
        results = []
        
        # Test malformed requests
        error_tests = [
            {
                "name": "Empty Query",
                "endpoint": "/api/v1/semantic/gremlin",
                "payload": {"query": ""},
                "expected_status": [400, 422]
            },
            {
                "name": "Invalid Gremlin Query",
                "endpoint": "/api/v1/semantic/execute",
                "payload": {"query": "invalid gremlin syntax"},
                "expected_status": [400, 500]
            },
            {
                "name": "Missing Required Fields",
                "endpoint": "/api/v1/semantic/ask",
                "payload": {},
                "expected_status": [400, 422]
            }
        ]
        
        for test in error_tests:
            status, data, exec_time = await self.make_request(
                "POST", test["endpoint"], test["payload"]
            )
            
            if status in test["expected_status"]:
                result = TestResult(
                    name=test["name"],
                    status=TestStatus.PASS,
                    execution_time_ms=exec_time,
                    details=f"Correctly returned HTTP {status} for invalid input",
                    response_data=data
                )
            else:
                result = TestResult(
                    name=test["name"],
                    status=TestStatus.WARN,
                    execution_time_ms=exec_time,
                    details=f"Expected {test['expected_status']}, got {status}",
                    response_data=data
                )
            
            results.append(result)
            self.print_result(result)
        
        return TestSuite("Error Handling", results)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and generate comprehensive report."""
        self.print_header("FINAL PRODUCTION VERIFICATION TEST SUITE")
        
        print(f"🔗 Testing endpoint: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Test configuration: Production mode verification")
        
        # Run all test suites
        try:
            # 1. Health and Status
            health_suite = await self.test_health_endpoints()
            self.test_suites.append(health_suite)
            
            # 2. Gremlin Translation
            translation_suite = await self.test_gremlin_translation()
            self.test_suites.append(translation_suite)
            
            # 3. Gremlin Execution
            execution_suite = await self.test_gremlin_execution()
            self.test_suites.append(execution_suite)
            
            # 4. Semantic Endpoints
            semantic_suite = await self.test_semantic_endpoints()
            self.test_suites.append(semantic_suite)
            
            # 5. Analytics Endpoints
            analytics_suite = await self.test_analytics_endpoints()
            self.test_suites.append(analytics_suite)
            
            # 6. Error Handling
            error_suite = await self.test_error_handling()
            self.test_suites.append(error_suite)
            
        except Exception as e:
            print(f"\n🚨 Critical error during testing: {e}")
            traceback.print_exc()
        
        # Generate final report
        return self.generate_final_report()
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        total_time = time.time() - self.start_time
        
        self.print_header("FINAL VERIFICATION REPORT")
        
        # Summary statistics
        total_tests = sum(len(suite.results) for suite in self.test_suites)
        total_passed = sum(suite.passed for suite in self.test_suites)
        total_failed = sum(suite.failed for suite in self.test_suites)
        total_warnings = sum(suite.warnings for suite in self.test_suites)
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   ⚠️ Warnings: {total_warnings}")
        print(f"   📈 Success Rate: {overall_success_rate:.1f}%")
        print(f"   ⏱️ Total Time: {total_time:.2f}s")
        
        # Suite-by-suite breakdown
        print(f"\n📋 SUITE BREAKDOWN")
        for suite in self.test_suites:
            status_icon = "✅" if suite.failed == 0 else "❌" if suite.failed > suite.passed else "⚠️"
            print(f"   {status_icon} {suite.name}: {suite.passed}/{len(suite.results)} passed ({suite.success_rate:.1f}%)")
        
        # Critical issues
        critical_failures = []
        for suite in self.test_suites:
            for result in suite.results:
                if result.status == TestStatus.FAIL:
                    critical_failures.append(f"{suite.name}: {result.name} - {result.error}")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_failures)}):")
            for failure in critical_failures[:5]:  # Show first 5
                print(f"   • {failure}")
            if len(critical_failures) > 5:
                print(f"   ... and {len(critical_failures) - 5} more")
        
        # Production readiness assessment
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT")
        
        health_passed = next((s for s in self.test_suites if s.name == "Health & Status"), None)
        gremlin_passed = next((s for s in self.test_suites if "Gremlin" in s.name), None)
        
        is_production_ready = (
            total_failed == 0 and
            overall_success_rate >= 90 and
            health_passed and health_passed.failed == 0
        )
        
        if is_production_ready:
            print(f"   ✅ PRODUCTION READY")
            print(f"   🚀 System is fully operational and ready for deployment")
        elif overall_success_rate >= 75:
            print(f"   ⚠️ MOSTLY READY")
            print(f"   🔧 Minor issues detected, review warnings before deployment")
        else:
            print(f"   ❌ NOT READY")
            print(f"   🛠️ Critical issues must be resolved before deployment")
        
        # Generate detailed report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_time_seconds": total_time,
            "statistics": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "warnings": total_warnings,
                "success_rate": overall_success_rate
            },
            "production_ready": is_production_ready,
            "test_suites": [
                {
                    "name": suite.name,
                    "total_tests": len(suite.results),
                    "passed": suite.passed,
                    "failed": suite.failed,
                    "warnings": suite.warnings,
                    "success_rate": suite.success_rate,
                    "results": [asdict(result) for result in suite.results]
                }
                for suite in self.test_suites
            ],
            "critical_failures": critical_failures
        }
        
        # Save detailed report
        report_file = Path(f"production_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return report_data

async def main():
    """Main function to run the production verification."""
    try:
        async with ProductionVerificationTester() as tester:
            report = await tester.run_all_tests()
            
            # Exit with appropriate code
            if report["production_ready"]:
                print(f"\n🎉 VERIFICATION COMPLETE: PRODUCTION READY! 🎉")
                return 0
            elif report["statistics"]["success_rate"] >= 75:
                print(f"\n⚠️ VERIFICATION COMPLETE: REVIEW WARNINGS")
                return 1
            else:
                print(f"\n❌ VERIFICATION FAILED: CRITICAL ISSUES DETECTED")
                return 2
                
    except KeyboardInterrupt:
        print(f"\n⏹️ Verification interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
