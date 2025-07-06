"""
Graph Query LLM Module

This module provides natural language to Gremlin query translation using 
Google Gemini LLM. It analyzes user queries and generates valid Gremlin 
queries based on the hotel review domain schema.
"""

import asyncio
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from loguru import logger

from app.core.domain_schema import VERTICES, EDGES, get_vertex_labels, get_edge_labels
from app.config.settings import get_settings

# Language detection support
try:
    from langdetect import detect, DetectorFactory
    # Set seed for consistent results
    DetectorFactory.seed = 0
    LANGUAGE_DETECTION_AVAILABLE = True
    logger.info("✅ Language detection available")
except ImportError:
    LANGUAGE_DETECTION_AVAILABLE = False
    logger.warning("⚠️ langdetect not available. Install with: pip install langdetect")


class GraphQueryLLM:
    """
    LLM-powered natural language to Gremlin query translator.
    
    Uses Google Gemini to parse user queries and generate valid Gremlin queries
    based on the hotel review domain schema.
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the Graph Query LLM.
        
        Args:
            api_key: Google Gemini API key
            model_name: Gemini model name to use
        """
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        self._is_initialized = False
        
        # Cache schema information for prompt generation
        self.vertex_labels = get_vertex_labels()
        self.edge_labels = get_edge_labels()
        self._schema_prompt = self._build_schema_prompt()
    
    async def initialize(self) -> None:
        """Initialize the Gemini client."""
        try:
            logger.info(f"Initializing Graph Query LLM with model: {self.model_name}")
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            
            self._is_initialized = True
            logger.info("✅ Graph Query LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Graph Query LLM: {e}")
            raise
    
    def _build_schema_prompt(self) -> str:
        """Build a comprehensive schema description for the LLM."""
        schema_description = """
Hotel Review Graph Schema:

VERTICES (Nodes):
"""
        
        for vertex in VERTICES:
            properties_desc = ", ".join([f"{name}: {prop.description}" 
                                       for name, prop in vertex.properties.items()])
            schema_description += f"- {vertex.label}: {vertex.description}\n"
            if properties_desc:
                schema_description += f"  Properties: {properties_desc}\n"
        
        schema_description += "\nEDGES (Relationships):\n"
        
        for edge in EDGES:
            schema_description += f"- {edge.label}: {edge.out_v} -> {edge.in_v} ({edge.description})\n"
        
        schema_description += """
GREMLIN SYNTAX EXAMPLES:
- Find all hotels: g.V().hasLabel('Hotel')
- Find hotel by name: g.V().hasLabel('Hotel').has('name', 'Hotel Name')
- Find reviews for a hotel: g.V().hasLabel('Hotel').has('name', 'Hotel Name').in('HAS_REVIEW')
- Find high-rated reviews: g.V().hasLabel('Review').has('score', gte(8))
- Find hotels with good cleanliness: g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0))
- Find reviews about specific aspects: g.V().hasLabel('Review').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service')
- Find reviews by language: g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'en')
- Find accommodation types: g.V().hasLabel('AccommodationType')
- Find hotels in a city: g.V().hasLabel('Hotel').has('city', 'New York')

IMPORTANT GREMLIN RULES:
- Always start with g.V() for vertex queries
- Use hasLabel('VertexName') to filter by vertex type
- Use has('property', 'value') for exact matches
- Use has('property', gte(value)) for greater than or equal
- Use has('property', lte(value)) for less than or equal
- Use in('EdgeLabel') to traverse incoming edges
- Use out('EdgeLabel') to traverse outgoing edges
- Use valueMap() or values('property') to get results
- Use limit(n) to limit results
"""
        
        return schema_description
    
    def _detect_language(self, query: str) -> str:
        """
        Detect the language of the user query.
        
        Args:
            query: User query text
            
        Returns:
            Language code (e.g., 'en', 'tr', 'unknown')
        """
        if not LANGUAGE_DETECTION_AVAILABLE:
            return 'unknown'
        
        try:
            # Clean the query for better detection
            clean_query = query.strip().lower()
            if len(clean_query) < 3:
                return 'unknown'
            
            detected_lang = detect(clean_query)
            logger.debug(f"Detected language: {detected_lang} for query: '{query[:50]}...'")
            return detected_lang
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return 'unknown'
    
    def _build_multilingual_prompt(self, user_query: str, detected_lang: str) -> str:
        """
        Build a language-aware prompt for Gremlin query generation.
        
        Args:
            user_query: Original user query
            detected_lang: Detected language code
            
        Returns:
            Enhanced prompt with language context
        """
        base_prompt = f"""
{self._schema_prompt}

TASK: Convert the following natural language query into a valid Gremlin query.
"""
        
        # Add language-specific instructions
        if detected_lang == 'tr':
            language_instruction = """
LANGUAGE NOTE: The input query is in Turkish. Please understand the meaning and convert to Gremlin.

Common Turkish hotel terms:
- "otel" = hotel
- "misafir" = guest  
- "oda" = room
- "temizlik" = cleanliness
- "şikayet" = complaint
- "yoram" = review/comment
- "hizmet" = service
- "VIP" = VIP (same in Turkish)
- "bakım" = maintenance
- "sorun" = problem/issue
- "göster" = show
- "bul" = find
"""
        elif detected_lang in ['es', 'fr', 'de', 'it']:
            language_instruction = f"""
LANGUAGE NOTE: The input query is in {detected_lang.upper()}. Please understand the meaning and convert to Gremlin.
Focus on the semantic meaning rather than literal translation.
"""
        else:
            language_instruction = ""
        
        return f"""{base_prompt}{language_instruction}

User Query: "{user_query}"

Requirements:
1. Generate ONLY the Gremlin query, no explanation
2. The query must be syntactically correct
3. Use the exact vertex and edge labels from the schema above
4. Include appropriate filters and traversals
5. Add .limit(10) at the end unless a specific limit is requested
6. If the query is ambiguous, make reasonable assumptions based on the hotel review domain

Gremlin Query:"""

    async def generate_gremlin_query(self, user_query: str) -> str:
        """
        Generate a Gremlin query from natural language input with multilingual support.
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Valid Gremlin query string
            
        Raises:
            RuntimeError: If LLM is not initialized
            Exception: If query generation fails
        """
        if not self._is_initialized:
            raise RuntimeError("Graph Query LLM not initialized")
        
        try:
            logger.debug(f"Generating Gremlin query for: '{user_query}'")
            
            # Detect language
            detected_lang = self._detect_language(user_query)
            logger.debug(f"Detected language: {detected_lang}")
            
            # Build language-aware prompt
            prompt = self._build_multilingual_prompt(user_query, detected_lang)
            
            # Generate response using Gemini
            response = await self._call_gemini(prompt)
            
            # Extract and clean the query
            gremlin_query = self._extract_gremlin_query(response)
            
            logger.debug(f"Generated Gremlin query: {gremlin_query}")
            return gremlin_query
            
        except Exception as e:
            logger.error(f"❌ Failed to generate Gremlin query: {e}")
            # Return a safe fallback query
            return "g.V().hasLabel('Hotel').limit(10)"
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with retry logic."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Run the API call in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                )
                
                return response.text.strip()
                
            except Exception as e:
                logger.warning(f"Gemini API call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Failed to call Gemini API after all retries")
    
    def _extract_gremlin_query(self, response: str) -> str:
        """Extract and validate the Gremlin query from the LLM response."""
        # Clean the response
        query = response.strip()
        
        # Remove common markdown formatting
        if query.startswith("```"):
            lines = query.split('\n')
            # Find the actual query line (usually starts with 'g.')
            for line in lines:
                line = line.strip()
                if line.startswith('g.'):
                    query = line
                    break
        
        # Remove any trailing explanation
        if '\n' in query:
            query = query.split('\n')[0]
        
        # Ensure the query starts with 'g.'
        if not query.startswith('g.'):
            logger.warning(f"Generated query doesn't start with 'g.': {query}")
            # Try to find a line that starts with 'g.'
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('g.'):
                    query = line
                    break
            else:
                # Fallback to a safe query
                query = "g.V().hasLabel('Hotel').limit(10)"
        
        return query
    
    async def explain_query(self, gremlin_query: str) -> str:
        """
        Generate a human-readable explanation of a Gremlin query.
        
        Args:
            gremlin_query: Gremlin query to explain
            
        Returns:
            Human-readable explanation
        """
        if not self._is_initialized:
            raise RuntimeError("Graph Query LLM not initialized")
        
        try:
            prompt = f"""
{self._schema_prompt}

TASK: Explain the following Gremlin query in simple, human-readable terms.

Gremlin Query: {gremlin_query}

Please provide a clear explanation of:
1. What this query is looking for
2. How it traverses the graph
3. What results it will return

Explanation:"""

            response = await self._call_gemini(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
            return f"Query explanation unavailable: {str(e)}"
    
    async def suggest_similar_queries(self, user_query: str) -> List[str]:
        """
        Suggest similar queries that the user might be interested in.
        
        Args:
            user_query: Original user query
            
        Returns:
            List of suggested query strings
        """
        if not self._is_initialized:
            raise RuntimeError("Graph Query LLM not initialized")
        
        try:
            prompt = f"""
{self._schema_prompt}

TASK: Based on the user's query, suggest 3-5 related questions they might ask about hotel reviews.

User Query: "{user_query}"

Please suggest similar but different questions that would be relevant for hotel review analysis. 
Return only the questions, one per line, without numbers or bullets.

Suggestions:"""

            response = await self._call_gemini(prompt)
            
            # Parse suggestions
            suggestions = [
                line.strip() 
                for line in response.split('\n') 
                if line.strip() and not line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '-', '*'))
            ]
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []


# Factory function for dependency injection
def get_graph_query_llm() -> GraphQueryLLM:
    """Get or create Graph Query LLM instance."""
    settings = get_settings()
    return GraphQueryLLM(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model
    )
