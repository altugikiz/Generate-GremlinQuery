"""
Data Transfer Objects (DTOs) for API requests and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
from datetime import datetime


class SearchType(str, Enum):
    """Supported search types."""
    GRAPH = "graph"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    search_type: SearchType = Field(default=SearchType.HYBRID, description="Type of search to perform")
    max_results: Optional[int] = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters for the search")
    include_embeddings: bool = Field(default=False, description="Whether to include embeddings in the response")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate and clean the query string."""
        return v.strip()


class GraphNode(BaseModel):
    """Represents a node in the graph database."""
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Node label/type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "hotel_123",
                "label": "Hotel",
                "properties": {
                    "name": "Grand Hotel",
                    "rating": 4.5,
                    "location": "New York"
                }
            }
        }


class GraphEdge(BaseModel):
    """Represents an edge in the graph database."""
    id: str = Field(..., description="Unique identifier for the edge")
    label: str = Field(..., description="Edge label/type")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "review_456",
                "label": "reviews",
                "source_id": "user_789",
                "target_id": "hotel_123",
                "properties": {
                    "rating": 5,
                    "review_text": "Excellent service!",
                    "date": "2023-01-15"
                }
            }
        }


class GraphResult(BaseModel):
    """Result from graph database query."""
    nodes: List[GraphNode] = Field(default_factory=list, description="Retrieved nodes")
    edges: List[GraphEdge] = Field(default_factory=list, description="Retrieved edges")
    total_count: int = Field(default=0, description="Total number of results")
    execution_time_ms: float = Field(default=0.0, description="Query execution time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {
                        "id": "hotel_123",
                        "label": "Hotel",
                        "properties": {"name": "Grand Hotel", "rating": 4.5}
                    }
                ],
                "edges": [
                    {
                        "id": "review_456",
                        "label": "reviews",
                        "source_id": "user_789",
                        "target_id": "hotel_123",
                        "properties": {"rating": 5, "review_text": "Excellent service!"}
                    }
                ],
                "total_count": 1,
                "execution_time_ms": 125.5
            }
        }


class SemanticResult(BaseModel):
    """Result from semantic/vector search."""
    id: str = Field(..., description="Document/item identifier")
    content: str = Field(..., description="Content text")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding: Optional[List[float]] = Field(default=None, description="Document embedding vector")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123",
                "content": "This hotel has excellent amenities and great service.",
                "score": 0.85,
                "metadata": {
                    "source": "review",
                    "hotel_id": "hotel_123",
                    "date": "2023-01-15"
                }
            }
        }


class HybridSearchResult(BaseModel):
    """Combined result from hybrid search (graph + semantic)."""
    query: str = Field(..., description="Original search query")
    graph_results: GraphResult = Field(..., description="Results from graph database")
    semantic_results: List[SemanticResult] = Field(default_factory=list, description="Results from semantic search")
    generated_response: Optional[str] = Field(default=None, description="LLM-generated response based on retrieved context")
    total_execution_time_ms: float = Field(default=0.0, description="Total execution time")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="Search metadata and statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "best hotels in New York",
                "graph_results": {
                    "nodes": [{"id": "hotel_123", "label": "Hotel", "properties": {"name": "Grand Hotel"}}],
                    "edges": [],
                    "total_count": 1,
                    "execution_time_ms": 125.5
                },
                "semantic_results": [
                    {
                        "id": "doc_123",
                        "content": "Grand Hotel offers excellent service",
                        "score": 0.85,
                        "metadata": {"source": "review"}
                    }
                ],
                "generated_response": "Based on the search results, Grand Hotel appears to be a top choice...",
                "total_execution_time_ms": 250.0,
                "search_metadata": {"graph_query_count": 1, "semantic_query_count": 1}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "SEARCH_ERROR",
                "message": "Failed to execute search query",
                "details": {"reason": "Invalid query syntax"},
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2023-01-15T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    components: Dict[str, str] = Field(default_factory=dict, description="Individual component statuses")
    version: str = Field(default="1.0.0", description="Application version")
    uptime_seconds: float = Field(default=0.0, description="Application uptime in seconds")
    development_mode: bool = Field(default=False, description="Whether running in development mode")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-01-15T10:30:00Z",
                "components": {
                    "gremlin": "healthy",
                    "vector_store": "healthy",
                    "rag_pipeline": "healthy"
                },
                "version": "1.0.0",
                "uptime_seconds": 3600.0,
                "development_mode": False
            }
        }


