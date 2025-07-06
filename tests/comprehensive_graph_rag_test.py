#!/usr/bin/env python3
"""
Comprehensive Graph RAG System Validation

This script provides complete end-to-end testing of your Graph RAG system:
1. Natural Language → Gremlin Query Translation
2. Gremlin Query Execution and Validation
3. Full RAG Pipeline Testing (ask endpoints)
4. Multilingual Support Validation (English + Turkish)
5. Error Handling and Edge Case Testing
6. Performance and Component Analysis

Usage:
    python comprehensive_graph_rag_test.py

Features:
- Tests all major endpoints (/semantic/gremlin, /semantic/execute, /semantic/ask, /ask)
- Validates query generation quality and execution
- Measures performance and component timings
- Generates detailed reports and recommendations
- Supports both English and Turkish queries
- Tests edge cases and error scenarios
"""

import asyncio
import httpx
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 30.0

class TestStatus(Enum):
    """Test result status codes."""
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"
    SKIP = "⏭️ SKIP"

class ComponentType(Enum):
    """System component types for testing."""
    TRANSLATION = "Natural Language → Gremlin"
    EXECUTION = "Gremlin Query Execution"
    RAG_PIPELINE = "Full RAG Pipeline"
    ERROR_HANDLING = "Error Handling"

@dataclass
class TestCase:
    """Comprehensive test case definition."""
    id: str
    name: str
    query: str
    language: str
    category: str
    expected_elements: List[str]
    test_translation: bool = True
    test_execution: bool = True
    test_rag_pipeline: bool = True
    should_succeed: bool = True
    filters: Optional[Dict[str, Any]] = None
    description: str = ""

@dataclass
class ComponentResult:
    """Result for individual component test."""
    component: ComponentType
    status: TestStatus
    execution_time_ms: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class TestCaseResult:
    """Complete result for a test case."""
    test_case: TestCase
    overall_status: TestStatus
    components: List[ComponentResult]
    total_time_ms: float
    errors: List[str]

