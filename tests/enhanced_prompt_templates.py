#!/usr/bin/env python3
"""
Enhanced Prompt Templates for LLM-to-Gremlin Translation

This module provides robust, multilingual prompt templates for converting
natural language queries into Gremlin graph database queries. Designed for
hotel review domain with comprehensive Turkish and English support.

Usage:
    from enhanced_prompt_templates import GremlinPromptGenerator
    
    generator = GremlinPromptGenerator()
    prompt = generator.create_prompt("Find VIP guests with maintenance issues", "en")
"""

from typing import Dict, List, Optional
from enum import Enum


class LanguageCode(str, Enum):
    """Supported language codes."""
    ENGLISH = "en"
    TURKISH = "tr"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    UNKNOWN = "unknown"


class GremlinPromptGenerator:
    """
    Enhanced prompt generator for multilingual Gremlin query generation.
    
    Features:
    - Comprehensive schema context
    - Language-specific instructions
    - Few-shot examples
    - Domain-specific vocabulary mapping
    - Complex query pattern support
    """
    
    def __init__(self):
        """Initialize the prompt generator with templates and examples."""
        self.base_schema = self._build_schema_description()
        self.gremlin_rules = self._build_gremlin_rules()
        self.few_shot_examples = self._build_few_shot_examples()
        self.language_mappings = self._build_language_mappings()
    
    def create_prompt(self, user_query: str, detected_language: str = "en") -> str:
        """
        Create a comprehensive prompt for Gremlin query generation.
        
        Args:
            user_query: Natural language query from user
            detected_language: Language code (en, tr, es, etc.)
            
        Returns:
            Complete prompt string ready for LLM
        """
        # Build the prompt components
        system_context = self._build_system_context()
        schema_section = self.base_schema
        rules_section = self.gremlin_rules
        examples_section = self._get_language_specific_examples(detected_language)
        language_instruction = self._get_language_instruction(detected_language)
        
        # Assemble the complete prompt
        prompt = f"""{system_context}

{schema_section}

{rules_section}

{examples_section}

{language_instruction}

User Query: "{user_query}"

Requirements:
1. Generate ONLY the Gremlin query, no explanation or markdown
2. The query must be syntactically correct and executable
3. Use exact vertex and edge labels from the schema above
4. Include appropriate filters and traversals based on user intent
5. Add .limit(10) at the end unless a specific limit is requested
6. If the query is ambiguous, make reasonable assumptions based on hotel review domain
7. For Turkish queries, focus on semantic meaning rather than literal translation

Gremlin Query:"""

        return prompt
    
    def _build_system_context(self) -> str:
        """Build the system context and role definition."""
        return """You are an expert Gremlin query translator specializing in hotel review graph databases. Your role is to convert natural language queries into precise, executable Gremlin traversal queries. You understand multiple languages and can interpret domain-specific terminology in the hospitality industry."""
    
    def _build_schema_description(self) -> str:
        """Build comprehensive schema description."""
        return """GRAPH SCHEMA - Hotel Review Domain:

VERTICES (Nodes):
- Hotel: Hotel properties (id, name, city, country, star_rating, address, phone, email)
- Review: Guest reviews (id, score, title, text, created_at, stay_date, verified, helpful_votes)
- Reviewer: Review authors (id, username, join_date, review_count, traveler_type, location)
- Analysis: AI sentiment analysis (id, sentiment_score, confidence, aspect_score, explanation)
- Aspect: Service aspects (id, name, category, description, weight)
- Language: Languages (code, name, family, script)
- Source: Review platforms (id, name, url, type, reliability_score)
- HotelGroup: Hotel chains (id, name, headquarters, founded, website)
- AccommodationType: Room types (id, name, category, capacity, amenities, size_sqm)
- Location: Geographic areas (id, name, type, latitude, longitude, timezone)
- Amenity: Hotel facilities (id, name, category, description, is_free, availability)

EDGES (Relationships):
- OWNS: HotelGroup -> Hotel (ownership relationship)
- HAS_REVIEW: Hotel -> Review (hotel receives review)
- WROTE: Reviewer -> Review (reviewer writes review)
- HAS_ANALYSIS: Review -> Analysis (review has sentiment analysis)
- ANALYZES_ASPECT: Analysis -> Aspect (analysis covers specific aspect)
- OFFERS: Hotel -> AccommodationType (hotel offers room type)
- PROVIDES: Hotel -> Amenity (hotel provides amenity)
- LOCATED_IN: Hotel -> Location (hotel located in area)
- SOURCED_FROM: Review -> Source (review from platform)
- WRITTEN_IN: Review -> Language (review written in language)
- SUPPORTS_LANGUAGE: Hotel -> Language (hotel supports language)
- REFERS_TO: Review -> Location (review mentions location)
- MENTIONS: Review -> Amenity (review mentions amenity)"""
    
    def _build_gremlin_rules(self) -> str:
        """Build Gremlin syntax rules and best practices."""
        return """GREMLIN SYNTAX RULES:
1. Always start with g.V() for vertex queries
2. Use hasLabel('VertexType') to filter by vertex type
3. Use has('property', 'value') for exact property matches
4. Use has('property', gte(value)) for greater than or equal comparisons
5. Use has('property', lte(value)) for less than or equal comparisons
6. Use has('property', within(['val1', 'val2'])) for multiple values
7. Use has('property', containing('text')) for text search
8. Use out('EdgeLabel') to traverse outgoing edges
9. Use in('EdgeLabel') to traverse incoming edges
10. Use both('EdgeLabel') to traverse both directions
11. Use where() for complex filtering conditions
12. Use valueMap() to return all properties, values('property') for specific properties
13. Use count() for counting results
14. Use order().by('property') for sorting
15. Use dedup() to remove duplicates
16. Always add .limit(10) for performance unless otherwise specified"""
    
    def _build_few_shot_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """Build few-shot examples for different languages."""
        return {
            "en": [
                {
                    "user": "Find all 5-star hotels in Istanbul",
                    "gremlin": "g.V().hasLabel('Hotel').has('city', 'Istanbul').has('star_rating', 5).valueMap().limit(10)"
                },
                {
                    "user": "Show VIP guests with more than 10 reviews",
                    "gremlin": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').has('review_count', gt(10)).valueMap().limit(10)"
                },
                {
                    "user": "Find hotels with poor cleanliness ratings",
                    "gremlin": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').has('aspect_score', lt(3.0))).valueMap().limit(10)"
                },
                {
                    "user": "Show recent reviews about service quality",
                    "gremlin": "g.V().hasLabel('Review').has('created_at', gte('2024-01-01')).where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service')).valueMap().limit(10)"
                },
                {
                    "user": "Find luxury hotels offering spa amenities",
                    "gremlin": "g.V().hasLabel('Hotel').has('star_rating', gte(4)).where(__.out('PROVIDES').has('name', containing('spa'))).valueMap().limit(10)"
                }
            ],
            "tr": [
                {
                    "user": "İstanbul'daki 5 yıldızlı otelleri bul",
                    "gremlin": "g.V().hasLabel('Hotel').has('city', 'Istanbul').has('star_rating', 5).valueMap().limit(10)"
                },
                {
                    "user": "VIP misafirlerin şikayetlerini göster",
                    "gremlin": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').where(__.has('score', lt(6))).valueMap().limit(10)"
                },
                {
                    "user": "Türkçe yazılmış temizlik şikayetlerini göster",
                    "gremlin": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').has('sentiment_score', lt(0))).valueMap().limit(10)"
                },
                {
                    "user": "Hizmet kalitesi yüksek otelleri listele",
                    "gremlin": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').has('aspect_score', gte(4.0))).valueMap().limit(10)"
                },
                {
                    "user": "Son bakım sorunlarını bul",
                    "gremlin": "g.V().hasLabel('Review').has('created_at', gte('2024-06-01')).where(__.has('text', containing('bakım')).or(__.has('text', containing('maintenance')))).valueMap().limit(10)"
                }
            ]
        }
    
    def _build_language_mappings(self) -> Dict[str, Dict[str, str]]:
        """Build language-specific term mappings."""
        return {
            "tr": {
                "otel": "hotel",
                "misafir": "guest",
                "oda": "room", 
                "temizlik": "cleanliness",
                "şikayet": "complaint",
                "yorum": "review",
                "hizmet": "service",
                "bakım": "maintenance",
                "sorun": "problem",
                "göster": "show",
                "bul": "find",
                "listele": "list",
                "ara": "search",
                "değerlendir": "evaluate",
                "puan": "score",
                "yıldız": "star",
                "lüks": "luxury",
                "ekonomik": "budget",
                "aile": "family",
                "iş": "business",
                "tatil": "vacation",
                "spa": "spa",
                "havuz": "pool",
                "wifi": "wifi",
                "kahvaltı": "breakfast",
                "park": "parking",
                "klima": "air conditioning",
                "manzara": "view",
                "deniz": "sea",
                "şehir": "city"
            },
            "es": {
                "hotel": "hotel",
                "huésped": "guest",
                "habitación": "room",
                "limpieza": "cleanliness",
                "queja": "complaint",
                "reseña": "review",
                "servicio": "service",
                "mantenimiento": "maintenance",
                "problema": "problem",
                "mostrar": "show",
                "encontrar": "find",
                "buscar": "search"
            },
            "fr": {
                "hôtel": "hotel",
                "client": "guest", 
                "chambre": "room",
                "propreté": "cleanliness",
                "plainte": "complaint",
                "avis": "review",
                "service": "service",
                "maintenance": "maintenance",
                "problème": "problem",
                "montrer": "show",
                "trouver": "find",
                "chercher": "search"
            }
        }
    
    def _get_language_specific_examples(self, language: str) -> str:
        """Get examples for specific language."""
        examples = self.few_shot_examples.get(language, self.few_shot_examples["en"])
        
        example_text = f"EXAMPLES ({language.upper()}):\n\n"
        
        for i, example in enumerate(examples, 1):
            example_text += f"Example {i}:\n"
            example_text += f"User: {example['user']}\n"
            example_text += f"Gremlin: {example['gremlin']}\n\n"
        
        return example_text
    
    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instructions."""
        if language == "tr":
            vocabulary_section = "\nCOMMON TURKISH HOTEL TERMS:\n"
            for turkish_term, english_equiv in self.language_mappings["tr"].items():
                vocabulary_section += f"- '{turkish_term}' = {english_equiv}\n"
            
            return f"""LANGUAGE NOTE: The input query is in Turkish. Please understand the semantic meaning and convert to Gremlin.
{vocabulary_section}
TURKISH PROCESSING TIPS:
- Focus on semantic meaning rather than literal translation
- Map Turkish hotel terminology to English concepts in the schema
- Understand context clues from Turkish grammatical structures
- Consider compound words and inflected forms in Turkish"""
        
        elif language in ["es", "fr", "de", "it"]:
            return f"""LANGUAGE NOTE: The input query is in {language.upper()}. Please understand the meaning and convert to Gremlin.
