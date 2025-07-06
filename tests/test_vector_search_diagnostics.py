#!/usr/bin/env python3
"""
Vector Search Diagnostic Script

This script tests and diagnoses vector search functionality by:
1. Loading existing FAISS index 
2. Verifying documents are properly embedded and stored
3. Testing various search queries including Turkish
4. Creating sample documents if index is empty
5. Providing detailed diagnostics and performance metrics
"""

import os
import sys
import asyncio
import pickle
import json
from typing import List, Dict, Any
import time
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.vector_store import VectorStore
from app.core.vector_retriever import VectorRetriever
from loguru import logger


class VectorSearchDiagnostic:
    """Comprehensive vector search diagnostic tool."""
    
    def __init__(self):
        self.vector_store = None
        self.vector_retriever = None
        self.test_results = {}
        
    async def initialize_components(self):
        """Initialize vector store and retriever."""
        logger.info("🚀 Initializing vector search components...")
        
        try:
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
            
            # Initialize vector retriever 
            self.vector_retriever = VectorRetriever(
                embedding_model="all-MiniLM-L6-v2",
                store_path="hf_faiss_index",
                index_name="hotel_reviews",
                embedding_dimension=384
            )
            await self.vector_retriever.initialize()
            logger.info("✅ Vector retriever initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    async def check_index_status(self):
        """Check the status of existing FAISS index."""
        logger.info("📊 Checking index status...")
        
        try:
            # Check vector store stats
            vs_stats = await self.vector_store.get_statistics()
            vr_stats = await self.vector_retriever.get_statistics()
            
            logger.info(f"📈 Vector Store Stats:")
            logger.info(f"  - Document count: {vs_stats.get('document_count', 0)}")
            logger.info(f"  - Index size: {vs_stats.get('index_size', 0)}")
            logger.info(f"  - Search count: {vs_stats.get('search_count', 0)}")
            logger.info(f"  - Embedding model: {vs_stats.get('model_name', 'unknown')}")
            
            logger.info(f"📈 Vector Retriever Stats:")
            logger.info(f"  - Document count: {vr_stats.get('document_count', 0)}")
            logger.info(f"  - Index size: {vr_stats.get('index_size', 0)}")
            logger.info(f"  - Search count: {vr_stats.get('search_count', 0)}")
            
            self.test_results['index_status'] = {
                'vector_store': vs_stats,
                'vector_retriever': vr_stats,
                'has_documents': vs_stats.get('document_count', 0) > 0
            }
            
            return vs_stats.get('document_count', 0) > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to check index status: {e}")
            return False
    
    async def load_sample_data_if_needed(self):
        """Load sample Turkish hotel review data if index is empty."""
        logger.info("📝 Checking if sample data needs to be loaded...")
        
        # Sample Turkish hotel review data
        sample_documents = [
            "Bu otel gerçekten harika! Temizlik konusunda çok titizler ve personel son derece yardımsever.",
            "Otel temizliği mükemmel, odalar her gün titizlikle temizleniyor.",
            "Otelin konumu çok güzel, denize yakın ve merkeze yürüme mesafesinde.",
            "Kahvaltı çeşitleri bol ve lezzetli, özellikle Türk kahvaltısı harika.",
            "Personel çok güler yüzlü ve misafirlere karşı son derece saygılı.",
            "Odalar ferah ve temiz, manzara muhteşem.",
            "SPA hizmetleri kaliteli, masaj çok rahatlatıcı.",
            "Yemek kalitesi çok iyi, özellikle akşam yemekleri lezzetli.",
            "Otelin havuzu temiz ve büyük, çocuklar için ayrı alan var.",
            "Klima sistemi çok iyi çalışıyor, odalar serin.",
            "Banyo temizliği mükemmel, havlular her gün değişiyor.",
            "Otelin çevresi güvenli ve huzurlu.",
            "Resepsiyon personeli 7/24 hizmet veriyor ve çok yardımsever.",
            "Wi-Fi hızı iyi, tüm otelde sorunsuz internet var.",
            "Otelin bahçesi çok güzel düzenlenmiş, yeşillik bol."
        ]
        
        sample_metadata = [
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "temizlik", "rating": 9.0},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "temizlik", "rating": 9.5},
            {"hotel_id": "hotel_002", "language": "tr", "aspect": "konum", "rating": 8.5},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "kahvaltı", "rating": 8.8},
            {"hotel_id": "hotel_002", "language": "tr", "aspect": "personel", "rating": 9.2},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "oda", "rating": 8.7},
            {"hotel_id": "hotel_003", "language": "tr", "aspect": "spa", "rating": 8.9},
            {"hotel_id": "hotel_002", "language": "tr", "aspect": "yemek", "rating": 8.6},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "havuz", "rating": 8.4},
            {"hotel_id": "hotel_003", "language": "tr", "aspect": "klima", "rating": 9.1},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "temizlik", "rating": 9.3},
            {"hotel_id": "hotel_002", "language": "tr", "aspect": "güvenlik", "rating": 8.8},
            {"hotel_id": "hotel_003", "language": "tr", "aspect": "personel", "rating": 9.0},
            {"hotel_id": "hotel_001", "language": "tr", "aspect": "wifi", "rating": 8.3},
            {"hotel_id": "hotel_002", "language": "tr", "aspect": "bahçe", "rating": 8.7}
        ]
        
        try:
            # Check current document count
            stats = await self.vector_store.get_statistics()
            current_count = stats.get('document_count', 0)
            
            if current_count == 0:
                logger.info("📥 Index is empty, loading sample Turkish hotel review data...")
                
                # Add documents to vector store
                added_count = await self.vector_store.add_documents(
                    documents=sample_documents,
                    metadata_list=sample_metadata,
                    batch_size=10
                )
                
                logger.info(f"✅ Added {added_count} sample documents to vector store")
                
                # Also add to vector retriever
                added_count_vr = await self.vector_retriever.add_documents(
                    documents=sample_documents,
                    metadata_list=sample_metadata,
                    batch_size=10
                )
                
                logger.info(f"✅ Added {added_count_vr} sample documents to vector retriever")
                
                self.test_results['sample_data_loaded'] = True
                return True
            else:
                logger.info(f"📋 Index already contains {current_count} documents")
                self.test_results['sample_data_loaded'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to load sample data: {e}")
            self.test_results['sample_data_loaded'] = False
            return False
    
    async def test_vector_search_queries(self):
        """Test various search queries including Turkish."""
        logger.info("🔍 Testing vector search queries...")
        
        test_queries = [
            # Turkish queries
            ("otel temizliği hakkında yorum", 5, 0.0),  # Target query from user
            ("temizlik", 3, 0.0),
            ("personel hizmet kalitesi", 3, 0.0),
            ("kahvaltı çeşitleri", 3, 0.0),
            ("oda temizliği", 3, 0.0),
            
            # English queries
            ("hotel cleanliness", 3, 0.0),
            ("staff service", 3, 0.0),
            ("room comfort", 3, 0.0),
            
            # High threshold test
            ("temizlik", 3, 0.7),
        ]
        
        query_results = {}
        
        for query, top_k, min_score in test_queries:
            try:
                logger.info(f"🔍 Testing query: '{query}' (top_k={top_k}, min_score={min_score})")
                
                # Test vector store
                start_time = time.time()
                vs_results = await self.vector_store.search(
                    query=query,
                    top_k=top_k,
                    min_score=min_score
                )
                vs_time = (time.time() - start_time) * 1000
                
                # Test vector retriever
                start_time = time.time()
                vr_results = await self.vector_retriever.retrieve_similar_docs_with_scores(
                    query=query,
                    top_k=top_k,
                    min_score=min_score
                )
                vr_time = (time.time() - start_time) * 1000
                
                query_results[query] = {
                    'vector_store': {
                        'results_count': len(vs_results),
                        'execution_time_ms': vs_time,
                        'results': [
                            {
                                'score': r.score,
                                'content_preview': r.content[:100] + "..." if len(r.content) > 100 else r.content,
                                'metadata': r.metadata
                            } for r in vs_results
                        ]
                    },
                    'vector_retriever': {
                        'results_count': len(vr_results),
                        'execution_time_ms': vr_time,
                        'results': [
                            {
                                'score': r.score,
                                'content_preview': r.content[:100] + "..." if len(r.content) > 100 else r.content,
                                'metadata': r.metadata
                            } for r in vr_results
                        ]
                    }
                }
                
                logger.info(f"  📊 Vector Store: {len(vs_results)} results in {vs_time:.2f}ms")
                logger.info(f"  📊 Vector Retriever: {len(vr_results)} results in {vr_time:.2f}ms")
                
                if vs_results:
                    logger.info(f"  🏆 Best VS match: {vs_results[0].score:.4f} - {vs_results[0].content[:50]}...")
                if vr_results:
                    logger.info(f"  🏆 Best VR match: {vr_results[0].score:.4f} - {vr_results[0].content[:50]}...")
                
                if not vs_results and not vr_results:
                    logger.warning(f"  ⚠️  No results found for query: '{query}'")
                
            except Exception as e:
                logger.error(f"❌ Failed to test query '{query}': {e}")
                query_results[query] = {'error': str(e)}
        
        self.test_results['query_tests'] = query_results
        return query_results
    
    async def test_specific_turkish_query(self):
        """Test the specific Turkish query mentioned in the issue."""
        logger.info("🎯 Testing specific Turkish query: 'otel temizliği hakkında yorum'")
        
        target_query = "otel temizliği hakkında yorum"
        
        try:
            # Test with different parameters
            test_configs = [
                {"top_k": 5, "min_score": 0.0},
                {"top_k": 10, "min_score": 0.0},
                {"top_k": 5, "min_score": 0.1},
                {"top_k": 5, "min_score": 0.3},
            ]
            
            results = {}
            
            for config in test_configs:
                config_key = f"top_k_{config['top_k']}_min_score_{config['min_score']}"
                logger.info(f"  🔧 Testing config: {config}")
                
                # Test vector store
                vs_results = await self.vector_store.search(
                    query=target_query,
                    **config
                )
                
                # Test vector retriever
                vr_results = await self.vector_retriever.retrieve_similar_docs_with_scores(
                    query=target_query,
                    **config
                )
                
                results[config_key] = {
                    'config': config,
                    'vector_store_results': len(vs_results),
                    'vector_retriever_results': len(vr_results),
                    'vs_top_scores': [r.score for r in vs_results[:3]],
                    'vr_top_scores': [r.score for r in vr_results[:3]],
                    'vs_sample_results': [
                        {'score': r.score, 'content': r.content[:100], 'metadata': r.metadata}
                        for r in vs_results[:2]
                    ],
                    'vr_sample_results': [
                        {'score': r.score, 'content': r.content[:100], 'metadata': r.metadata}
                        for r in vr_results[:2]
                    ]
                }
                
                logger.info(f"    📊 VS Results: {len(vs_results)}, VR Results: {len(vr_results)}")
                if vs_results:
                    logger.info(f"    🏆 VS Top score: {vs_results[0].score:.4f}")
                if vr_results:
                    logger.info(f"    🏆 VR Top score: {vr_results[0].score:.4f}")
            
            self.test_results['turkish_query_test'] = results
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to test Turkish query: {e}")
            return {'error': str(e)}
    
    async def generate_diagnostics_report(self):
        """Generate comprehensive diagnostics report."""
        logger.info("📋 Generating diagnostics report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": self.test_results,
            "recommendations": []
        }
        
        # Analyze results and provide recommendations
        index_status = self.test_results.get('index_status', {})
        if index_status.get('has_documents', False):
            report["recommendations"].append("✅ Index contains documents and is ready for search")
        else:
            report["recommendations"].append("⚠️  Index is empty - consider loading documents")
        
        # Check query performance
        query_tests = self.test_results.get('query_tests', {})
        if query_tests:
            successful_queries = sum(1 for result in query_tests.values() if 'error' not in result)
            total_queries = len(query_tests)
            success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
            
            report["recommendations"].append(f"📊 Query success rate: {success_rate:.1f}% ({successful_queries}/{total_queries})")
            
            # Check for queries with no results
            no_result_queries = []
            for query, result in query_tests.items():
                if 'error' not in result:
                    vs_count = result.get('vector_store', {}).get('results_count', 0)
                    vr_count = result.get('vector_retriever', {}).get('results_count', 0)
                    if vs_count == 0 and vr_count == 0:
                        no_result_queries.append(query)
            
            if no_result_queries:
                report["recommendations"].append(f"⚠️  Queries with no results: {', '.join(no_result_queries)}")
                report["recommendations"].append("💡 Consider lowering min_score or checking query relevance")
        
        # Save report
        report_filename = f"vector_search_diagnostics_{int(time.time())}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Diagnostics report saved to: {report_filename}")
        return report
    
    async def run_full_diagnostics(self):
        """Run complete vector search diagnostics."""
        logger.info("🚀 Starting comprehensive vector search diagnostics...")
        
        try:
            # Initialize components
            await self.initialize_components()
            
            # Check index status
            has_docs = await self.check_index_status()
            
            # Load sample data if needed
            if not has_docs:
                await self.load_sample_data_if_needed()
                # Recheck status after loading data
                await self.check_index_status()
            
            # Test search queries
            await self.test_vector_search_queries()
            
            # Test specific Turkish query
            await self.test_specific_turkish_query()
            
            # Generate report
            report = await self.generate_diagnostics_report()
            report_filename = f"vector_search_diagnostics_{int(time.time())}.json"
            
            logger.info("🎉 Vector search diagnostics completed successfully!")
            
            # Print summary
            print("\n" + "="*60)
            print("📊 VECTOR SEARCH DIAGNOSTICS SUMMARY")
            print("="*60)
            
            index_status = self.test_results.get('index_status', {})
            vs_stats = index_status.get('vector_store', {})
            vr_stats = index_status.get('vector_retriever', {})
            
            print(f"📈 Vector Store Documents: {vs_stats.get('document_count', 0)}")
            print(f"📈 Vector Retriever Documents: {vr_stats.get('document_count', 0)}")
            print(f"🔍 Total Search Tests: {len(self.test_results.get('query_tests', {}))}")
            
            # Print Turkish query test results
            turkish_test = self.test_results.get('turkish_query_test', {})
            if turkish_test:
                print(f"\n🎯 Turkish Query Test Results:")
                for config_key, result in turkish_test.items():
                    if 'error' not in result:
                        vs_count = result.get('vector_store_results', 0)
                        vr_count = result.get('vector_retriever_results', 0)
                        print(f"  {config_key}: VS={vs_count}, VR={vr_count}")
            
            print(f"\n📄 Full report: {report_filename}")
            print("="*60)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Diagnostics failed: {e}")
            raise


async def main():
    """Main diagnostic execution."""
    diagnostic = VectorSearchDiagnostic()
    await diagnostic.run_full_diagnostics()


if __name__ == "__main__":
    asyncio.run(main())
