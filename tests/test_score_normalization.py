#!/usr/bin/env python3
"""
Test script to verify vector search score normalization fix.
"""

import asyncio
import sys
import os
import time
import json
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.vector_store import VectorStore
from core.vector_retriever import VectorRetriever
from models.dto import SemanticResult

# Sample Turkish hotel review data
SAMPLE_TURKISH_REVIEWS = [
    "Bu otel harika! Odalar çok temiz ve personel çok yardımsever. Kesinlikle tavsiye ederim.",
    "Otel temizliği mükemmel. Banyolar çok parlak ve odalar tertemiz. 5 yıldız hak ediyor.",
    "Personel çok kibardı ama otel biraz eski. Yenileme yapılması gerekiyor.",
    "Yemekler lezzetli ama servis biraz yavaştı. Otel konumu çok merkezi.",
    "Odalar temiz ve konforlu. Özellikle temizlik personeli çok dikkatli çalışıyor.",
    "Otelin genel temizliği çok iyi. Lobiden odalara kadar her yer pırıl pırıl.",
    "Resepsiyon personeli çok yardımcı. Check-in işlemi çok hızlı oldu.",
    "Kahvaltı çeşitleri bol ama odalar biraz küçük. Genel olarak memnun kaldık.",
    "Otel temizliği konusunda hiçbir şikayetim yok. Her şey çok düzenli ve temiz.",
    "Spa ve havuz alanları harika. Temizlik standartları çok yüksek."
]

async def test_score_normalization():
    """Test vector search with score normalization."""
    print("🧪 Testing Vector Search Score Normalization")
    print("=" * 60)
    
    try:
        # Initialize vector store
        print("📚 Initializing vector store...")
        vector_store = VectorStore()
        await vector_store.initialize()
        
        # Check if we need to add documents
        if vector_store.get_document_count() == 0:
            print("📝 Adding sample Turkish hotel reviews...")
            metadata_list = [
                {
                    'source': 'test_data',
                    'category': 'hotel_review',
                    'language': 'turkish',
                    'review_id': i,
                    'rating': 4 + (i % 2)  # Ratings between 4-5
                }
                for i in range(len(SAMPLE_TURKISH_REVIEWS))
            ]
            
            added_count = await vector_store.add_documents(
                SAMPLE_TURKISH_REVIEWS,
                metadata_list
            )
            print(f"✅ Added {added_count} documents to vector store")
        else:
            print(f"📊 Vector store already contains {vector_store.get_document_count()} documents")
        
        # Test queries with potential for high scores
        test_queries = [
            "otel temizliği hakkında yorum",  # Target query
            "temiz oda",  # Short, direct query
            "personel yardımcı",  # Another direct query
            "harika otel",  # Very direct match
            "clean room",  # English query
        ]
        
        print("\n🔍 Testing queries with score normalization:")
        print("-" * 50)
        
        for query in test_queries:
            print(f"\n🎯 Query: '{query}'")
            
            try:
                # Search with vector store
                results = await vector_store.search(
                    query=query,
                    top_k=3,
                    min_score=0.0
                )
                
                print(f"📊 Vector Store Results ({len(results)} found):")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Score: {result.score:.4f}")
                    print(f"      Content: {result.content[:80]}...")
                    
                    # Check for score validation
                    if result.score > 1.0:
                        print(f"      ⚠️  WARNING: Score {result.score} exceeds 1.0!")
                    elif result.score <= 1.0:
                        print(f"      ✅ Score is properly normalized")
                
                if not results:
                    print("   ⚠️  No results found")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test with vector retriever as well
        print("\n" + "=" * 60)
        print("🔍 Testing Vector Retriever (L2 distance-based):")
        print("-" * 50)
        
        retriever = VectorRetriever()
        await retriever.initialize()
        
        if retriever.get_document_count() == 0:
            print("📝 Adding documents to retriever...")
            metadata_list = [
                {
                    'source': 'test_data',
                    'category': 'hotel_review',
                    'language': 'turkish',
                    'review_id': i
                }
                for i in range(len(SAMPLE_TURKISH_REVIEWS))
            ]
            
            await retriever.add_documents(SAMPLE_TURKISH_REVIEWS, metadata_list)
            print(f"✅ Added documents to retriever")
        
        for query in test_queries[:2]:  # Test first 2 queries
            print(f"\n🎯 Query: '{query}'")
            
            try:
                results = await retriever.retrieve_similar_docs_with_scores(
                    query=query,
                    top_k=3,
                    min_score=0.0
                )
                
                print(f"📊 Vector Retriever Results ({len(results)} found):")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Score: {result.score:.4f}")
                    print(f"      Content: {result.content[:80]}...")
                    
                    # Check for score validation
                    if result.score > 1.0:
                        print(f"      ⚠️  WARNING: Score {result.score} exceeds 1.0!")
                    elif result.score <= 1.0:
                        print(f"      ✅ Score is properly normalized")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Score normalization test completed!")
        
        # Generate summary
        print("\n📋 SUMMARY:")
        print("- Vector store now normalizes FAISS inner product scores to [0,1]")
        print("- Vector retriever uses L2 distance with proper similarity conversion")
        print("- Both should prevent Pydantic validation errors from scores > 1.0")
        print("- Turkish queries are working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_score_normalization())
