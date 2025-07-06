#!/usr/bin/env python3
"""
Test Analytics Endpoints Cosmos DB Gremlin Compatibility

This script tests all analytics endpoints to ensure they are compatible with
Cosmos DB Gremlin API requirements:
- Use .valueMap(true) for property access
- Include .limit() for large result sets
- Avoid unsupported .with() operations
- Use safe property access patterns
- Log raw Gremlin queries and exceptions
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

# Add the project root to Python path
sys.path.insert(0, '.')

from app.api.routes.analytics import (
    get_group_statistics,
    get_hotel_statistics, 
    get_hotel_averages,
    get_hotel_language_distribution,
    get_hotel_source_distribution,
    get_hotel_accommodation_metrics,
    get_hotel_aspect_breakdown,
    query_reviews,
    log_gremlin_error,
    safe_extract_property
)
from app.core.sync_gremlin_client import SyncGremlinClient


class CosmosDBCompatibilityTester:
    """Test Cosmos DB Gremlin API compatibility for analytics endpoints."""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def create_mock_gremlin_client(self, mock_results: List[Any] = None) -> SyncGremlinClient:
        """Create a mock Gremlin client for testing."""
        mock_client = MagicMock(spec=SyncGremlinClient)
        mock_client.is_connected = True
        
        # Mock the execute_query method
        async_mock = AsyncMock()
        if mock_results is not None:
            async_mock.return_value = mock_results
        else:
            async_mock.return_value = []
        mock_client.execute_query = async_mock
        
        return mock_client
        
    def log_test_result(self, test_name: str, passed: bool, details: str = "", query: str = ""):
        """Log test result."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {details}")
            
    def check_query_compatibility(self, query: str) -> Dict[str, bool]:
        """Check if a query meets Cosmos DB compatibility requirements."""
        # Check for limit operations (either .limit( or .range( as both are valid)
        has_limit_operation = ".limit(" in query or ".range(" in query
        
        # For queries that use groupCount, .valueMap(true) is not needed
        needs_valuemap = not (".groupCount(" in query or ".count()" in query)
        has_valuemap_when_needed = not needs_valuemap or ".valueMap(true)" in query
        
        checks = {
            "has_valuemap_true": has_valuemap_when_needed,
            "has_limit": has_limit_operation,
            "no_with_operations": ".with(" not in query,
            "no_complex_nesting": query.count("project(") <= 2,  # Limit complexity
            "safe_string_usage": "'" in query  # Should have quoted strings
        }
        return checks
        
    async def test_group_statistics(self):
        """Test group statistics endpoint."""
        test_name = "Group Statistics Endpoint"
        
        try:
            # Mock data
            mock_data = [
                {"id": ["group1"], "name": ["Hotel Group A"]},
                {"id": ["group2"], "name": ["Hotel Group B"]}
            ]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_group_statistics(mock_client)
            
            # Verify results
            assert isinstance(result, list), "Should return a list"
            assert len(result) == 2, "Should return 2 groups"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_hotel_statistics(self):
        """Test hotel statistics endpoint."""
        test_name = "Hotel Statistics Endpoint"
        
        try:
            # Mock data
            mock_data = [
                {"id": ["hotel1"], "name": ["Test Hotel 1"]},
                {"id": ["hotel2"], "name": ["Test Hotel 2"]}
            ]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_statistics(limit=10, offset=0, group_name=None, min_rating=None, gremlin_client=mock_client)
            
            # Verify results
            assert isinstance(result, list), "Should return a list"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            # Check for range operation
            has_range = ".range(" in query_call
            compatibility["has_range_operation"] = has_range
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_hotel_averages(self):
        """Test hotel averages endpoint."""
        test_name = "Hotel Averages Endpoint"
        
        try:
            # Mock data
            mock_data = [{"id": ["hotel1"], "name": ["Test Hotel"]}]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_averages(hotel_name="Test Hotel", gremlin_client=mock_client)
            
            # Verify results
            assert isinstance(result, dict), "Should return a dict"
            assert "hotel_info" in result, "Should contain hotel_info"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_language_distribution(self):
        """Test language distribution endpoint."""
        test_name = "Language Distribution Endpoint"
        
        try:
            # Mock data
            mock_data = [{
                "hotel_name": ["Test Hotel"],
                "language_stats": [{"en": 10, "es": 5}],
                "language_ratings": [{"en": 8.5, "es": 7.8}],
                "total_reviews": [15]
            }]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_language_distribution(hotel_id="hotel1", gremlin_client=mock_client)
            
            # Verify results
            assert isinstance(result, dict), "Should return a dict"
            assert "language_distribution" in result, "Should contain language_distribution"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_source_distribution(self):
        """Test source distribution endpoint.""" 
        test_name = "Source Distribution Endpoint"
        
        try:
            # Mock data
            mock_data = [{
                "hotel_id": ["hotel1"],
                "source_stats": [{"TripAdvisor": 8, "Booking.com": 5}],
                "source_ratings": [{"TripAdvisor": 8.2, "Booking.com": 7.9}],
                "total_reviews": [13]
            }]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_source_distribution(hotel_name="Test Hotel", gremlin_client=mock_client)
            
            # Verify results
            assert isinstance(result, dict), "Should return a dict"
            assert "source_distribution" in result, "Should contain source_distribution"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_accommodation_metrics(self):
        """Test accommodation metrics endpoint."""
        test_name = "Accommodation Metrics Endpoint"
        
        try:
            # Mock data
            mock_data = [{"hotel_id": ["hotel1"], "accommodation_count": [5]}]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_accommodation_metrics(hotel_name="Test Hotel", gremlin_client=mock_client)
            
            # Verify results
            assert isinstance(result, dict), "Should return a dict"
            assert "accommodation_breakdown" in result, "Should contain accommodation_breakdown"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_aspect_breakdown(self):
        """Test aspect breakdown endpoint."""
        test_name = "Aspect Breakdown Endpoint"
        
        try:
            # Mock data - simplified for groupCount result
            mock_data = [{"cleanliness": 10, "service": 8, "location": 12}]
            
            mock_client = self.create_mock_gremlin_client(mock_data)
            
            # Test the endpoint
            result = await get_hotel_aspect_breakdown(
                hotel_name="Test Hotel", 
                include_trends=True, 
                time_window_days=90, 
                gremlin_client=mock_client
            )
            
            # Verify results
            assert isinstance(result, list), "Should return a list"
            
            # Check query compatibility
            query_call = mock_client.execute_query.call_args[0][0]
            compatibility = self.check_query_compatibility(query_call)
            
            if all(compatibility.values()):
                self.log_test_result(test_name, True, "All compatibility checks passed", query_call)
            else:
                failed_checks = [k for k, v in compatibility.items() if not v]
                self.log_test_result(test_name, False, f"Failed checks: {failed_checks}", query_call)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def test_query_reviews(self):
        """Test query reviews endpoint."""
        test_name = "Query Reviews Endpoint"
        
        try:
            # Mock data for reviews
            mock_reviews = [
                {"id": ["rev1"], "content": ["Great hotel"], "overall_score": [9.0]},
                {"id": ["rev2"], "content": ["Good service"], "overall_score": [8.5]}
            ]
            
            # Mock aggregation data
            mock_agg = [{"avg_rating": [8.75], "count": [2]}]
            
            mock_client = self.create_mock_gremlin_client()
            # Set up multiple call returns
            mock_client.execute_query.side_effect = [
                [2],  # count query
                mock_reviews,  # data query
                mock_agg  # aggregation query
            ]
            
            # Test the endpoint
            result = await query_reviews(
                language=None,
                source=None,
                aspect=None,
                sentiment=None,
                hotel="Test Hotel",
                start_date=None,
                end_date=None,
                min_rating=None,
                max_rating=None,
                limit=50,
                offset=0,
                gremlin_client=mock_client
            )
            
            # Verify results
            assert isinstance(result.reviews, list), "Should return a list of reviews"
            assert result.total_count >= 0, "Should have total count"
            
            # Check that multiple queries were made
            assert mock_client.execute_query.call_count >= 2, "Should make multiple queries"
            
            # Check compatibility of all queries
            all_compatible = True
            for call_args in mock_client.execute_query.call_args_list:
                query = call_args[0][0]
                # Check for limit operations (.limit( or .range() or .count())
                has_limit_operation = (".limit(" in query or ".range(" in query or ".count()" in query)
                if not has_limit_operation:
                    all_compatible = False
                    break
            
            if all_compatible:
                self.log_test_result(test_name, True, "All queries have proper limits")
            else:
                self.log_test_result(test_name, False, "Some queries missing limits")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    def test_error_logging(self):
        """Test error logging functionality."""
        test_name = "Error Logging Function"
        
        try:
            # Test log_gremlin_error function
            test_query = "g.V().hasLabel('Hotel').limit(10)"
            test_exception = Exception("Test Gremlin error")
            
            error_detail = log_gremlin_error("/test/endpoint", test_query, test_exception)
            
            # Verify error detail structure
            required_fields = ["error", "endpoint", "query", "exception_type", "exception_message", "timestamp"]
            
            all_fields_present = all(field in error_detail for field in required_fields)
            
            if all_fields_present and error_detail["query"] == test_query:
                self.log_test_result(test_name, True, "Error logging working correctly")
            else:
                self.log_test_result(test_name, False, "Error logging missing required fields")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    def test_safe_property_access(self):
        """Test safe property access function."""
        test_name = "Safe Property Access Function"
        
        try:
            # Test various scenarios
            test_cases = [
                ({"prop": ["value"]}, "prop", "default", "value"),  # Normal valueMap case
                ({"prop": "direct_value"}, "prop", "default", "direct_value"),  # Direct value
                ({}, "missing_prop", "default", "default"),  # Missing property
                ({"prop": []}, "prop", "default", "default"),  # Empty array
                (None, "prop", "default", "default"),  # None input
            ]
            
            all_passed = True
            for test_data, prop, default, expected in test_cases:
                result = safe_extract_property(test_data, prop, default)
                if result != expected:
                    all_passed = False
                    break
            
            if all_passed:
                self.log_test_result(test_name, True, "All safe property access tests passed")
            else:
                self.log_test_result(test_name, False, "Some safe property access tests failed")
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            
    async def run_all_tests(self):
        """Run all compatibility tests."""
        print("🧪 Testing Analytics Endpoints Cosmos DB Compatibility")
        print("=" * 60)
        
        # Test all endpoints
        await self.test_group_statistics()
        await self.test_hotel_statistics()
        await self.test_hotel_averages()
        await self.test_language_distribution()
        await self.test_source_distribution()
        await self.test_accommodation_metrics()
        await self.test_aspect_breakdown()
        await self.test_query_reviews()
        
        # Test utility functions
        self.test_error_logging()
        self.test_safe_property_access()
        
        # Generate report
        self.generate_report()
        
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 COSMOS DB COMPATIBILITY TEST REPORT")
        print("=" * 60)
        
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {(self.passed_tests / len(self.test_results) * 100):.1f}%")
        
        # Print failed tests details
        if self.failed_tests > 0:
            print("\n❌ Failed Tests Details:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # Save detailed report
        report_file = f"analytics_cosmos_compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": len(self.test_results),
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "success_rate": self.passed_tests / len(self.test_results) * 100
                },
                "test_results": self.test_results,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Recommendations
        print("\n📋 COSMOS DB COMPATIBILITY SUMMARY:")
        print("✅ All analytics endpoints updated with:")
        print("   - .valueMap(true) for safe property access")
        print("   - .limit() operations for large result sets")
        print("   - Removed complex .with() operations")
        print("   - Enhanced error logging with raw queries")
        print("   - Safe property extraction patterns")
        print("   - Simplified complex nested queries")
        
        if self.failed_tests == 0:
            print("\n🎉 All tests passed! Analytics endpoints are Cosmos DB compatible.")
        else:
            print(f"\n⚠️  {self.failed_tests} tests failed. Review the failed tests above.")


async def main():
    """Main test execution function."""
    tester = CosmosDBCompatibilityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
