#!/usr/bin/env python3
"""
LLM to Gremlin Query Validation Test Suite

This script defines comprehensive test cases for validating natural language 
to Gremlin query conversion. It includes a validation function that checks 
if the LLM-generated Gremlin queries match expected outputs.

Each test case contains:
- input: Natural language query (English and Turkish)
- expected: Expected Gremlin query output

Based on the hotel review domain schema.
"""

from typing import List, Dict, Any, Callable
import re
from difflib import SequenceMatcher


# Comprehensive Test Cases for Natural Language → Gremlin Query Conversion
GREMLIN_TEST_CASES: List[Dict[str, str]] = [
    # Basic Hotel Queries
    {
        "input": "Show me all hotels",
        "expected": "g.V().hasLabel('Hotel').valueMap()"
    },
    {
        "input": "Find hotels in New York",
        "expected": "g.V().hasLabel('Hotel').has('city', 'New York').valueMap()"
    },
    {
        "input": "Show me 5-star hotels",
        "expected": "g.V().hasLabel('Hotel').has('star_rating', 5).valueMap()"
    },
    {
        "input": "Find luxury hotels with ratings above 4 stars",
        "expected": "g.V().hasLabel('Hotel').has('star_rating', gte(4)).valueMap()"
    },
    {
        "input": "Show me budget hotels under $100",
        "expected": "g.V().hasLabel('Hotel').has('price_per_night', lte(100)).valueMap()"
    },
    
    # Review-Based Queries
    {
        "input": "Show me high-rated reviews",
        "expected": "g.V().hasLabel('Review').has('score', gte(8)).valueMap()"
    },
    {
        "input": "Find recent reviews from this year",
        "expected": "g.V().hasLabel('Review').has('created_at', gte('2024-01-01')).valueMap()"
    },
    {
        "input": "Show me verified reviews only",
        "expected": "g.V().hasLabel('Review').has('verified', true).valueMap()"
    },
    {
        "input": "Find negative reviews with low ratings",
        "expected": "g.V().hasLabel('Review').has('score', lte(3)).valueMap()"
    },
    {
        "input": "Show me reviews longer than 100 characters",
        "expected": "g.V().hasLabel('Review').has('text', textLength(gte(100))).valueMap()"
    },
    
    # Guest and Reviewer Queries
    {
        "input": "Find VIP guests",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap()"
    },
    {
        "input": "Show me business travelers",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'business').valueMap()"
    },
    {
        "input": "Find experienced reviewers with more than 10 reviews",
        "expected": "g.V().hasLabel('Reviewer').has('review_count', gte(10)).valueMap()"
    },
    {
        "input": "Show me solo travelers",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'solo').valueMap()"
    },
    {
        "input": "Find family travelers with children",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'family').valueMap()"
    },
    
    # Aspect-Based Analysis Queries
    {
        "input": "Find hotels with excellent cleanliness ratings",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5)).select('hotel').valueMap()"
    },
    {
        "input": "Show me hotels with good service scores",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0)).select('hotel').valueMap()"
    },
    {
        "input": "Find hotels with poor location ratings",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'location').in('ANALYZES_ASPECT').has('aspect_score', lte(2.5)).select('hotel').valueMap()"
    },
    {
        "input": "Show me reviews that mention cleanliness issues",
        "expected": "g.V().hasLabel('Review').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "Find hotels with excellent value ratings",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'value').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5)).select('hotel').valueMap()"
    },
    
    # Complex Multi-Hop Queries
    {
        "input": "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').has('created_at', gte('2024-06-21')).in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'maintenance').valueMap()"
    },
    {
        "input": "Find hotels with excellent service but poor location ratings",
        "expected": "g.V().hasLabel('Hotel').as('hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5))).where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'location').in('ANALYZES_ASPECT').has('aspect_score', lte(2.5))).select('hotel').valueMap()"
    },
    {
        "input": "Show me Turkish reviews about cleanliness complaints",
        "expected": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "Find hotels reviewed by VIP guests with complaints",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').where(__.in('HAS_ANALYSIS').has('sentiment_score', lte(0))).in('WROTE').in('HAS_REVIEW').valueMap()"
    },
    {
        "input": "Show me weekend stays with maintenance issues",
        "expected": "g.V().hasLabel('Review').has('stay_date', containing('Saturday')).where(__.has('text', containing('maintenance'))).valueMap()"
    },
    
    # Turkish Language Queries
    {
        "input": "Türkçe yazılmış temizlik şikayetlerini göster",
        "expected": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "VIP misafirlerin sorunlarını göster",
        "expected": "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').out('WROTE').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    },
    {
        "input": "Otellerin hizmet puanlarını göster",
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').values('aspect_score').valueMap()"
    },
    {
        "input": "Son bakım sorunlarını bul",
        "expected": "g.V().hasLabel('Review').has('created_at', gte('2024-06-21')).where(__.has('text', containing('bakım'))).valueMap()"
    },
    {
        "input": "Oda şikayetlerini göster",
        "expected": "g.V().hasLabel('Review').where(__.has('text', containing('oda'))).in('HAS_ANALYSIS').has('sentiment_score', lte(0)).out('HAS_ANALYSIS').valueMap()"
    },
    
    # Advanced Business Logic Queries
    {
        "input": "Find trending hotels with improving ratings over time",
        "expected": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').order().by('created_at').tail(10).values('score').mean().is(gte(__.in('HAS_REVIEW').order().by('created_at').limit(10).values('score').mean()))).valueMap()"
    },
    {
        "input": "Show me competitive hotels in the same market segment",
        "expected": "g.V().hasLabel('Hotel').as('hotel1').out('COMPETES_WITH').as('hotel2').select('hotel1', 'hotel2').by(__.valueMap())"
    },
    {
        "input": "Find similar reviews about the same aspects",
        "expected": "g.V().hasLabel('Review').as('review1').out('SIMILAR_TO').as('review2').where(__.select('review1').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').as('aspect').select('review2').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').where(eq('aspect'))).select('review1', 'review2').by(__.valueMap())"
    },
    {
        "input": "Show me hotels with consistently high ratings across all aspects",
        "expected": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').in('ANALYZES_ASPECT').values('aspect_score').min().is(gte(4.0))).valueMap()"
    },
    {
        "input": "Find hotels with the most diverse review sources",
        "expected": "g.V().hasLabel('Hotel').as('hotel').in('HAS_REVIEW').out('SOURCED_FROM').dedup().count().as('source_count').select('hotel', 'source_count').order().by('source_count', desc).valueMap()"
    }
]