Focus on the semantic meaning rather than literal translation.
Map language-specific terms to the English schema concepts."""
        
        else:
            return ""
    
    def create_validation_prompt(self, gremlin_query: str) -> str:
        """Create a prompt for validating generated Gremlin queries."""
        return f"""You are a Gremlin query validator. Check if this query is syntactically correct and follows best practices:

QUERY TO VALIDATE:
{gremlin_query}

VALIDATION CRITERIA:
1. Starts with g.V() or g.E()
2. Uses correct hasLabel() syntax
3. Property filters use correct syntax
4. Edge traversals use out(), in(), or both()
5. Ends with appropriate result step (valueMap(), values(), count(), etc.)
6. Includes limit() for performance
7. Uses correct comparison operators (gt(), lt(), gte(), lte(), within(), containing())

RESPOND WITH:
- VALID: [Yes/No]
- ISSUES: [List any syntax or logical problems]
- SUGGESTIONS: [Improvements if any]

Analysis:"""
    
    def create_explanation_prompt(self, gremlin_query: str) -> str:
        """Create a prompt for explaining Gremlin queries in human language."""
        return f"""Explain this Gremlin query in simple, human-readable terms:

{self.base_schema}

GREMLIN QUERY:
{gremlin_query}

Please provide a clear explanation that covers:
1. What this query is looking for (the main goal)
2. How it navigates through the graph (step by step)
3. What filters and conditions are applied
4. What kind of results it will return
5. Any performance considerations

