#!/usr/bin/env python3
"""
Standalone Gremlin Connection Test Script

This script tests Gremlin connectivity independently of FastAPI to help diagnose
connection issues during application startup.

Usage:
    python test_gremlin_standalone.py

Environment Variables Required:
    - GREMLIN_URL: Cosmos DB Gremlin endpoint URL
    - GREMLIN_DATABASE: Database name
    - GREMLIN_GRAPH: Graph name
    - GREMLIN_USERNAME: Username (usually /dbs/{db}/colls/{graph})
    - GREMLIN_KEY: Primary or secondary key
    - GREMLIN_TRAVERSAL_SOURCE: Traversal source (default: g)
"""

import asyncio
import os
import sys
import time
from typing import Optional
from loguru import logger
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.config.settings import get_settings


class GremlinConnectionTester:
    """Comprehensive Gremlin connection testing utility."""
    
    def __init__(self):
        """Initialize the tester with environment-based configuration."""
        self.settings = get_settings()
        self.client: Optional[SchemaAwareGremlinClient] = None
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str, duration: float = 0):
        """Log and store test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        logger.info(f"{status} {test_name}: {message}{duration_str}")
        
    def print_environment_info(self):
        """Print current environment configuration (without sensitive data)."""
        logger.info("🔍 Environment Configuration:")
        logger.info(f"   GREMLIN_URL: {self.settings.gremlin_url}")
        logger.info(f"   GREMLIN_DATABASE: {self.settings.gremlin_database}")
        logger.info(f"   GREMLIN_GRAPH: {self.settings.gremlin_graph}")
        logger.info(f"   GREMLIN_USERNAME: {self.settings.gremlin_username}")
        logger.info(f"   GREMLIN_KEY: {'*' * (len(self.settings.gremlin_key) - 4) + self.settings.gremlin_key[-4:] if self.settings.gremlin_key else 'NOT SET'}")
        logger.info(f"   GREMLIN_TRAVERSAL_SOURCE: {self.settings.gremlin_traversal_source}")
        logger.info(f"   DEVELOPMENT_MODE: {self.settings.development_mode}")
        
    async def test_environment_variables(self):
        """Test that all required environment variables are set."""
        logger.info("🧪 Testing Environment Variables...")
        
        required_vars = [
            ("GREMLIN_URL", self.settings.gremlin_url),
            ("GREMLIN_DATABASE", self.settings.gremlin_database),
            ("GREMLIN_GRAPH", self.settings.gremlin_graph),
            ("GREMLIN_USERNAME", self.settings.gremlin_username),
            ("GREMLIN_KEY", self.settings.gremlin_key),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
                
        if missing_vars:
            self.log_test_result(
                "Environment Variables",
                False,
                f"Missing required variables: {', '.join(missing_vars)}"
            )
            return False
        else:
            self.log_test_result(
                "Environment Variables",
                True,
                "All required environment variables are set"
            )
            return True
            
    async def test_client_creation(self):
        """Test creating the Gremlin client instance."""
        logger.info("🧪 Testing Client Creation...")
        
        start_time = time.time()
        try:
            self.client = SchemaAwareGremlinClient(
                url=self.settings.gremlin_url,
                database=self.settings.gremlin_database,
                graph=self.settings.gremlin_graph,
                username=self.settings.gremlin_username,
                password=self.settings.gremlin_key,
                traversal_source=self.settings.gremlin_traversal_source
            )
            duration = time.time() - start_time
            self.log_test_result(
                "Client Creation",
                True,
                "SchemaAwareGremlinClient created successfully",
                duration
            )
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Client Creation",
                False,
                f"Failed to create client: {e}",
                duration
            )
            return False
            
    async def test_connection(self):
        """Test establishing connection to Gremlin."""
        if not self.client:
            self.log_test_result(
                "Connection Test",
                False,
                "No client available (client creation failed)"
            )
            return False
            
        logger.info("🧪 Testing Gremlin Connection...")
        
        start_time = time.time()
        try:
            await self.client.connect()
            duration = time.time() - start_time
            self.log_test_result(
                "Connection Test",
                True,
                f"Connected to {self.settings.gremlin_url}",
                duration
            )
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Connection Test",
                False,
                f"Connection failed: {e}",
                duration
            )
            return False
            
    async def test_basic_query(self):
        """Test executing a basic Gremlin query."""
        if not self.client:
            self.log_test_result(
                "Basic Query Test",
                False,
                "No client available"
            )
            return False
            
        logger.info("🧪 Testing Basic Query...")
        
        start_time = time.time()
        try:
            # Simple count query
            result = await self.client.execute_query("g.V().count()")
            duration = time.time() - start_time
            
            if result and len(result) > 0:
                vertex_count = result[0]
                self.log_test_result(
                    "Basic Query Test",
                    True,
                    f"Query successful - found {vertex_count} vertices",
                    duration
                )
                return True
            else:
                self.log_test_result(
                    "Basic Query Test",
                    False,
                    "Query returned empty result",
                    duration
                )
                return False
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Basic Query Test",
                False,
                f"Query failed: {e}",
                duration
            )
            return False
            
    async def test_schema_methods(self):
        """Test schema-aware methods."""
        if not self.client:
            self.log_test_result(
                "Schema Methods Test",
                False,
                "No client available"
            )
            return False
            
        logger.info("🧪 Testing Schema Methods...")
        
        start_time = time.time()
        try:
            # Test getting schema info (this method exists)
            schema_info = await self.client.get_schema_info()
            duration = time.time() - start_time
            
            vertex_count = len(schema_info.get("vertices", []))
            edge_count = len(schema_info.get("edges", []))
            
            self.log_test_result(
                "Schema Methods Test",
                True,
                f"Retrieved schema info: {vertex_count} vertex types, {edge_count} edge types",
                duration
            )
            return True
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result(
                "Schema Methods Test",
                False,
                f"Schema method failed: {e}",
                duration
            )
            return False
            
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            try:
                await self.client.close()
                logger.info("🧹 Client connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error during cleanup: {e}")
                
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "="*60)
        logger.info("📊 GREMLIN CONNECTION TEST SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%")
        
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"   • {result['test']}: {result['message']}")
                    
            logger.info("\n💡 TROUBLESHOOTING TIPS:")
            logger.info("   • Verify your Cosmos DB Gremlin API is enabled")
            logger.info("   • Check that your connection string and keys are correct")
            logger.info("   • Ensure your IP address is allowed in Cosmos DB firewall")
            logger.info("   • Verify the database and graph names exist")
            logger.info("   • Check Azure Portal for any service outages")
        else:
            logger.info("\n🎉 All tests passed! Your Gremlin connection is working properly.")
            
        logger.info("="*60 + "\n")
        
        return failed_tests == 0


async def main():
    """Run comprehensive Gremlin connection tests."""
    logger.info("🔬 Starting Standalone Gremlin Connection Test")
    logger.info("="*60)
    
    tester = GremlinConnectionTester()
    tester.print_environment_info()
    
    # Run tests in sequence
    tests = [
        tester.test_environment_variables,
        tester.test_client_creation,
        tester.test_connection,
        tester.test_basic_query,
        tester.test_schema_methods,
    ]
    
    try:
        for test in tests:
            success = await test()
            # Continue with remaining tests even if one fails
            # to get a complete picture of what's working
            
        # Print final summary
        all_passed = tester.print_summary()
        
        # Return appropriate exit code
        return 0 if all_passed else 1
        
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"💥 Unexpected error during testing: {e}")
        return 1
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
