#!/usr/bin/env python3
"""
Demo: test_llm_to_gremlin Function

This script demonstrates the comprehensive test_llm_to_gremlin validation function
that was requested in the task. It shows how to validate LLM-to-Gremlin conversion
with both mock and real LLM functions.

The test_llm_to_gremlin function:
1. Takes a generator function as input
2. Runs it through 35+ test cases (input/expected pairs) 
3. Validates syntax, calculates similarity, and provides detailed analysis
4. Returns comprehensive results with pass/fail breakdown
"""

import asyncio
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Import the comprehensive test suite
from tests.test_llm_gremlin_validation import test_llm_to_gremlin

# Import the actual LLM for real testing
try:
    from app.core.graph_query_llm import GraphQueryLLM
    from app.core.config import get_settings
    HAS_REAL_LLM = True
except ImportError:
    HAS_REAL_LLM = False
    print("⚠️ Real LLM not available, using mock only")

def enhanced_mock_llm(natural_language_query: str) -> str:
    """
    Enhanced mock LLM function for demonstration.
    This shows better coverage than the simple demo function.
    """
    query_lower = natural_language_query.lower()
    
    # Handle hotel queries
    if "hotels" in query_lower:
        if "all" in query_lower:
            return "g.V().hasLabel('Hotel').valueMap()"
        elif "new york" in query_lower:
            return "g.V().hasLabel('Hotel').has('city', 'New York').valueMap()"
        elif "5-star" in query_lower or "5 star" in query_lower:
            return "g.V().hasLabel('Hotel').has('star_rating', 5).valueMap()"
        elif "luxury" in query_lower:
            return "g.V().hasLabel('Hotel').has('star_rating', gte(4)).valueMap()"
        elif "budget" in query_lower:
            return "g.V().hasLabel('Hotel').has('price_per_night', lte(100)).valueMap()"
        elif "cleanliness" in query_lower:
            return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5)).select('hotel').valueMap()"
        elif "service" in query_lower:
            return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0)).select('hotel').valueMap()"
        elif "location" in query_lower and "poor" in query_lower:
            return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'location').in('ANALYZES_ASPECT').has('aspect_score', lte(2.5)).select('hotel').valueMap()"
    
    # Handle review queries
    elif "reviews" in query_lower:
        if "high-rated" in query_lower:
            return "g.V().hasLabel('Review').has('score', gte(8)).valueMap()"
        elif "recent" in query_lower or "this year" in query_lower:
            return "g.V().hasLabel('Review').has('created_at', gte('2024-01-01')).valueMap()"
        elif "verified" in query_lower:
            return "g.V().hasLabel('Review').has('verified', true).valueMap()"
        elif "negative" in query_lower:
            return "g.V().hasLabel('Review').has('score', lte(3)).valueMap()"
        elif "longer than" in query_lower:
            return "g.V().hasLabel('Review').has('text', textLength(gte(100))).valueMap()"
        elif "cleanliness" in query_lower:
            return "g.V().hasLabel('Review').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    
    # Handle guest/reviewer queries
    elif "vip" in query_lower:
        if "guest" in query_lower or "misafir" in query_lower:
            return "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap()"
        elif "maintenance" in query_lower or "issues" in query_lower:
            return "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').has('created_at', gte('2024-06-21')).in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'maintenance').valueMap()"
    elif "business travelers" in query_lower:
        return "g.V().hasLabel('Reviewer').has('traveler_type', 'business').valueMap()"
    elif "experienced reviewers" in query_lower:
        return "g.V().hasLabel('Reviewer').has('review_count', gte(10)).valueMap()"
    elif "solo travelers" in query_lower:
        return "g.V().hasLabel('Reviewer').has('traveler_type', 'solo').valueMap()"
    elif "family travelers" in query_lower:
        return "g.V().hasLabel('Reviewer').has('traveler_type', 'family').valueMap()"
    
    # Handle Turkish queries
    elif "türkçe" in query_lower or "temizlik" in query_lower:
        return "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    elif "hizmet puanlarını" in query_lower:
        return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').values('aspect_score').valueMap()"
    elif "bakım sorunlarını" in query_lower:
        return "g.V().hasLabel('Review').has('created_at', gte('2024-06-21')).where(__.has('text', containing('bakım'))).valueMap()"
    elif "oda şikayetlerini" in query_lower:
        return "g.V().hasLabel('Review').where(__.has('text', containing('oda'))).in('HAS_ANALYSIS').has('sentiment_score', lte(0)).out('HAS_ANALYSIS').valueMap()"
    
    # Complex queries fallback
    elif "excellent service but poor location" in query_lower:
        return "g.V().hasLabel('Hotel').as('hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5))).where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'location').in('ANALYZES_ASPECT').has('aspect_score', lte(2.5))).select('hotel').valueMap()"
    elif "consistently high ratings" in query_lower:
        return "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').in('ANALYZES_ASPECT').group().by(__.out('HAS_ANALYSIS').out('HAS_REVIEW')).by(__.values('aspect_score').mean()).unfold().where(__.select(values).is(gte(4.0)))).valueMap()"
    
    # Default fallback
    else:
        return "g.V().limit(10).valueMap()"


