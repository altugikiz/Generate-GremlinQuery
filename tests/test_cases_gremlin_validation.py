#!/usr/bin/env python3
"""
Gremlin Query Validation Test Cases

This script defines comprehensive test cases for validating natural language 
to Gremlin query conversion in the hotel review Graph RAG system.

Each test case contains:
- input: Natural language query
- expected: Expected Gremlin query output

These test cases are based on the hotel review domain schema and cover
various query patterns, complexity levels, and business use cases.
"""

from typing import List, Dict, Any
import json

# Test Cases for Natural Language → Gremlin Query Conversion
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
        "input": "Find reviews for Grand Marriott Times Square",
        "expected": "g.V().hasLabel('Hotel').has('name', 'Grand Marriott Times Square').in('HAS_REVIEW').valueMap()"
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
        "input": "Show me reviews written in Turkish about cleanliness",
        "expected": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'tr').in('WRITTEN_IN').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').select('review').valueMap()"
    },
    
    # Language and Source Queries
    {
        "input": "Find reviews written in English",
        "expected": "g.V().hasLabel('Review').out('WRITTEN_IN').has('code', 'en').in('WRITTEN_IN').valueMap()"
    },
    {
        "input": "Show me reviews from TripAdvisor",
        "expected": "g.V().hasLabel('Review').out('SOURCED_FROM').has('name', 'TripAdvisor').in('SOURCED_FROM').valueMap()"
    },
    {
        "input": "Find hotels that support multiple languages",
        "expected": "g.V().hasLabel('Hotel').out('SUPPORTS_LANGUAGE').groupCount().by(__.in('SUPPORTS_LANGUAGE')).unfold().where(__.select(values).is(gte(2))).select(keys).valueMap()"
    },
    
    # Hotel Group and Chain Queries
    {
        "input": "Show me all Marriott hotels",
        "expected": "g.V().hasLabel('HotelGroup').has('name', containing('Marriott')).in('OWNS').valueMap()"
    },
    {
        "input": "Find hotels owned by Hilton Worldwide",
        "expected": "g.V().hasLabel('HotelGroup').has('name', 'Hilton Worldwide').in('OWNS').valueMap()"
    },
    {
        "input": "Show me independent hotels not part of any chain",
        "expected": "g.V().hasLabel('Hotel').not(__.out('OWNS')).valueMap()"
    },
    
    # Amenity and Accommodation Queries
    {
        "input": "Find hotels with swimming pools",
        "expected": "g.V().hasLabel('Hotel').in('PROVIDES').has('name', containing('pool')).out('PROVIDES').valueMap()"
    },
    {
        "input": "Show me hotels offering suites",
        "expected": "g.V().hasLabel('Hotel').in('OFFERS').has('category', 'suite').out('OFFERS').valueMap()"
    },
    {
        "input": "Find hotels with free WiFi",
        "expected": "g.V().hasLabel('Hotel').in('PROVIDES').has('name', containing('WiFi')).has('is_free', true).out('PROVIDES').valueMap()"
    },
    
    # Sentiment and Analysis Queries
    {
        "input": "Find reviews with positive sentiment",
        "expected": "g.V().hasLabel('Review').in('HAS_ANALYSIS').has('sentiment_score', gte(0.5)).out('HAS_ANALYSIS').valueMap()"
    },
    {
        "input": "Show me reviews with high confidence analysis",
        "expected": "g.V().hasLabel('Review').in('HAS_ANALYSIS').has('confidence', gte(0.8)).out('HAS_ANALYSIS').valueMap()"
    },
    {
        "input": "Find hotels with consistently negative reviews",
        "expected": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').in('HAS_ANALYSIS').has('sentiment_score', lte(-0.3)).count().is(gte(3))).valueMap()"
    },
    
    # Date and Time-Based Queries
    {
        "input": "Show me reviews from the last 30 days",
        "expected": "g.V().hasLabel('Review').has('created_at', gte('2024-06-05')).valueMap()"
    },
    {
        "input": "Find hotels reviewed in 2024",
        "expected": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW').has('created_at', between('2024-01-01', '2024-12-31'))).valueMap()"
    },
    {
        "input": "Show me weekend stays (Saturday check-ins)",
        "expected": "g.V().hasLabel('Review').has('stay_date', containing('Saturday')).valueMap()"
    }
]

