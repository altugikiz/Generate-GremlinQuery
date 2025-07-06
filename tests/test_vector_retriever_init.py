#!/usr/bin/env python3
"""
Test Vector Retriever Initialization
"""

import asyncio
from app.core.vector_retriever import VectorRetriever
from app.config.settings import get_settings
from loguru import logger

async def test_vector_retriever_initialization():
    """Test if vector retriever properly loads existing files."""
    
    settings = get_settings()
    
    logger.info("🧪 Testing Vector Retriever Initialization")
    logger.info(f"📁 Store path: {settings.vector_db_uri}")
    logger.info(f"📇 Index name: {settings.vector_index}")
    logger.info(f"🤖 Embedding model: {settings.huggingface_embedding_model}")
    
    # Create vector retriever instance
    vector_retriever = VectorRetriever(
        embedding_model=settings.huggingface_embedding_model,
        store_path=settings.vector_db_uri,
        index_name=settings.vector_index,
        api_token=settings.huggingface_api_token
    )
    
    logger.info(f"📂 Looking for files:")
    logger.info(f"   Index: {vector_retriever.index_file}")
    logger.info(f"   Metadata: {vector_retriever.metadata_file}")
    
    # Check if files exist
    import os
    index_exists = os.path.exists(vector_retriever.index_file)
    metadata_exists = os.path.exists(vector_retriever.metadata_file)
    
    logger.info(f"📊 File existence check:")
    logger.info(f"   Index file exists: {index_exists}")
    logger.info(f"   Metadata file exists: {metadata_exists}")
    
    if not (index_exists and metadata_exists):
        logger.error("❌ Required files not found!")
        return False
    
    # Initialize vector retriever
    logger.info("🔄 Initializing vector retriever...")
    await vector_retriever.initialize()
    
    # Check statistics
    stats = await vector_retriever.get_statistics()
    logger.info(f"📈 Vector retriever statistics:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    # Test a search
    if stats.get('document_count', 0) > 0:
        logger.info("🔍 Testing search functionality...")
        results = await vector_retriever.retrieve_similar_docs_with_scores(
            query="otel temizliği hakkında yorum",
            top_k=3,
            min_score=0.0
        )
        
        logger.info(f"✅ Search completed: {len(results)} results found")
        for i, result in enumerate(results[:3], 1):
            logger.info(f"   {i}. Score: {result.score:.4f} | Content: {result.content[:50]}...")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_vector_retriever_initialization())
