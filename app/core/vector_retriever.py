"""
Vector Retriever Module

This module provides semantic document retrieval using Hugging Face embeddings
and FAISS vector search. It supports document indexing, similarity search,
and metadata filtering for the RAG pipeline.
"""

import os
import asyncio
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import time
from loguru import logger

from app.models.dto import SemanticResult
from app.config.settings import get_settings


class VectorRetriever:
    """
    Hugging Face-based vector retriever for semantic document search.
    
    Features:
    - Sentence transformer embeddings (Hugging Face)
    - FAISS vector index for fast similarity search
    - Persistent storage and loading
    - Metadata filtering and ranking
    - Batch processing support
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        store_path: str = "hf_faiss_index",
        index_name: str = "hotel_reviews",
        embedding_dimension: int = 384,
        api_token: Optional[str] = None
    ):
        """
        Initialize the vector retriever.
        
        Args:
            embedding_model: Hugging Face model name for embeddings
            store_path: Path for storing FAISS index files
            index_name: Name of the vector index
            embedding_dimension: Dimension of embedding vectors
            api_token: Hugging Face API token (optional)
        """
        self.embedding_model_name = embedding_model
        self.store_path = store_path
        self.index_name = index_name
        self.embedding_dimension = embedding_dimension
        self.api_token = api_token
        
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
        
        # File paths
        self.index_file = f"{self.store_path}_{self.index_name}.faiss"
        self.metadata_file = f"{self.store_path}_{self.index_name}_metadata.pkl"
    
    async def initialize(self) -> None:
        """Initialize the vector retriever and load existing index if available."""
        try:
            logger.info(f"Initializing vector retriever with model: {self.embedding_model_name}")
            
            # Load sentence transformer model
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.embedding_model_name)
            )
            logger.info(f"✅ Loaded embedding model: {self.embedding_model_name}")
            
            # Initialize or load FAISS index
            await self._initialize_index()
            
            self._is_initialized = True
            logger.info("✅ Vector retriever initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector retriever: {e}")
            raise
    
    async def _initialize_index(self) -> None:
        """Initialize or load the FAISS index."""
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            # Load existing index
            logger.info(f"Loading existing FAISS index from {self.index_file}")
            
            loop = asyncio.get_event_loop()
            self.index = await loop.run_in_executor(
                None,
                faiss.read_index,
                self.index_file
            )
            
            with open(self.metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.metadata = data.get('metadata', [])
            
            logger.info(f"✅ Loaded index with {len(self.documents)} documents")
        else:
            # Create new index
            logger.info("Creating new FAISS index")
            self.index = faiss.IndexFlatL2(self.embedding_dimension)  # L2 distance
            self.documents = []
            self.metadata = []
            logger.info("✅ Created new FAISS index")
    
    async def retrieve_similar_docs(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Retrieve semantically similar documents.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold (0-1)
            filters: Optional metadata filters
            
        Returns:
            List of similar document texts
        """
        if not self._is_initialized:
            raise RuntimeError("Vector retriever not initialized")
        
        if self.index.ntotal == 0:
            logger.warning("No documents in index")
            return []
        
        start_time = time.time()
        
        try:
            logger.debug(f"Retrieving similar docs for: '{query}' (top_k={top_k})")
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Search in FAISS index
            # Note: FAISS returns squared L2 distances, lower is better
            distances, indices = self.index.search(
                query_embedding, 
                min(top_k * 2, self.index.ntotal)
            )
            
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                # Convert distance to similarity score (0-1, higher is better)
                # For L2 distance, we use: similarity = 1 / (1 + distance)
                similarity = 1.0 / (1.0 + distance)
                
                if similarity < min_score:
                    continue
                
                # Get document and metadata
                doc = self.documents[idx]
                meta = self.metadata[idx]
                
                # Apply filters if specified
                if filters and not self._matches_filters(meta, filters):
                    continue
                
                results.append(doc)
                
                if len(results) >= top_k:
                    break
            
            execution_time = (time.time() - start_time) * 1000
            self._search_count += 1
            self._total_search_time += execution_time
            
            logger.debug(f"Retrieved {len(results)} documents in {execution_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ Document retrieval failed: {e}")
            raise
    
    async def retrieve_similar_docs_with_scores(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SemanticResult]:
        """
        Retrieve semantically similar documents with scores and metadata.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            min_score: Minimum similarity score threshold (0-1)
            filters: Optional metadata filters
            
        Returns:
            List of SemanticResult objects with content, scores, and metadata
        """
        if not self._is_initialized:
            raise RuntimeError("Vector retriever not initialized")
        
        if self.index.ntotal == 0:
            logger.warning("No documents in index")
            return []
        
        start_time = time.time()
        
        try:
            logger.debug(f"Retrieving similar docs with scores for: '{query}' (top_k={top_k})")
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            # Search in FAISS index
            distances, indices = self.index.search(
                query_embedding, 
                min(top_k * 2, self.index.ntotal)
            )
            
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue
                
                # Convert distance to similarity score (0-1, higher is better)
                similarity = 1.0 / (1.0 + distance)
                
                if similarity < min_score:
                    continue
                
                # Get document and metadata
                doc = self.documents[idx]
                meta = self.metadata[idx]
                
                # Apply filters if specified
                if filters and not self._matches_filters(meta, filters):
                    continue
                
                result = SemanticResult(
                    id=str(meta.get('doc_id', idx)),
                    content=doc,
                    score=float(similarity),
                    metadata=meta
                )
                results.append(result)
                
                if len(results) >= top_k:
                    break
            
            execution_time = (time.time() - start_time) * 1000
            self._search_count += 1
            self._total_search_time += execution_time
            
            logger.debug(f"Retrieved {len(results)} documents with scores in {execution_time:.2f}ms")
            return results
            
        except Exception as e:
            logger.error(f"❌ Document retrieval with scores failed: {e}")
            raise
    
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
            raise RuntimeError("Vector retriever not initialized")
        
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
            # Save FAISS index
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                faiss.write_index,
                self.index,
                self.index_file
            )
            
            # Save metadata
            data = {
                'documents': self.documents,
                'metadata': self.metadata,
                'embedding_model': self.embedding_model_name,
                'dimension': self.embedding_dimension
            }
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug(f"Index saved to {self.index_file}")
            
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector retriever statistics."""
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
        logger.info("Clearing vector retriever index")
        
        self.index = faiss.IndexFlatL2(self.embedding_dimension)
        self.documents = []
        self.metadata = []
        
        await self._save_index()
        logger.info("✅ Index cleared successfully")
    
    async def close(self) -> None:
        """Close the vector retriever and save any pending changes."""
        if self._is_initialized:
            await self._save_index()
            logger.info("✅ Vector retriever closed successfully")


# Factory function for dependency injection
def get_vector_retriever() -> VectorRetriever:
    """Get or create Vector Retriever instance."""
    settings = get_settings()
    return VectorRetriever(
        embedding_model=settings.huggingface_embedding_model,
        store_path=settings.vector_db_uri,
        index_name=settings.vector_index,
        api_token=settings.huggingface_api_token
    )
