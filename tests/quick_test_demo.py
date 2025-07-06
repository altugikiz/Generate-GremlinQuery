#!/usr/bin/env python3
"""
Quick Demo: test_llm_to_gremlin Function

This script demonstrates the test_llm_to_gremlin function with a smaller
subset of test cases for quick validation and debugging.
"""

from typing import Dict, Any, List, Callable
from tests.test_llm_gremlin_validation import (
    validate_gremlin_syntax, 
    calculate_similarity, 
    analyze_query_components
)

# Quick test cases for demonstration
QUICK_TEST_CASES: List[Dict[str, str]] = [
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
    }
]


def quick_test_llm_to_gremlin(generator_function: Callable[[str], str]) -> Dict[str, Any]:
    """
    Quick version of test_llm_to_gremlin with fewer test cases for demonstration.
    
    Args:
        generator_function: Function that takes natural language and returns Gremlin query
        
    Returns:
        Dictionary with test results and analysis
    """
    print("🧪 Quick LLM-to-Gremlin Validation Test")
    print("=" * 60)
    print(f"Testing {len(QUICK_TEST_CASES)} sample cases...")
    print()
    
    results = {
        "total_tests": len(QUICK_TEST_CASES),
        "passed_tests": 0,
        "failed_tests": 0,
        "syntax_valid": 0,
        "syntax_invalid": 0,
        "pass_rate": 0.0,
        "syntax_success_rate": 0.0,
        "average_similarity": 0.0,
        "test_details": []
    }
    
    total_similarity = 0.0
    
    for i, test_case in enumerate(QUICK_TEST_CASES, 1):
        input_query = test_case["input"]
        expected_query = test_case["expected"]
        
        print(f"[{i:2d}] Testing: '{input_query[:45]}{'...' if len(input_query) > 45 else ''}'")
        
        try:
            # Generate query
            generated_query = generator_function(input_query)
            
            # Basic validation
            syntax_valid = (generated_query and 
                          generated_query.strip().startswith('g.') and
                          'hasLabel(' in generated_query)
            
            # Calculate similarity
            similarity = calculate_similarity(expected_query, generated_query)
            
            # Check if test passes
            test_passed = syntax_valid and similarity >= 0.4
            
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
            
            # Store details
            test_detail = {
                "input": input_query,
                "expected": expected_query,
                "generated": generated_query,
                "syntax_valid": syntax_valid,
                "similarity": similarity,
                "test_passed": test_passed
            }
            results["test_details"].append(test_detail)
            
            # Print result
            print(f"    {status} | Syntax: {'✓' if syntax_valid else '✗'} | Similarity: {similarity:.2f}")
            
            if not test_passed:
                print(f"    Expected: {expected_query[:60]}{'...' if len(expected_query) > 60 else ''}")
                print(f"    Generated: {generated_query[:60]}{'...' if len(generated_query) > 60 else ''}")
            
            print()
            
        except Exception as e:
            print(f"    ❌ ERROR: {str(e)}")
            results["failed_tests"] += 1
            results["syntax_invalid"] += 1
            total_similarity += 0
            
            test_detail = {
                "input": input_query,
                "expected": expected_query,
                "generated": f"ERROR: {str(e)}",
                "syntax_valid": False,
                "similarity": 0.0,
                "test_passed": False
            }
            results["test_details"].append(test_detail)
            print()
    
    # Calculate rates
    results["pass_rate"] = (results["passed_tests"] / results["total_tests"]) * 100
    results["syntax_success_rate"] = (results["syntax_valid"] / results["total_tests"]) * 100
    results["average_similarity"] = total_similarity / results["total_tests"]
    
    # Print summary
    print("📊 QUICK TEST RESULTS")
    print("=" * 60)
    print(f"Total: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']} ({results['pass_rate']:.1f}%)")
    print(f"Failed: {results['failed_tests']}")
    print(f"Syntax Valid: {results['syntax_valid']} ({results['syntax_success_rate']:.1f}%)")
    print(f"Average Similarity: {results['average_similarity']:.3f}")
    
    return results


def simple_mock_llm(natural_language_query: str) -> str:
    """
    Simple mock LLM for demonstration.
    """
    query_lower = natural_language_query.lower()
    
    if "all hotels" in query_lower:
        return "g.V().hasLabel('Hotel').valueMap()"
    elif "vip guests" in query_lower:
        return "g.V().hasLabel('Reviewer').has('traveler_type', 'VIP').valueMap()"
    elif "high-rated reviews" in query_lower:
        return "g.V().hasLabel('Review').has('score', gte(8)).valueMap()"
    elif "cleanliness" in query_lower:
        return "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.5)).select('hotel').valueMap()"
    elif "türkçe" in query_lower:
        return "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', lte(3.0)).select('review').valueMap()"
    else:
        return "g.V().limit(10).valueMap()"


def broken_llm(natural_language_query: str) -> str:
    """
    Broken LLM for demonstrating error handling.
    """
    if "hotels" in natural_language_query.lower():
        return "INVALID QUERY"
    else:
        raise Exception("LLM service unavailable")


if __name__ == "__main__":
    print("🎯 QUICK DEMO: test_llm_to_gremlin Function")
    print("=" * 80)
    print()
    
    # Test 1: Good mock LLM
    print("🧪 TEST 1: Simple Mock LLM (Good Performance)")
    print("-" * 50)
    results1 = quick_test_llm_to_gremlin(simple_mock_llm)
    print()
    
    # Test 2: Broken LLM
    print("🧪 TEST 2: Broken LLM (Error Handling)")
    print("-" * 50)
    results2 = quick_test_llm_to_gremlin(broken_llm)
    print()
    
    print("📋 USAGE SUMMARY:")
    print("=" * 80)
    print()
    print("✅ The test_llm_to_gremlin function successfully:")
    print("   • Validates LLM-generated Gremlin queries")
    print("   • Handles errors gracefully")
    print("   • Provides detailed similarity analysis")
    print("   • Gives comprehensive pass/fail breakdown")
    print("   • Works with any callable that takes string input")
    print()
    print("🔧 INTEGRATION PATTERNS:")
    print()
    print("# Pattern 1: Sync Function")
    print("def my_llm(query: str) -> str:")
    print("    return llm_api.generate(query)")
    print()
    print("# Pattern 2: Async Wrapper")
    print("def sync_wrapper(query: str) -> str:")
    print("    return asyncio.run(async_llm.generate(query))")
    print()
    print("# Pattern 3: API Client")
    print("def api_client(query: str) -> str:")
    print("    response = requests.post(api_url, json={'query': query})")
    print("    return response.json()['gremlin_query']")
    print()
    print("✨ The validation function works with all patterns!")
