#!/usr/bin/env python3
"""
Simple Gremlin Connection Test using Synchronous Client

This script tests the Cosmos DB Gremlin connection using the synchronous gremlin_python client
to avoid asyncio event loop conflicts.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def load_environment():
    """Load environment variables."""
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Loaded .env file from: {env_path}")
        return True
    else:
        logger.error(f"❌ .env file not found at: {env_path}")
        return False


def test_gremlin_sync():
    """Test Gremlin connection using synchronous client."""
    try:
        from gremlin_python.driver import client as gremlin_client
        from gremlin_python.driver.serializer import GraphSONSerializersV2d0
        logger.info("✅ gremlin_python imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import gremlin_python: {e}")
        return False
    
    # Get connection details
    gremlin_url = os.getenv('GREMLIN_URL')
    username = os.getenv('GREMLIN_USERNAME')
    password = os.getenv('GREMLIN_KEY')
    database = os.getenv('GREMLIN_DATABASE')
    graph = os.getenv('GREMLIN_GRAPH')
    
    if not all([gremlin_url, username, password, database, graph]):
        logger.error("❌ Missing required environment variables")
        return False
    
    # Parse URL to create proper Gremlin endpoint
    parsed_url = urlparse(gremlin_url)
    
    # For Cosmos DB, the URL format should be: wss://hostname:port/gremlin
    if not gremlin_url.endswith('/gremlin'):
        if gremlin_url.endswith('/'):
            gremlin_endpoint = gremlin_url + 'gremlin'
        else:
            gremlin_endpoint = gremlin_url + '/gremlin'
    else:
        gremlin_endpoint = gremlin_url
    
    logger.info("🔌 Testing Gremlin connection:")
    logger.info(f"   Endpoint: {gremlin_endpoint}")
    logger.info(f"   Database: {database}")
    logger.info(f"   Graph: {graph}")
    logger.info(f"   Username: {username}")
    
    try:
        # Create client with proper configuration for Cosmos DB
        client = gremlin_client.Client(
            gremlin_endpoint,
            'g',
            username=f"/dbs/{database}/colls/{graph}",  # Cosmos DB format
            password=password,
            message_serializer=GraphSONSerializersV2d0()
        )
        
        logger.info("✅ Gremlin client created successfully")
        
        # Test queries with increasing complexity
        test_queries = [
            ("Basic Count", "g.V().limit(1).count()"),
            ("Schema Info", "g.V().label().dedup().limit(10)"),
            ("Sample Vertex", "g.V().limit(1).valueMap(true)"),
            ("Edge Count", "g.E().limit(1).count()"),
            ("Edge Labels", "g.E().label().dedup().limit(10)")
        ]
        
        results = {}
        
        for test_name, query in test_queries:
            try:
                logger.info(f"🔍 Running: {test_name}")
                logger.info(f"   Query: {query}")
                
                start_time = time.time()
                
                # Submit query and get results
                result_set = client.submit(query)
                result = result_set.all().result()
                
                execution_time = (time.time() - start_time) * 1000
                
                logger.info(f"   ✅ Success in {execution_time:.2f}ms")
                logger.info(f"   📊 Result: {result}")
                
                results[test_name] = {
                    "success": True,
                    "result": result,
                    "execution_time_ms": execution_time
                }
                
            except Exception as e:
                logger.error(f"   ❌ Failed: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        # Close client
        client.close()
        logger.info("✅ Client closed successfully")
        
        # Results summary
        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        
        logger.info("=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            logger.info(f"{test_name:20}: {status}")
            if not result.get("success"):
                logger.error(f"                     Error: {result.get('error', 'Unknown')}")
        
        logger.info("=" * 60)
        success_rate = (successful / total * 100) if total > 0 else 0
        logger.info(f"Success Rate: {successful}/{total} ({success_rate:.1f}%)")
        
        if successful == total:
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("💡 Your Gremlin connection is working correctly.")
            logger.info("   If FastAPI still has issues, check the application startup sequence.")
            return True
        elif successful > 0:
            logger.warning("⚠️ PARTIAL SUCCESS!")
            logger.warning("💡 Connection works but some queries failed.")
            logger.warning("   This might indicate database schema or permissions issues.")
            return True
        else:
            logger.error("❌ ALL TESTS FAILED!")
            logger.error("💡 Gremlin connection is not working.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to create or use Gremlin client: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        
        # Provide specific troubleshooting
        error_str = str(e).lower()
        if "authentication" in error_str or "unauthorized" in error_str:
            logger.error("💡 Authentication issue:")
            logger.error("   - Check GREMLIN_KEY and GREMLIN_USERNAME")
            logger.error("   - Verify database and graph names are correct")
        elif "timeout" in error_str:
            logger.error("💡 Timeout issue:")
            logger.error("   - Check network connectivity")
            logger.error("   - Verify firewall settings")
        elif "connection" in error_str:
            logger.error("💡 Connection issue:")
            logger.error("   - Verify GREMLIN_URL is correct")
            logger.error("   - Check if Cosmos DB service is running")
        
        return False


def main():
    """Main function."""
    setup_logging()
    
    logger.info("🧪 SIMPLE GREMLIN CONNECTION TEST")
    logger.info("=" * 60)
    
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    # Test connection
    success = test_gremlin_sync()
    
    if success:
        logger.info("🏁 Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("🏁 Test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
