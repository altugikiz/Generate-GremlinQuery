#!/usr/bin/env python3
"""
Direct Vector Search Test with App State Simulation
"""

import asyncio
from fastapi import Request
from unittest.mock import MagicMock
from app.core.vector_retriever import VectorRetriever
from app.api.routes.semantic import get_vector_retriever
from app.config.settings import get_settings

async def test_vector_search_with_proper_state():
    """Test vector search with properly initialized state."""
    
    print("🧪 Testing Vector Search with Proper App State")
    print("=" * 60)
    
    # Step 1: Create and initialize vector retriever like main.py does
    print("📝 Step 1: Initialize vector retriever (simulating main.py startup)")
    settings = get_settings()
    
    vector_retriever = VectorRetriever(
        embedding_model=settings.huggingface_embedding_model,
        store_path=settings.vector_db_uri,
        index_name=settings.vector_index,
        api_token=settings.huggingface_api_token
    )
    
    await vector_retriever.initialize()
    
    # Check stats
    stats = await vector_retriever.get_statistics()
    print(f"✅ Vector retriever initialized: {stats['document_count']} documents")
    
    # Step 2: Create mock request with app state
    print("\n📝 Step 2: Create mock app state (simulating FastAPI)")
    mock_request = MagicMock()
    mock_app_state = MagicMock()
    mock_app_state.vector_retriever = vector_retriever
    mock_request.app.state = mock_app_state
    
    # Step 3: Test dependency injection
    print("\n📝 Step 3: Test dependency injection")
    retrieved_instance = get_vector_retriever(mock_request)
    print(f"✅ Dependency injection returns: {type(retrieved_instance)}")
    print(f"✅ Same instance: {retrieved_instance is vector_retriever}")
    
    if retrieved_instance:
        dep_stats = await retrieved_instance.get_statistics()
        print(f"✅ Dependency instance stats: {dep_stats['document_count']} documents")
    
    # Step 4: Test actual search
    print("\n📝 Step 4: Test vector search")
    test_query = "otel temizliği hakkında yorum"
    
    results = await retrieved_instance.retrieve_similar_docs_with_scores(
        query=test_query,
        top_k=5,
        min_score=0.0
    )
    
    print(f"✅ Search results: {len(results)} documents found")
    
    if results:
        print("\n🎯 Top results:")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result.score:.4f}")
            print(f"      Content: {result.content[:80]}...")
            print(f"      Metadata: {result.metadata}")
    else:
        print("❌ No results found!")
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSIS:")
    
    if stats['document_count'] > 0:
        print("✅ FAISS index loads correctly with documents")
    else:
        print("❌ FAISS index has no documents")
    
    if retrieved_instance is vector_retriever:
        print("✅ Dependency injection returns correct instance")
    else:
        print("❌ Dependency injection returns wrong instance")
    
    if len(results) > 0:
        print("✅ Vector search works correctly")
        print("\n🎉 CONCLUSION: Vector search is WORKING correctly!")
        print("   The issue is likely that the FastAPI server needs to be restarted")
        print("   to pick up the dependency injection changes.")
    else:
        print("❌ Vector search returns no results")
        print("\n❌ CONCLUSION: There's still an issue with vector search.")

if __name__ == "__main__":
    asyncio.run(test_vector_search_with_proper_state())