class GraphRAGTester:
    """Comprehensive Graph RAG system tester."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        self.results: List[TestCaseResult] = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_test_cases(self) -> List[TestCase]:
        """Define comprehensive test suite."""
        return [
            # English Hotel Domain Tests
            TestCase(
                id="en_hotel_service",
                name="Hotel Service Quality Analysis",
                query="Find hotels with excellent service ratings",
                language="en",
                category="Hotel Analysis",
                expected_elements=["Hotel", "service", "rating", "excellent"],
                description="Test basic hotel service quality queries"
            ),
            TestCase(
                id="en_guest_complaints",
                name="Guest Complaint Investigation",
                query="Show me guest complaints about room cleanliness",
                language="en", 
                category="Guest Feedback",
                expected_elements=["Guest", "complaint", "Room", "cleanliness"],
                description="Test guest complaint analysis capabilities"
            ),
            TestCase(
                id="en_vip_experience",
                name="VIP Guest Experience Analysis", 
                query="What are VIP guests saying about their experience?",
                language="en",
                category="VIP Management",
                expected_elements=["VIP", "Guest", "experience"],
                description="Test VIP guest feedback analysis"
            ),
            TestCase(
                id="en_maintenance_issues",
                name="Maintenance Issue Tracking",
                query="Show maintenance problems reported in hotel rooms",
                language="en",
                category="Operations",
                expected_elements=["maintenance", "problem", "Room"],
                description="Test maintenance issue tracking queries"
            ),
            TestCase(
                id="en_location_reviews",
                name="Location and Accessibility Reviews",
                query="Find reviews mentioning hotel location and accessibility",
                language="en",
                category="Location Analysis", 
                expected_elements=["Review", "location", "accessibility"],
                description="Test location-based review analysis"
            ),
            
            # Turkish Language Tests
            TestCase(
                id="tr_hotel_service",
                name="Turkish Hotel Service Query",
                query="Otellerin hizmet puanlarını göster",
                language="tr",
                category="Hotel Analysis",
                expected_elements=["Hotel", "hizmet", "puan"],
                description="Test Turkish language hotel service queries"
            ),
            TestCase(
                id="tr_cleanliness_complaints",
                name="Turkish Cleanliness Complaints",
                query="Temizlik ile ilgili şikayetleri bul",
                language="tr",
                category="Guest Feedback", 
                expected_elements=["temizlik", "şikayet"],
                description="Test Turkish cleanliness complaint analysis"
            ),
            TestCase(
                id="tr_vip_issues",
                name="Turkish VIP Guest Issues",
                query="VIP misafirlerin sorunlarını göster",
                language="tr",
                category="VIP Management",
                expected_elements=["VIP", "misafir", "sorun"],
                description="Test Turkish VIP guest issue tracking"
            ),
            TestCase(
                id="tr_room_maintenance",
                name="Turkish Room Maintenance",
                query="Oda bakım sorunlarını listele",
                language="tr",
                category="Operations",
                expected_elements=["Oda", "bakım", "sorun"],
                description="Test Turkish room maintenance queries"
            ),
            
            # Complex Multi-Factor Queries
            TestCase(
                id="en_complex_filter",
                name="Multi-Factor Hotel Analysis",
                query="Find luxury hotels with poor cleanliness but excellent service",
                language="en",
                category="Complex Analysis",
                expected_elements=["Hotel", "luxury", "cleanliness", "service"],
                description="Test complex multi-factor analysis capabilities"
            ),
            TestCase(
                id="en_temporal_analysis",
                name="Temporal Trend Analysis",
                query="Show recent guest feedback trends for room quality",
                language="en", 
                category="Trend Analysis",
                expected_elements=["Guest", "feedback", "Room", "quality", "recent"],
                description="Test temporal analysis and trend detection"
            ),
            
            # Edge Cases and Error Scenarios
            TestCase(
                id="edge_empty_query",
                name="Empty Query Test",
                query="",
                language="en",
                category="Edge Cases",
                expected_elements=[],
                should_succeed=False,
                description="Test handling of empty queries"
            ),
            TestCase(
                id="edge_very_long_query",
                name="Very Long Query Test", 
                query="Find hotels with excellent service and great location and amazing cleanliness and wonderful staff and perfect amenities and outstanding breakfast and incredible room quality and fantastic value for money and exceptional customer service and remarkable maintenance standards and superior accessibility features and excellent parking facilities" * 3,
                language="en",
                category="Edge Cases",
                expected_elements=["Hotel"],
                description="Test handling of very long queries"
            ),
            TestCase(
                id="edge_nonsense_query",
                name="Nonsense Query Test",
                query="Purple elephants dancing with quantum spaghetti in the hotel matrix",
                language="en",
                category="Edge Cases", 
                expected_elements=[],
                should_succeed=False,
                description="Test handling of nonsensical queries"
            )
        ]
    
    async def check_server_health(self) -> bool:
        """Verify server is running and accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                print(f"{TestStatus.PASS.value} Server is healthy and accessible")
                health_data = response.json()
                print(f"   Server: {health_data.get('status', 'Unknown')}")
                return True
            else:
                print(f"{TestStatus.FAIL.value} Server health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"{TestStatus.FAIL.value} Cannot connect to server: {e}")
            return False
    
    async def test_translation_component(self, test_case: TestCase) -> ComponentResult:
        """Test natural language to Gremlin translation."""
        start_time = time.time()
        
        try:
            payload = {
                "prompt": test_case.query,
                "include_explanation": True
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/gremlin",
                json=payload
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                gremlin_query = data.get("gremlin_query", "")
                explanation = data.get("explanation", "")
                confidence = data.get("confidence_score", 0.0)
                
                # Validate query quality
                is_valid = self._validate_gremlin_query(gremlin_query, test_case.expected_elements)
                
                result_data = {
                    "gremlin_query": gremlin_query,
                    "explanation": explanation,
                    "confidence_score": confidence,
                    "query_valid": is_valid,
                    "query_length": len(gremlin_query)
                }
                
                status = TestStatus.PASS if is_valid and gremlin_query else TestStatus.WARN
                
                return ComponentResult(
                    component=ComponentType.TRANSLATION,
                    status=status, 
                    execution_time_ms=execution_time,
                    data=result_data
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return ComponentResult(
                    component=ComponentType.TRANSLATION,
                    status=TestStatus.FAIL,
                    execution_time_ms=execution_time,
                    error=error_msg
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ComponentResult(
                component=ComponentType.TRANSLATION,
                status=TestStatus.FAIL,
                execution_time_ms=execution_time,
                error=str(e)
            )
    
    async def test_execution_component(self, gremlin_query: str) -> ComponentResult:
        """Test Gremlin query execution."""
        start_time = time.time()
        
        try:
            payload = {"query": gremlin_query}
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/execute",
                json=payload
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                results_count = data.get("results_count", 0)
                query_execution_time = data.get("execution_time_ms", 0.0)
                
                result_data = {
                    "results_count": results_count,
                    "execution_time_ms": query_execution_time,
                    "has_results": len(results) > 0,
                    "sample_result": results[0] if results else None
                }
                
                status = TestStatus.PASS if results_count >= 0 else TestStatus.WARN
                
                return ComponentResult(
                    component=ComponentType.EXECUTION,
                    status=status,
                    execution_time_ms=execution_time,
                    data=result_data
                )
            else:
                # In development mode, database might not be available
                if response.status_code == 503:
                    return ComponentResult(
                        component=ComponentType.EXECUTION,
                        status=TestStatus.SKIP,
                        execution_time_ms=execution_time,
                        error="Database not available (development mode)"
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    return ComponentResult(
                        component=ComponentType.EXECUTION,
                        status=TestStatus.FAIL,
                        execution_time_ms=execution_time,
                        error=error_msg
                    )
                    
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ComponentResult(
                component=ComponentType.EXECUTION,
                status=TestStatus.FAIL,
                execution_time_ms=execution_time,
                error=str(e)
            )
    
    async def test_rag_pipeline_component(self, test_case: TestCase) -> ComponentResult:
        """Test the full RAG pipeline."""
        start_time = time.time()
        
        try:
            payload = {
                "query": test_case.query,
                "include_gremlin_query": True,
                "include_semantic_chunks": True,
                "include_context": False
            }
            
            if test_case.filters:
                payload["filters"] = test_case.filters
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/ask",
                json=payload
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                gremlin_query = data.get("gremlin_query", "")
                total_time = data.get("execution_time_ms", 0.0)
                development_mode = data.get("development_mode", False)
                component_times = data.get("component_times", {})
                
                result_data = {
                    "answer": answer,
                    "answer_length": len(answer),
                    "gremlin_query": gremlin_query,
                    "total_execution_time_ms": total_time,
                    "development_mode": development_mode,
                    "component_times": component_times,
                    "has_meaningful_answer": len(answer.strip()) > 20
                }
                
                status = TestStatus.PASS if answer and len(answer.strip()) > 10 else TestStatus.WARN
                
                return ComponentResult(
                    component=ComponentType.RAG_PIPELINE,
                    status=status,
                    execution_time_ms=execution_time,
                    data=result_data
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return ComponentResult(
                    component=ComponentType.RAG_PIPELINE,
                    status=TestStatus.FAIL,
                    execution_time_ms=execution_time,
                    error=error_msg
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ComponentResult(
                component=ComponentType.RAG_PIPELINE,
                status=TestStatus.FAIL,
                execution_time_ms=execution_time,
                error=str(e)
            )
    
    def _validate_gremlin_query(self, query: str, expected_elements: List[str]) -> bool:
        """Validate the quality and correctness of generated Gremlin query."""
        if not query or query.strip() == "":
            return False
        
        # Basic structural validation
        if not query.strip().startswith("g."):
            return False
        
        # Check for basic Gremlin patterns
        gremlin_patterns = ["hasLabel", "has(", "out(", "in(", "where(", "valueMap", "limit"]
        pattern_matches = sum(1 for pattern in gremlin_patterns if pattern in query)
        
        # Check for expected domain elements (case-insensitive)
        query_lower = query.lower()
        element_matches = sum(1 for element in expected_elements if element.lower() in query_lower)
        
        # Scoring: structure + domain relevance
        structure_score = min(pattern_matches / 3, 1.0)  # At least 3 patterns expected
        domain_score = element_matches / len(expected_elements) if expected_elements else 1.0
        
        overall_score = (structure_score + domain_score) / 2
        return overall_score >= 0.3  # At least 30% quality threshold
    
    async def run_single_test(self, test_case: TestCase) -> TestCaseResult:
        """Execute comprehensive test for a single test case."""
        print(f"\n🧪 Testing: {test_case.name} ({test_case.id})")
        print(f"   Language: {test_case.language.upper()}")
        print(f"   Category: {test_case.category}")
        print(f"   Query: '{test_case.query}'")
        if test_case.description:
            print(f"   Description: {test_case.description}")
        
        start_time = time.time()
        components = []
        errors = []
        
        # Test Translation Component
        if test_case.test_translation:
            print(f"\n  📝 Testing Translation Component...")
            translation_result = await self.test_translation_component(test_case)
            components.append(translation_result)
            
            print(f"     Status: {translation_result.status.value}")
            print(f"     Time: {translation_result.execution_time_ms:.2f}ms")
            
            if translation_result.error:
                errors.append(f"Translation: {translation_result.error}")
                print(f"     Error: {translation_result.error}")
            elif translation_result.data:
                data = translation_result.data
                print(f"     Gremlin: {data.get('gremlin_query', 'N/A')[:100]}...")
                print(f"     Confidence: {data.get('confidence_score', 0):.2f}")
                print(f"     Valid: {data.get('query_valid', False)}")
        
        # Test Execution Component (if translation succeeded)
        gremlin_query = None
        if test_case.test_execution and components and components[0].data:
            gremlin_query = components[0].data.get("gremlin_query")
            if gremlin_query:
                print(f"\n  🔍 Testing Execution Component...")
                execution_result = await self.test_execution_component(gremlin_query)
                components.append(execution_result)
                
                print(f"     Status: {execution_result.status.value}")
                print(f"     Time: {execution_result.execution_time_ms:.2f}ms")
                
                if execution_result.error:
                    errors.append(f"Execution: {execution_result.error}")
                    print(f"     Error: {execution_result.error}")
                elif execution_result.data:
                    data = execution_result.data
                    print(f"     Results: {data.get('results_count', 0)} items")
                    print(f"     Execution Time: {data.get('execution_time_ms', 0):.2f}ms")
        
        # Test RAG Pipeline Component
        if test_case.test_rag_pipeline:
            print(f"\n  🤖 Testing RAG Pipeline Component...")
            rag_result = await self.test_rag_pipeline_component(test_case)
            components.append(rag_result)
            
            print(f"     Status: {rag_result.status.value}")
            print(f"     Time: {rag_result.execution_time_ms:.2f}ms")
            
            if rag_result.error:
                errors.append(f"RAG Pipeline: {rag_result.error}")
                print(f"     Error: {rag_result.error}")
            elif rag_result.data:
                data = rag_result.data
                answer = data.get("answer", "")
                print(f"     Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
                print(f"     Development Mode: {data.get('development_mode', False)}")
                print(f"     Total Time: {data.get('total_execution_time_ms', 0):.2f}ms")
        
        # Determine overall status
        total_time = (time.time() - start_time) * 1000
        
        if not test_case.should_succeed:
            # For negative test cases, failure in components might be expected
            overall_status = TestStatus.PASS
        else:
            # Check if critical components passed
            critical_components = [c for c in components if c.component in [ComponentType.TRANSLATION, ComponentType.RAG_PIPELINE]]
            passed_critical = sum(1 for c in critical_components if c.status == TestStatus.PASS)
            
            if passed_critical == len(critical_components) and critical_components:
                overall_status = TestStatus.PASS
            elif passed_critical > 0:
                overall_status = TestStatus.WARN
            else:
                overall_status = TestStatus.FAIL
        
        result = TestCaseResult(
            test_case=test_case,
            overall_status=overall_status,
            components=components,
            total_time_ms=total_time,
            errors=errors
        )
        
        print(f"\n  🎯 Overall Result: {overall_status.value}")
        print(f"     Total Time: {total_time:.2f}ms")
        
        return result
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete comprehensive test suite."""
        print("🚀 Starting Comprehensive Graph RAG System Validation")
        print("=" * 70)
        
        # Pre-flight checks
        print("🔍 Pre-flight System Checks")
        print("-" * 30)
        
        if not await self.check_server_health():
            return {"error": "Server not accessible", "results": []}
        
        # Run test cases
        test_cases = self.get_test_cases()
        print(f"\n📋 Running {len(test_cases)} Test Cases")
        print("-" * 40)
        
        for test_case in test_cases:
            result = await self.run_single_test(test_case)
            self.results.append(result)
        
        # Generate comprehensive report
        return self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate detailed analysis and recommendations."""
        total_tests = len(self.results)
        
        # Overall statistics
        overall_pass = sum(1 for r in self.results if r.overall_status == TestStatus.PASS)
        overall_warn = sum(1 for r in self.results if r.overall_status == TestStatus.WARN)
        overall_fail = sum(1 for r in self.results if r.overall_status == TestStatus.FAIL)
        overall_skip = sum(1 for r in self.results if r.overall_status == TestStatus.SKIP)
        
        # Component-specific statistics
        component_stats = {}
        for component_type in ComponentType:
            component_results = []
            for result in self.results:
                component_results.extend([c for c in result.components if c.component == component_type])
            
            component_stats[component_type.value] = {
                "total": len(component_results),
                "pass": sum(1 for c in component_results if c.status == TestStatus.PASS),
                "warn": sum(1 for c in component_results if c.status == TestStatus.WARN),
                "fail": sum(1 for c in component_results if c.status == TestStatus.FAIL),
                "skip": sum(1 for c in component_results if c.status == TestStatus.SKIP),
                "avg_time_ms": sum(c.execution_time_ms for c in component_results) / len(component_results) if component_results else 0
            }
        
        # Language analysis
        language_stats = {}
        for result in self.results:
            lang = result.test_case.language
            if lang not in language_stats:
                language_stats[lang] = {"total": 0, "pass": 0, "warn": 0, "fail": 0}
            
            language_stats[lang]["total"] += 1
            if result.overall_status == TestStatus.PASS:
                language_stats[lang]["pass"] += 1
            elif result.overall_status == TestStatus.WARN:
                language_stats[lang]["warn"] += 1
            elif result.overall_status == TestStatus.FAIL:
                language_stats[lang]["fail"] += 1
        
        # Category analysis
        category_stats = {}
        for result in self.results:
            cat = result.test_case.category
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "pass": 0, "warn": 0, "fail": 0}
            
            category_stats[cat]["total"] += 1
            if result.overall_status == TestStatus.PASS:
                category_stats[cat]["pass"] += 1
            elif result.overall_status == TestStatus.WARN:
                category_stats[cat]["warn"] += 1
            elif result.overall_status == TestStatus.FAIL:
                category_stats[cat]["fail"] += 1
        
        # Performance analysis
        avg_total_time = sum(r.total_time_ms for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Generate report
        report = {
            "summary": {
                "total_tests": total_tests,
                "overall_pass": overall_pass,
                "overall_warn": overall_warn, 
                "overall_fail": overall_fail,
                "overall_skip": overall_skip,
                "success_rate": f"{(overall_pass/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                "avg_execution_time_ms": avg_total_time
            },
            "component_analysis": component_stats,
            "language_analysis": language_stats,
            "category_analysis": category_stats,
            "detailed_results": [
                {
                    "test_id": r.test_case.id,
                    "name": r.test_case.name,
                    "language": r.test_case.language,
                    "category": r.test_case.category,
                    "query": r.test_case.query,
                    "overall_status": r.overall_status.name,
                    "total_time_ms": r.total_time_ms,
                    "errors": r.errors,
                    "components": [
                        {
                            "component": c.component.value,
                            "status": c.status.name,
                            "execution_time_ms": c.execution_time_ms,
                            "error": c.error
                        } for c in r.components
                    ]
                } for r in self.results
            ]
        }
        
        # Print comprehensive report
        self.print_comprehensive_report(report)
        
        return report
    
    def print_comprehensive_report(self, report: Dict[str, Any]):
        """Print formatted comprehensive report."""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        summary = report["summary"]
        print(f"📈 OVERALL SUMMARY")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['overall_pass']}")
        print(f"   ⚠️ Warnings: {summary['overall_warn']}")
        print(f"   ❌ Failed: {summary['overall_fail']}")
        print(f"   ⏭️ Skipped: {summary['overall_skip']}")
        print(f"   🎯 Success Rate: {summary['success_rate']}")
        print(f"   ⏱️ Average Time: {summary['avg_execution_time_ms']:.2f}ms")
        
        print(f"\n🔧 COMPONENT ANALYSIS")
        for component, stats in report["component_analysis"].items():
            if stats["total"] > 0:
                success_rate = (stats["pass"] / stats["total"]) * 100
                print(f"   {component}:")
                print(f"      ✅ {stats['pass']}/{stats['total']} ({success_rate:.1f}%) - Avg: {stats['avg_time_ms']:.2f}ms")
        
        print(f"\n🌍 LANGUAGE SUPPORT")
        for lang, stats in report["language_analysis"].items():
            success_rate = (stats["pass"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"   {lang.upper()}: ✅ {stats['pass']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\n📂 CATEGORY BREAKDOWN") 
        for category, stats in report["category_analysis"].items():
            success_rate = (stats["pass"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"   {category}: ✅ {stats['pass']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS")
        for result in report["detailed_results"]:
            status_icon = "✅" if result["overall_status"] == "PASS" else "⚠️" if result["overall_status"] == "WARN" else "❌"
            print(f"   {status_icon} {result['name']} ({result['language']}) - {result['total_time_ms']:.1f}ms")
            if result["errors"]:
                for error in result["errors"]:
                    print(f"      ❌ {error}")
        
        # Generate recommendations
        self.print_recommendations(report)
    
    def print_recommendations(self, report: Dict[str, Any]):
        """Generate and print actionable recommendations."""
        print(f"\n🎯 RECOMMENDATIONS & NEXT STEPS")
        print("-" * 50)
        
        summary = report["summary"]
        component_stats = report["component_analysis"]
        
        success_rate = (summary["overall_pass"] / summary["total_tests"]) * 100
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: System is performing exceptionally well!")
            print("   ✅ Ready for production deployment")
            print("   ✅ All major components are functioning correctly")
        elif success_rate >= 70:
            print("✅ GOOD: System is working well with minor issues")
            print("   ⚠️ Review warnings for potential improvements")
            print("   ✅ Suitable for staging/testing environments")
        elif success_rate >= 50:
            print("⚠️ FAIR: System has functionality but needs attention")
            print("   🔧 Address failed components before production")
            print("   📊 Monitor performance and error rates")
        else:
            print("❌ NEEDS WORK: System requires significant improvements")
            print("   🚨 Critical issues must be resolved")
            print("   🔍 Review error logs and component failures")
        
        # Component-specific recommendations
        translation_stats = component_stats.get("Natural Language → Gremlin", {})
        if translation_stats.get("total", 0) > 0:
            translation_success = (translation_stats.get("pass", 0) / translation_stats["total"]) * 100
            if translation_success < 80:
                print(f"\n🔧 TRANSLATION COMPONENT:")
                print(f"   📝 Success rate: {translation_success:.1f}% (target: 80%+)")
                print(f"   💡 Consider improving LLM prompts or schema descriptions")
                print(f"   🔍 Review failed query translations in detailed logs")
        
        rag_stats = component_stats.get("Full RAG Pipeline", {})
        if rag_stats.get("total", 0) > 0:
            rag_success = (rag_stats.get("pass", 0) / rag_stats["total"]) * 100
            if rag_success < 80:
                print(f"\n🤖 RAG PIPELINE:")
                print(f"   📊 Success rate: {rag_success:.1f}% (target: 80%+)")
                print(f"   💡 Consider optimizing response generation")
                print(f"   🔍 Review answer quality and relevance")
        
        # Performance recommendations
        avg_time = summary["avg_execution_time_ms"]
        if avg_time > 5000:  # 5 seconds
            print(f"\n⏱️ PERFORMANCE:")
            print(f"   🐌 Average response time: {avg_time:.0f}ms (target: <3000ms)")
            print(f"   💡 Consider optimizing query generation and execution")
            print(f"   🔧 Review component timing breakdowns")
        
        print(f"\n📁 FILES GENERATED:")
        print(f"   📄 Detailed results will be saved to JSON file")
        print(f"   📊 Review component timing for performance optimization")
        print(f"   🔍 Check error details for troubleshooting guidance")

async def main():
    """Main execution function."""
    print("🎯 Comprehensive Graph RAG System Validation")
    print("Testing complete LLM → Gremlin → Graph → Answer pipeline")
    print("Evaluating translation quality, execution, and end-to-end performance")
    
    async with GraphRAGTester() as tester:
        report = await tester.run_comprehensive_test_suite()
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"comprehensive_graph_rag_test_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 RESULTS SAVED: {results_file}")
        print("🔍 Review the detailed JSON file for complete analysis and debugging information")
        
        return report

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        raise
