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
- Find all hotels: g.V().hasLabel('Hotel').valueMap(true).select('hotel_name')
- Find hotel by name: g.V().hasLabel('Hotel').has('name', 'Hotel Name').valueMap(true)
- Find reviews for a hotel: g.V().hasLabel('Hotel').has('name', 'Hotel Name').in('HAS_REVIEW').valueMap(true)
- Find high-rated reviews: g.V().hasLabel('Review').has('score', gte(8)).valueMap(true)
- Find hotels with good cleanliness: g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').values('aspect_score').is(gte(4.0))).valueMap(true).select('hotel_name')
- Find reviews about specific aspects: g.V().hasLabel('Review').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').valueMap(true)
- Find reviews by language: g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'en').in('WRITTEN_IN').valueMap(true)
- Find accommodation types: g.V().hasLabel('AccommodationType').valueMap(true)
- Find hotels in a city: g.V().hasLabel('Hotel').has('city', 'New York').valueMap(true).select('hotel_name')

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
- "yorum" = review/comment
- "hizmet" = service
- "VIP" = VIP (same in Turkish)
- "bakım" = maintenance
- "sorun" = problem/issue
- "göster" = show
- "bul" = find
- "isim/isimler" = name/names
- "listele" = list
- "puanı" = score/rating
- "kalite" = quality
- "iyi" = good
- "kötü" = bad
- "yüksek" = high
- "düşük" = low
- "tüm" = all
- "konaklama" = accommodation
- "türü" = type
- "yazılmış" = written
- "tipi" = type
- "olan" = that/which
- "tür" = type/kind

TURKISH QUERY EXAMPLES (Few-Shot Learning):
1. "Otellerin isimlerini göster" → g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)
2. "Tüm otelleri listele" → g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)
3. "VIP misafirlerin bilgilerini listele" → g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap(true).limit(10)
4. "Temizlik puanı düşük otelleri bul" → g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').values('aspect_score').is(lt(3.0))).valueMap(true).select('hotel_name').limit(10)
5. "Türkçe şikayetleri göster" → g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').valueMap(true).limit(10)
6. "Türkçe yazılmış yorumları listele" → g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').valueMap(true).limit(10)
7. "Hizmet puanları yüksek oteller" → g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').values('aspect_score').is(gte(4.0))).valueMap(true).select('hotel_name').limit(10)
8. "VIP misafirlerin şikayetleri" → g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').has('sentiment', 'negative').valueMap(true).limit(10)
9. "Oda bakım sorunlarını bul" → g.V().hasLabel('MaintenanceIssue').where(__.in('HAS_ISSUE').hasLabel('Room')).valueMap(true).limit(10)
10. "Misafir tipi VIP olan yorumları göster" → g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').valueMap(true).limit(10)
11. "Temizlik şikayetlerini göster" → g.V().hasLabel('Review').where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').values('sentiment_score').is(lt(0))).valueMap(true).limit(10)
12. "Hizmet kalitesi iyi olan otellerin isimlerini listele" → g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').values('aspect_score').is(gte(4.0))).valueMap(true).select('hotel_name').limit(10)
13. "Konaklama türlerini göster" → g.V().hasLabel('AccommodationType').valueMap(true).limit(10)
14. "İngilizce yazılmış yorumları bul" → g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'en').in('WRITTEN_IN').valueMap(true).limit(10)
15. "Düşük puanlı otelleri listele" → g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').values('score').is(lt(3.0))).valueMap(true).select('hotel_name').limit(10)

CRITICAL REQUIREMENTS FOR TURKISH QUERIES:
- ALWAYS use .valueMap(true) instead of .valueMap() when returning vertex properties
- ALWAYS include hotel_name in select() when listing hotels
- For hotel listings, the pattern MUST be: g.V().hasLabel('Hotel').[filters].valueMap(true).select('hotel_name').limit(10)
- For property retrieval, always end with .valueMap(true) not just .valueMap()
- When the intent includes "göster" (show) or "listele" (list), ensure .valueMap(true) is included
- Never generate queries without .valueMap(true) for Turkish hotel listing queries
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

