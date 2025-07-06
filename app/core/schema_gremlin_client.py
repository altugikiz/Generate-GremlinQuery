"""
Enhanced Gremlin client with domain schema integration.
Provides schema-aware query building and validation.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.gremlin_client import GremlinClient as BaseGremlinClient
from app.core.domain_schema import VERTICES, EDGES, get_vertex_by_label, get_edges_for_vertex
from app.models.dto import GraphResult, GraphNode, GraphEdge


class SchemaAwareGremlinClient(BaseGremlinClient):
    """
    Enhanced Gremlin client with domain schema integration.
    
    Provides schema-aware query building, validation, and enhanced search capabilities
    based on the defined domain schema.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema_vertices = {v.label: v for v in VERTICES}
        self.schema_edges = {e.label: e for e in EDGES}
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the domain schema."""
        return {
            "vertices": [
                {
                    "label": v.label,
                    "description": v.description,
                    "properties": v.properties
                }
                for v in VERTICES
            ],
            "edges": [
                {
                    "label": e.label,
                    "from": e.out_v,
                    "to": e.in_v,
                    "description": e.description,
                    "properties": e.properties
                }
                for e in EDGES
            ]
        }
    
    async def search_by_vertex_type(
        self,
        vertex_label: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> GraphResult:
        """
        Search for vertices of a specific type with optional filters.
        
        Args:
            vertex_label: Type of vertex to search for
            filters: Property filters to apply
            limit: Maximum number of results
            
        Returns:
            GraphResult containing matching vertices
        """
        if vertex_label not in self.schema_vertices:
            raise ValueError(f"Unknown vertex type: {vertex_label}")
        
        # Build query based on filters
        query_parts = [f"g.V().hasLabel('{vertex_label}')"]
        
        if filters:
            for prop, value in filters.items():
                if isinstance(value, str):
                    query_parts.append(f".has('{prop}', '{value}')")
                elif isinstance(value, (int, float)):
                    query_parts.append(f".has('{prop}', {value})")
                elif isinstance(value, dict):
                    # Handle range queries
                    if "$gte" in value:
                        query_parts.append(f".has('{prop}', gte({value['$gte']}))")
                    if "$lte" in value:
                        query_parts.append(f".has('{prop}', lte({value['$lte']}))")
                    if "$gt" in value:
                        query_parts.append(f".has('{prop}', gt({value['$gt']}))")
                    if "$lt" in value:
                        query_parts.append(f".has('{prop}', lt({value['$lt']}))")
        
        query_parts.extend([
            f".limit({limit})",
            ".project('id', 'label', 'properties')",
            ".by(id)",
            ".by(label)",
            ".by(valueMap(true))"
        ])
        
        query = "".join(query_parts)
        
        try:
            results = await self.execute_query(query)
            nodes = []
            
            for result in results:
                node = GraphNode(
                    id=str(result['id']),
                    label=result['label'],
                    properties=self._parse_properties(result['properties'])
                )
                nodes.append(node)
            
            return GraphResult(
                nodes=nodes,
                edges=[],
                total_count=len(nodes),
                execution_time_ms=0.0  # Would be calculated in real implementation
            )
            
        except Exception as e:
            logger.error(f"Schema-aware search failed for {vertex_label}: {e}")
            raise
    
    async def get_related_entities(
        self,
        node_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 50
    ) -> GraphResult:
        """
        Get entities related to a specific node through specified relationships.
        
        Args:
            node_id: ID of the source node
            relationship_types: List of edge labels to traverse (None for all)
            max_depth: Maximum traversal depth
            limit: Maximum number of results
            
        Returns:
            GraphResult containing related nodes and edges
        """
        # Build relationship filter
        edge_filter = ""
        if relationship_types:
            valid_edges = [e for e in relationship_types if e in self.schema_edges]
            if valid_edges:
                edge_labels = "', '".join(valid_edges)
                edge_filter = f".hasLabel('{edge_labels}')"
        
        query = f"""
        g.V('{node_id}')
         .repeat(bothE(){edge_filter}.otherV().simplePath())
         .times({max_depth})
         .limit({limit})
         .path()
         .by(project('id', 'label', 'properties').by(id).by(label).by(valueMap(true)))
         .by(project('id', 'label', 'source', 'target', 'properties')
            .by(id)
            .by(label)
            .by(outV().id())
            .by(inV().id())
            .by(valueMap(true)))
        """
        
        try:
            results = await self.execute_query(query)
            nodes = []
            edges = []
            node_ids = set()
            edge_ids = set()
            
            for path in results:
                path_objects = path.objects if hasattr(path, 'objects') else path
                
                for i, obj in enumerate(path_objects):
                    if i % 2 == 0:  # Node
                        if obj['id'] not in node_ids:
                            node = GraphNode(
                                id=str(obj['id']),
                                label=obj['label'],
                                properties=self._parse_properties(obj['properties'])
                            )
                            nodes.append(node)
                            node_ids.add(obj['id'])
                    else:  # Edge
                        if obj['id'] not in edge_ids:
                            edge = GraphEdge(
                                id=str(obj['id']),
                                label=obj['label'],
                                source_id=str(obj['source']),
                                target_id=str(obj['target']),
                                properties=self._parse_properties(obj['properties'])
                            )
                            edges.append(edge)
                            edge_ids.add(obj['id'])
            
            return GraphResult(
                nodes=nodes,
                edges=edges,
                total_count=len(nodes) + len(edges),
                execution_time_ms=0.0
            )
            
        except Exception as e:
            logger.error(f"Related entities search failed: {e}")
            raise
    
    async def search_hotels_with_aspects(
        self,
        aspect_names: List[str],
        min_score: float = 3.0,
        limit: int = 10
    ) -> GraphResult:
        """
        Search for hotels based on specific aspect scores.
        
        Args:
            aspect_names: List of aspect names to search for
            min_score: Minimum aspect score threshold
            limit: Maximum number of results
            
        Returns:
            GraphResult containing hotels and related data
        """
        aspect_filter = "', '".join(aspect_names)
        
        query = f"""
        g.V().hasLabel('Hotel')
         .where(
           __.in('HAS_REVIEW')
             .in('HAS_ANALYSIS')
             .out('ANALYZES_ASPECT')
             .has('name', within('{aspect_filter}'))
             .in('ANALYZES_ASPECT')
             .has('aspect_score', gte({min_score}))
         )
         .limit({limit})
         .project('hotel', 'reviews', 'aspects')
         .by(project('id', 'label', 'properties').by(id).by(label).by(valueMap(true)))
         .by(__.in('HAS_REVIEW').limit(5).project('id', 'label', 'properties').by(id).by(label).by(valueMap(true)).fold())
         .by(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', within('{aspect_filter}')).dedup().limit(10).valueMap(true).fold())
        """
        
        try:
            results = await self.execute_query(query)
            nodes = []
            edges = []
            
            for result in results:
                # Add hotel node
                hotel_data = result['hotel']
                hotel_node = GraphNode(
                    id=str(hotel_data['id']),
                    label=hotel_data['label'],
                    properties=self._parse_properties(hotel_data['properties'])
                )
                nodes.append(hotel_node)
                
                # Add review nodes
                for review_data in result.get('reviews', []):
                    review_node = GraphNode(
                        id=str(review_data['id']),
                        label=review_data['label'],
                        properties=self._parse_properties(review_data['properties'])
                    )
                    nodes.append(review_node)
                
                # Add aspect nodes
                for aspect_data in result.get('aspects', []):
                    if 'id' in aspect_data:
                        aspect_node = GraphNode(
                            id=str(aspect_data['id']),
                            label='Aspect',
                            properties=self._parse_properties(aspect_data)
                        )
                        nodes.append(aspect_node)
            
            return GraphResult(
                nodes=nodes,
                edges=edges,
                total_count=len(nodes),
                execution_time_ms=0.0
            )
            
        except Exception as e:
            logger.error(f"Hotel aspect search failed: {e}")
            raise
    
    async def get_sentiment_trends(
        self,
        hotel_id: str,
        time_range_days: int = 90
    ) -> Dict[str, Any]:
        """
        Get sentiment trends for a hotel over time.
        
        Args:
            hotel_id: Hotel ID to analyze
            time_range_days: Number of days to look back
            
        Returns:
            Dictionary containing sentiment trend data
        """
        query = f"""
        g.V('{hotel_id}').hasLabel('Hotel')
         .in('HAS_REVIEW')
         .where(__.has('created_at', gte(datetime().minus(P{time_range_days}D))))
         .in('HAS_ANALYSIS')
         .group()
         .by(__.values('analyzed_at').map(datetime().format('yyyy-MM-dd')))
         .by(__.values('sentiment_score').fold())
        """
        
        try:
            results = await self.execute_query(query)
            
            trend_data = {}
            for date, scores in results[0].items() if results else {}:
                if scores:
                    avg_score = sum(scores) / len(scores)
                    trend_data[date] = {
                        "average_sentiment": avg_score,
                        "review_count": len(scores),
                        "scores": scores
                    }
            
            return {
                "hotel_id": hotel_id,
                "time_range_days": time_range_days,
                "trend_data": trend_data,
                "summary": {
                    "total_reviews": sum(data["review_count"] for data in trend_data.values()),
                    "average_sentiment": sum(data["average_sentiment"] * data["review_count"] 
                                           for data in trend_data.values()) / 
                                       max(sum(data["review_count"] for data in trend_data.values()), 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Sentiment trend analysis failed: {e}")
            raise
    
    def validate_query_against_schema(self, vertex_labels: List[str], edge_labels: List[str]) -> bool:
        """
        Validate that a query uses only schema-defined vertices and edges.
        
        Args:
            vertex_labels: List of vertex labels used in query
            edge_labels: List of edge labels used in query
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        # Check vertices
        for label in vertex_labels:
            if label not in self.schema_vertices:
                raise ValueError(f"Unknown vertex label in query: {label}")
        
        # Check edges
        for label in edge_labels:
            if label not in self.schema_edges:
                raise ValueError(f"Unknown edge label in query: {label}")
        
        return True
    
    async def get_schema_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current graph data based on schema."""
        stats = {}
        
        # Count vertices by type
        vertex_counts = {}
        for vertex in VERTICES:
            try:
                count_query = f"g.V().hasLabel('{vertex.label}').count()"
                result = await self.execute_query(count_query)
                vertex_counts[vertex.label] = result[0] if result else 0
            except Exception as e:
                logger.warning(f"Failed to count {vertex.label} vertices: {e}")
                vertex_counts[vertex.label] = 0
        
        # Count edges by type
        edge_counts = {}
        for edge in EDGES:
            try:
                count_query = f"g.E().hasLabel('{edge.label}').count()"
                result = await self.execute_query(count_query)
                edge_counts[edge.label] = result[0] if result else 0
            except Exception as e:
                logger.warning(f"Failed to count {edge.label} edges: {e}")
                edge_counts[edge.label] = 0
        
        stats = {
            "vertex_counts": vertex_counts,
            "edge_counts": edge_counts,
            "total_vertices": sum(vertex_counts.values()),
            "total_edges": sum(edge_counts.values()),
            "schema_coverage": {
                "defined_vertex_types": len(VERTICES),
                "present_vertex_types": len([c for c in vertex_counts.values() if c > 0]),
                "defined_edge_types": len(EDGES),
                "present_edge_types": len([c for c in edge_counts.values() if c > 0])
            }
        }
        
        return stats
