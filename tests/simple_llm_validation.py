#!/usr/bin/env python3
"""
Simple LLM Validation Example

A streamlined version that directly integrates with the existing GraphQueryLLM
and provides quick validation results.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings


# Quick test cases for immediate validation
QUICK_TEST_CASES = [
    {
        "input": "Show me all hotels",
        "expected": "g.V().hasLabel('Hotel').valueMap()"
    },
    {
        "input": "Find VIP guests",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap()"
    },
    {
        "input": "Show me high-rated reviews",
        "expected": "g.V().hasLabel('Review').has('score', gte(8)).valueMap()"
    },
    {
        "input": "Find hotels with excellent cleanliness ratings",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5)).select('hotel').valueMap()"
    },
    {
        "input": "Türkçe yazılmış temizlik şikayetlerini göster",
        "expected": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').has('created_at', gte('2024-06-21')).in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'maintenance').valueMap()"
    },
    {
        "input": "Find hotels with excellent service but poor location ratings",
        "expected": "g.V().hasLabel('Hotel').as('hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5))).where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'location').in('ANALYZES_ASPECT').has('aspect_score', lte(2.5))).select('hotel').valueMap()"
    },
    {
        "input": "VIP misafirlerin sorunlarını göster",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "Find recent reviews from this year",
        "expected": "g.V().hasLabel('Review').has('created_at', gte('2024-01-01')).valueMap()"
    },
    {
        "input": "Show me hotels with good service scores",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0)).select('hotel').valueMap()"
    }
]


def test_llm_to_gremlin(generator_function):
    """
    Simple validation function that tests LLM-to-Gremlin conversion.
    
    Args:
        generator_function: Function that takes natural language and returns Gremlin query
    """
    print("🧪 LLM-to-Gremlin Validation Test")
    print("=" * 50)
    
    passed = 0
    total = len(QUICK_TEST_CASES)
    
    for i, test_case in enumerate(QUICK_TEST_CASES, 1):
        input_query = test_case["input"]
        expected_query = test_case["expected"]
        
        print(f"\n[{i:2d}] Testing: '{input_query[:45]}{'...' if len(input_query) > 45 else ''}'")
        
        try:
            # Generate query
            generated_query = generator_function(input_query)
            
            # Basic validation
            syntax_valid = (generated_query and 
                          generated_query.strip().startswith('g.') and
                          'hasLabel(' in generated_query)
            
            # Simple similarity check (contains key components)
            expected_parts = expected_query.lower().split('.')
            generated_parts = generated_query.lower().split('.')
            common_parts = len(set(expected_parts) & set(generated_parts))
            similarity = common_parts / max(len(expected_parts), 1)
            
            # Test passes if syntax valid and reasonable similarity
            test_passed = syntax_valid and similarity >= 0.3
            
            if test_passed:
                passed += 1
                print(f"    ✅ PASS - Generated: {generated_query[:50]}{'...' if len(generated_query) > 50 else ''}")
            else:
                print(f"    ❌ FAIL - Generated: {generated_query[:50]}{'...' if len(generated_query) > 50 else ''}")
                print(f"    Expected: {expected_query[:50]}{'...' if len(expected_query) > 50 else ''}")
                
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
    
    # Summary
    pass_rate = (passed / total) * 100
    print(f"\n📊 RESULTS: {passed}/{total} tests passed ({pass_rate:.1f}%)")
    
    if pass_rate >= 80:
        print("🎉 Excellent! Your LLM is working very well.")
    elif pass_rate >= 60:
        print("👍 Good performance with room for improvement.")
    elif pass_rate >= 40:
        print("⚠️  Moderate performance, needs work.")
    else:
        print("❌ Poor performance, major improvements needed.")
    
    return pass_rate >= 70


async def test_graph_query_llm():
    """Test the actual GraphQueryLLM from the system."""
    print("🤖 TESTING ACTUAL GRAPH RAG LLM")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    print(f"✅ Environment loaded: {settings.model_provider} - {settings.gemini_model}")
    
    try:
        # Initialize LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ GraphQueryLLM initialized successfully")
        
        # Create async wrapper function
        async def async_generator(query: str) -> str:
            try:
                result = await llm.generate_gremlin_query(query)
                return result if result else "g.V().limit(10).valueMap()"
            except Exception as e:
                return f"ERROR: {str(e)}"
        
        # Convert to sync for the test function
        def sync_generator(query: str) -> str:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(async_generator(query))
                return result
            finally:
                loop.close()
        
        # Run tests
        success = test_llm_to_gremlin(sync_generator)
        return success
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_graph_query_llm())
    sys.exit(0 if success else 1)
