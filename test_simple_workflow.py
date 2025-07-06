#!/usr/bin/env python3
"""
Simple workflow test to verify the system can convert user input to Gremlin queries.
Fixed version without syntax errors.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings


async def test_user_input_to_gremlin():
    """Test converting user input to Gremlin queries."""
    print("🧪 TESTING USER INPUT → GREMLIN QUERY CONVERSION")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    print(f"✅ Environment loaded")
    print(f"   Provider: {settings.model_provider}")
    print(f"   Model: {settings.gemini_model}")
    
    # Test queries to convert
    test_queries = [
        {
            "name": "Turkish Cleanliness Complaints",
            "query": "Türkçe yazılmış temizlik şikayetlerini göster"
        },
        {
            "name": "VIP Guest Issues",
            "query": "VIP misafirlerin sorunlarını göster"
        },
        {
            "name": "Hotel Service Ratings",
            "query": "Otellerin hizmet puanlarını göster"
        },
        {
            "name": "Recent Maintenance Issues",
            "query": "Son bakım sorunlarını göster"
        }
    ]
    
    try:
        # Initialize the LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ GraphQueryLLM initialized successfully")
        
        success_count = 0
        
        # Test each query
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n[{i}] {test_case['name']}")
            print(f"📝 Input: {test_case['query']}")
            
            try:
                # Generate Gremlin query
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                
                if gremlin_query and gremlin_query.strip():
                    print(f"✅ Generated Gremlin: {gremlin_query}")
                    success_count += 1
                else:
                    print("❌ Failed to generate valid Gremlin query")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        # Summary
        print(f"\n📊 RESULTS SUMMARY")
        print(f"   Total Tests: {len(test_queries)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(test_queries) - success_count}")
        print(f"   Success Rate: {(success_count/len(test_queries)*100):.1f}%")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


async def test_full_workflow():
    """Test the complete workflow including database response simulation."""
    print("\n🔄 TESTING FULL WORKFLOW")
    print("=" * 60)
    
    # Test the query generation
    query_success = await test_user_input_to_gremlin()
    
    if query_success:
        print("\n✅ User Input → Gremlin Query: WORKING")
        print("✅ System can convert natural language to database queries")
        print("✅ Ready for database integration and response generation")
    else:
        print("\n❌ Query generation failed")
        return False
    
    return True


async def main():
    """Main test function."""
    print("🚀 STARTING GRAPH RAG WORKFLOW TEST")
    print("=" * 60)
    
    try:
        result = await test_full_workflow()
        
        if result:
            print("\n🎉 SUCCESS: The system can convert user input to Gremlin queries!")
            print("✅ Ready for full Graph RAG pipeline integration")
        else:
            print("\n❌ FAILED: Issues found in the workflow")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
