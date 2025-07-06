"""
Search and retrieval endpoints for the Graph RAG pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.models.dto import (
    SearchRequest, 
    HybridSearchResult, 
    IndexRequest, 
    IndexResponse,
    ErrorResponse,
    SearchType
)
from app.core.gremlin_client import GremlinClient
from app.core.vector_store import VectorStore
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()


def get_gremlin_client(request) -> GremlinClient:
    """Dependency to get Gremlin client from app state."""
    return request.app.state.gremlin_client


def get_vector_store(request) -> VectorStore:
    """Dependency to get vector store from app state."""
    return request.app.state.vector_store


def get_rag_pipeline(request) -> RAGPipeline:
    """Dependency to get RAG pipeline from app state."""
    return request.app.state.rag_pipeline


@router.post("/search", response_model=HybridSearchResult)
async def search(
    request: SearchRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Perform hybrid search combining graph and semantic search.
    
    This endpoint supports multiple search types:
    - **graph**: Search only in the graph database using Gremlin queries
    - **semantic**: Search only in the vector store using embeddings
    - **hybrid**: Combine both graph and semantic search (default)
    
    The response includes:
    - Graph database results (nodes and edges)
    - Semantic search results with similarity scores
    - Generated response from LLM based on retrieved context
    - Performance metrics and metadata
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        result = await rag_pipeline.search(request)
        return result
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="SEARCH_ERROR",
            message=f"Search operation failed: {str(e)}",
            details={"search_type": request.search_type, "query": request.query}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.get("/search/simple")
async def simple_search(
    q: str = Query(..., description="Search query", min_length=1, max_length=1000),
    search_type: SearchType = Query(SearchType.HYBRID, description="Type of search to perform"),
    max_results: Optional[int] = Query(10, ge=1, le=100, description="Maximum number of results"),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Simple search endpoint with query parameters.
    
    A convenience endpoint for quick searches without requiring a JSON payload.
    Supports the same functionality as the main search endpoint.
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        request = SearchRequest(
            query=q,
            search_type=search_type,
            max_results=max_results
        )
        
        result = await rag_pipeline.search(request)
        return result
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="SEARCH_ERROR",
            message=f"Search operation failed: {str(e)}",
            details={"search_type": search_type, "query": q}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.post("/index", response_model=IndexResponse)
async def index_documents(
    request: IndexRequest,
    background_tasks: BackgroundTasks,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Index documents in the vector store for semantic search.
    
    This endpoint allows you to add new documents to the vector store.
    Documents should include:
    - **content**: The main text content to be indexed
    - **metadata**: Optional metadata for filtering and context
    
    Large batches are processed in the background to avoid timeouts.
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        # For large batches, process in background
        if len(request.documents) > 500:
            # Start background indexing
            background_tasks.add_task(
                _background_index_documents,
                rag_pipeline,
                request.documents,
                request.batch_size
            )
            
            return IndexResponse(
                indexed_count=0,
                failed_count=0,
                errors=[],
                execution_time_ms=0.0
            )
        else:
            # Process immediately for smaller batches
            result = await rag_pipeline.index_documents(
                documents=request.documents,
                batch_size=request.batch_size
            )
            
            return IndexResponse(
                indexed_count=result["indexed_count"],
                failed_count=result["failed_count"],
                errors=[],
                execution_time_ms=result["execution_time_ms"]
            )
            
    except Exception as e:
        error_response = ErrorResponse(
            error_code="INDEX_ERROR",
            message=f"Indexing operation failed: {str(e)}",
            details={"document_count": len(request.documents)}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


async def _background_index_documents(
    rag_pipeline: RAGPipeline,
    documents: List[Dict[str, Any]],
    batch_size: int
):
    """Background task for indexing large document batches."""
    try:
        await rag_pipeline.index_documents(
            documents=documents,
            batch_size=batch_size
        )
    except Exception as e:
        # Log error - in production, you might want to store this in a job queue
        print(f"Background indexing failed: {e}")


@router.get("/graph/nodes/{node_id}/relationships")
async def get_node_relationships(
    node_id: str,
    max_depth: int = Query(2, ge=1, le=5, description="Maximum traversal depth"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    gremlin_client: GremlinClient = Depends(get_gremlin_client)
):
    """
    Get relationships for a specific node in the graph database.
    
    This endpoint traverses the graph to find connected nodes and edges
    up to the specified depth. Useful for exploring graph structure
    and understanding entity relationships.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        result = await gremlin_client.get_node_relationships(
            node_id=node_id,
            max_depth=max_depth,
            limit=limit
        )
        return result
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="GRAPH_ERROR",
            message=f"Failed to get node relationships: {str(e)}",
            details={"node_id": node_id, "max_depth": max_depth}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.get("/graph/search")
async def graph_search(
    label: str = Query(..., description="Node label to search"),
    property_name: str = Query(..., description="Property name to search by"),
    property_value: str = Query(..., description="Property value to match"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    gremlin_client: GremlinClient = Depends(get_gremlin_client)
):
    """
    Search for nodes in the graph database by property values.
    
    This endpoint performs targeted searches in the graph database
    using specific node labels and property filters.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        result = await gremlin_client.search_nodes_by_property(
            label=label,
            property_name=property_name,
            property_value=property_value,
            limit=limit
        )
        return result
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="GRAPH_ERROR",
            message=f"Graph search failed: {str(e)}",
            details={
                "label": label,
                "property_name": property_name,
                "property_value": property_value
            }
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.get("/semantic/search")
async def semantic_search(
    query: str = Query(..., description="Search query", min_length=1, max_length=1000),
    top_k: int = Query(5, ge=1, le=50, description="Number of top results"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Perform semantic search in the vector store.
    
    This endpoint searches for semantically similar documents
    using embedding similarity. Results are ranked by similarity score.
    """
    if not vector_store or not vector_store.is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector store not available"
        )
    
    try:
        results = await vector_store.search(
            query=query,
            top_k=top_k,
            min_score=min_score
        )
        return {"results": results}
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="SEMANTIC_ERROR",
            message=f"Semantic search failed: {str(e)}",
            details={"query": query, "top_k": top_k}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.get("/statistics")
async def get_statistics(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get comprehensive statistics for the RAG pipeline.
    
    Returns performance metrics, usage statistics, and system information
    for all components of the pipeline.
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        stats = await rag_pipeline.get_statistics()
        return stats
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="STATS_ERROR",
            message=f"Failed to get statistics: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.delete("/index/clear")
async def clear_index(
    confirm: bool = Query(False, description="Confirmation required"),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Clear all documents from the vector store index.
    
    **WARNING**: This operation is irreversible and will delete all indexed documents.
    Requires explicit confirmation via the 'confirm' parameter.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Index clearing requires explicit confirmation. Set confirm=true"
        )
    
    if not vector_store or not vector_store.is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Vector store not available"
        )
    
    try:
        await vector_store.clear_index()
        return {
            "message": "Index cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_response = ErrorResponse(
            error_code="CLEAR_ERROR",
            message=f"Failed to clear index: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
