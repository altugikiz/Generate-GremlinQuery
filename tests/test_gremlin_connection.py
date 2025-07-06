#!/usr/bin/env python3
"""
Standalone Gremlin Connection Test Script
========================================

This script tests the Cosmos DB Gremlin connection independently of the FastAPI application.
It helps isolate whether connection issues are due to credentials or application startup.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time
from loguru import logger

# Add the app directory to Python path so we can import our modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.schema_gremlin_client import SchemaAwareGremlinClient


def setup_logging():
    """Configure logging for clear output."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def load_environment():
    """Load environment variables from .env file."""
    env_path = project_root / ".env"
    
    if not env_path.exists():
        logger.error(f"❌ .env file not found at: {env_path}")
        return False
    
    load_dotenv(env_path)
    logger.info(f"✅ Loaded environment variables from: {env_path}")
    return True


def validate_env_vars():
    """Validate that all required environment variables are present."""
    required_vars = {
        'GREMLIN_URL': 'Gremlin server URL',
        'GREMLIN_DATABASE': 'Database name', 
        'GREMLIN_GRAPH': 'Graph name',
        'GREMLIN_KEY': 'Authentication key',
        'GREMLIN_USERNAME': 'Username'
    }
    
    missing_vars = []
    present_vars = {}
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"  - {var}: {description}")
        else:
            # Mask sensitive values for logging
            if 'KEY' in var or 'PASSWORD' in var:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                present_vars[var] = masked_value
            else:
                present_vars[var] = value
    
    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(var)
        return False
    
    logger.info("✅ All required environment variables present:")
    for var, value in present_vars.items():
        logger.info(f"  - {var}: {value}")
    
    return True


async def test_gremlin_connection():
    """Test the Gremlin connection with comprehensive error handling."""
    logger.info("🚀 Starting Gremlin connection test...")
    
    # Load and validate environment
    if not load_environment():
        return False
    
    if not validate_env_vars():
        return False
    
    # Initialize client
    try:
        client = SchemaAwareGremlinClient(
            url=os.getenv('GREMLIN_URL'),
            database=os.getenv('GREMLIN_DATABASE'),
            graph=os.getenv('GREMLIN_GRAPH'),
            username=os.getenv('GREMLIN_USERNAME'),
            password=os.getenv('GREMLIN_KEY'),
            traversal_source=os.getenv('GREMLIN_TRAVERSAL_SOURCE', 'g'),
            timeout=30,
            max_retries=3
        )
        logger.info("✅ SchemaAwareGremlinClient initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gremlin client: {e}")
        return False
    
    # Test connection
    try:
        logger.info("🔌 Attempting to connect to Gremlin server...")
        start_time = time.time()
        
        await client.connect()
        
        connection_time = (time.time() - start_time) * 1000
        logger.info(f"✅ Connected successfully in {connection_time:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        
        # Provide specific troubleshooting based on error type
        if "SSL" in str(e):
            logger.error("   💡 SSL Issue: Check if the URL uses 'wss://' and certificates are valid")
        elif "Authentication" in str(e) or "Unauthorized" in str(e):
            logger.error("   💡 Auth Issue: Verify GREMLIN_KEY and GREMLIN_USERNAME are correct")
        elif "timeout" in str(e).lower():
            logger.error("   💡 Timeout Issue: Check network connectivity and firewall settings")
        elif "Connection refused" in str(e):
            logger.error("   💡 Connection Issue: Verify GREMLIN_URL and that the service is running")
        
        return False
    
    # Test basic queries
    test_queries = [
        ("Basic vertex count", "g.V().limit(1).count()"),
        ("Graph structure test", "g.V().limit(1)"),
        ("Edge count test", "g.E().limit(1).count()"),
        ("Schema validation", "g.V().label().dedup().limit(5)")
    ]
    
    query_results = {}
    
    for test_name, query in test_queries:
        try:
            logger.info(f"🔍 Running test: {test_name}")
            logger.info(f"   Query: {query}")
            
            start_time = time.time()
            result = await client.execute_query(query)
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(f"   ✅ Success in {execution_time:.2f}ms")
            logger.info(f"   📊 Result: {result}")
            
            query_results[test_name] = {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")
            query_results[test_name] = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    # Test schema-aware features
    try:
        logger.info("🏗️ Testing schema-aware features...")
        
        # Get schema info
        schema_info = await client.get_schema_info()
        logger.info(f"   📋 Available vertex types: {len(schema_info['vertices'])}")
        logger.info(f"   🔗 Available edge types: {len(schema_info['edges'])}")
        
        # Get schema statistics
        schema_stats = await client.get_schema_statistics()
        logger.info(f"   📊 Total vertices: {schema_stats['total_vertices']}")
        logger.info(f"   📊 Total edges: {schema_stats['total_edges']}")
        
        if schema_stats['total_vertices'] == 0:
            logger.warning("   ⚠️ Database appears to be empty (no vertices found)")
        else:
            logger.info("   ✅ Database contains data")
            
    except Exception as e:
        logger.error(f"   ❌ Schema test failed: {e}")
    
    # Get client statistics
    try:
        stats = await client.get_statistics()
        logger.info("📈 Client Statistics:")
        logger.info(f"   - Connection status: {stats['is_connected']}")
        logger.info(f"   - Queries executed: {stats['query_count']}")
        logger.info(f"   - Average query time: {stats['average_query_time_ms']:.2f}ms")
        
    except Exception as e:
        logger.error(f"❌ Failed to get client statistics: {e}")
    
    # Clean up
    try:
        await client.close()
        logger.info("✅ Connection closed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error closing connection: {e}")
    
    # Summary
    successful_tests = sum(1 for result in query_results.values() if result.get("success"))
    total_tests = len(query_results)
    
    logger.info("=" * 60)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Your Gremlin connection is working correctly.")
        logger.info("💡 If FastAPI startup fails, the issue is likely with application configuration.")
        return True
    elif successful_tests > 0:
        logger.warning("⚠️ PARTIAL SUCCESS: Connection works but some queries failed.")
        logger.warning("💡 This might indicate database schema or data issues.")
        return True
    else:
        logger.error("❌ ALL TESTS FAILED: Gremlin connection is not working.")
        logger.error("💡 Check your credentials, network, and Cosmos DB service status.")
        return False


def main():
    """Main function to run the connection test."""
    setup_logging()
    
    logger.info("🧪 COSMOS DB GREMLIN CONNECTION TEST")
    logger.info("=" * 60)
    
    try:
        # Run the async test
        result = asyncio.run(test_gremlin_connection())
        
        if result:
            logger.info("🏁 Test completed successfully!")
            sys.exit(0)
        else:
            logger.error("🏁 Test completed with errors!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error during test: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
