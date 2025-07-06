"""
Enhanced Graph RAG endpoints - /ask and /filter
Implements the exact specifications for natural language and structured filter queries.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
import time
from loguru import logger

from app.models.dto import (
    AskRequest, 
    AskResponse, 
    FilterRequest, 
    FilterResponse, 
    SemanticChunk,
    GraphRAGFilters
)
from app.core.rag_pipeline import EnhancedRAGPipeline
from app.core.graph_query_llm import GraphQueryLLM
from app.core.vector_retriever import VectorRetriever
from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.config.settings import get_settings

router = APIRouter(prefix="/api/v1", tags=["graph-rag"])

# Dependency functions
def get_rag_pipeline():
    """Dependency to get RAG pipeline from app state."""
    from main import app
    return getattr(app.state, 'rag_pipeline', None)

def get_graph_query_llm():
    """Dependency to get Graph Query LLM."""
    from main import app
    return getattr(app.state, 'graph_query_llm', None)

def get_gremlin_client():
    """Dependency to get Gremlin client from app state."""
    from main import app
    return getattr(app.state, 'gremlin_client', None)

def get_vector_retriever():
    """Dependency to get Vector Retriever from app state."""
    from main import app
    return getattr(app.state, 'vector_retriever', None)


@router.post("/ask", response_model=AskResponse)
async def ask_natural_language_query(
    request: AskRequest,
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline),
    graph_query_llm: GraphQueryLLM = Depends(get_graph_query_llm),
    vector_retriever: VectorRetriever = Depends(get_vector_retriever)
):
    """
    Natural Language Query Endpoint
    
    Accepts a JSON request with:
    {
        "query": "natural language question",
        "filters": {
            "language": "en",
            "source": "booking",
            "aspect": "staff",
            "sentiment": "negative",
            "room": "205",
            "date_range": "last_30_days"
        }
    }
    
    Process:
    - Use LLM to translate the query (optionally enriched with filters) into a Gremlin query
    - Optionally apply filters directly to Gremlin traversal
    - Optionally retrieve semantic matches using vector store (Hugging Face embeddings)
    
    Returns:
    {
        "gremlin_query": "...",
        "semantic_chunks": [...],
        "answer": "..."
    }
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        start_time = time.time()
        component_times = {}
        
        logger.info(f"Processing natural language query: '{request.query}'")
        
        # Step 1: Translate natural language to Gremlin query using LLM
        gremlin_query = None
        query_translation_start = time.time()
        
        if graph_query_llm and request.include_gremlin_query:
            try:
                # Enrich query with filters if provided
                enriched_query = request.query
                if request.filters:
                    filter_context = _build_filter_context(request.filters)
                    enriched_query = f"{request.query}\\n\\nFilters: {filter_context}"
                
                gremlin_query = await graph_query_llm.generate_gremlin_query(enriched_query)
                logger.info(f"Generated Gremlin query: {gremlin_query}")
            except Exception as e:
                logger.warning(f"Failed to generate Gremlin query: {e}")
        
        component_times["query_translation"] = (time.time() - query_translation_start) * 1000
        
        # Step 2: Execute graph search (if Gremlin client available)
        graph_results_count = 0
        graph_search_start = time.time()
        
        if gremlin_query and request.max_graph_results:
            try:
                # Execute the generated Gremlin query
                # This would be implemented with actual graph execution
                pass
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")
        
        component_times["graph_search"] = (time.time() - graph_search_start) * 1000
        
        # Step 3: Retrieve semantic matches using vector store
        semantic_chunks = []
        semantic_results_count = 0
        semantic_search_start = time.time()
        
        if vector_retriever and request.include_semantic_chunks:
            try:
                max_semantic = request.max_semantic_results or 5
                semantic_results = await vector_retriever.search(
                    query=request.query,
                    top_k=max_semantic,
                    filters=_convert_filters_to_metadata(request.filters) if request.filters else None
                )
                
                # Convert to SemanticChunk objects
                for result in semantic_results[:max_semantic]:
                    if isinstance(result, dict):
                        chunk = SemanticChunk(
                            content=result.get("content", ""),
                            similarity_score=result.get("similarity_score", 0.0),
                            metadata=result.get("metadata", {}),
                            source=result.get("source")
                        )
                        semantic_chunks.append(chunk)
                        semantic_results_count += 1
                
                logger.info(f"Retrieved {semantic_results_count} semantic chunks")
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")
        
        component_times["semantic_search"] = (time.time() - semantic_search_start) * 1000
        
        # Step 4: Generate answer using LLM
        answer = "No answer generated"
        response_generation_start = time.time()
        
        if request.use_llm_summary and rag_pipeline:
            try:
                # Use the existing RAG pipeline to generate answer
                result = await rag_pipeline.graph_rag_answer(
                    user_query=request.query,
                    include_context=request.include_context,
                    include_query_translation=False,  # We already did this
                    filters=_convert_filters_to_dict(request.filters) if request.filters else None
                )
                answer = result.get("answer", "No answer generated")
            except Exception as e:
                logger.warning(f"Answer generation failed: {e}")
                answer = f"I encountered an issue generating an answer: {str(e)}"
        
        component_times["response_generation"] = (time.time() - response_generation_start) * 1000
        
        # Calculate total execution time
        total_execution_time = (time.time() - start_time) * 1000
        
        # Build response
        response = AskResponse(
            query=request.query,
            answer=answer,
            gremlin_query=gremlin_query if request.include_gremlin_query else None,
            semantic_chunks=semantic_chunks if request.include_semantic_chunks else None,
            context=None,  # Implement if request.include_context is True
            graph_results_count=graph_results_count,
            semantic_results_count=semantic_results_count,
            execution_time_ms=total_execution_time,
            component_times=component_times,
            development_mode=getattr(get_settings(), 'development_mode', False),
            filters_applied=_convert_filters_to_dict(request.filters) if request.filters else None
        )
        
        logger.info(f"Natural language query completed in {total_execution_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Natural language query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process natural language query: {str(e)}"
        )