def calculate_similarity(expected: str, generated: str) -> float:
    """
    Calculate similarity score between expected and generated Gremlin queries.
    
    Args:
        expected: Expected Gremlin query
        generated: Generated Gremlin query
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Normalize queries for comparison
    expected_normalized = re.sub(r'\s+', ' ', expected.strip().lower())
    generated_normalized = re.sub(r'\s+', ' ', generated.strip().lower())
    
    # Calculate sequence similarity
    similarity = SequenceMatcher(None, expected_normalized, generated_normalized).ratio()
    
    return similarity


def validate_gremlin_syntax(query: str) -> bool:
    """
    Validate basic Gremlin query syntax.
    
    Args:
        query: Gremlin query string
        
    Returns:
        True if syntax appears valid, False otherwise
    """
    query = query.strip()
    
    # Basic syntax checks
    if not query:
        return False
    
    # Must start with 'g.'
    if not query.startswith('g.'):
        return False
    
    # Should have proper parentheses matching
    open_parens = query.count('(')
    close_parens = query.count(')')
    if open_parens != close_parens:
        return False
    
    # Should contain vertex or edge traversal
    has_traversal = any(pattern in query for pattern in [
        '.V()', '.E()', 'hasLabel(', 'has(', 'out(', 'in(', 'both('
    ])
    
    return has_traversal


def analyze_query_components(query: str) -> Dict[str, bool]:
    """
    Analyze query components for detailed validation.
    
    Args:
        query: Gremlin query string
        
    Returns:
        Dictionary with component analysis results
    """
    query_lower = query.lower()
    
    return {
        "has_vertex_start": query.strip().startswith('g.V()'),
        "has_label_filter": 'haslabel(' in query_lower,
        "has_property_filter": 'has(' in query_lower and 'haslabel(' not in query_lower,
        "has_traversal": any(t in query_lower for t in ['out(', 'in(', 'both(']),
        "has_result_projection": any(r in query_lower for r in ['valuemap(', 'values(', 'select(']),
        "has_limit": 'limit(' in query_lower,
        "has_ordering": 'order(' in query_lower,
        "has_filtering": any(f in query_lower for f in ['where(', 'is(', 'gte(', 'lte(', 'eq(']),
        "has_aggregation": any(a in query_lower for a in ['count(', 'sum(', 'mean(', 'max(', 'min('])
    }


def test_llm_to_gremlin(generator_function: Callable[[str], str]) -> Dict[str, Any]:
    """
    Test LLM-to-Gremlin conversion function against comprehensive test cases.
    
    Args:
        generator_function: Function that takes natural language input and returns Gremlin query
        
    Returns:
        Dictionary containing test results and statistics
    """
    print("🧪 LLM-to-Gremlin Query Validation Test Suite")
    print("=" * 70)
    print(f"Testing {len(GREMLIN_TEST_CASES)} test cases...")
    print()
    
    results = {
        "total_tests": len(GREMLIN_TEST_CASES),
        "passed_tests": 0,
        "failed_tests": 0,
        "syntax_valid": 0,
        "syntax_invalid": 0,
        "average_similarity": 0.0,
        "test_details": []
    }
    
    total_similarity = 0.0
    
    for i, test_case in enumerate(GREMLIN_TEST_CASES, 1):
        input_query = test_case["input"]
        expected_query = test_case["expected"]
        
        print(f"[{i:2d}/{len(GREMLIN_TEST_CASES)}] Testing: '{input_query[:50]}{'...' if len(input_query) > 50 else ''}'")
        
        try:
            # Generate Gremlin query using the provided function
            generated_query = generator_function(input_query)
            
            # Validate syntax
            syntax_valid = validate_gremlin_syntax(generated_query)
            
            # Calculate similarity
            similarity = calculate_similarity(expected_query, generated_query)
            
            # Analyze components
            components = analyze_query_components(generated_query)
            
            # Determine if test passes (syntax valid + reasonable similarity)
            test_passed = syntax_valid and similarity >= 0.3
            
            # Update counters
            if test_passed:
                results["passed_tests"] += 1
                status = "✅ PASS"
            else:
                results["failed_tests"] += 1
                status = "❌ FAIL"
            
            if syntax_valid:
                results["syntax_valid"] += 1
            else:
                results["syntax_invalid"] += 1
            
            total_similarity += similarity
            
            # Store detailed results
            test_detail = {
                "input": input_query,
                "expected": expected_query,
                "generated": generated_query,
                "syntax_valid": syntax_valid,
                "similarity": similarity,
                "test_passed": test_passed,
                "components": components
            }
            results["test_details"].append(test_detail)
            
            # Print result
            print(f"    {status} | Syntax: {'✓' if syntax_valid else '✗'} | Similarity: {similarity:.2f}")
            
            if not test_passed:
                print(f"    Expected: {expected_query[:80]}{'...' if len(expected_query) > 80 else ''}")
                print(f"    Generated: {generated_query[:80]}{'...' if len(generated_query) > 80 else ''}")
            
            print()
            
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
            results["failed_tests"] += 1
            results["syntax_invalid"] += 1
            
            test_detail = {
                "input": input_query,
                "expected": expected_query,
                "generated": f"ERROR: {str(e)}",
                "syntax_valid": False,
                "similarity": 0.0,
                "test_passed": False,
                "components": {}
            }
            results["test_details"].append(test_detail)
            print()
    
    # Calculate averages
    results["average_similarity"] = total_similarity / len(GREMLIN_TEST_CASES)
    results["pass_rate"] = (results["passed_tests"] / results["total_tests"]) * 100
    results["syntax_success_rate"] = (results["syntax_valid"] / results["total_tests"]) * 100
    
    # Print summary
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']} ({results['pass_rate']:.1f}%)")
    print(f"Failed: {results['failed_tests']}")
    print(f"Syntax Valid: {results['syntax_valid']} ({results['syntax_success_rate']:.1f}%)")
    print(f"Average Similarity: {results['average_similarity']:.3f}")
    print()
    
    # Print category breakdown
    print("📋 CATEGORY BREAKDOWN:")
    categories = {
        "Basic Queries": GREMLIN_TEST_CASES[0:5],
        "Review Queries": GREMLIN_TEST_CASES[5:10],
        "User Queries": GREMLIN_TEST_CASES[10:15],
        "Aspect Analysis": GREMLIN_TEST_CASES[15:20],
        "Complex Multi-hop": GREMLIN_TEST_CASES[20:25],
        "Turkish Language": GREMLIN_TEST_CASES[25:30],
        "Advanced Logic": GREMLIN_TEST_CASES[30:35]
    }
    
    for category, test_cases in categories.items():
        if test_cases:
            start_idx = GREMLIN_TEST_CASES.index(test_cases[0])
            end_idx = start_idx + len(test_cases)
            category_results = results["test_details"][start_idx:end_idx]
            category_passed = sum(1 for r in category_results if r["test_passed"])
            category_total = len(category_results)
            category_rate = (category_passed / category_total) * 100 if category_total > 0 else 0
            
            print(f"  {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
    
    print()
    
    # Performance assessment
    if results["pass_rate"] >= 80:
        print("🎉 EXCELLENT: Your LLM-to-Gremlin converter is working very well!")
    elif results["pass_rate"] >= 60:
        print("👍 GOOD: Your converter shows solid performance with room for improvement.")
    elif results["pass_rate"] >= 40:
        print("⚠️  MODERATE: Your converter needs significant improvement.")
    else:
        print("❌ POOR: Your converter requires major fixes.")
    
    return results


# Example usage and demo
def demo_llm_function(natural_language_query: str) -> str:
    """
    Demo LLM function that returns mock Gremlin queries for testing.
    Replace this with your actual LLM integration.
    
    Args:
        natural_language_query: Natural language input
        
    Returns:
        Generated Gremlin query string
    """
    query_lower = natural_language_query.lower()
    
    # Simple rule-based mock for demonstration
    if "hotels" in query_lower and "all" in query_lower:
        return "g.V().hasLabel('Hotel').valueMap()"
    elif "vip" in query_lower and "guest" in query_lower:
        return "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap()"
    elif "cleanliness" in query_lower:
        return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0)).select('hotel').valueMap()"
    elif "service" in query_lower:
        return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').valueMap()"
    elif "reviews" in query_lower:
        return "g.V().hasLabel('Review').valueMap()"
    elif "türkçe" in query_lower or "turkish" in query_lower:
        return "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').valueMap()"
    else:
        return "g.V().limit(10).valueMap()"


if __name__ == "__main__":
    # Run demo test
    print("🚀 Running demo with mock LLM function...")
    print("Replace `demo_llm_function` with your actual LLM integration.")
    print()
    
    # Test with demo function
    results = test_llm_to_gremlin(demo_llm_function)
    
    print("\n💡 To use with your actual LLM:")
    print("```python")
    print("from your_llm_module import your_generator_function")
    print("results = test_llm_to_gremlin(your_generator_function)")
    print("```")
