"""
Gremlin client for connecting to Azure Cosmos DB Gremlin API.
Implements connection management, query execution, and error handling.
"""

import asyncio
import json
import websockets
import ssl
from typing import List, Dict, Any, Optional, Union
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.dto import GraphNode, GraphEdge, GraphResult


class GremlinClient:
    """
    Azure Cosmos DB Gremlin API client with connection management and query execution.
    
    Features:
    - Automatic connection retry with exponential backoff
    - Query result parsing and transformation
    - Connection pooling and management
    - Comprehensive error handling
    - Performance monitoring
    """
    
    def __init__(
        self,
        url: str,
        database: str,
        graph: str,
        username: str,
        password: str,
        traversal_source: str = "g",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Gremlin client.
        
        Args:
            url: Gremlin server URL (wss://...)
            database: Database name
            graph: Graph name
            username: Authentication username
            password: Authentication password
            traversal_source: Traversal source name (default: "g")
            timeout: Connection timeout in seconds
            max_retries: Maximum retry attempts for failed operations
        """
        self.url = url
        self.database = database
        self.graph = graph
        self.username = username
        self.password = password
        self.traversal_source = traversal_source
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._client = None
        self._connection = None
        self._g = None
        self._is_connected = False
        
        # Performance metrics
        self._query_count = 0
        self._total_query_time = 0.0
        
    async def connect(self) -> None:
        """Establish connection to Gremlin server."""
        try:
            logger.info(f"Connecting to Gremlin server: {self.url}")
            
            # Create SSL context for secure connection
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Initialize Gremlin client
            self._client = client.Client(
                url=self.url,
                traversal_source=self.traversal_source,
                username=f"/dbs/{self.database}/colls/{self.graph}",
                password=self.password,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Create remote connection for traversal
            connection_string = f"{self.url}/gremlin"
            self._connection = DriverRemoteConnection(
                connection_string,
                self.traversal_source,
                username=f"/dbs/{self.database}/colls/{self.graph}",
                password=self.password,
                transport_factory=lambda: websockets.connect(
                    connection_string,
                    ssl=ssl_context,
                    extra_headers={"Authorization": f"Basic {self.password}"}
                )
            )
            
            # Create graph traversal source
            self._g = traversal().withRemote(self._connection)
            
            # Test connection
            await self._test_connection()
            
            self._is_connected = True
            logger.info("✅ Successfully connected to Gremlin server")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Gremlin server: {e}")
            await self.close()
            raise
    
    async def _test_connection(self) -> None:
        """Test the connection by executing a simple query."""
        try:
            result = await self.execute_query("g.V().limit(1).count()")
            logger.info(f"Connection test successful. Graph has vertices: {result}")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((GremlinServerError, ConnectionError))
    )
    async def execute_query(self, query: str, bindings: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a Gremlin query with retry logic.
        
        Args:
            query: Gremlin query string
            bindings: Query parameter bindings
            
        Returns:
            List of query results
            
        Raises:
            ConnectionError: If not connected to server
            GremlinServerError: If query execution fails
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to Gremlin server")
        
        start_time = time.time()
        
        try:
            logger.debug(f"Executing Gremlin query: {query}")
            
            # Execute query using client
            if bindings:
                result = self._client.submit(query, bindings)
            else:
                result = self._client.submit(query)
            
            # Get all results
            results = result.all().result()
            
            execution_time = (time.time() - start_time) * 1000
            self._query_count += 1
            self._total_query_time += execution_time
            
            logger.debug(f"Query executed successfully in {execution_time:.2f}ms, returned {len(results)} results")
            
            return results
            
        except GremlinServerError as e:
            logger.error(f"Gremlin server error: {e}")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise ConnectionError(f"Failed to execute query: {e}")
    
    async def search_nodes_by_property(
        self,
        label: str,
        property_name: str,
        property_value: Union[str, int, float],
        limit: int = 10
    ) -> GraphResult:
        """
        Search for nodes by property value.
        
        Args:
            label: Node label to search
            property_name: Property name to search by
            property_value: Property value to match
            limit: Maximum number of results
            
        Returns:
            GraphResult containing matching nodes
        """
        start_time = time.time()
        
        try:
            query = f"""
            g.V().hasLabel('{label}')
                 .has('{property_name}', '{property_value}')
                 .limit({limit})
                 .project('id', 'label', 'properties')
                 .by(id)
                 .by(label)
                 .by(valueMap(true))
            """
            
            results = await self.execute_query(query)
            nodes = []
            
            for result in results:
                node = GraphNode(
                    id=str(result['id']),
                    label=result['label'],
                    properties=self._parse_properties(result['properties'])
                )
                nodes.append(node)
            
            execution_time = (time.time() - start_time) * 1000
            
            return GraphResult(
                nodes=nodes,
                edges=[],
                total_count=len(nodes),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Node search failed: {e}")
            raise
    
    async def get_node_relationships(
        self,
        node_id: str,
        max_depth: int = 2,
        limit: int = 50
    ) -> GraphResult:
        """
        Get node relationships up to specified depth.
        
        Args:
            node_id: Source node ID
            max_depth: Maximum traversal depth
            limit: Maximum number of results
            
        Returns:
            GraphResult containing nodes and relationships
        """
        start_time = time.time()
        
        try:
            # Query for nodes and their relationships
            query = f"""
            g.V('{node_id}')
             .repeat(bothE().otherV().simplePath())
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
            
            execution_time = (time.time() - start_time) * 1000
            
            return GraphResult(
                nodes=nodes,
                edges=edges,
                total_count=len(nodes) + len(edges),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Relationship search failed: {e}")
            raise
    
    async def text_search(self, search_text: str, limit: int = 10) -> GraphResult:
        """
        Perform text search across node properties.
        
        Args:
            search_text: Text to search for
            limit: Maximum number of results
            
        Returns:
            GraphResult containing matching nodes
        """
        start_time = time.time()
        
        try:
            # Search across common text properties
            query = f"""
            g.V()
             .or(
                has('name', containing('{search_text}')),
                has('title', containing('{search_text}')),
                has('description', containing('{search_text}')),
                has('content', containing('{search_text}')),
                has('text', containing('{search_text}'))
             )
             .limit({limit})
             .project('id', 'label', 'properties')
             .by(id)
             .by(label)
             .by(valueMap(true))
            """
            
            results = await self.execute_query(query)
            nodes = []
            
            for result in results:
                node = GraphNode(
                    id=str(result['id']),
                    label=result['label'],
                    properties=self._parse_properties(result['properties'])
                )
                nodes.append(node)
            
            execution_time = (time.time() - start_time) * 1000
            
            return GraphResult(
                nodes=nodes,
                edges=[],
                total_count=len(nodes),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            raise
    
    def _parse_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Gremlin property format to simple dictionary.
        
        Args:
            properties: Raw Gremlin properties
            
        Returns:
            Cleaned property dictionary
        """
        parsed = {}
        
        for key, value in properties.items():
            if key.startswith('_'):  # Skip internal properties
                continue
                
            if isinstance(value, list) and len(value) > 0:
                # Gremlin returns properties as lists
                parsed[key] = value[0] if len(value) == 1 else value
            else:
                parsed[key] = value
                
        return parsed
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get client performance statistics."""
        return {
            "is_connected": self._is_connected,
            "query_count": self._query_count,
            "total_query_time_ms": self._total_query_time,
            "average_query_time_ms": self._total_query_time / max(self._query_count, 1),
            "database": self.database,
            "graph": self.graph
        }
    
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        try:
            logger.info("Closing Gremlin client connections...")
            
            if self._client:
                self._client.close()
                self._client = None
            
            if self._connection:
                self._connection.close()
                self._connection = None
            
            self._g = None
            self._is_connected = False
            
            logger.info("✅ Gremlin client connections closed")
            
        except Exception as e:
            logger.error(f"Error closing Gremlin client: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected
