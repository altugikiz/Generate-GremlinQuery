#!/usr/bin/env python3
"""
Standalone Gremlin Connection Test Script

This script tests the Gremlin (Azure Cosmos DB) connection independently of FastAPI.
It validates environment variables, connection parameters, and performs basic queries.

Usage:
    python test_gremlin_connection.py

Features:
- Loads configuration from .env file
- Tests connection with detailed error reporting
- Validates credentials and network connectivity
- Provides troubleshooting guidance
- Tests basic graph operations if connection succeeds
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from typing import Optional
import time

# Add the app directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.config.settings import get_settings

class GremlinConnectionTester:
    """Standalone Gremlin connection tester."""
    
    def __init__(self):
        self.client: Optional[SchemaAwareGremlinClient] = None
        self.settings = None
        
    def load_environment(self) -> bool:
        """Load and validate environment variables."""
        print("🔧 Loading Environment Configuration")
        print("-" * 40)
        
        # Load .env file
        env_file = ".env"
        if not os.path.exists(env_file):
            print(f"❌ Environment file not found: {env_file}")
            return False
        
        load_dotenv(env_file)
        print(f"✅ Loaded environment from: {env_file}")
        
        # Get settings
        try:
            self.settings = get_settings()
            print(f"✅ Settings loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load settings: {e}")
            return False
        
        # Validate required Gremlin configuration
        required_vars = [
            ("GREMLIN_URL", self.settings.gremlin_url),
            ("GREMLIN_KEY", self.settings.gremlin_key),
            ("GREMLIN_DATABASE", self.settings.gremlin_database),
            ("GREMLIN_GRAPH", self.settings.gremlin_graph)
        ]
        
        print(f"\n📋 Gremlin Configuration:")
        all_present = True
        
        for var_name, var_value in required_vars:
            if var_value:
                # Mask sensitive information
                display_value = var_value
                if "key" in var_name.lower() and len(display_value) > 10:
                    display_value = display_value[:10] + "..." + display_value[-4:]
                print(f"   ✅ {var_name}: {display_value}")
            else:
                print(f"   ❌ {var_name}: Not set")
                all_present = False
        
        if not all_present:
            print(f"\n❌ Missing required Gremlin configuration variables")
            self.print_configuration_help()
            return False
        
        return True
    
    def print_configuration_help(self):
        """Print configuration troubleshooting help."""
        print(f"\n🔧 CONFIGURATION HELP")
        print("-" * 30)
        print("Required environment variables for Gremlin connection:")
        print("   GREMLIN_URL=wss://your-cosmos-account.gremlin.cosmos.azure.com:443/")
        print("   GREMLIN_KEY=your-primary-or-secondary-key")
        print("   GREMLIN_DATABASE=your-database-name")
        print("   GREMLIN_GRAPH=your-graph-name")
        print("   GREMLIN_USERNAME=your-cosmos-account-name")
        print()
        print("📚 Azure Cosmos DB Gremlin API Setup:")
        print("   1. Create a Cosmos DB account with Gremlin API")
        print("   2. Create a database and graph container") 
        print("   3. Get connection string from Azure portal > Keys section")
        print("   4. Ensure firewall allows your IP address")
        print("   5. Verify the account is not paused or suspended")
    
    async def test_connection(self) -> bool:
        """Test the Gremlin connection with detailed diagnostics."""
        print(f"\n🔌 Testing Gremlin Connection")
        print("-" * 35)
        
        try:
            # Create client instance
            print("   🏗️ Creating Gremlin client...")
            self.client = SchemaAwareGremlinClient(
                url=self.settings.gremlin_url,
                database=self.settings.gremlin_database,
                graph=self.settings.gremlin_graph,
                username=self.settings.gremlin_username,
                password=self.settings.gremlin_key,  # Cosmos DB uses the key as password
                traversal_source=self.settings.gremlin_traversal_source
            )
            print("   ✅ Client created successfully")
            
            # Attempt connection
            print("   🌐 Attempting connection...")
            start_time = time.time()
            
            await self.client.connect()
            
            connection_time = (time.time() - start_time) * 1000
            print(f"   ✅ Connected successfully in {connection_time:.2f}ms")
            
            # Test basic functionality
            await self.test_basic_operations()
            
            return True
            
        except ConnectionError as e:
            print(f"   ❌ Connection failed: {e}")
            self.print_connection_troubleshooting()
            return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            print(f"   📋 Error type: {type(e).__name__}")
            return False
    
    async def test_basic_operations(self):
        """Test basic Gremlin operations."""
        print(f"\n🧪 Testing Basic Operations")
        print("-" * 30)
        
        test_queries = [
            ("Count all vertices", "g.V().count()"),
            ("Count all edges", "g.E().count()"),
            ("Sample vertices", "g.V().limit(3).valueMap().with('~tinkerpop.valueMap.tokens')"),
            ("Vertex labels", "g.V().label().dedup().limit(10)"),
            ("Edge labels", "g.E().label().dedup().limit(10)")
        ]
        
        for test_name, query in test_queries:
            try:
                print(f"   🔍 {test_name}...")
                start_time = time.time()
                
                result = await self.client.execute_query(query)
                
                execution_time = (time.time() - start_time) * 1000
                print(f"      ✅ Success in {execution_time:.2f}ms")
                
                # Display result summary
                if isinstance(result, list):
                    print(f"      📊 Results: {len(result)} items")
                    if result and len(result) > 0:
                        print(f"      📄 Sample: {str(result[0])[:60]}{'...' if len(str(result[0])) > 60 else ''}")
                else:
                    print(f"      📊 Result: {result}")
                    
            except Exception as e:
                print(f"      ❌ Failed: {e}")
    
    def print_connection_troubleshooting(self):
        """Print connection troubleshooting guidance."""
        print(f"\n🔧 CONNECTION TROUBLESHOOTING")
        print("-" * 35)
        print("Common issues and solutions:")
        print()
        print("1. 🔐 Authentication Issues:")
        print("   - Verify GREMLIN_KEY is correct (primary or secondary key)")
        print("   - Check GREMLIN_USERNAME matches your Cosmos account name")
        print("   - Ensure key hasn't been regenerated recently")
        print()
        print("2. 🌐 Network Connectivity:")
        print("   - Check firewall settings in Azure Cosmos DB")
        print("   - Verify your IP address is allowed")
        print("   - Test from same network as production if applicable")
        print()
        print("3. 📝 Configuration Issues:")
        print("   - Verify GREMLIN_URL format: wss://account.gremlin.cosmos.azure.com:443/")
        print("   - Check database and graph names are correct")
        print("   - Ensure Cosmos account is using Gremlin API (not SQL API)")
        print()
        print("4. ⚡ Service Issues:")
        print("   - Check if Cosmos DB account is active (not paused)")
        print("   - Verify subscription is active and not suspended")
        print("   - Check Azure service status for outages")
        print()
        print("5. 🔧 Development Mode:")
        print("   - Consider running FastAPI with DEVELOPMENT_MODE=true")
        print("   - This allows testing without database connection")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            try:
                await self.client.close()
                print(f"\n🧹 Connection closed successfully")
            except Exception as e:
                print(f"\n⚠️ Error during cleanup: {e}")
    
    async def run_comprehensive_test(self) -> bool:
        """Run the complete connection test suite."""
        print("🧪 Standalone Gremlin Connection Test")
        print("=" * 50)
        
        try:
            # Step 1: Load environment
            if not self.load_environment():
                return False
            
            # Step 2: Test connection
            connection_success = await self.test_connection()
            
            if connection_success:
                print(f"\n🎉 SUCCESS: Gremlin connection is working!")
                print("   ✅ Ready for production use")
                print("   ✅ FastAPI server should start successfully")
            else:
                print(f"\n⚠️ CONNECTION FAILED")
                print("   🔧 Review the troubleshooting guidance above")
                print("   💡 Consider running FastAPI in development mode")
                print("      Set DEVELOPMENT_MODE=true in .env file")
            
            return connection_success
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main execution function."""
    tester = GremlinConnectionTester()
    success = await tester.run_comprehensive_test()
    
    print(f"\n📋 NEXT STEPS:")
    if success:
        print("   1. ✅ Connection is working - proceed with FastAPI server")
        print("   2. 🚀 Run: python -m uvicorn main:app --reload")
        print("   3. 🧪 Test endpoints with the comprehensive test script")
    else:
        print("   1. 🔧 Fix connection issues using troubleshooting guide")
        print("   2. 💡 OR run in development mode:")
        print("      - Set DEVELOPMENT_MODE=true in .env")
        print("      - Modify FastAPI lifespan to skip database requirement")
        print("   3. 🧪 Test LLM translation without database dependency")
    
    return success

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
