"""
Schema API endpoints for exploring the domain model.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional

from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.core.domain_schema import get_schema_summary, VERTICES, EDGES

router = APIRouter()


def get_schema_gremlin_client(request) -> SchemaAwareGremlinClient:
    """Dependency to get schema-aware Gremlin client from app state."""
    return request.app.state.gremlin_client


@router.get("/schema/info")
async def get_schema_info(
    gremlin_client: SchemaAwareGremlinClient = Depends(get_schema_gremlin_client)
) -> Dict[str, Any]:
    """
    Get comprehensive information about the domain schema.
    
    Returns the complete schema definition including vertices, edges,
    and their properties and descriptions.
    """
    try:
        schema_info = await gremlin_client.get_schema_info()
        summary = get_schema_summary()
        
        return {
            "schema_definition": schema_info,
            "summary": summary,
            "version": "1.0",
            "description": "Hotel Review Graph RAG Domain Schema"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schema information: {str(e)}"
        )


@router.get("/schema/vertices")
async def get_vertex_types() -> Dict[str, Any]:
    """
    Get all vertex types defined in the schema.
    
    Returns detailed information about each vertex type including
    properties and descriptions.
    """
    return {
        "vertices": [
            {
                "label": vertex.label,
                "description": vertex.description,
                "properties": vertex.properties,
                "property_count": len(vertex.properties)
            }
            for vertex in VERTICES
        ],
        "total_count": len(VERTICES)
    }


@router.get("/schema/edges")
async def get_edge_types() -> Dict[str, Any]:
    """
    Get all edge types defined in the schema.
    
    Returns detailed information about each edge type including
    source/target vertices and descriptions.
    """
    return {
        "edges": [
            {
                "label": edge.label,
                "description": edge.description,
                "source_vertex": edge.out_v,
                "target_vertex": edge.in_v,
                "properties": edge.properties,
                "property_count": len(edge.properties)
            }
            for edge in EDGES
        ],
        "total_count": len(EDGES)
    }


@router.get("/schema/statistics")
async def get_schema_statistics(
    gremlin_client: SchemaAwareGremlinClient = Depends(get_schema_gremlin_client)
) -> Dict[str, Any]:
    """
    Get statistics about the actual graph data based on the schema.
    
    Returns counts of vertices and edges by type, showing how much
    data is present for each schema element.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        stats = await gremlin_client.get_schema_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schema statistics: {str(e)}"
        )


@router.get("/schema/vertex/{vertex_label}")
async def get_vertex_details(vertex_label: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific vertex type.
    
    Includes the vertex definition and related edges.
    """
    # Find the vertex
    vertex = None
    for v in VERTICES:
        if v.label == vertex_label:
            vertex = v
            break
    
    if not vertex:
        raise HTTPException(
            status_code=404,
            detail=f"Vertex type '{vertex_label}' not found"
        )
    
    # Find related edges
    incoming_edges = [e for e in EDGES if e.in_v == vertex_label]
    outgoing_edges = [e for e in EDGES if e.out_v == vertex_label]
    
    return {
        "vertex": {
            "label": vertex.label,
            "description": vertex.description,
            "properties": vertex.properties
        },
        "relationships": {
            "incoming": [
                {
                    "label": e.label,
                    "from": e.out_v,
                    "description": e.description
                }
                for e in incoming_edges
            ],
            "outgoing": [
                {
                    "label": e.label,
                    "to": e.in_v,
                    "description": e.description
                }
                for e in outgoing_edges
            ]
        },
        "connectivity": {
            "incoming_count": len(incoming_edges),
            "outgoing_count": len(outgoing_edges),
            "total_connections": len(incoming_edges) + len(outgoing_edges)
        }
    }


@router.post("/schema/search/vertex")
async def search_vertices_by_type(
    vertex_label: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    gremlin_client: SchemaAwareGremlinClient = Depends(get_schema_gremlin_client)
):
    """
    Search for vertices of a specific type with optional filters.
    
    Uses the schema-aware client to perform type-safe searches.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        result = await gremlin_client.search_by_vertex_type(
            vertex_label=vertex_label,
            filters=filters,
            limit=limit
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/schema/hotels/aspects")
async def search_hotels_by_aspects(
    aspects: str,  # Comma-separated list
    min_score: float = 3.0,
    limit: int = 10,
    gremlin_client: SchemaAwareGremlinClient = Depends(get_schema_gremlin_client)
):
    """
    Search for hotels based on specific aspect scores.
    
    Example usage: /schema/hotels/aspects?aspects=cleanliness,service&min_score=4.0
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        aspect_list = [aspect.strip() for aspect in aspects.split(',')]
        result = await gremlin_client.search_hotels_with_aspects(
            aspect_names=aspect_list,
            min_score=min_score,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Hotel aspect search failed: {str(e)}"
        )


@router.get("/schema/hotels/{hotel_id}/sentiment-trends")
async def get_hotel_sentiment_trends(
    hotel_id: str,
    days: int = 90,
    gremlin_client: SchemaAwareGremlinClient = Depends(get_schema_gremlin_client)
):
    """
    Get sentiment trends for a specific hotel over time.
    
    Analyzes review sentiment patterns to show how hotel perception
    has changed over the specified time period.
    """
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Gremlin client not available"
        )
    
    try:
        trends = await gremlin_client.get_sentiment_trends(
            hotel_id=hotel_id,
            time_range_days=days
        )
        return trends
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sentiment trend analysis failed: {str(e)}"
        )
