"""
Enhanced RAG Pipeline implementation combining graph search, semantic search, and LLM generation.
Now includes natural language to Gremlin query translation and improved hybrid retrieval.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from loguru import logger

from app.core.gremlin_client import GremlinClient
from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.core.vector_store import VectorStore
from app.core.graph_query_llm import GraphQueryLLM
from app.core.vector_retriever import VectorRetriever
from app.models.dto import SearchRequest, HybridSearchResult, GraphResult, SemanticResult


class EnhancedRAGPipeline:
    """
    Enhanced RAG (Retrieval-Augmented Generation) pipeline combining:
    - Natural language to Gremlin query translation
    - Graph database search using Gremlin
    - Semantic search using Hugging Face embeddings
    - LLM response generation using Gemini
    
    Features:
    - Intelligent query translation from natural language
    - Hybrid search combining graph and semantic results
    - Context-aware response generation with multi-hop reasoning
    - Performance monitoring and optimization
    - Development mode support with graceful fallbacks
    """
    
    def __init__(
        self,
        gremlin_client: Optional[SchemaAwareGremlinClient] = None,
        vector_store: Optional[VectorStore] = None,
        graph_query_llm: Optional[GraphQueryLLM] = None,
        vector_retriever: Optional[VectorRetriever] = None,
        model_provider: str = "gemini",
        gemini_api_key: Optional[str] = None,
        gemini_model: str = "gemini-2.0-flash",
        max_graph_results: int = 10,
        max_semantic_results: int = 5,
        context_window_size: int = 4000,
        development_mode: bool = False
    ):
        """
        Initialize enhanced RAG pipeline.
        
        Args:
            gremlin_client: Connected schema-aware Gremlin client (can be None in development mode)
            vector_store: Initialized vector store (can be None in development mode)
            graph_query_llm: LLM for natural language to Gremlin translation
            vector_retriever: Enhanced vector retriever for semantic search
            model_provider: LLM provider ("gemini")
            gemini_api_key: Gemini API key
            gemini_model: Gemini model name
            max_graph_results: Maximum graph search results
            max_semantic_results: Maximum semantic search results
            context_window_size: Maximum context size for LLM
            development_mode: Whether running in development mode
        """
        self.gremlin_client = gremlin_client
        self.vector_store = vector_store
        self.graph_query_llm = graph_query_llm
        self.vector_retriever = vector_retriever
        self.model_provider = model_provider
        self.gemini_model = gemini_model
        self.max_graph_results = max_graph_results
        self.max_semantic_results = max_semantic_results
        self.context_window_size = context_window_size
        self.development_mode = development_mode
        
        # Initialize LLM for response generation
        if model_provider == "gemini" and gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.llm = genai.GenerativeModel(gemini_model)
        else:
            self.llm = None
            logger.warning("LLM not configured - responses will not be generated")
        
        # Performance tracking
        self._search_count = 0
        self._total_search_time = 0.0
        self._query_translation_count = 0
        self._total_translation_time = 0.0
    
    async def search(self, request: SearchRequest) -> HybridSearchResult:
        """
        Perform hybrid search combining graph and semantic search.
        
        Args:
            request: Search request with query and parameters
            
        Returns:
            HybridSearchResult with combined results and generated response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting {request.search_type} search for: '{request.query}'")
            
            # Initialize result components
            graph_results = GraphResult(nodes=[], edges=[], total_count=0, execution_time_ms=0.0)
            semantic_results = []
            search_metadata = {}
            
            # Perform searches based on type
            if request.search_type in ["graph", "hybrid"]:
                graph_results = await self._perform_graph_search(
                    request.query,
                    request.max_results or self.max_graph_results,
                    request.filters
                )
                search_metadata["graph_query_count"] = 1
            
            if request.search_type in ["semantic", "hybrid"]:
                semantic_results = await self._perform_semantic_search(
                    request.query,
                    request.max_results or self.max_semantic_results,
                    request.filters
                )
                search_metadata["semantic_query_count"] = 1
            
            # Generate response if LLM is available
            generated_response = None
            if self.llm and (graph_results.nodes or semantic_results):
                generated_response = await self._generate_response(
                    request.query,
                    graph_results,
                    semantic_results
                )
            
            total_execution_time = (time.time() - start_time) * 1000
            self._search_count += 1
            self._total_search_time += total_execution_time
            
            # Add embedding data if requested
            if request.include_embeddings:
                semantic_results = await self._add_embeddings_to_results(semantic_results)
            
            # Add development mode info to metadata
            if self.development_mode:
                search_metadata["development_mode"] = True
                search_metadata["note"] = "Running in development mode - some features may be limited"
            
            result = HybridSearchResult(
                query=request.query,
                graph_results=graph_results,
                semantic_results=semantic_results,
                generated_response=generated_response,
                total_execution_time_ms=total_execution_time,
                search_metadata=search_metadata
            )
            
            logger.info(f"Search completed in {total_execution_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise
    
    async def _perform_graph_search(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict[str, Any]]
    ) -> GraphResult:
        """Perform graph database search."""
        try:
            logger.debug(f"Performing graph search with max_results={max_results}")
            
            # Check if gremlin client is available
            if not self.gremlin_client:
                logger.warning("Graph search not available in development mode")
                return GraphResult(nodes=[], edges=[], total_count=0, execution_time_ms=0.0)
            
            # Try different graph search strategies
            
            # Strategy 1: Text search across node properties
            result = await self.gremlin_client.text_search(query, max_results)
            
            if result.total_count == 0 and filters:
                # Strategy 2: Property-based search if filters are provided
                for prop_name, prop_value in filters.items():
                    if isinstance(prop_value, (str, int, float)):
                        # Try searching by this property
                        property_result = await self.gremlin_client.search_nodes_by_property(
                            label="*",  # Search all labels
                            property_name=prop_name,
                            property_value=prop_value,
                            limit=max_results
                        )
                        if property_result.total_count > 0:
                            result = property_result
                            break
            
            return result
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return GraphResult(nodes=[], edges=[], total_count=0, execution_time_ms=0.0)
    
    async def _perform_semantic_search(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[SemanticResult]:
        """Perform semantic vector search."""
        try:
            logger.debug(f"Performing semantic search with max_results={max_results}")
            
            # Check if vector store is available
            if not self.vector_store:
                logger.warning("Semantic search not available in development mode")
                return []
            
            results = await self.vector_store.search(
                query=query,
                top_k=max_results,
                min_score=0.3,  # Configurable threshold
                filters=filters
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def _generate_response(
        self,
        query: str,
        graph_results: GraphResult,
        semantic_results: List[SemanticResult]
    ) -> Optional[str]:
        """Generate LLM response based on retrieved context."""
        if not self.llm:
            return None
        
        try:
            # Build context from search results
            context = self._build_context(graph_results, semantic_results)
            
            if not context:
                return "I couldn't find relevant information to answer your question."
            
            # Prepare prompt
            prompt = self._build_prompt(query, context)
            
            # Generate response
            logger.debug("Generating LLM response...")
            response = await asyncio.to_thread(
                self.llm.generate_content,
                prompt
            )
            
            generated_text = response.text if hasattr(response, 'text') else str(response)
            logger.debug(f"Generated response length: {len(generated_text)} characters")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I encountered an error while generating a response."
    
    def _build_context(
        self,
        graph_results: GraphResult,
        semantic_results: List[SemanticResult]
    ) -> str:
        """Build context string from search results."""
        context_parts = []
        
        # Add graph context
        if graph_results.nodes:
            context_parts.append("Graph Database Information:")
            for node in graph_results.nodes[:5]:  # Limit nodes
                node_info = f"- {node.label}: {node.properties.get('name', node.id)}"
                if 'description' in node.properties:
                    node_info += f" - {node.properties['description']}"
                context_parts.append(node_info)
        
        # Add semantic context
        if semantic_results:
            context_parts.append("\nRelevant Documents:")
            for result in semantic_results[:3]:  # Limit documents
                context_parts.append(f"- {result.content[:200]}...")  # Truncate long content
        
        context = "\n".join(context_parts)
        
        # Ensure context fits within window
        if len(context) > self.context_window_size:
            context = context[:self.context_window_size] + "..."
        
        return context
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM generation."""
        prompt = f"""You are a helpful assistant that provides accurate and informative answers based on the given context.

User Question: {query}

Context Information:
{context}

Instructions:
- Answer the user's question based on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but comprehensive
- Cite specific information from the context when possible
- If asked about data from the graph database, focus on relationships and connections
- If asked about content from documents, provide relevant excerpts

Answer:"""
        
        return prompt
    
    async def _add_embeddings_to_results(
        self,
        semantic_results: List[SemanticResult]
    ) -> List[SemanticResult]:
        """Add embedding vectors to semantic results if requested."""
        # This would require modifying the vector store to return embeddings
        # For now, return results as-is
        return semantic_results
    
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index documents in the vector store.
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
            batch_size: Batch size for processing
            
        Returns:
            Indexing statistics
        """
        start_time = time.time()
        
        try:
            logger.info(f"Indexing {len(documents)} documents")
            
            # Extract content and metadata
            contents = []
            metadata_list = []
            
            for doc in documents:
                if 'content' not in doc:
                    raise ValueError("Each document must have a 'content' field")
                
                contents.append(doc['content'])
                metadata_list.append(doc.get('metadata', {}))
            
            # Add to vector store
            indexed_count = await self.vector_store.add_documents(
                documents=contents,
                metadata_list=metadata_list,
                batch_size=batch_size
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "indexed_count": indexed_count,
                "failed_count": len(documents) - indexed_count,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise
    
    async def graph_rag_answer(self, user_query: str) -> str:
        """
        Main Graph RAG method that combines natural language to Gremlin translation,
        graph search, semantic search, and LLM response generation.
        
        Args:
            user_query: Natural language question from user
            
        Returns:
            Generated answer string
        """
        try:
            logger.info(f"Processing Graph RAG query: '{user_query}'")
            start_time = time.time()
            
            # Step 1: Translate natural language to Gremlin query
            gremlin_query = None
            if self.graph_query_llm:
                try:
                    gremlin_query = await self.graph_query_llm.generate_gremlin_query(user_query)
                    logger.debug(f"Generated Gremlin query: {gremlin_query}")
                except Exception as e:
                    logger.warning(f"Query translation failed: {e}")
            
            # Step 2: Execute graph search
            graph_results = GraphResult(nodes=[], edges=[], total_count=0, execution_time_ms=0.0)
            if self.gremlin_client and gremlin_query:
                try:
                    # Execute the generated Gremlin query
                    raw_results = await self.gremlin_client.execute_query(gremlin_query)
                    
                    # Convert raw results to GraphResult format
                    nodes = []
                    for result in raw_results:
                        if hasattr(result, 'id') and hasattr(result, 'label'):
                            from app.models.dto import GraphNode
                            node = GraphNode(
                                id=str(result.id),
                                label=result.label,
                                properties=dict(result) if hasattr(result, '__iter__') else {}
                            )
                            nodes.append(node)
                    
                    graph_results = GraphResult(
                        nodes=nodes,
                        edges=[],
                        total_count=len(nodes),
                        execution_time_ms=0.0
                    )
                    
                except Exception as e:
                    logger.warning(f"Graph search failed: {e}")
            
            # Step 3: Perform semantic search
            semantic_results = []
            if self.vector_store or self.vector_retriever:
                try:
                    if self.vector_retriever:
                        # Use enhanced vector retriever
                        semantic_results = await self.vector_retriever.retrieve_similar_docs_with_scores(
                            query=user_query,
                            top_k=self.max_semantic_results,
                            min_score=0.3
                        )
                    elif self.vector_store:
                        # Fallback to vector store
                        semantic_results = await self.vector_store.search(
                            query=user_query,
                            top_k=self.max_semantic_results,
                            min_score=0.3
                        )
                except Exception as e:
                    logger.warning(f"Semantic search failed: {e}")
            
            # Step 4: Generate response using LLM
            if self.llm and (graph_results.nodes or semantic_results):
                response = await self._generate_response(user_query, graph_results, semantic_results)
                if response:
                    execution_time = (time.time() - start_time) * 1000
                    logger.info(f"Graph RAG completed in {execution_time:.2f}ms")
                    return response
            
            # Fallback response
            if self.development_mode:
                execution_time = (time.time() - start_time) * 1000
                fallback_response = f"""I'm running in development mode and couldn't fully process your query: "{user_query}"

Here's what I tried:
- Generated Gremlin query: {gremlin_query or 'Failed to generate'}
- Graph search: {'✅ Attempted' if self.gremlin_client else '❌ Not available'}
- Semantic search: {'✅ Attempted' if (self.vector_store or self.vector_retriever) else '❌ Not available'}
- Found {len(graph_results.nodes)} graph results and {len(semantic_results)} semantic results

To get better results, ensure your database connections are properly configured.
                
Processing time: {execution_time:.2f}ms"""
                return fallback_response
            else:
                return "I couldn't find relevant information to answer your question. Please try rephrasing your query or check if the system is properly configured."
            
        except Exception as e:
            logger.error(f"Graph RAG processing failed: {e}")
            return f"I encountered an error while processing your question: {str(e)}"

    async def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced pipeline performance statistics."""
        stats = {
            "pipeline": {
                "search_count": self._search_count,
                "total_search_time_ms": self._total_search_time,
                "average_search_time_ms": self._total_search_time / max(self._search_count, 1),
                "query_translation_count": self._query_translation_count,
                "total_translation_time_ms": self._total_translation_time,
                "average_translation_time_ms": self._total_translation_time / max(self._query_translation_count, 1),
                "model_provider": self.model_provider,
                "llm_model": self.gemini_model,
                "max_graph_results": self.max_graph_results,
                "max_semantic_results": self.max_semantic_results,
                "development_mode": self.development_mode
            }
        }
        
        # Add component statistics if available
        if self.gremlin_client:
            try:
                stats["gremlin"] = await self.gremlin_client.get_statistics()
            except Exception as e:
                stats["gremlin"] = {"error": str(e)}
        
        if self.vector_store:
            try:
                stats["vector_store"] = await self.vector_store.get_statistics()
            except Exception as e:
                stats["vector_store"] = {"error": str(e)}
                
        if self.vector_retriever:
            try:
                stats["vector_retriever"] = await self.vector_retriever.get_statistics()
            except Exception as e:
                stats["vector_retriever"] = {"error": str(e)}
        
        return stats
        
        return stats


# Backward compatibility alias
RAGPipeline = EnhancedRAGPipeline
