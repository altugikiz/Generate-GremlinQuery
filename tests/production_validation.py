#!/usr/bin/env python3
"""
Production Mode Validation Script

This script validates that your Graph RAG system is properly configured for production:
1. Verifies environment variables are set correctly
2. Tests Gremlin connection and query execution
3. Validates LLM services
4. Confirms no development mode fallbacks
5. Tests complete RAG pipeline functionality

Usage:
    python production_validation.py

This should be run BEFORE deploying to production to ensure all systems work correctly.
"""

import asyncio
import os
import json
import httpx
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

class ValidationStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"
    INFO = "ℹ️ INFO"

@dataclass
class ValidationResult:
    component: str
    test: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None

class ProductionValidator:
    """Comprehensive production readiness validator."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results: List[ValidationResult] = []
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def add_result(self, component: str, test: str, status: ValidationStatus, message: str, details: Dict[str, Any] = None):
        """Add validation result."""
        self.results.append(ValidationResult(component, test, status, message, details))
        print(f"{status.value} {component}: {test} - {message}")
    
    async def validate_environment_config(self):
        """Validate environment configuration."""
        print("\n🔧 VALIDATING ENVIRONMENT CONFIGURATION")
        print("=" * 60)
        
        # Load environment variables
        load_dotenv()
        
        # Critical environment variables
        required_vars = {
            "DEVELOPMENT_MODE": {"expected": "false", "critical": True},
            "GREMLIN_URL": {"expected": "wss://", "critical": True},
            "GREMLIN_KEY": {"expected": "", "critical": True},
            "GREMLIN_DATABASE": {"expected": "", "critical": True},
            "GREMLIN_GRAPH": {"expected": "", "critical": True},
            "GEMINI_API_KEY": {"expected": "", "critical": True},
            "HUGGINGFACE_API_TOKEN": {"expected": "", "critical": True}
        }
        
        for var_name, config in required_vars.items():
            value = os.getenv(var_name, "")
            
            if not value:
                status = ValidationStatus.FAIL if config["critical"] else ValidationStatus.WARN
                self.add_result("Environment", f"{var_name}", status, "Not set or empty")
            elif var_name == "DEVELOPMENT_MODE":
                if value.lower() == "false":
                    self.add_result("Environment", var_name, ValidationStatus.PASS, f"Set to '{value}' (production mode)")
                else:
                    self.add_result("Environment", var_name, ValidationStatus.FAIL, f"Set to '{value}' - MUST be 'false' for production")
            elif var_name == "GREMLIN_URL" and config["expected"]:
                if value.startswith(config["expected"]):
                    self.add_result("Environment", var_name, ValidationStatus.PASS, f"Valid Gremlin URL format")
                else:
                    self.add_result("Environment", var_name, ValidationStatus.WARN, f"URL format may be incorrect")
            else:
                self.add_result("Environment", var_name, ValidationStatus.PASS, f"Set (length: {len(value)})")
    
    async def validate_server_startup(self):
        """Validate server can start and initialize all services."""
        print("\n🚀 VALIDATING SERVER STARTUP")
        print("=" * 60)
        
        try:
            # Test if server is running
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            
            if response.status_code == 200:
                self.add_result("Server", "Health Check", ValidationStatus.PASS, "Server is running and healthy")
                
                # Check health response details
                health_data = response.json()
                if "status" in health_data:
                    if health_data["status"] == "healthy":
                        self.add_result("Server", "Health Status", ValidationStatus.PASS, "All services healthy")
                    else:
                        self.add_result("Server", "Health Status", ValidationStatus.WARN, f"Status: {health_data['status']}")
                
                # Check for development mode indicators
                if "development_mode" in health_data:
                    if health_data["development_mode"]:
                        self.add_result("Server", "Development Mode", ValidationStatus.FAIL, "Server indicates development mode is enabled")
                    else:
                        self.add_result("Server", "Development Mode", ValidationStatus.PASS, "Production mode confirmed")
                
            else:
                self.add_result("Server", "Health Check", ValidationStatus.FAIL, f"Server returned status {response.status_code}")
                
        except httpx.ConnectError:
            self.add_result("Server", "Connection", ValidationStatus.FAIL, "Cannot connect to server - is it running?")
        except Exception as e:
            self.add_result("Server", "Health Check", ValidationStatus.FAIL, f"Error: {str(e)}")
    
    async def validate_gremlin_functionality(self):
        """Validate Gremlin query generation and execution."""
        print("\n🔍 VALIDATING GREMLIN FUNCTIONALITY")
        print("=" * 60)
        
        # Test 1: Natural language to Gremlin translation
        try:
            translation_request = {
                "prompt": "Show me all hotels",
                "include_explanation": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/gremlin",
                json=translation_request
            )
            
            if response.status_code == 200:
                data = response.json()
                gremlin_query = data.get("gremlin_query", "")
                
                if gremlin_query and gremlin_query.startswith("g."):
                    self.add_result("Gremlin", "Query Translation", ValidationStatus.PASS, f"Valid Gremlin query generated")
                    
                    # Test 2: Query execution
                    await self._test_gremlin_execution(gremlin_query)
                else:
                    self.add_result("Gremlin", "Query Translation", ValidationStatus.FAIL, f"Invalid or empty Gremlin query: {gremlin_query}")
            else:
                self.add_result("Gremlin", "Query Translation", ValidationStatus.FAIL, f"Translation failed with status {response.status_code}")
                
        except Exception as e:
            self.add_result("Gremlin", "Query Translation", ValidationStatus.FAIL, f"Error: {str(e)}")
    
    async def _test_gremlin_execution(self, gremlin_query: str):
        """Test Gremlin query execution against real database."""
        try:
            execution_request = {"query": gremlin_query}
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/execute",
                json=execution_request
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                execution_time = data.get("execution_time_ms", 0)
                
                if isinstance(results, list):
                    self.add_result("Gremlin", "Query Execution", ValidationStatus.PASS, 
                                  f"Query executed successfully, returned {len(results)} results in {execution_time:.2f}ms")
                    
                    # Check if results look like real data (not development mode responses)
                    if results and not any("development mode" in str(result).lower() for result in results):
                        self.add_result("Gremlin", "Real Data", ValidationStatus.PASS, "Results appear to be real database data")
                    elif not results:
                        self.add_result("Gremlin", "Real Data", ValidationStatus.WARN, "No results returned - database may be empty")
                    else:
                        self.add_result("Gremlin", "Real Data", ValidationStatus.FAIL, "Results contain development mode indicators")
                else:
                    self.add_result("Gremlin", "Query Execution", ValidationStatus.WARN, f"Unexpected result format: {type(results)}")
                    
            elif response.status_code == 503:
                self.add_result("Gremlin", "Query Execution", ValidationStatus.FAIL, "Database connection not available (503)")
            else:
                self.add_result("Gremlin", "Query Execution", ValidationStatus.FAIL, f"Execution failed with status {response.status_code}")
                
        except Exception as e:
            self.add_result("Gremlin", "Query Execution", ValidationStatus.FAIL, f"Error: {str(e)}")
    
    async def validate_rag_pipeline(self):
        """Validate complete RAG pipeline functionality."""
        print("\n🧠 VALIDATING RAG PIPELINE")
        print("=" * 60)
        
        test_queries = [
            "Show me hotels with poor service ratings",
            "What are common cleanliness complaints?",
            "Find VIP guest issues"
        ]
        
        for i, query in enumerate(test_queries, 1):
            await self._test_rag_query(query, f"Test {i}")
    
    async def _test_rag_query(self, query: str, test_name: str):
        """Test a single RAG pipeline query."""
        try:
            rag_request = {
                "query": query,
                "include_gremlin_query": True,
                "include_semantic_chunks": True,
                "max_graph_results": 5,
                "max_semantic_results": 3
            }
            
            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/api/v1/semantic/ask",
                json=rag_request
            )
            execution_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                gremlin_query = data.get("gremlin_query", "")
                
                # Check for development mode indicators
                if "development mode" in answer.lower() or "I'm running in development mode" in answer:
                    self.add_result("RAG Pipeline", test_name, ValidationStatus.FAIL, "Response contains development mode messages")
                elif answer and len(answer.strip()) > 20:  # Reasonable answer length
                    self.add_result("RAG Pipeline", test_name, ValidationStatus.PASS, 
                                  f"Generated proper answer ({len(answer)} chars) in {execution_time:.2f}ms")
                    
                    # Validate Gremlin query was generated
                    if gremlin_query and gremlin_query.startswith("g."):
                        self.add_result("RAG Pipeline", f"{test_name} - Gremlin", ValidationStatus.PASS, "Valid Gremlin query generated")
                    else:
                        self.add_result("RAG Pipeline", f"{test_name} - Gremlin", ValidationStatus.WARN, "No valid Gremlin query in response")
                else:
                    self.add_result("RAG Pipeline", test_name, ValidationStatus.WARN, f"Short or empty answer: '{answer[:100]}...'")
            else:
                self.add_result("RAG Pipeline", test_name, ValidationStatus.FAIL, f"Request failed with status {response.status_code}")
                
        except Exception as e:
            self.add_result("RAG Pipeline", test_name, ValidationStatus.FAIL, f"Error: {str(e)}")
    
    async def validate_error_handling(self):
        """Validate proper error handling in production mode."""
        print("\n🚨 VALIDATING ERROR HANDLING")
        print("=" * 60)
        
        # Test 1: Invalid Gremlin query
        try:
            invalid_request = {"query": "INVALID GREMLIN SYNTAX"}
            response = await self.client.post(f"{self.base_url}/api/v1/semantic/execute", json=invalid_request)
            
            if response.status_code >= 400:
                self.add_result("Error Handling", "Invalid Gremlin", ValidationStatus.PASS, f"Properly rejected invalid query (status {response.status_code})")
            else:
                self.add_result("Error Handling", "Invalid Gremlin", ValidationStatus.WARN, f"Unexpected success with invalid query")
                
        except Exception as e:
            self.add_result("Error Handling", "Invalid Gremlin", ValidationStatus.FAIL, f"Error: {str(e)}")
        
        # Test 2: Malformed request
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/semantic/ask", json={"invalid": "request"})
            
            if response.status_code >= 400:
                self.add_result("Error Handling", "Malformed Request", ValidationStatus.PASS, f"Properly rejected malformed request (status {response.status_code})")
            else:
                self.add_result("Error Handling", "Malformed Request", ValidationStatus.WARN, f"Unexpected success with malformed request")
                
        except Exception as e:
            self.add_result("Error Handling", "Malformed Request", ValidationStatus.FAIL, f"Error: {str(e)}")
    
    def generate_summary_report(self):
        """Generate final validation summary."""
        print("\n" + "=" * 80)
        print("🎯 PRODUCTION VALIDATION SUMMARY")
        print("=" * 80)
        
        # Count results by status
        counts = {status: 0 for status in ValidationStatus}
        for result in self.results:
            counts[result.status] += 1
        
        print(f"Total Tests: {len(self.results)}")
        for status, count in counts.items():
            if count > 0:
                print(f"{status.value}: {count}")
        
        # Check for critical failures
        failures = [r for r in self.results if r.status == ValidationStatus.FAIL]
        critical_failures = [
            r for r in failures 
            if "DEVELOPMENT_MODE" in r.test or "Connection" in r.test or "development mode" in r.message.lower()
        ]
        
        print("\n" + "=" * 80)
        
        if critical_failures:
            print("❌ PRODUCTION READINESS: FAILED")
            print("\nCritical Issues Found:")
            for failure in critical_failures:
                print(f"  • {failure.component}: {failure.test} - {failure.message}")
            print("\n🚨 DO NOT DEPLOY TO PRODUCTION until these issues are resolved!")
            
        elif failures:
            print("⚠️ PRODUCTION READINESS: PARTIAL")
            print("\nNon-Critical Issues Found:")
            for failure in failures:
                print(f"  • {failure.component}: {failure.test} - {failure.message}")
            print("\n💡 Consider resolving these issues before production deployment.")
            
        else:
            print("✅ PRODUCTION READINESS: PASSED")
            print("\n🎉 System is ready for production deployment!")
            print("\nFinal Checklist:")
            print("  ✅ Environment configured correctly")
            print("  ✅ Server starts and initializes all services")
            print("  ✅ Gremlin queries generate and execute against real database")
            print("  ✅ RAG pipeline functions without development mode fallbacks")
            print("  ✅ Error handling works correctly")
        
        print("\n" + "=" * 80)
        
        return len(critical_failures) == 0

async def main():
    """Run complete production validation."""
    print("🎯 Graph RAG Production Mode Validation")
    print("=" * 80)
    print("This script validates your system is ready for production deployment.")
    print("Ensure the server is running before starting validation.")
    print("=" * 80)
    
    async with ProductionValidator() as validator:
        # Run all validation tests
        await validator.validate_environment_config()
        await validator.validate_server_startup()
        await validator.validate_gremlin_functionality()
        await validator.validate_rag_pipeline()
        await validator.validate_error_handling()
        
        # Generate final report
        is_production_ready = validator.generate_summary_report()
        
        return 0 if is_production_ready else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
