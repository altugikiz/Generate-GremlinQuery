#!/usr/bin/env python3
"""
Check FAISS Index Contents
"""

import pickle
import faiss
from loguru import logger

def check_faiss_index():
    """Check the contents of the FAISS index files."""
    
    index_file = "hf_faiss_index_hotel_reviews.faiss"
    metadata_file = "hf_faiss_index_hotel_reviews_metadata.pkl"
    
    logger.info("🔍 Checking FAISS index files...")
    
    try:
        # Load FAISS index
        index = faiss.read_index(index_file)
        logger.info(f"✅ FAISS index loaded: {index.ntotal} documents")
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            data = pickle.load(f)
            documents = data.get('documents', [])
            metadata = data.get('metadata', [])
            
        logger.info(f"✅ Metadata loaded: {len(documents)} documents, {len(metadata)} metadata entries")
        
        if documents:
            logger.info(f"📝 Sample documents:")
            for i, doc in enumerate(documents[:3]):
                logger.info(f"   {i+1}. {doc[:100]}...")
                
        if metadata:
            logger.info(f"📋 Sample metadata:")
            for i, meta in enumerate(metadata[:3]):
                logger.info(f"   {i+1}. {meta}")
        
        return len(documents)
        
    except Exception as e:
        logger.error(f"❌ Error checking FAISS index: {e}")
        return 0

if __name__ == "__main__":
    document_count = check_faiss_index()
    print(f"\n📊 Final count: {document_count} documents in FAISS index")