Make the explanation accessible to someone who doesn't know Gremlin syntax.

Explanation:"""


def create_advanced_prompt_template() -> str:
    """
    Create an advanced prompt template with comprehensive coverage.
    
    This template includes:
    - Multi-hop traversal patterns
    - Complex filtering scenarios
    - Aggregation and grouping queries
    - Time-based filtering
    - Text search patterns
    """
    return """You are an expert Gremlin query translator for hotel review graph databases. Convert natural language to precise Gremlin queries.

ADVANCED QUERY PATTERNS:

Multi-hop Traversals:
- "Hotels with guests who wrote negative reviews about service"
  → g.V().hasLabel('Hotel').in('HAS_REVIEW').has('score', lt(5)).where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service')).out('WROTE').dedup().valueMap().limit(10)

Aggregation Patterns:
- "Average rating by hotel"
  → g.V().hasLabel('Hotel').project('hotel', 'avg_rating').by('name').by(__.in('HAS_REVIEW').values('score').mean()).limit(10)

Time-based Filtering:
- "Reviews from last month"
  → g.V().hasLabel('Review').has('created_at', gte('2024-06-01')).has('created_at', lt('2024-07-01')).valueMap().limit(10)

Text Search:
- "Reviews mentioning wifi problems"
  → g.V().hasLabel('Review').has('text', containing('wifi')).where(__.has('text', containing('problem')).or().has('score', lt(6))).valueMap().limit(10)