@router.post("/filter", response_model=FilterResponse)
async def structured_filter_query(
    request: FilterRequest,
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client),
    graph_query_llm: GraphQueryLLM = Depends(get_graph_query_llm)
):
    """
    Structured Filter Query Endpoint
    
    Accepts a JSON body with only filters, no natural language query:
    {
        "filters": {
            "language": "tr",
            "aspect": "cleanliness",
            "sentiment": "negative",
            "source": "tripadvisor",
            "room": "301",
            "date_range": "last_7_days"
        }
    }
    
    Process:
    - Directly build and run a Gremlin query using the filter parameters
    - Do not use LLM for query generation
    - Optionally summarize the results with LLM
    
    Returns:
    {
        "gremlin_query": "...",
        "results": [...],
        "summary": "..."
    }
    """
    try:
        start_time = time.time()
        component_times = {}
        
        logger.info(f"Processing structured filter query with filters: {request.filters}")
        
        # Step 1: Build Gremlin query directly from filters (no LLM)
        query_generation_start = time.time()
        gremlin_query = await _build_gremlin_from_filters(
            request.filters, 
            request.max_results
        )
        component_times["query_generation"] = (time.time() - query_generation_start) * 1000
        
        logger.info(f"Generated filter-based Gremlin query: {gremlin_query}")
        
        # Step 2: Execute the query
        results = []
        results_count = 0
        graph_search_start = time.time()
        
        if gremlin_client and gremlin_client.is_connected:
            try:
                raw_results = await gremlin_client.execute_query(gremlin_query)
                results = raw_results if isinstance(raw_results, list) else [raw_results]
                results_count = len(results)
                logger.info(f"Retrieved {results_count} results from graph database")
            except Exception as e:
                logger.error(f"Graph query execution failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to execute graph query: {str(e)}"
                )
        else:
            logger.warning("Gremlin client not available - returning empty results")
        
        component_times["graph_search"] = (time.time() - graph_search_start) * 1000
        
        # Step 3: Generate summary with LLM (optional)
        summary = None
        summary_generation_start = time.time()
        
        if request.use_llm_summary and graph_query_llm and results:
            try:
                summary_prompt = f"""
                Analyze these query results from a hotel review database and provide a concise summary:
                
                Applied Filters: {request.filters}
                Results Count: {results_count}
                Sample Results: {str(results[:3]) if results else 'No results'}
                
                Provide insights about what these results reveal about hotel performance,
                guest satisfaction, and any notable patterns. Be specific and actionable.
                """
                summary = await graph_query_llm._call_gemini(summary_prompt)
                logger.info("Generated LLM summary for filter results")
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")
        
        component_times["summary_generation"] = (time.time() - summary_generation_start) * 1000
        
        # Calculate total execution time
        total_execution_time = (time.time() - start_time) * 1000
        
        # Assess query complexity
        query_complexity = _assess_query_complexity(request.filters)
        
        # Build response
        response = FilterResponse(
            filters=_convert_filters_to_dict(request.filters),
            gremlin_query=gremlin_query if request.include_gremlin_query else None,
            results=results if request.include_results else None,
            results_count=results_count,
            summary=summary,
            execution_time_ms=total_execution_time,
            component_times=component_times,
            query_complexity=query_complexity
        )
        
        logger.info(f"Structured filter query completed in {total_execution_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Structured filter query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process filter query: {str(e)}"
        )


