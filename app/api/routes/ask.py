"""
Ask endpoint for natural language queries using Graph RAG pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.core.rag_pipeline import EnhancedRAGPipeline


router = APIRouter(prefix="/api/v1", tags=["ask"])


class AskRequest(BaseModel):
    """Request model for natural language queries."""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=500)
    include_context: bool = Field(False, description="Whether to include search context in response")
    include_query_translation: bool = Field(False, description="Whether to include the generated Gremlin query")


class AskResponse(BaseModel):
    """Response model for natural language queries."""
    answer: str = Field(..., description="Generated answer")
    query: str = Field(..., description="Original user query")
    gremlin_query: Optional[str] = Field(None, description="Generated Gremlin query (if requested)")
    context: Optional[str] = Field(None, description="Search context (if requested)")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    development_mode: bool = Field(False, description="Whether running in development mode")


def get_rag_pipeline():
    """Dependency to get RAG pipeline from app state."""
    from main import app
    return app.state.rag_pipeline


def get_development_mode():
    """Dependency to get development mode status."""
    from main import app
    return app.state.development_mode


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline),
    development_mode: bool = Depends(get_development_mode)
):
    """
    Ask a natural language question using the Graph RAG pipeline.
    
    This endpoint:
    1. Translates natural language to Gremlin queries
    2. Performs graph database search
    3. Conducts semantic vector search
    4. Combines results and generates comprehensive answers
    
    Examples:
    - "What are the best hotels in New York?"
    - "Show me reviews with complaints about cleanliness"
    - "Which hotels have the highest rated service?"
    - "Find hotels mentioned in reviews about location and convenience"
    """
    if not rag_pipeline:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not available"
        )
    
    try:
        logger.info(f"Processing ask request: '{request.query}'")
        
        import time
        start_time = time.time()
        
        # Generate answer using Graph RAG pipeline
        answer = await rag_pipeline.graph_rag_answer(request.query)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Prepare response
        response = AskResponse(
            answer=answer,
            query=request.query,
            execution_time_ms=execution_time,
            development_mode=development_mode
        )
        
        # Add optional context if requested
        if request.include_query_translation and rag_pipeline.graph_query_llm:
            try:
                gremlin_query = await rag_pipeline.graph_query_llm.generate_gremlin_query(request.query)
                response.gremlin_query = gremlin_query
            except Exception as e:
                logger.warning(f"Failed to generate Gremlin query for response: {e}")
        
        if request.include_context:
            # This would require refactoring the pipeline to return context
            # For now, we'll include a note about this feature
            response.context = "Context extraction feature coming soon. Use the detailed search endpoints for raw results."
        
        logger.info(f"Ask request completed in {execution_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Ask request failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/ask/examples")
async def get_ask_examples():
    """
    Get example queries that work well with the Graph RAG system.
    
    Returns a list of example questions organized by category.
    """
    examples = {
        "hotel_search": [
            "What are the best hotels in New York?",
            "Find luxury hotels with high ratings",
            "Show me hotels in Paris with good location scores"
        ],
        "review_analysis": [
            "What are the most common complaints about hotel service?",
            "Find reviews that mention cleanliness issues",
            "Show me positive reviews about hotel amenities"
        ],
        "aspect_analysis": [
            "Which hotels have the best cleanliness ratings?",
            "Find hotels with excellent service but poor location",
            "Show me hotels with consistent high ratings across all aspects"
        ],
        "comparative_analysis": [
            "Compare Marriott and Hilton hotels based on guest reviews",
            "Which hotel chain has the best customer service?",
            "Find hotels that compete with luxury brands"
        ],
        "trend_analysis": [
            "How have hotel ratings changed over the past year?",
            "Show me trending issues in recent hotel reviews",
            "Find hotels with improving or declining reputation"
        ]
    }
    
    return {
        "examples": examples,
        "tips": [
            "Be specific about what you're looking for",
            "Mention locations, hotel names, or specific aspects when relevant",
            "Ask about trends, comparisons, or specific criteria",
            "Use natural language - the system will translate to appropriate queries"
        ],
        "supported_entities": [
            "Hotels", "Reviews", "Hotel Groups", "Aspects (cleanliness, service, location, etc.)",
            "Languages", "Sources", "Accommodation Types", "Amenities"
        ]
    }


@router.get("/ask/suggestions/{query}")
async def get_query_suggestions(
    query: str,
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get suggested related queries based on the input query.
    
    Args:
        query: Base query to generate suggestions for
        
    Returns:
        List of suggested related queries
    """
    if not rag_pipeline or not rag_pipeline.graph_query_llm:
        raise HTTPException(
            status_code=503,
            detail="Query suggestion service not available"
        )
    
    try:
        suggestions = await rag_pipeline.graph_query_llm.suggest_similar_queries(query)
        
        return {
            "original_query": query,
            "suggestions": suggestions,
            "suggestion_count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate query suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get("/ask/explain/{gremlin_query}")
async def explain_gremlin_query(
    gremlin_query: str,
    rag_pipeline: EnhancedRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Get a human-readable explanation of a Gremlin query.
    
    Args:
        gremlin_query: Gremlin query to explain
        
    Returns:
        Human-readable explanation of the query
    """
    if not rag_pipeline or not rag_pipeline.graph_query_llm:
        raise HTTPException(
            status_code=503,
            detail="Query explanation service not available"
        )
    
    try:
        explanation = await rag_pipeline.graph_query_llm.explain_query(gremlin_query)
        
        return {
            "gremlin_query": gremlin_query,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Failed to explain Gremlin query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to explain query: {str(e)}"
        )