class IndexRequest(BaseModel):
    """Request model for indexing operations."""
    documents: List[Dict[str, Any]] = Field(..., min_items=1, description="Documents to index")
    index_name: Optional[str] = Field(default=None, description="Target index name")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch size for indexing")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "doc_123",
                        "content": "Hotel review content",
                        "metadata": {"hotel_id": "hotel_123", "rating": 5}
                    }
                ],
                "index_name": "hotel_reviews",
                "batch_size": 100,
                "overwrite": False
            }
        }


class IndexResponse(BaseModel):
    """Response model for indexing operations."""
    indexed_count: int = Field(..., description="Number of documents successfully indexed")
    failed_count: int = Field(default=0, description="Number of documents that failed to index")
    errors: List[str] = Field(default_factory=list, description="List of indexing errors")
    execution_time_ms: float = Field(default=0.0, description="Indexing execution time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indexed_count": 95,
                "failed_count": 5,
                "errors": ["Document doc_123 already exists"],
                "execution_time_ms": 1500.0
            }
        }


# New models for Graph RAG endpoints

class GraphRAGFilters(BaseModel):
    """Standard filters for Graph RAG queries."""
    language: Optional[str] = Field(None, description="Filter by language code (e.g., 'en', 'tr')")
    source: Optional[str] = Field(None, description="Filter by review source (e.g., 'booking', 'tripadvisor')")
    aspect: Optional[str] = Field(None, description="Filter by aspect (e.g., 'staff', 'cleanliness', 'location')")
    sentiment: Optional[str] = Field(None, description="Filter by sentiment (e.g., 'positive', 'negative', 'neutral')")
    room: Optional[str] = Field(None, description="Filter by room number or identifier")
    date_range: Optional[str] = Field(None, description="Filter by date range (e.g., 'last_30_days', 'last_7_days')")
    hotel: Optional[str] = Field(None, description="Filter by hotel name or identifier")
    guest_type: Optional[str] = Field(None, description="Filter by guest type (e.g., 'VIP', 'regular', 'business')")
    min_rating: Optional[float] = Field(None, ge=0, le=10, description="Minimum rating filter")
    max_rating: Optional[float] = Field(None, ge=0, le=10, description="Maximum rating filter")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "en",
                "source": "booking",
                "aspect": "staff",
                "sentiment": "negative",
                "room": "205",
                "date_range": "last_30_days",
                "hotel": "Grand Plaza Hotel",
                "guest_type": "business",
                "min_rating": 1.0,
                "max_rating": 5.0
            }
        }


class AskRequest(BaseModel):
    """Request model for the /ask endpoint with natural language queries."""
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language question")
    filters: Optional[GraphRAGFilters] = Field(None, description="Optional filters to apply")
    include_gremlin_query: bool = Field(True, description="Include generated Gremlin query in response")
    include_semantic_chunks: bool = Field(True, description="Include retrieved semantic chunks")
    include_context: bool = Field(False, description="Include full context used for answer generation")
    max_graph_results: Optional[int] = Field(None, ge=1, le=100, description="Maximum graph results to retrieve")
    max_semantic_results: Optional[int] = Field(None, ge=1, le=50, description="Maximum semantic results to retrieve")
    use_llm_summary: bool = Field(True, description="Use LLM to generate summary/answer")
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        """Validate and clean the query string."""
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are guests saying about the staff at luxury hotels?",
                "filters": {
                    "aspect": "staff",
                    "sentiment": "positive",
                    "guest_type": "business",
                    "date_range": "last_30_days"
                },
                "include_gremlin_query": True,
                "include_semantic_chunks": True,
                "include_context": False,
                "max_graph_results": 10,
                "max_semantic_results": 5,
                "use_llm_summary": True
            }
        }


class SemanticChunk(BaseModel):
    """Semantic search result chunk."""
    content: str = Field(..., description="Text content of the chunk")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    source: Optional[str] = Field(None, description="Source identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "The staff was incredibly helpful and professional during our stay.",
                "similarity_score": 0.89,
                "metadata": {
                    "hotel": "Grand Plaza Hotel",
                    "review_date": "2024-01-15",
                    "guest_type": "business"
                },
                "source": "review_12345"
            }
        }


class AskResponse(BaseModel):
    """Response model for the /ask endpoint."""
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="LLM-generated answer based on retrieved context")
    gremlin_query: Optional[str] = Field(None, description="Generated Gremlin query (if requested)")
    semantic_chunks: Optional[List[SemanticChunk]] = Field(None, description="Retrieved semantic chunks (if requested)")
    context: Optional[str] = Field(None, description="Full context used for answer generation (if requested)")
    graph_results_count: int = Field(default=0, description="Number of graph results retrieved")
    semantic_results_count: int = Field(default=0, description="Number of semantic results retrieved")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    component_times: Dict[str, float] = Field(default_factory=dict, description="Breakdown of execution times by component")
    development_mode: bool = Field(False, description="Whether running in development mode")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are guests saying about the staff at luxury hotels?",
                "answer": "Based on recent reviews, guests consistently praise the staff at luxury hotels for their professionalism, attentiveness, and exceptional service quality. Common positive themes include personalized attention, quick problem resolution, and multilingual capabilities.",
                "gremlin_query": "g.V().hasLabel('Hotel').where(__.out('HAS_REVIEW').out('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'staff')).limit(10)",
                "semantic_chunks": [
                    {
                        "content": "The staff was incredibly helpful and professional during our stay.",
                        "similarity_score": 0.89,
                        "metadata": {"hotel": "Grand Plaza Hotel", "review_date": "2024-01-15"}
                    }
                ],
                "context": None,
                "graph_results_count": 5,
                "semantic_results_count": 3,
                "execution_time_ms": 1450.2,
                "component_times": {
                    "query_translation": 320.5,
                    "graph_search": 180.3,
                    "semantic_search": 290.1,
                    "response_generation": 659.3
                },
                "development_mode": False,
                "filters_applied": {
                    "aspect": "staff",
                    "sentiment": "positive"
                }
            }
        }


class FilterRequest(BaseModel):
    """Request model for the /filter endpoint with structured filters only."""
    filters: GraphRAGFilters = Field(..., description="Structured filters to apply")
    include_gremlin_query: bool = Field(True, description="Include generated Gremlin query in response")
    include_results: bool = Field(True, description="Include query results in response")
    use_llm_summary: bool = Field(True, description="Generate LLM summary of results")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results to retrieve")
    result_format: str = Field(default="summary", description="Format for results: 'summary', 'detailed', 'raw'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness",
                    "sentiment": "negative",
                    "source": "tripadvisor",
                    "room": "301",
                    "date_range": "last_7_days"
                },
                "include_gremlin_query": True,
                "include_results": True,
                "use_llm_summary": True,
                "max_results": 15,
                "result_format": "summary"
            }
        }


class FilterResponse(BaseModel):
    """Response model for the /filter endpoint."""
    filters: Dict[str, Any] = Field(..., description="Applied filters")
    gremlin_query: Optional[str] = Field(None, description="Generated Gremlin query (if requested)")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Query results (if requested)")
    results_count: int = Field(default=0, description="Number of results retrieved")
    summary: Optional[str] = Field(None, description="LLM-generated summary of results (if requested)")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    component_times: Dict[str, float] = Field(default_factory=dict, description="Breakdown of execution times by component")
    query_complexity: str = Field(default="simple", description="Assessed complexity of the generated query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness",
                    "sentiment": "negative",
                    "source": "tripadvisor",
                    "date_range": "last_7_days"
                },
                "gremlin_query": "g.V().hasLabel('Review').where(__.out('WRITTEN_IN').has('code', 'tr')).where(__.out('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness')).limit(15)",
                "results": [
                    {
                        "hotel": "Hotel Example",
                        "review_text": "Oda temizliği yetersizdi",
                        "rating": 2.5,
                        "date": "2024-01-10"
                    }
                ],
                "results_count": 8,
                "summary": "Analysis of 8 Turkish reviews shows consistent complaints about room cleanliness in the past week, with average ratings of 2.3/5 for cleanliness aspect.",
                "execution_time_ms": 890.1,
                "component_times": {
                    "query_generation": 45.2,
                    "graph_search": 320.8,
                    "summary_generation": 524.1
                },
                "query_complexity": "medium"
            }
        }