# Helper Functions

def _build_filter_context(filters: GraphRAGFilters) -> str:
    """Build a context string from filters for LLM enhancement."""
    context_parts = []
    
    if filters.language:
        context_parts.append(f"Language: {filters.language}")
    if filters.source:
        context_parts.append(f"Source: {filters.source}")
    if filters.aspect:
        context_parts.append(f"Aspect: {filters.aspect}")
    if filters.sentiment:
        context_parts.append(f"Sentiment: {filters.sentiment}")
    if filters.room:
        context_parts.append(f"Room: {filters.room}")
    if filters.date_range:
        context_parts.append(f"Date Range: {filters.date_range}")
    if filters.hotel:
        context_parts.append(f"Hotel: {filters.hotel}")
    if filters.guest_type:
        context_parts.append(f"Guest Type: {filters.guest_type}")
    if filters.min_rating is not None:
        context_parts.append(f"Min Rating: {filters.min_rating}")
    if filters.max_rating is not None:
        context_parts.append(f"Max Rating: {filters.max_rating}")
    
    return ", ".join(context_parts)


def _convert_filters_to_metadata(filters: GraphRAGFilters) -> Dict[str, Any]:
    """Convert GraphRAGFilters to metadata dict for vector search."""
    metadata = {}
    
    if filters.language:
        metadata["language"] = filters.language
    if filters.source:
        metadata["source"] = filters.source
    if filters.aspect:
        metadata["aspect"] = filters.aspect
    if filters.sentiment:
        metadata["sentiment"] = filters.sentiment
    if filters.hotel:
        metadata["hotel"] = filters.hotel
    if filters.guest_type:
        metadata["guest_type"] = filters.guest_type
    
    return metadata


def _convert_filters_to_dict(filters: GraphRAGFilters) -> Dict[str, Any]:
    """Convert GraphRAGFilters to a dictionary."""
    if not filters:
        return {}
        
    return {
        k: v for k, v in filters.dict().items() 
        if v is not None
    }


