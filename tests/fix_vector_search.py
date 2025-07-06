#!/usr/bin/env python3
"""
Vector Search Diagnostics Script

This script will diagnose and fix issues with the vector search endpoint by:
1. Verifying that documents are being embedded and stored
2. Loading sample data into the vector store
3. Ensuring the correct embedding model is being used
4. Testing the vector query and analyzing results
5. Adding enhanced logging to track indexed document count and similarity scores
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.vector_retriever import VectorRetriever
from core.vector_store import VectorStore
from models.dto import SemanticResult
from loguru import logger

# Configure logging for detailed diagnostics
logger.remove()
logger.add(sys.stdout, level="DEBUG", format="{time} | {level} | {name}:{line} - {message}")

# Sample Turkish hotel review data
SAMPLE_TURKISH_REVIEWS = [
    {
        "content": "Bu otel harika! Odalar çok temiz ve personel çok yardımsever. Kesinlikle tavsiye ederim.",
        "metadata": {"hotel_name": "Grand Hotel", "language": "tr", "rating": 5, "aspect": "general"}
    },
    {
        "content": "Otel temizliği mükemmel. Banyolar çok parlak ve odalar tertemiz. 5 yıldız hak ediyor.",
        "metadata": {"hotel_name": "Grand Hotel", "language": "tr", "rating": 5, "aspect": "cleanliness"}
    },
    {
        "content": "Temizlik konusunda gerçekten çok başarılılar. Odada hiçbir toz yoktu.",
        "metadata": {"hotel_name": "Palace Hotel", "language": "tr", "rating": 5, "aspect": "cleanliness"}
    },
    {
        "content": "Personel çok kibardı ama otel biraz eski. Yenileme yapılması gerekiyor.",
        "metadata": {"hotel_name": "Old Town Hotel", "language": "tr", "rating": 3, "aspect": "general"}
    },
    {
        "content": "Kahvaltı çok zengin ve lezzetliydi. Özellikle Türk kahvaltısı harika.",
        "metadata": {"hotel_name": "Breakfast Inn", "language": "tr", "rating": 4, "aspect": "food"}
    },
    {
        "content": "Havuz alanı çok güzeldi. Çocuklar çok eğlendi.",
        "metadata": {"hotel_name": "Family Resort", "language": "tr", "rating": 4, "aspect": "facilities"}
    },
    {
        "content": "Konum mükemmel, her yere yürüyerek gidebiliyorsunuz.",
        "metadata": {"hotel_name": "City Center Hotel", "language": "tr", "rating": 5, "aspect": "location"}
    },
    {
        "content": "Oda servisi hızlı ve kaliteli. Yemekler sıcak geldi.",
        "metadata": {"hotel_name": "Service Hotel", "language": "tr", "rating": 4, "aspect": "service"}
    },
    {
        "content": "Wi-Fi hızı çok iyiydi. İş için gitmiştim, hiç sorun yaşamadım.",
        "metadata": {"hotel_name": "Business Hotel", "language": "tr", "rating": 4, "aspect": "facilities"}
    },
    {
        "content": "Fiyat performans açısından çok iyi. Tekrar gelmek isterim.",
        "metadata": {"hotel_name": "Budget Hotel", "language": "tr", "rating": 4, "aspect": "value"}
    },
    {
        "content": "The cleanliness of this hotel is exceptional. Every room is spotless.",
        "metadata": {"hotel_name": "International Hotel", "language": "en", "rating": 5, "aspect": "cleanliness"}
    },
    {
        "content": "Staff was very helpful and friendly. Great customer service.",
        "metadata": {"hotel_name": "International Hotel", "language": "en", "rating": 5, "aspect": "service"}
    },
    {
        "content": "The room was clean but the bathroom needs renovation.",
        "metadata": {"hotel_name": "Old Inn", "language": "en", "rating": 3, "aspect": "cleanliness"}
    },
    {
        "content": "Excellent location in the city center. Walking distance to everything.",
        "metadata": {"hotel_name": "Downtown Hotel", "language": "en", "rating": 5, "aspect": "location"}
    },
    {
        "content": "The pool area was very well maintained and clean.",
        "metadata": {"hotel_name": "Resort Paradise", "language": "en", "rating": 4, "aspect": "facilities"}
    }
]

# Test queries
TEST_QUERIES = [
    {
        "query": "otel temizliği hakkında yorum",
        "description": "Turkish query about hotel cleanliness",
        "expected_aspects": ["cleanliness"]
    },
    {
        "query": "hotel cleanliness reviews",
        "description": "English query about hotel cleanliness",
        "expected_aspects": ["cleanliness"]
    },
    {
        "query": "personel hizmeti nasıl",
        "description": "Turkish query about staff service",
        "expected_aspects": ["service"]
    },
    {
        "query": "konum ve ulaşım",
        "description": "Turkish query about location",
        "expected_aspects": ["location"]
    }
]

class VectorSearchDiagnostics:
    """Comprehensive vector search diagnostics and testing."""
    
    def __init__(self):
        self.vector_retriever = None
        self.vector_store = None
        self.test_results = []
        
    async def initialize_components(self):
        """Initialize vector retriever and store components."""
        logger.info("🚀 Initializing vector search components...")
        
        try:
            # Initialize vector retriever
            self.vector_retriever = VectorRetriever(
                embedding_model="all-MiniLM-L6-v2",
                store_path="hf_faiss_index",
                index_name="hotel_reviews",
                embedding_dimension=384
            )
            await self.vector_retriever.initialize()
            logger.info("✅ Vector retriever initialized")
            
            # Initialize vector store
            self.vector_store = VectorStore(
                store_type="huggingface",
                db_uri="hf_faiss_index",
                index_name="hotel_reviews",
                embedding_model="all-MiniLM-L6-v2",
                embedding_dimension=384
            )
            await self.vector_store.initialize()
            logger.info("✅ Vector store initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
            
    async def check_existing_data(self):
        """Check if there's existing data in the vector indices."""
        logger.info("📊 Checking existing data in vector indices...")
        
        # Check vector retriever stats
        retriever_stats = await self.vector_retriever.get_statistics()
        logger.info(f"📈 Vector Retriever Stats: {retriever_stats}")
        
        # Check vector store stats
        store_stats = await self.vector_store.get_statistics()
        logger.info(f"📈 Vector Store Stats: {store_stats}")
        
        return retriever_stats, store_stats
        
    async def load_sample_data(self, force_reload: bool = False):
        """Load sample data into both vector retriever and store."""
        logger.info("📥 Loading sample data into vector indices...")
        
        retriever_stats, store_stats = await self.check_existing_data()
        
        if (retriever_stats.get('document_count', 0) == 0 or 
            store_stats.get('document_count', 0) == 0 or 
            force_reload):
            
            logger.info("💾 Adding sample documents to indices...")
            
            # Prepare documents and metadata
            documents = [item['content'] for item in SAMPLE_TURKISH_REVIEWS]
            metadata_list = [item['metadata'] for item in SAMPLE_TURKISH_REVIEWS]
            
            # Add to vector retriever
            retriever_count = await self.vector_retriever.add_documents(
                documents=documents,
                metadata_list=metadata_list
            )
            logger.info(f"✅ Added {retriever_count} documents to vector retriever")
            
            # Add to vector store
            store_count = await self.vector_store.add_documents(
                documents=documents,
                metadata_list=metadata_list
            )
            logger.info(f"✅ Added {store_count} documents to vector store")
            
        else:
            logger.info("📋 Using existing data in indices")
            
        # Verify final stats
        final_retriever_stats = await self.vector_retriever.get_statistics()
        final_store_stats = await self.vector_store.get_statistics()
        
        logger.info(f"📊 Final Vector Retriever: {final_retriever_stats['document_count']} documents")
        logger.info(f"📊 Final Vector Store: {final_store_stats['document_count']} documents")
        
    async def test_embedding_generation(self):
        """Test embedding generation for queries."""
        logger.info("🔬 Testing embedding generation...")
        
        test_query = "otel temizliği hakkında yorum"
        
        # Test vector retriever embedding
        retriever_embedding = await self.vector_retriever.get_query_embedding(test_query)
        if retriever_embedding:
            logger.info(f"✅ Vector retriever embedding: {len(retriever_embedding)} dimensions")
            logger.debug(f"📊 Embedding sample: {retriever_embedding[:5]}")
        else:
            logger.error("❌ Vector retriever failed to generate embedding")
            
        return retriever_embedding is not None
        
    async def test_vector_search(self, query: str, description: str, expected_aspects: List[str]):
        """Test vector search with detailed logging."""
        logger.info(f"🔍 Testing vector search: {description}")
        logger.info(f"🎯 Query: '{query}'")
        
        start_time = time.time()
        
        try:
            # Test with vector retriever
            retriever_results = await self.vector_retriever.retrieve_similar_docs_with_scores(
                query=query,
                top_k=10,
                min_score=0.0  # Lower threshold to see all results
            )
            
            # Test with vector store
            store_results = await self.vector_store.search(
                query=query,
                top_k=10,
                min_score=0.0  # Lower threshold to see all results
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            logger.info(f"📈 Vector Retriever found {len(retriever_results)} results")
            logger.info(f"📈 Vector Store found {len(store_results)} results")
            
            # Analyze results
            result_analysis = {
                "query": query,
                "description": description,
                "execution_time_ms": execution_time,
                "retriever_results": len(retriever_results),
                "store_results": len(store_results),
                "top_retriever_scores": [r.score for r in retriever_results[:5]],
                "top_store_scores": [r.score for r in store_results[:5]],
                "relevant_results": 0,
                "aspects_found": []
            }
            
            # Analyze relevance (check if expected aspects are found)
            for result in retriever_results:
                aspect = result.metadata.get('aspect', '')
                if aspect in expected_aspects:
                    result_analysis["relevant_results"] += 1
                    if aspect not in result_analysis["aspects_found"]:
                        result_analysis["aspects_found"].append(aspect)
                        
                logger.info(f"📋 Result: score={result.score:.4f}, aspect={aspect}, content='{result.content[:50]}...'")
            
            self.test_results.append(result_analysis)
            
            if len(retriever_results) > 0:
                logger.info(f"✅ Search successful: {len(retriever_results)} results")
                return True
            else:
                logger.warning("⚠️  No results found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return False
            
    async def run_comprehensive_tests(self):
        """Run all diagnostic tests."""
        logger.info("🧪 Starting comprehensive vector search diagnostics...")
        
        # Step 1: Initialize components
        await self.initialize_components()
        
        # Step 2: Check existing data
        await self.check_existing_data()
        
        # Step 3: Load sample data if needed
        await self.load_sample_data()
        
        # Step 4: Test embedding generation
        embedding_test = await self.test_embedding_generation()
        
        # Step 5: Run search tests
        search_tests = []
        for test_query in TEST_QUERIES:
            result = await self.test_vector_search(
                query=test_query["query"],
                description=test_query["description"],
                expected_aspects=test_query["expected_aspects"]
            )
            search_tests.append(result)
            
        # Step 6: Generate report
        await self.generate_diagnostic_report(embedding_test, search_tests)
        
    async def generate_diagnostic_report(self, embedding_test: bool, search_tests: List[bool]):
        """Generate comprehensive diagnostic report."""
        logger.info("📊 Generating diagnostic report...")
        
        successful_searches = sum(search_tests)
        total_searches = len(search_tests)
        
        report = {
            "timestamp": time.time(),
            "diagnostic_summary": {
                "embedding_generation": "✅ PASS" if embedding_test else "❌ FAIL",
                "vector_searches": f"{successful_searches}/{total_searches} PASS",
                "overall_status": "✅ HEALTHY" if embedding_test and successful_searches > 0 else "❌ ISSUES FOUND"
            },
            "component_status": {
                "vector_retriever_initialized": self.vector_retriever._is_initialized if self.vector_retriever else False,
                "vector_store_initialized": self.vector_store._is_initialized if self.vector_store else False,
                "embedding_model": "all-MiniLM-L6-v2",
                "index_type": "FAISS"
            },
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # Add recommendations based on results
        if not embedding_test:
            report["recommendations"].append("Fix embedding generation - check model loading")
            
        if successful_searches == 0:
            report["recommendations"].append("No search results found - check data loading and indexing")
            
        if successful_searches < total_searches:
            report["recommendations"].append("Some searches failed - check query processing and scoring")
            
        # Save report
        report_file = f"vector_search_diagnostics_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📄 Diagnostic report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 VECTOR SEARCH DIAGNOSTIC SUMMARY")
        print("="*60)
        print(f"🔬 Embedding Generation: {report['diagnostic_summary']['embedding_generation']}")
        print(f"🔍 Vector Searches: {report['diagnostic_summary']['vector_searches']}")
        print(f"🎯 Overall Status: {report['diagnostic_summary']['overall_status']}")
        print("="*60)
        
        if report["recommendations"]:
            print("💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")
        else:
            print("✅ No issues found! Vector search is working correctly.")
            
        return report

async def main():
    """Main diagnostic function."""
    diagnostics = VectorSearchDiagnostics()
    
    try:
        await diagnostics.run_comprehensive_tests()
    except Exception as e:
        logger.error(f"❌ Diagnostic failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(main())
