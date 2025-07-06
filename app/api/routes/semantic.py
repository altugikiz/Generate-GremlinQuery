"""
Semantic RAG + Graph Intelligence endpoints.
Provides intelligent endpoints using LLM + Gremlin + Vector Search.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from loguru import logger
import time

from app.core.rag_pipeline import EnhancedRAGPipeline
from app.core.graph_query_llm import GraphQueryLLM
from app.core.vector_retriever import VectorRetriever
from app.core.sync_gremlin_client import SyncGremlinClient
from app.models.dto import ErrorResponse
from app.config.settings import get_settings


router = APIRouter(prefix="/api/v1/semantic", tags=["semantic"])


# Request/Response Models for Semantic Endpoints
class SemanticAskRequest(BaseModel):
    """Request model for semantic ask queries."""
    query: str = Field(..., description="Natural language question", min_length=1, max_length=1000)
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply")
    include_gremlin_query: bool = Field(True, description="Include generated Gremlin query in response")
    include_semantic_chunks: bool = Field(True, description="Include retrieved semantic chunks")
    include_context: bool = Field(False, description="Include full context used for generation")
    max_graph_results: Optional[int] = Field(None, ge=1, le=100, description="Max graph results to retrieve")
    max_semantic_results: Optional[int] = Field(None, ge=1, le=50, description="Max semantic results to retrieve")


class SemanticAskResponse(BaseModel):
    """Response model for semantic ask queries."""
    answer: str = Field(..., description="LLM-generated final answer")
    query: str = Field(..., description="Original user query")
    gremlin_query: Optional[str] = Field(None, description="Generated Gremlin query")
    semantic_chunks: Optional[List[Dict[str, Any]]] = Field(None, description="Retrieved semantic text chunks")
    context: Optional[str] = Field(None, description="Full context used for generation")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    component_times: Dict[str, float] = Field(..., description="Breakdown of execution times")
    development_mode: bool = Field(False, description="Whether running in development mode")


class FilterRequest(BaseModel):
    """Request model for structured filter queries."""
    filters: Dict[str, Any] = Field(..., description="Structured filters to convert to Gremlin")
    summarize_with_llm: bool = Field(True, description="Whether to summarize results with LLM")
    max_results: int = Field(20, ge=1, le=100, description="Maximum results to return")


class FilterResponse(BaseModel):
    """Response model for filter queries."""
    gremlin_query: str = Field(..., description="Generated Gremlin query from filters")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    summary: Optional[str] = Field(None, description="LLM-generated summary of results")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class GremlinTranslationRequest(BaseModel):
    """Request model for natural language to Gremlin translation."""
    prompt: str = Field(..., description="Natural language prompt to convert", min_length=1, max_length=500)
    include_explanation: bool = Field(True, description="Include explanation of the generated query")


class GremlinTranslationResponse(BaseModel):
    """Response model for Gremlin translation."""
    gremlin_query: str = Field(..., description="Generated Gremlin query")
    explanation: Optional[str] = Field(None, description="Explanation of the query")
    confidence_score: float = Field(..., description="Confidence in the translation (0-1)")
    execution_time_ms: float = Field(..., description="Translation time in milliseconds")


class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    top_k: int = Field(10, ge=1, le=50, description="Number of top results to return")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    include_embeddings: bool = Field(False, description="Include embedding vectors in response")


class VectorSearchResponse(BaseModel):
    """Response model for vector search."""
    results: List[Dict[str, Any]] = Field(..., description="Search results with similarity scores")
    query_embedding: Optional[List[float]] = Field(None, description="Query embedding vector")
    execution_time_ms: float = Field(..., description="Search execution time")
    total_documents: int = Field(..., description="Total documents in index")


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    llm_provider: str = Field(..., description="LLM provider name")
    llm_model: str = Field(..., description="LLM model name")
    embedding_model: str = Field(..., description="Embedding model name")
    vector_store_type: str = Field(..., description="Vector store type")
    model_versions: Dict[str, str] = Field(..., description="Model version information")
    capabilities: List[str] = Field(..., description="Supported capabilities")
    performance_stats: Dict[str, Any] = Field(..., description="Performance statistics")


# Dependency functions
def get_rag_pipeline(request: Request) -> EnhancedRAGPipeline:
    """Dependency to get RAG pipeline from app state."""
    return getattr(request.app.state, 'rag_pipeline', None)


def get_graph_query_llm(request: Request) -> GraphQueryLLM:
    """Dependency to get Graph Query LLM from app state."""
    return getattr(request.app.state, 'graph_query_llm', None)


def get_vector_retriever(request: Request) -> VectorRetriever:
    """Dependency to get Vector Retriever from app state."""
    return getattr(request.app.state, 'vector_retriever', None)


def get_gremlin_client(request: Request) -> SyncGremlinClient:
    """Dependency to get Gremlin client from app state."""
    return getattr(request.app.state, 'gremlin_client', None)


# SECTION 2: Semantic RAG + Graph Intelligence Endpoints

@router.post("/ask", response_model=SemanticAskResponse)
async def semantic_ask(
    request: SemanticAskRequest,
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Accept a natural language question and return an intelligent answer.
    
    Uses LLM + Gremlin + vector search to:
    1. Translate natural language to Gremlin query
    2. Execute graph search
    3. Perform semantic vector search
    4. Generate comprehensive answer using LLM
    
    Example:
    {
      "query": "Why are guests complaining about room cleanliness?",
      "filters": {
        "language": "en",
        "aspect": "cleanliness",
        "sentiment": "negative",
        "date_range": "last_14_days"
      }
    }
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available - service initialization failed"
        )
    
    try:
        start_time = time.time()
        
        # Execute RAG pipeline with real database operations
        answer = await rag_pipeline.graph_rag_answer(request.query)
        
        total_time = (time.time() - start_time) * 1000
        
        # Build response with available data
        response = SemanticAskResponse(
            answer=answer,
            query=request.query,
            gremlin_query=None,  # TODO: Add support if needed
            semantic_chunks=None,  # TODO: Add support if needed
            context=None,  # TODO: Add support if needed
            execution_time_ms=total_time,
            component_times={
                "total_execution": total_time,
                "query_translation": 0,
                "graph_search": 0,
                "semantic_search": 0,
                "response_generation": total_time
            },
            development_mode=False  # Always false in production
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in semantic ask: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process semantic query: {str(e)}"
        )


@router.post("/filter", response_model=FilterResponse)
async def semantic_filter(
    request: FilterRequest,
    gremlin_client: SyncGremlinClient = Depends(get_gremlin_client),
    graph_query_llm: GraphQueryLLM = Depends(get_graph_query_llm)
):
    """
    Convert structured filters into a direct Gremlin query.
    
    No LLM translation - direct filter to query conversion.
    Optionally summarizes results with LLM.
    
    Supports filters like:
    - hotel_group: "Marriott"
    - aspect_score: {"cleanliness": ">= 8"}
    - date_range: {"start": "2024-01-01", "end": "2024-12-31"}
    - sentiment: "positive"
    """
    if not gremlin_client:
        raise HTTPException(
            status_code=503,
            detail="Graph database client not available - service initialization failed"
        )

    if not gremlin_client.is_connected:
        logger.error("PRODUCTION MODE: Gremlin client is not connected - failing request")
        raise HTTPException(
            status_code=503,
            detail="Graph database connection not available - check Cosmos DB Gremlin API connectivity"
        )
    
    try:
        start_time = time.time()
        
        # Convert structured filters to Gremlin query
        gremlin_query = await _build_gremlin_from_filters(request.filters, request.max_results)
        
        # Execute the query against real database
        results = await gremlin_client.execute_query(gremlin_query)
        
        # Generate summary if requested and LLM is available
        summary = None
        if request.summarize_with_llm and graph_query_llm and results:
            summary_prompt = f"""
            Analyze these hotel review query results and provide a concise summary:
            
            Applied Filters: {request.filters}
            Results Count: {len(results)}
            Sample Results: {str(results[:3])}
            
            Provide insights about what these results reveal about hotel performance,
            guest satisfaction, and any notable patterns.
            """
            summary = await graph_query_llm._call_gemini(summary_prompt)
        
        execution_time = (time.time() - start_time) * 1000
        
        return FilterResponse(
            gremlin_query=gremlin_query,
            results=results,
            summary=summary,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error in semantic filter execution: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process filter query: {str(e)}"
        )


@router.post("/gremlin", response_model=GremlinTranslationResponse)
async def semantic_gremlin_translation(
    request: GremlinTranslationRequest,
    graph_query_llm: GraphQueryLLM = Depends(get_graph_query_llm)
):
    """
    Convert natural language prompt to Gremlin query only.
    
    Useful for debugging, admin testing, or getting raw queries.
    Returns the Gremlin query without executing it.
    
    Example:
    {
      "prompt": "Find all hotels with cleanliness scores above 8",
      "include_explanation": true
    }
    """
    if not graph_query_llm:
        raise HTTPException(
            status_code=503,
            detail="Graph Query LLM not available - service initialization failed"
        )
    
    try:
        start_time = time.time()
        
        # Generate Gremlin query using real LLM
        gremlin_query = await graph_query_llm.generate_gremlin_query(request.prompt)
        
        if not gremlin_query:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate Gremlin query from natural language prompt"
            )
        
        # Generate explanation if requested
        explanation = None
        confidence_score = 0.8  # Default confidence
        
        if request.include_explanation:
            explanation = await graph_query_llm.explain_query(gremlin_query)
            confidence_score = 0.9  # Higher confidence if explanation was generated
        
        execution_time = (time.time() - start_time) * 1000
        
        return GremlinTranslationResponse(
            gremlin_query=gremlin_query,
            explanation=explanation,
            confidence_score=confidence_score,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Error in Gremlin translation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate to Gremlin: {str(e)}"
        )


@router.post("/vector", response_model=VectorSearchResponse)
async def semantic_vector_search(
    request: VectorSearchRequest,
    vector_retriever: VectorRetriever = Depends(get_vector_retriever)
):
    """
    Perform Hugging Face embedding and FAISS search.
    
    Returns top-K matching texts based on semantic similarity.
    Useful for finding relevant document chunks without graph context.
    
    Example:
    {
      "query": "hotel room cleanliness problems",
      "top_k": 10,
      "min_score": 0.7
    }
    """
    # Enhanced logging for debugging
    logger.info(f"🔍 Vector search endpoint called with query: '{request.query}'")
    logger.info(f"📊 Vector retriever instance: {vector_retriever}")
    logger.info(f"📊 Vector retriever type: {type(vector_retriever)}")
    
    if vector_retriever:
        try:
            stats = await vector_retriever.get_statistics()
            logger.info(f"📈 Vector retriever stats: {stats}")
        except Exception as e:
            logger.error(f"❌ Error getting vector retriever stats: {e}")
    
    if not vector_retriever:
        raise HTTPException(
            status_code=503,
            detail="Vector retriever not available - service initialization failed"
        )
        raise HTTPException(
            status_code=503,
            detail="Vector retriever not available - service initialization failed"
        )
    
    try:
        start_time = time.time()
        
        # Perform vector search against real FAISS index
        search_results = await vector_retriever.retrieve_similar_docs_with_scores(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score
        )
        
        # Convert SemanticResult objects to dictionaries for response
        formatted_results = []
        for result in search_results:
            formatted_result = {
                "id": result.id,
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata
            }
            if request.include_embeddings and hasattr(result, 'embedding') and result.embedding:
                formatted_result["embedding"] = result.embedding
            formatted_results.append(formatted_result)
        
        # Get query embedding if requested
        query_embedding = None
        if request.include_embeddings:
            query_embedding = await vector_retriever.get_query_embedding(request.query)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Get total document count from vector retriever
        stats = await vector_retriever.get_statistics()
        total_documents = stats.get('document_count', 0)
        
        logger.info(f"✅ Vector search completed: {len(formatted_results)} results in {execution_time:.2f}ms")
        
        return VectorSearchResponse(
            results=formatted_results,
            query_embedding=query_embedding,
            execution_time_ms=execution_time,
            total_documents=total_documents
        )
        
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform vector search: {str(e)}"
        )


@router.get("/models", response_model=ModelInfoResponse)
async def get_semantic_models_info(
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline),
    vector_retriever: VectorRetriever = Depends(get_vector_retriever)
):
    """
    Get information about active models and their configurations.
    
    Returns details about:
    - LLM provider and model
    - Embedding model
    - Vector store configuration
    - Performance statistics
    - Supported capabilities
    """
    try:
        settings = get_settings()
        
        # Gather model information
        model_info = {
            "llm_provider": settings.model_provider,
            "llm_model": settings.gemini_model,
            "embedding_model": settings.embedding_model_name,
            "vector_store_type": settings.vector_store_type,
            "model_versions": {
                "gemini": settings.gemini_model,
                "embedding": settings.embedding_model_name,
                "vector_store": settings.vector_store_type
            },
            "capabilities": [
                "natural_language_to_gremlin",
                "semantic_vector_search",
                "hybrid_retrieval",
                "response_generation",
                "query_explanation",
                "filter_translation"
            ],
            "performance_stats": {}
        }
        
        # Get performance statistics if available
        if rag_pipeline:
            try:
                pipeline_stats = await rag_pipeline.get_statistics()
                model_info["performance_stats"]["pipeline"] = pipeline_stats
            except Exception as e:
                logger.warning(f"Could not get pipeline stats: {e}")
        
        if vector_retriever:
            try:
                # Add vector retriever stats if available
                model_info["performance_stats"]["vector_retriever"] = {
                    "status": "available",
                    "embedding_model": getattr(vector_retriever, 'embedding_model', 'unknown')
                }
            except Exception as e:
                logger.warning(f"Could not get vector retriever stats: {e}")
        
        return ModelInfoResponse(**model_info)
        
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model information: {str(e)}"
        )




@router.post("/execute", response_model=Dict[str, Any])
async def execute_gremlin_query(
    request: Dict[str, str],
    gremlin_client: SyncGremlinClient = Depends(get_gremlin_client)
):
    """
    **PRODUCTION MODE** - Execute a raw Gremlin query.
    
    ⚠️  WARNING: This endpoint executes arbitrary Gremlin queries and includes
    basic validation to prevent dangerous operations.
    
    Request body:
    {
        "query": "g.V().hasLabel('Hotel').limit(5).valueMap()"
    }
    
    Returns the raw query results.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available - check Cosmos DB Gremlin API connectivity"
        )
    
    gremlin_query = request.get("query", "").strip()
    if not gremlin_query:
        raise HTTPException(
            status_code=400,
            detail="Query parameter is required"
        )
    
    # Basic validation to prevent obviously dangerous queries
    dangerous_patterns = ["drop", "delete", "clear", "truncate"]
    query_lower = gremlin_query.lower()
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains potentially dangerous operation: {pattern}"
            )
    
    try:
        start_time = time.time()
        results = await gremlin_client.execute_query(gremlin_query)
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "query": gremlin_query,
            "results": results,
            "results_count": len(results) if isinstance(results, list) else 1,
            "execution_time_ms": execution_time,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error executing Gremlin query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )

# Helper Functions

async def _build_gremlin_from_filters(filters: Dict[str, Any], max_results: int) -> str:
    """
    Convert structured filters to a Gremlin query.
    
    This is a simplified implementation - in production you'd want
    more sophisticated filter parsing and validation.
    """
    query_parts = ["g.V()"]
    
    # Handle different filter types
    if "hotel_group" in filters:
        query_parts.append(f".hasLabel('Hotel').where(__.out('BELONGS_TO').has('name', '{filters['hotel_group']}'))")
    elif "hotel_name" in filters:
        query_parts.append(f".hasLabel('Hotel').has('name', '{filters['hotel_name']}')")
    else:
        query_parts.append(".hasLabel('Hotel')")
    
    # Handle aspect score filters
    if "aspect_score" in filters:
        aspect_filters = filters["aspect_score"]
        for aspect, condition in aspect_filters.items():
            if isinstance(condition, str) and ">=" in condition:
                score = float(condition.replace(">=", "").strip())
                query_parts.append(f".where(__.in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', '{aspect}').values('aspect_score').is(gte({score})))")
    
    # Handle sentiment filter
    if "sentiment" in filters:
        sentiment = filters["sentiment"]
        query_parts.append(f".where(__.in('BELONGS_TO').in('HAS_REVIEW').in('HAS_ANALYSIS').has('overall_sentiment', '{sentiment}'))")
    
    # Handle date range
    if "date_range" in filters:
        date_range = filters["date_range"]
        if "start" in date_range:
            query_parts.append(f".where(__.in('BELONGS_TO').in('HAS_REVIEW').has('date', gte('{date_range['start']}')))")
        if "end" in date_range:
            query_parts.append(f".where(__.in('BELONGS_TO').in('HAS_REVIEW').has('date', lte('{date_range['end']}')))")
    
    # Add result limit and output format
    query_parts.append(f".limit({max_results})")
    query_parts.append(".valueMap(true)")  # Use true parameter instead of with() modifier
    
    return "".join(query_parts)