async def _build_gremlin_from_filters(filters: GraphRAGFilters, max_results: int) -> str:
    """
    Build a Gremlin query directly from structured filters.
    No LLM involved - pure filter-to-query conversion.
    """
    query_parts = ["g.V()"]
    
    # Start with appropriate vertex type based on filters
    if filters.hotel:
        query_parts.append(f".hasLabel('Hotel').has('name', '{filters.hotel}')")
    elif filters.aspect or filters.sentiment:
        query_parts.append(".hasLabel('Review')")
    else:
        query_parts.append(".hasLabel('Review')")  # Default to reviews
    
    # Apply language filter
    if filters.language:
        query_parts.append(f".where(__.out('WRITTEN_IN').has('code', '{filters.language}'))")
    
    # Apply source filter
    if filters.source:
        query_parts.append(f".where(__.out('FROM_SOURCE').has('name', '{filters.source}'))")
    
    # Apply aspect filter
    if filters.aspect:
        query_parts.append(f".where(__.out('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', '{filters.aspect}'))")
    
    # Apply sentiment filter
    if filters.sentiment:
        query_parts.append(f".where(__.out('HAS_ANALYSIS').has('overall_sentiment', '{filters.sentiment}'))")
    
    # Apply room filter
    if filters.room:
        query_parts.append(f".where(__.out('ABOUT_ROOM').has('number', '{filters.room}'))")
    
    # Apply guest type filter
    if filters.guest_type:
        query_parts.append(f".where(__.in('WROTE').has('type', '{filters.guest_type}'))")
    
    # Apply rating filters
    if filters.min_rating is not None:
        query_parts.append(f".has('overall_score', gte({filters.min_rating}))")
    
    if filters.max_rating is not None:
        query_parts.append(f".has('overall_score', lte({filters.max_rating}))")
    
    # Apply date range filter (simplified)
    if filters.date_range:
        if filters.date_range == "last_7_days":
            query_parts.append(".has('date', gte('now-7d'))")
        elif filters.date_range == "last_30_days":
            query_parts.append(".has('date', gte('now-30d'))")
        elif filters.date_range == "last_14_days":
            query_parts.append(".has('date', gte('now-14d'))")
    
    # Add result limiting and output format
    query_parts.append(f".limit({max_results})")
    query_parts.append(".valueMap().with('~tinkerpop.valueMap.tokens')")
    
    return "".join(query_parts)


def _assess_query_complexity(filters: GraphRAGFilters) -> str:
    """Assess the complexity of the generated query based on filters."""
    filter_count = sum(1 for v in filters.dict().values() if v is not None)
    
    if filter_count <= 2:
        return "simple"
    elif filter_count <= 5:
        return "medium"
    else:
        return "complex"


# Additional utility endpoints for debugging and testing

@router.get("/ask/examples")
async def get_ask_examples():
    """Get example queries for the /ask endpoint."""
    return {
        "examples": [
            {
                "query": "What are guests saying about the staff at luxury hotels?",
                "filters": {
                    "aspect": "staff",
                    "sentiment": "positive",
                    "guest_type": "business"
                }
            },
            {
                "query": "Find hotels with cleanliness complaints",
                "filters": {
                    "aspect": "cleanliness",
                    "sentiment": "negative",
                    "date_range": "last_30_days"
                }
            },
            {
                "query": "Show me Turkish reviews about location",
                "filters": {
                    "language": "tr",
                    "aspect": "location",
                    "source": "tripadvisor"
                }
            }
        ]
    }


@router.get("/filter/examples")
async def get_filter_examples():
    """Get example filter configurations for the /filter endpoint."""
    return {
        "examples": [
            {
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness",
                    "sentiment": "negative",
                    "source": "tripadvisor",
                    "date_range": "last_7_days"
                }
            },
            {
                "filters": {
                    "hotel": "Grand Plaza Hotel",
                    "guest_type": "VIP",
                    "min_rating": 8.0,
                    "aspect": "service"
                }
            },
            {
                "filters": {
                    "room": "301",
                    "date_range": "last_14_days",
                    "sentiment": "negative"
                }
            }
        ]
    }