# Additional test cases for edge cases and Turkish language support
EXTENDED_TEST_CASES: List[Dict[str, str]] = [
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
        "expected": "g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').in('ANALYZES_ASPECT').group().by(__.out('HAS_ANALYSIS').out('HAS_REVIEW')).by(__.values('aspect_score').mean())"
    },
    
    # Complex Business Logic Queries
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
    }
]

# Combine all test cases
ALL_TEST_CASES = GREMLIN_TEST_CASES + EXTENDED_TEST_CASES

def validate_test_case(test_case: Dict[str, str], generated_query: str) -> Dict[str, Any]:
    """
    Validate a generated Gremlin query against the expected result.
    
    Args:
        test_case: Test case with 'input' and 'expected' keys
        generated_query: The query generated by the LLM
        
    Returns:
        Validation result dictionary
    """
    input_query = test_case["input"]
    expected_query = test_case["expected"]
    
    # Basic syntax validation
    syntax_valid = (
        generated_query.strip().startswith("g.") and
        len(generated_query.strip()) > 5 and
        not generated_query.strip().endswith(".")
    )
    
    # Structural similarity check (basic pattern matching)
    expected_parts = expected_query.lower().split(".")
    generated_parts = generated_query.lower().split(".")
    
    # Check for key components
    has_vertex_start = "hasLabel" in generated_query or "V()" in generated_query
    has_proper_traversal = any(part in generated_query.lower() for part in ["in(", "out(", "has("])
    has_result_projection = any(part in generated_query.lower() for part in ["valueMap", "values(", "select("])
    
    # Similarity score (basic implementation)
    common_parts = len(set(expected_parts) & set(generated_parts))
    total_parts = len(set(expected_parts) | set(generated_parts))
    similarity_score = common_parts / max(total_parts, 1) if total_parts > 0 else 0
    
    return {
        "input": input_query,
        "expected": expected_query,
        "generated": generated_query,
        "syntax_valid": syntax_valid,
        "has_vertex_start": has_vertex_start,
        "has_proper_traversal": has_proper_traversal,
        "has_result_projection": has_result_projection,
        "similarity_score": round(similarity_score, 2),
        "passed": syntax_valid and has_vertex_start and similarity_score >= 0.3
    }

def run_validation_suite(llm_function) -> Dict[str, Any]:
    """
    Run the complete validation suite against an LLM function.
    
    Args:
        llm_function: Function that takes a natural language query and returns Gremlin query
        
    Returns:
        Complete validation results
    """
    results = []
    passed_count = 0
    
    print("🧪 Running Gremlin Query Validation Suite")
    print("=" * 60)
    print(f"Total test cases: {len(ALL_TEST_CASES)}")
    print()
    
    for i, test_case in enumerate(ALL_TEST_CASES, 1):
        print(f"[{i:2d}/{len(ALL_TEST_CASES)}] Testing: {test_case['input'][:50]}...")
        
        try:
            # Generate query using the provided LLM function
            generated_query = llm_function(test_case["input"])
            
            # Validate the result
            validation_result = validate_test_case(test_case, generated_query)
            results.append(validation_result)
            
            if validation_result["passed"]:
                passed_count += 1
                print(f"    ✅ PASS (similarity: {validation_result['similarity_score']})")
            else:
                print(f"    ❌ FAIL (similarity: {validation_result['similarity_score']})")
                print(f"    Generated: {generated_query[:80]}...")
                
        except Exception as e:
            print(f"    ❌ ERROR: {e}")
            results.append({
                "input": test_case["input"],
                "expected": test_case["expected"],
                "generated": "",
                "error": str(e),
                "passed": False
            })
    
    # Calculate summary statistics
    success_rate = (passed_count / len(ALL_TEST_CASES)) * 100
    avg_similarity = sum(r.get("similarity_score", 0) for r in results) / len(results)
    
    summary = {
        "total_tests": len(ALL_TEST_CASES),
        "passed": passed_count,
        "failed": len(ALL_TEST_CASES) - passed_count,
        "success_rate": round(success_rate, 1),
        "average_similarity": round(avg_similarity, 2),
        "results": results
    }
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed_count}/{len(ALL_TEST_CASES)} ({success_rate:.1f}%)")
    print(f"Average similarity: {avg_similarity:.2f}")
    print(f"Syntax validation: {sum(1 for r in results if r.get('syntax_valid', False))}/{len(ALL_TEST_CASES)}")
    
    return summary

