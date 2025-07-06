"""
Synchronous Gremlin client wrapper for Azure Cosmos DB Gremlin API.
This resolves event loop conflicts by properly separating sync operations.
"""

import asyncio
import json
import ssl
from typing import List, Dict, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T
import time
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.models.dto import GraphNode, GraphEdge, GraphResult


class SyncGremlinClient:
    """
    Synchronous Azure Cosmos DB Gremlin API client with async wrapper.
    
    This client resolves event loop conflicts by:
    1. Using synchronous gremlin_python client operations
    2. Wrapping sync operations in ThreadPoolExecutor for async compatibility
    3. Maintaining proper connection lifecycle management
    4. Providing consistent error handling and retry logic
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
        Initialize synchronous Gremlin client.
        
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
        self._is_connected = False
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gremlin")
        
        # Performance metrics
        self._query_count = 0
        self._total_query_time = 0.0
    
    @property
    def is_connected(self) -> bool:
        """Property to check if client is connected (for API compatibility)."""
        return self._is_connected
    
    def _create_sync_client(self) -> None:
        """Create synchronous Gremlin client connection."""
        try:
            logger.info(f"Creating sync Gremlin client connection to: {self.url}")
            
            # Create the client with proper Cosmos DB authentication
            self._client = client.Client(
                url=self.url,
                traversal_source=self.traversal_source,
                username=f"/dbs/{self.database}/colls/{self.graph}",
                password=self.password,
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            logger.info("✅ Sync Gremlin client created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create sync Gremlin client: {e}")
            raise
    
    def _test_sync_connection(self) -> None:
        """Test the synchronous connection by executing a simple query."""
        try:
            logger.info("Testing sync Gremlin connection...")
            result = self._client.submit("g.V().limit(1).count()").all().result()
            logger.info(f"✅ Sync connection test successful. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Sync connection test failed: {e}")
            raise
    
    async def connect(self) -> None:
        """Establish connection to Gremlin server using async wrapper."""
        try:
            logger.info("Connecting to Gremlin server via sync client...")
            
            # Run sync operations in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._executor, self._create_sync_client)
            await loop.run_in_executor(self._executor, self._test_sync_connection)
            
            self._is_connected = True
            logger.info("✅ Successfully connected to Gremlin server via sync client")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Gremlin server: {e}")
            await self.close()
            raise
    
    def _execute_sync_query(self, query: str, bindings: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute a synchronous Gremlin query."""
        if not self._is_connected or not self._client:
            raise ConnectionError("Not connected to Gremlin server")
        
        start_time = time.time()
        
        try:
            logger.debug(f"Executing sync Gremlin query: {query}")
            
            # Execute query using synchronous client
            if bindings:
                result = self._client.submit(query, bindings)
            else:
                result = self._client.submit(query)
            
            # Get all results synchronously
            results = result.all().result()
            
            execution_time = (time.time() - start_time) * 1000
            self._query_count += 1
            self._total_query_time += execution_time
            
            logger.debug(f"Sync query executed successfully in {execution_time:.2f}ms, returned {len(results)} results")
            
            return results
            
        except GremlinServerError as e:
            logger.error(f"Gremlin server error: {e}")
            raise
        except Exception as e:
            logger.error(f"Sync query execution failed: {e}")
            raise ConnectionError(f"Failed to execute query: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((GremlinServerError, ConnectionError))
    )
    async def execute_query(self, query: str, bindings: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Execute a Gremlin query with retry logic (async wrapper).
        
        Args:
            query: Gremlin query string
            bindings: Query parameter bindings
            
        Returns:
            List of query results
            
        Raises:
            ConnectionError: If not connected to server
            GremlinServerError: If query execution fails
        """
        try:
            # Execute sync query in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor, 
                self._execute_sync_query, 
                query, 
                bindings
            )
            return result
            
        except Exception as e:
            logger.error(f"Async query wrapper failed: {e}")
            raise
    
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
            GraphResult with matching nodes
        """
        try:
            # Build Gremlin query for property search
            if isinstance(property_value, str):
                query = f"g.V().hasLabel('{label}').has('{property_name}', '{property_value}').limit({limit})"
            else:
                query = f"g.V().hasLabel('{label}').has('{property_name}', {property_value}).limit({limit})"
            
            results = await self.execute_query(query)
            
            # Parse results into GraphNode objects
            nodes = []
            for result in results:
                if isinstance(result, dict):
                    node = GraphNode(
                        id=result.get('id', ''),
                        label=result.get('label', label),
                        properties=result.get('properties', {})
                    )
                    nodes.append(node)
            
            return GraphResult(
                nodes=nodes,
                edges=[],
                query=query,
                execution_time_ms=0  # Will be populated by performance tracking
            )
            
        except Exception as e:
            logger.error(f"Failed to search nodes by property: {e}")
            raise
    
    async def search_edges_by_property(
        self,
        label: str,
        property_name: str,
        property_value: Union[str, int, float],
        limit: int = 10
    ) -> GraphResult:
        """
        Search for edges by property value.
        
        Args:
            label: Edge label to search
            property_name: Property name to search by
            property_value: Property value to match
            limit: Maximum number of results
            
        Returns:
            GraphResult with matching edges
        """
        try:
            # Build Gremlin query for edge property search
            if isinstance(property_value, str):
                query = f"g.E().hasLabel('{label}').has('{property_name}', '{property_value}').limit({limit})"
            else:
                query = f"g.E().hasLabel('{label}').has('{property_name}', {property_value}).limit({limit})"
            
            results = await self.execute_query(query)
            
            # Parse results into GraphEdge objects
            edges = []
            for result in results:
                if isinstance(result, dict):
                    edge = GraphEdge(
                        id=result.get('id', ''),
                        label=result.get('label', label),
                        source=result.get('inV', ''),
                        target=result.get('outV', ''),
                        properties=result.get('properties', {})
                    )
                    edges.append(edge)
            
            return GraphResult(
                nodes=[],
                edges=edges,
                query=query,
                execution_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Failed to search edges by property: {e}")
            raise
    
    async def get_node_relationships(
        self,
        node_id: str,
        direction: str = "both",
        limit: int = 50
    ) -> GraphResult:
        """
        Get relationships for a specific node.
        
        Args:
            node_id: Node ID to get relationships for
            direction: Relationship direction ("in", "out", "both")
            limit: Maximum number of relationships
            
        Returns:
            GraphResult with nodes and edges
        """
        try:
            # Build direction-specific query
            if direction == "out":
                query = f"g.V('{node_id}').outE().limit({limit})"
            elif direction == "in":
                query = f"g.V('{node_id}').inE().limit({limit})"
            else:  # both
                query = f"g.V('{node_id}').bothE().limit({limit})"
            
            results = await self.execute_query(query)
            
            # Parse results
            edges = []
            for result in results:
                if isinstance(result, dict):
                    edge = GraphEdge(
                        id=result.get('id', ''),
                        label=result.get('label', ''),
                        source=result.get('inV', ''),
                        target=result.get('outV', ''),
                        properties=result.get('properties', {})
                    )
                    edges.append(edge)
            
            return GraphResult(
                nodes=[],
                edges=edges,
                query=query,
                execution_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"Failed to get node relationships: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Gremlin connection.
        
        Returns:
            Health status dictionary
        """
        try:
            start_time = time.time()
            
            # Simple vertex count query
            result = await self.execute_query("g.V().count()")
            vertex_count = result[0] if result else 0
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "connected": self._is_connected,
                "vertex_count": vertex_count,
                "response_time_ms": round(execution_time, 2),
                "query_count": self._query_count,
                "average_query_time_ms": round(self._total_query_time / max(self._query_count, 1), 2)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "vertex_count": 0,
                "response_time_ms": 0
            }
    
    async def close(self) -> None:
        """Close the Gremlin client connection and cleanup resources."""
        try:
            if self._client:
                # Close client synchronously in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, self._client.close)
                self._client = None
                
            self._is_connected = False
            
            # Shutdown thread pool
            self._executor.shutdown(wait=True)
            
            logger.info("✅ Gremlin client closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing Gremlin client: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            if self._client:
                self._client.close()
            if hasattr(self, '_executor') and self._executor:
                self._executor.shutdown(wait=False)
        except:
            pass  # Ignore cleanup errors during destruction
