#!/usr/bin/env python3
"""
Test Graph Query LLM functionality directly
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings

async def test_graph_query_llm():
    """Test the GraphQueryLLM directly"""
    print("🧪 TESTING GRAPH QUERY LLM DIRECTLY")
    print("=" * 50)
    
    # Initialize settings
    settings = get_settings()
    print(f"✅ Model Provider: {settings.model_provider}")
    print(f"✅ Gemini Model: {settings.gemini_model}")
    
    # Initialize Graph Query LLM
    try:
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ GraphQueryLLM initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GraphQueryLLM: {e}")
        return
    
    # Test queries
    test_queries = [
        "Show me all hotels",
        "Find VIP guests",
        "Türkçe yazılmış temizlik şikayetlerini göster",
        "Otelde hangi milletin müşterisi daha fazla?",
        "Show me maintenance issues related to VIP guest rooms"
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} queries:")
    print("-" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] 📝 Query: '{query}'")
        
        try:
            gremlin_query = await llm.generate_gremlin_query(query)
            print(f"    ✅ Generated: {gremlin_query}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("\n🎉 Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_graph_query_llm())