CRITICAL PROPERTY RETRIEVAL RULES:
- ALWAYS use .valueMap(true) instead of .valueMap() when returning vertex properties
- For hotel listings, ALWAYS include hotel_name: .valueMap(true).select('hotel_name')
- For queries asking "show hotels" or "list hotels": g.V().hasLabel('Hotel').[filters].valueMap(true).select('hotel_name')
- The .valueMap(true) includes the vertex ID and label which is essential for proper results
- Never omit .valueMap(true) when the user wants to see property values

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
            
            # Extract and clean the query (includes enhancement)
            gremlin_query = self._extract_gremlin_query(response)
            
            # Apply Turkish-specific validation if needed
            if detected_lang == 'tr':
                gremlin_query = self._validate_turkish_query(gremlin_query, user_query)
                logger.debug(f"Applied Turkish validation to query: {gremlin_query}")
            
            logger.debug(f"Final Gremlin query: {gremlin_query}")
            return gremlin_query
            
        except Exception as e:
            logger.error(f"❌ Failed to generate Gremlin query: {e}")
            
            # Intelligent fallback based on Turkish query intent
            detected_lang = self._detect_language(user_query)
            fallback_query = self._get_intelligent_fallback(user_query, detected_lang)
            
            # Apply Turkish validation to fallback if needed
            if detected_lang == 'tr':
                fallback_query = self._validate_turkish_query(fallback_query, user_query)
                logger.debug(f"Applied Turkish validation to fallback query: {fallback_query}")
            
            return fallback_query
    
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
                query = "g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)"
        
        # Post-processing to enhance query quality
        query = self._enhance_gremlin_query(query)
        
        return query

    def _enhance_gremlin_query(self, query: str) -> str:
        """
        Post-process the Gremlin query to ensure best practices.
        
        Args:
            query: Raw Gremlin query from LLM
            
        Returns:
            Enhanced Gremlin query with enforced patterns
        """
        # Fix .valueMap() to .valueMap(true) for better property retrieval
        if '.valueMap()' in query and '.valueMap(true)' not in query:
            query = query.replace('.valueMap()', '.valueMap(true)')
            logger.debug("Enhanced query: Added .valueMap(true) instead of .valueMap()")
        
        # For Hotel queries that end with just valueMap(true), add hotel_name selection
        if 'hasLabel(\'Hotel\')' in query and query.endswith('.valueMap(true)'):
            if 'select(' not in query:
                query = query.replace('.valueMap(true)', '.valueMap(true).select(\'hotel_name\')')
                logger.debug("Enhanced query: Added hotel_name selection for Hotel queries")
        
        # Ensure limit exists for performance (unless it's already there)
        if '.limit(' not in query and not query.endswith('limit(10)'):
            query = query + '.limit(10)'
            logger.debug("Enhanced query: Added .limit(10) for performance")
        
        # Enhanced Turkish query patterns detection and fixing
        turkish_keywords = ['hotel', 'otel', 'misafir', 'guest', 'göster', 'listele', 'isim', 'isimleri']
        is_turkish_context = any(turkish_word in query.lower() for turkish_word in turkish_keywords)
        
        if is_turkish_context:
            # Fix Turkish hotel listing queries - ensure proper structure
            if 'hasLabel(\'Hotel\')' in query:
                # Case 1: Hotel query without any value extraction
                if not ('valueMap(' in query or 'values(' in query or 'select(' in query):
                    query = query.replace('hasLabel(\'Hotel\')', 'hasLabel(\'Hotel\').valueMap(true).select(\'hotel_name\')')
                    logger.debug("Enhanced query: Added valueMap(true).select('hotel_name') for Turkish hotel query")
                
                # Case 2: Hotel query with .valueMap() but missing hotel_name selection
                elif '.valueMap(true)' in query and 'select(' not in query:
                    query = query.replace('.valueMap(true)', '.valueMap(true).select(\'hotel_name\')')
                    logger.debug("Enhanced query: Added hotel_name selection for Turkish hotel query")
                
                # Case 3: Hotel query ending with just .limit() but missing valueMap
                elif query.count('hasLabel(\'Hotel\')') > 0 and '.limit(' in query and not ('valueMap(' in query or 'values(' in query):
                    # Insert valueMap before limit
                    limit_pos = query.find('.limit(')
                    if limit_pos > 0:
                        query = query[:limit_pos] + '.valueMap(true).select(\'hotel_name\')' + query[limit_pos:]
                        logger.debug("Enhanced query: Inserted valueMap(true).select('hotel_name') before limit for Turkish query")
            
            # Fix any remaining .valueMap() without true parameter
            if '.valueMap()' in query:
                query = query.replace('.valueMap()', '.valueMap(true)')
                logger.debug("Enhanced query: Fixed .valueMap() to .valueMap(true) in Turkish context")
        
        return query
    
    def _validate_turkish_query(self, query: str, original_query: str) -> str:
        """
        Validate and fix Turkish queries to ensure they include essential elements.
        
        Args:
            query: Generated Gremlin query
            original_query: Original Turkish user query
            
        Returns:
            Enhanced/validated Gremlin query
        """
        # Check if original query was Turkish
        turkish_indicators = [
            'otel', 'misafir', 'göster', 'listele', 'isim', 'isimleri', 'puanı', 
            'şikayet', 'temizlik', 'hizmet', 'tüm', 'kalite', 'iyi', 'kötü', 
            'yüksek', 'düşük', 'konaklama', 'türü', 'yazılmış', 'tipi', 'olan', 'bul'
        ]
        is_turkish = any(indicator in original_query.lower() for indicator in turkish_indicators)
        
        if not is_turkish:
            return query
            
        # Ensure .valueMap(true) is used instead of .valueMap()
        if '.valueMap()' in query and '.valueMap(true)' not in query:
            query = query.replace('.valueMap()', '.valueMap(true)')
            logger.info("Fixed Turkish query: Changed .valueMap() to .valueMap(true)")
            
        # Validate hotel listing queries
        hotel_listing_words = ['otel', 'hotel']
        action_words = ['göster', 'listele', 'isim', 'isimleri', 'tüm']
        
        if (any(word in original_query.lower() for word in hotel_listing_words) and 
            any(word in original_query.lower() for word in action_words)):
            
            # This is a hotel listing query - ensure proper structure
            if 'hasLabel(\'Hotel\')' in query:
                # Must have valueMap(true) and hotel_name selection
                needs_fixing = False
                
                if '.valueMap(true)' not in query:
                    needs_fixing = True
                    logger.warning(f"Turkish hotel query missing .valueMap(true): {query}")
                    
                if 'hotel_name' not in query and 'select(' not in query:
                    needs_fixing = True
                    logger.warning(f"Turkish hotel query missing hotel_name selection: {query}")
                
                if needs_fixing:
                    # Reconstruct the query with proper structure
                    base_query = "g.V().hasLabel('Hotel')"
                    
                    # Add any filters that were in the original query
                    if '.has(' in query:
                        # Extract has conditions
                        has_conditions = []
                        import re
                        has_matches = re.findall(r'\.has\([^)]+\)', query)
                        for match in has_matches:
                            has_conditions.append(match)
                        base_query += ''.join(has_conditions)
                    
                    # Add where conditions if present
                    if '.where(' in query:
                        where_start = query.find('.where(')
                        where_end = query.find(')', where_start)
                        if where_end > where_start:
                            # Find the complete where clause (handle nested parentheses)
                            paren_count = 0
                            for i in range(where_start, len(query)):
                                if query[i] == '(':
                                    paren_count += 1
                                elif query[i] == ')':
                                    paren_count -= 1
                                    if paren_count == 0:
                                        where_clause = query[where_start:i+1]
                                        base_query += where_clause
                                        break
                    
                    # Add proper value retrieval and selection
                    base_query += '.valueMap(true).select(\'hotel_name\')'
                    
                    # Add limit if present in original or default
                    if '.limit(' in query:
                        limit_match = re.search(r'\.limit\(\d+\)', query)
                        if limit_match:
                            base_query += limit_match.group()
                    else:
                        base_query += '.limit(10)'
                    
                    query = base_query
                    logger.info(f"Reconstructed Turkish hotel listing query: {query}")
        
        # Validate VIP guest queries
        if 'vip' in original_query.lower() and 'misafir' in original_query.lower():
            if 'hasLabel(\'Reviewer\')' in query and 'traveler_type' not in query:
                # Add VIP filter if missing
                query = query.replace('hasLabel(\'Reviewer\')', 'hasLabel(\'Reviewer\').has(\'traveler_type\', \'VIP\')')
                logger.info("Added VIP filter to Turkish guest query")
        
        # Validate review language queries
        if any(lang in original_query.lower() for lang in ['türkçe', 'ingilizce']) and 'yazılmış' in original_query.lower():
            lang_code = 'tr' if 'türkçe' in original_query.lower() else 'en'
            if f"has('code', '{lang_code}')" not in query:
                # Ensure language filtering is present
                if 'hasLabel(\'Review\')' in query:
                    query = query.replace(
                        'hasLabel(\'Review\')', 
                        f'hasLabel(\'Review\').out(\'WRITTEN_IN\').has(\'code\', \'{lang_code}\').in(\'WRITTEN_IN\')'
                    )
                    logger.info(f"Added {lang_code} language filter to Turkish review query")
        
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
    
    def _get_intelligent_fallback(self, user_query: str, detected_lang: str) -> str:
        """
        Generate an intelligent fallback query based on user intent.
        
        Args:
            user_query: Original user query
            detected_lang: Detected language code
            
        Returns:
            Appropriate fallback Gremlin query
        """
        query_lower = user_query.lower()
        
        # Turkish hotel name/listing queries
        if any(term in query_lower for term in ['otel', 'hotel']) and any(term in query_lower for term in ['isim', 'göster', 'listele', 'tüm']):
            return "g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)"
        
        # VIP guest queries (Turkish and English)
        elif any(term in query_lower for term in ['vip', 'misafir']):
            return "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap(true).limit(10)"
        
        # Service rating queries
        elif any(term in query_lower for term in ['hizmet', 'service']) and any(term in query_lower for term in ['puan', 'rating', 'yüksek', 'iyi', 'kalite']):
            return "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').values('aspect_score').is(gte(4.0))).valueMap(true).select('hotel_name').limit(10)"
        
        # Cleanliness queries  
        elif any(term in query_lower for term in ['temizlik', 'cleanliness']):
            return "g.V().hasLabel('Review').where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness')).valueMap(true).limit(10)"
        
        # Turkish language reviews
        elif any(term in query_lower for term in ['türkçe', 'turkish']) and any(term in query_lower for term in ['yorum', 'review', 'yazılmış']):
            return "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').valueMap(true).limit(10)"
        
        # English language reviews
        elif any(term in query_lower for term in ['ingilizce', 'english']) and any(term in query_lower for term in ['yorum', 'review', 'yazılmış']):
            return "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'en').in('WRITTEN_IN').valueMap(true).limit(10)"
        
        # Maintenance/bakım issues
        elif any(term in query_lower for term in ['bakım', 'maintenance', 'sorun', 'issue']):
            return "g.V().hasLabel('MaintenanceIssue').valueMap(true).limit(10)"
        
        # Room queries
        elif any(term in query_lower for term in ['oda', 'room']):
            return "g.V().hasLabel('Room').valueMap(true).limit(10)"
        
        # Accommodation type queries
        elif any(term in query_lower for term in ['konaklama', 'accommodation', 'türü', 'type']):
            return "g.V().hasLabel('AccommodationType').valueMap(true).limit(10)"
        
        # Low rating/score queries
        elif any(term in query_lower for term in ['düşük', 'kötü', 'low', 'bad']) and any(term in query_lower for term in ['puan', 'rating', 'score']):
            return "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').values('score').is(lt(3.0))).valueMap(true).select('hotel_name').limit(10)"
        
        # Generic hotel fallback
        elif any(term in query_lower for term in ['otel', 'hotel']):
            return "g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)"
        
        # Generic review fallback
        elif any(term in query_lower for term in ['yorum', 'review', 'şikayet', 'complaint']):
            return "g.V().hasLabel('Review').valueMap(true).limit(10)"
        
        # Default safe fallback
        else:
            return "g.V().hasLabel('Hotel').valueMap(true).select('hotel_name').limit(10)"

# Factory function for dependency injection
def get_graph_query_llm() -> GraphQueryLLM:
    """Get or create Graph Query LLM instance."""
    settings = get_settings()
    return GraphQueryLLM(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model
    )