def sync_real_llm_wrapper(natural_language_query: str) -> str:
    """
    Synchronous wrapper for the async GraphQueryLLM.
    This demonstrates how to properly integrate async LLMs with the validation function.
    """
    if not HAS_REAL_LLM:
        return "ERROR: Real LLM not available"
    
    async def async_generate():
        # Load environment
        load_dotenv()
        settings = get_settings()
        
        # Initialize LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        
        # Generate query
        result = await llm.generate_gremlin_query(natural_language_query)
        return result if result else "ERROR: No query generated"
    
    try:
        # Run in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_generate())
        finally:
            loop.close()
    except Exception as e:
        return f"ERROR: {str(e)}"


def demo_test_validation():
    """
    Demonstrate the test_llm_to_gremlin function with multiple LLM implementations.
    """
    print("🎯 DEMO: test_llm_to_gremlin Function")
    print("=" * 80)
    print()
    print("This demonstrates the comprehensive validation function that:")
    print("✅ Takes a generator function as input")
    print("✅ Runs 35+ test cases (input/expected pairs)")
    print("✅ Validates syntax and calculates similarity")
    print("✅ Provides detailed analysis and breakdown")
    print("✅ Returns comprehensive results")
    print()
    
    # Test 1: Enhanced Mock LLM
    print("🧪 TEST 1: Enhanced Mock LLM")
    print("-" * 50)
    mock_results = test_llm_to_gremlin(enhanced_mock_llm)
    
    print(f"\n📊 Mock LLM Results:")
    print(f"   • Pass Rate: {mock_results['pass_rate']:.1f}%")
    print(f"   • Syntax Success: {mock_results['syntax_success_rate']:.1f}%")
    print(f"   • Average Similarity: {mock_results['average_similarity']:.3f}")
    print()
    
    # Test 2: Real LLM (if available)
    if HAS_REAL_LLM:
        print("🤖 TEST 2: Real GraphQueryLLM")
        print("-" * 50)
        print("⚠️ Note: This may take a while as it calls the actual LLM...")
        
        try:
            real_results = test_llm_to_gremlin(sync_real_llm_wrapper)
            
            print(f"\n📊 Real LLM Results:")
            print(f"   • Pass Rate: {real_results['pass_rate']:.1f}%")
            print(f"   • Syntax Success: {real_results['syntax_success_rate']:.1f}%")
            print(f"   • Average Similarity: {real_results['average_similarity']:.3f}")
            
        except Exception as e:
            print(f"❌ Real LLM test failed: {str(e)}")
    else:
        print("⚠️ TEST 2: Real LLM not available (import failed)")
    
    print()
    print("🎉 DEMO COMPLETE!")
    print("=" * 80)
    print()
    print("📋 HOW TO USE test_llm_to_gremlin:")
    print("```python")
    print("from test_llm_gremlin_validation import test_llm_to_gremlin")
    print()
    print("# Define your LLM function")
    print("def my_llm_function(natural_language_query: str) -> str:")
    print("    # Your LLM implementation here")
    print("    return gremlin_query")
    print()
    print("# Run validation")
    print("results = test_llm_to_gremlin(my_llm_function)")
    print("```")
    print()
    print("📊 RESULTS STRUCTURE:")
    print("```python")
    print("results = {")
    print("    'total_tests': 35,")
    print("    'passed_tests': int,")
    print("    'failed_tests': int,")
    print("    'pass_rate': float,")
    print("    'syntax_valid': int,")
    print("    'syntax_success_rate': float,")
    print("    'average_similarity': float,")
    print("    'test_details': [")
    print("        {")
    print("            'input': str,")
    print("            'expected': str,")
    print("            'generated': str,")
    print("            'syntax_valid': bool,")
    print("            'similarity': float,")
    print("            'test_passed': bool,")
    print("            'components': dict")
    print("        },")
    print("        # ... more test details")
    print("    ]")
    print("}")
    print("```")


if __name__ == "__main__":
    demo_test_validation()