Complex Conditions:
- "VIP guests at 4+ star hotels with service complaints"
  → g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').where(__.out('HAS_REVIEW').has('star_rating', gte(4))).where(__.in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').has('sentiment_score', lt(0))).valueMap().limit(10)

PERFORMANCE OPTIMIZATIONS:
- Always use hasLabel() first for vertex type filtering
- Add property filters early in the traversal
- Use where() for complex conditions
- Include limit() to prevent large result sets
- Consider using project() for custom result formatting

Convert this query following all patterns and optimizations above:"""


def demo_prompt_usage():
    """Demonstrate usage of the enhanced prompt system."""
    print("🚀 ENHANCED PROMPT TEMPLATES DEMO")
    print("=" * 60)
    
    generator = GremlinPromptGenerator()
    
    # Test queries in different languages
    test_cases = [
        {
            "query": "Find luxury hotels with spa amenities in Istanbul",
            "language": "en",
            "description": "English complex query"
        },
        {
            "query": "VIP misafirlerin şikayetlerini göster",
            "language": "tr", 
            "description": "Turkish VIP complaints"
        },
        {
            "query": "Temizlik puanı düşük olan otelleri bul",
            "language": "tr",
            "description": "Turkish cleanliness ratings"
        },
        {
            "query": "Show hotels with recent maintenance issues",
            "language": "en",
            "description": "English maintenance query"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}] {test['description']}")
        print(f"Query: {test['query']}")
        print(f"Language: {test['language']}")
        print("-" * 40)
        
        # Generate prompt
        prompt = generator.create_prompt(test['query'], test['language'])
        
        # Show prompt preview (first 300 chars)
        print(f"Prompt Preview:")
        print(prompt[:300] + "...")
        print("-" * 40)
    
    print("\n✅ Enhanced prompt templates ready for production use!")
    print("\nKey Features:")
    print("- Comprehensive schema coverage")
    print("- Language-specific instructions") 
    print("- Rich few-shot examples")
    print("- Advanced query pattern support")
    print("- Performance optimization guidance")
    print("- Multilingual vocabulary mapping")


if __name__ == "__main__":
    demo_prompt_usage()