def export_test_cases(filename: str = "gremlin_test_cases.json"):
    """Export test cases to a JSON file for external use."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "description": "Test cases for Natural Language to Gremlin Query conversion",
            "domain": "Hotel Review Graph Database",
            "total_cases": len(ALL_TEST_CASES),
            "test_cases": ALL_TEST_CASES
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(ALL_TEST_CASES)} test cases to {filename}")

def get_test_cases_by_category() -> Dict[str, List[Dict[str, str]]]:
    """Group test cases by category for targeted testing."""
    categories = {
        "basic_hotel": [],
        "reviews": [],
        "guests": [],
        "aspects": [],
        "complex": [],
        "language": [],
        "business_logic": []
    }
    
    # Simple categorization based on keywords
    for test_case in ALL_TEST_CASES:
        input_lower = test_case["input"].lower()
        
        if any(word in input_lower for word in ["türkçe", "turkish", "vip misafir"]):
            categories["language"].append(test_case)
        elif any(word in input_lower for word in ["excellent", "poor", "trending", "competitive", "similar"]):
            categories["business_logic"].append(test_case)
        elif any(word in input_lower for word in ["cleanliness", "service", "location", "aspect"]):
            categories["aspects"].append(test_case)
        elif any(word in input_lower for word in ["vip", "business", "reviewer", "guest"]):
            categories["guests"].append(test_case)
        elif any(word in input_lower for word in ["review", "rating", "score"]):
            categories["reviews"].append(test_case)
        elif len(test_case["expected"].split(".")) > 8:  # Complex queries have many chained operations
            categories["complex"].append(test_case)
        else:
            categories["basic_hotel"].append(test_case)
    
    return categories

# Example usage function for demonstration
def example_llm_function(natural_language_query: str) -> str:
    """
    Example LLM function that returns a mock Gremlin query.
    Replace this with your actual LLM integration.
    """
    # This is just a mock implementation for demonstration
    if "hotels" in natural_language_query.lower():
        return "g.V().hasLabel('Hotel').valueMap()"
    elif "reviews" in natural_language_query.lower():
        return "g.V().hasLabel('Review').valueMap()"
    else:
        return "g.V().limit(10).valueMap()"

if __name__ == "__main__":
    print("🎯 Gremlin Query Validation Test Cases")
    print("=" * 60)
    print(f"📋 Available test cases: {len(ALL_TEST_CASES)}")
    print(f"📁 Categories: {list(get_test_cases_by_category().keys())}")
    print()
    
    # Export test cases to JSON
    export_test_cases()
    
    # Show sample test cases
    print("\n📝 Sample Test Cases:")
    for i, test_case in enumerate(ALL_TEST_CASES[:5], 1):
        print(f"\n{i}. Input: {test_case['input']}")
        print(f"   Expected: {test_case['expected'][:80]}...")
    
    print(f"\n... and {len(ALL_TEST_CASES) - 5} more test cases")
    
    # Demonstrate validation (commented out to avoid running mock function)
    # print("\n🧪 Running sample validation...")
    # results = run_validation_suite(example_llm_function)
    
    print("\n✅ Test cases ready for validation!")
    print("To use these test cases with your LLM function:")
    print("  results = run_validation_suite(your_llm_function)")
