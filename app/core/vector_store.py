"""
Vector store implementation for semantic search using Hugging Face embeddings and FAISS.
Supports document indexing, similarity search, and embedding management.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.metrics.pairwise import cosine_similarity
import time
from loguru import logger

from app.models.dto import SemanticResult


class VectorStore:
    """
    Vector store for semantic search using Hugging Face embeddings and FAISS index.
    
    Features:
    - Sentence transformer embeddings
    - FAISS vector index for fast similarity search
    - Persistent storage and loading
    - Batch processing for large datasets
    - Configurable similarity thresholds
    """
    
    def __init__(
        self,
        store_type: str = "huggingface",
        db_uri: str = "hf_faiss_index",
        index_name: str = "default",
        embedding_model: str = "all-MiniLM-L6-v2",
        api_token: Optional[str] = None,
        embedding_dimension: int = 384
    ):
        """
        Initialize vector store.
        
        Args:
            store_type: Type of vector store (currently supports 'huggingface')
            db_uri: Database URI or file path for persistence
            index_name: Name of the vector index
            embedding_model: Hugging Face model name for embeddings
            api_token: Hugging Face API token (optional)
            embedding_dimension: Dimension of embedding vectors
        """
        self.store_type = store_type
        self.db_uri = db_uri
        self.index_name = index_name
        self.embedding_model_name = embedding_model
        self.api_token = api_token
        self.embedding_dimension = embedding_dimension
        
        # Initialize components
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self._is_initialized = False
        
        # Performance tracking
        self._search_count = 0
        self._total_search_time = 0.0
        self._index_count = 0
        
    async def initialize(self) -> None:
        """Initialize the vector store and load existing index if available."""
        try:
            logger.info(f"Initializing vector store with model: {self.embedding_model_name}")
            
            # Load sentence transformer model
            self.model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"✅ Loaded embedding model: {self.embedding_model_name}")
            
            # Initialize or load FAISS index
            await self._initialize_index()
            
            self._is_initialized = True
            logger.info("✅ Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
            raise
    
    async def _initialize_index(self) -> None:
        """Initialize or load the FAISS index."""
        index_file = f"{self.db_uri}_{self.index_name}.faiss"
        metadata_file = f"{self.db_uri}_{self.index_name}_metadata.pkl"
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            # Load existing index
            logger.info(f"Loading existing FAISS index from {index_file}")
            self.index = faiss.read_index(index_file)
            
            with open(metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.metadata = data.get('metadata', [])
            
            logger.info(f"✅ Loaded index with {len(self.documents)} documents")
        else:
            # Create new index
            logger.info("Creating new FAISS index")
            self.index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
            self.documents = []
            self.metadata = []
            logger.info("✅ Created new FAISS index")
    
    async def add_documents(
        self,
        documents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100
    ) -> int:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata_list: Optional metadata for each document
            batch_size: Batch size for processing
            
        Returns:
            Number of documents successfully added
        """
        if not self._is_initialized:
            raise RuntimeError("Vector store not initialized")
        
        if metadata_list is None:
            metadata_list = [{}] * len(documents)
        
        if len(documents) != len(metadata_list):
            raise ValueError("Documents and metadata lists must have the same length")
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        start_time = time.time()
        
        try:
            added_count = 0
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_metadata = metadata_list[i:i + batch_size]
                
                # Generate embeddings for batch
                embeddings = await self._generate_embeddings(batch_docs)
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Add to index
                self.index.add(embeddings)
                
                # Store documents and metadata
                for j, (doc, meta) in enumerate(zip(batch_docs, batch_metadata)):
                    doc_id = len(self.documents)
                    self.documents.append(doc)
                    
                    # Add document ID to metadata
                    meta_with_id = {**meta, 'doc_id': doc_id, 'added_at': time.time()}
                    self.metadata.append(meta_with_id)
                    
                    added_count += 1
                
                logger.debug(f"Processed batch {i//batch_size + 1}, added {len(batch_docs)} documents")
            
            # Save updated index
            await self._save_index()
            
            execution_time = time.time() - start_time
            self._index_count += added_count
            
            logger.info(f"✅ Added {added_count} documents in {execution_time:.2f}s")
            return added_count
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SemanticResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold
            filters: Optional metadata filters
            
        Returns:
            List of semantic search results
        """
        if not self._is_initialized:
            raise RuntimeError("Vector store not initialized")
        
        if self.index.ntotal == 0:
            logger.warning("No documents in index")
            return []
        
        # Add enhanced logging for debugging
        logger.info(f"🔍 Vector search query: '{query}'")
        logger.info(f"📊 Index contains {self.index.ntotal} documents")
        logger.info(f"🎯 Searching for top_k={top_k}, min_score={min_score}")
        
        start_time = time.time()
        
        try:
            logger.debug(f"Searching for: '{query}' (top_k={top_k})")
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            faiss.normalize_L2(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding, min(top_k * 2, self.index.ntotal))
            
            logger.info(f"📈 Raw FAISS search returned {len(scores[0])} candidates")
            logger.debug(f"🔢 Raw scores: {scores[0][:10]}")  # Log first 10 scores
            logger.debug(f"🔢 Raw indices: {indices[0][:10]}")  # Log first 10 indices
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx == -1:  # Invalid index
                    logger.debug(f"⚠️  Skipping invalid index at position {i}")
                    continue
                
                if score < min_score:
                    logger.debug(f"⚠️  Score {score:.4f} below threshold {min_score} at position {i}")
                    continue
                
                # Normalize score to prevent Pydantic validation errors
                # FAISS inner product scores can exceed 1.0, but our model expects scores <= 1.0
                normalized_score = min(float(score), 1.0)
                
                # Get document and metadata
                doc = self.documents[idx]
                meta = self.metadata[idx]
                
                # Apply filters if specified
                if filters and not self._matches_filters(meta, filters):
                    logger.debug(f"⚠️  Document {idx} filtered out by metadata filters")
                    continue
                
                result = SemanticResult(
                    id=str(meta.get('doc_id', idx)),
                    content=doc,
                    score=normalized_score,
                    metadata=meta
                )
                results.append(result)
                
                logger.debug(f"✅ Added result {len(results)}: raw_score={score:.4f}, normalized_score={normalized_score:.4f}, doc_id={meta.get('doc_id', idx)}")
                
                if len(results) >= top_k:
                    break
            
            execution_time = (time.time() - start_time) * 1000
            self._search_count += 1
            self._total_search_time += execution_time
            
            logger.info(f"🎉 Search completed in {execution_time:.2f}ms, found {len(results)} results")
            if results:
                logger.info(f"📋 Top result score: {results[0].score:.4f}")
                logger.info(f"📋 Lowest result score: {results[-1].score:.4f}")
            else:
                logger.warning("⚠️  No results found - check query relevance or lower min_score")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                self.model.encode,
                texts
            )
            return np.array(embeddings, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches the specified filters."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            meta_value = metadata[key]
            
            if isinstance(value, dict):
                # Handle range filters like {"$gte": 4.0}
                if "$gte" in value and meta_value < value["$gte"]:
                    return False
                if "$lte" in value and meta_value > value["$lte"]:
                    return False
                if "$gt" in value and meta_value <= value["$gt"]:
                    return False
                if "$lt" in value and meta_value >= value["$lt"]:
                    return False
                if "$eq" in value and meta_value != value["$eq"]:
                    return False
                if "$ne" in value and meta_value == value["$ne"]:
                    return False
            elif isinstance(value, list):
                # Handle "in" filters
                if meta_value not in value:
                    return False
            else:
                # Exact match
                if meta_value != value:
                    return False
        
        return True
    
    async def _save_index(self) -> None:
        """Save the FAISS index and metadata to disk."""
        try:
            index_file = f"{self.db_uri}_{self.index_name}.faiss"
            metadata_file = f"{self.db_uri}_{self.index_name}_metadata.pkl"
            
            # Save FAISS index
            faiss.write_index(self.index, index_file)
            
            # Save metadata
            data = {
                'documents': self.documents,
                'metadata': self.metadata,
                'embedding_model': self.embedding_model_name,
                'dimension': self.embedding_dimension
            }
            
            with open(metadata_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug(f"Index saved to {index_file}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "is_initialized": self._is_initialized,
            "document_count": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_dimension,
            "search_count": self._search_count,
            "total_search_time_ms": self._total_search_time,
            "average_search_time_ms": self._total_search_time / max(self._search_count, 1),
            "index_count": self._index_count,
            "model_name": self.embedding_model_name
        }
    
    async def clear_index(self) -> None:
        """Clear all documents from the index."""
        logger.info("Clearing vector store index")
        
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.documents = []
        self.metadata = []
        
        await self._save_index()
        logger.info("✅ Index cleared successfully")
    
    async def close(self) -> None:
        """Close and cleanup vector store resources."""
        try:
            logger.info("Closing vector store...")
            
            if self.index and len(self.documents) > 0:
                await self._save_index()
            
            # Cleanup
            self.model = None
            self.index = None
            self._is_initialized = False
            
            logger.info("✅ Vector store closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if vector store is initialized."""
        return self._is_initialized
