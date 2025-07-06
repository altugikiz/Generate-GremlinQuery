# test_llm_to_gremlin Function - Comprehensive Guide

## Overview

The `test_llm_to_gremlin` function is a comprehensive validation tool that tests LLM-to-Gremlin query conversion using 35+ predefined test cases. It validates syntax, calculates similarity scores, and provides detailed analysis of LLM performance.

## Function Signature

```python
def test_llm_to_gremlin(generator_function: Callable[[str], str]) -> Dict[str, Any]:
    """
    Comprehensive validation function for LLM-to-Gremlin conversion.
    
    Args:
        generator_function: Function that takes natural language input and returns Gremlin query
        
    Returns:
        Dictionary with comprehensive test results and analysis
    """
```

## Test Cases Coverage

The function tests **35 different scenarios** across multiple categories:

### 📊 Test Categories

1. **Basic Queries (5 cases)**
   - "Show me all hotels"
   - "Find hotels in New York" 
   - "Show me 5-star hotels"
   - "Find luxury hotels with ratings above 4 stars"
   - "Show me budget hotels under $100"

2. **Review Queries (5 cases)**
   - "Show me high-rated reviews"
   - "Find recent reviews from this year"
   - "Show me verified reviews only"
   - "Find negative reviews with low ratings"
   - "Show me reviews longer than 100 characters"

3. **User/Reviewer Queries (5 cases)**
   - "Find VIP guests"
   - "Show me business travelers"
   - "Find experienced reviewers with more than 10 reviews"
   - "Show me solo travelers"
   - "Find family travelers with children"

4. **Aspect Analysis (5 cases)**
   - "Find hotels with excellent cleanliness ratings"
   - "Show me hotels with good service scores"
   - "Find hotels with poor location ratings"
   - "Show me reviews that mention cleanliness issues"
   - "Find hotels with excellent value ratings"

5. **Complex Multi-Hop (5 cases)**
   - "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks"
   - "Find hotels with excellent service but poor location ratings"
   - "Show me Turkish reviews about cleanliness complaints"
   - "Find hotels reviewed by VIP guests with complaints"
   - "Show me weekend stays with maintenance issues"

6. **Turkish Language (5 cases)**
   - "Türkçe yazılmış temizlik şikayetlerini göster"
   - "VIP misafirlerin sorunlarını göster"
   - "Otellerin hizmet puanlarını göster"
   - "Son bakım sorunlarını bul"
   - "Oda şikayetlerini göster"

7. **Advanced Logic (5 cases)**
   - "Find trending hotels with improving ratings over time"
   - "Show me competitive hotels in the same market segment"
   - "Find similar reviews about the same aspects"
   - "Show me hotels with consistently high ratings across all aspects"
   - "Find hotels with the most diverse review sources"

## Validation Process

For each test case, the function:

1. **Generates Query**: Calls your function with natural language input
2. **Validates Syntax**: Checks if output is valid Gremlin (starts with `g.`, proper parentheses, etc.)
3. **Calculates Similarity**: Compares generated query to expected query using sequence matching
4. **Analyzes Components**: Breaks down query structure (traversals, filters, etc.)
5. **Determines Pass/Fail**: Based on syntax validity and similarity threshold (≥30%)

## Return Value Structure

```python
{
    "total_tests": 35,
    "passed_tests": int,           # Number of tests that passed
    "failed_tests": int,           # Number of tests that failed
    "pass_rate": float,            # Percentage pass rate
    "syntax_valid": int,           # Number with valid Gremlin syntax
    "syntax_invalid": int,         # Number with invalid syntax
    "syntax_success_rate": float,  # Percentage with valid syntax
    "average_similarity": float,   # Average similarity score (0.0-1.0)
    "test_details": [              # Detailed results for each test
        {
            "input": str,          # Natural language input
            "expected": str,       # Expected Gremlin query
            "generated": str,      # Generated Gremlin query
            "syntax_valid": bool,  # Whether syntax is valid
            "similarity": float,   # Similarity score (0.0-1.0)
            "test_passed": bool,   # Whether test passed overall
            "components": dict     # Query component analysis
        },
        # ... 34 more test details
    ]
}
```

## Usage Examples

### Example 1: Simple Mock LLM

```python
from test_llm_gremlin_validation import test_llm_to_gremlin

def simple_llm(natural_language_query: str) -> str:
    query_lower = natural_language_query.lower()
    
    if "hotels" in query_lower:
        return "g.V().hasLabel('Hotel').valueMap()"
    elif "reviews" in query_lower:
        return "g.V().hasLabel('Review').valueMap()"
    else:
        return "g.V().limit(10).valueMap()"

# Run validation
results = test_llm_to_gremlin(simple_llm)
print(f"Pass rate: {results['pass_rate']:.1f}%")
```

### Example 2: OpenAI Integration

```python
import openai

def openai_gremlin_generator(natural_language_query: str) -> str:
    prompt = f"""
    Convert this natural language query to Gremlin:
    Query: {natural_language_query}
    
    Graph Schema: Hotel review database with vertices (Hotel, Review, Reviewer)
    Return only the Gremlin query:
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()

# Test with validation suite
results = test_llm_to_gremlin(openai_gremlin_generator)
```

### Example 3: Async LLM Wrapper

```python
import asyncio
from your_async_llm import AsyncGraphQueryLLM

def sync_wrapper(natural_language_query: str) -> str:
    async def async_generate():
        llm = AsyncGraphQueryLLM()
        await llm.initialize()
        return await llm.generate_gremlin_query(natural_language_query)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_generate())
        finally:
            loop.close()
    except Exception as e:
        return f"ERROR: {str(e)}"

# Test async LLM
results = test_llm_to_gremlin(sync_wrapper)
```

### Example 4: API Client

```python
import requests

def api_gremlin_generator(natural_language_query: str) -> str:
    response = requests.post(
        "https://your-llm-api.com/generate-gremlin",
        json={"query": natural_language_query},
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    
    if response.status_code == 200:
        return response.json()["gremlin_query"]
    else:
        return f"ERROR: API returned {response.status_code}"

# Test API integration
results = test_llm_to_gremlin(api_gremlin_generator)
```

## Performance Interpretation

### Excellent (90-100%)
- LLM understands domain well
- Generates syntactically correct queries
- High similarity to expected outputs
- Ready for production use

### Good (70-89%)
- Solid performance with room for improvement
- Most queries work correctly
- May need prompt engineering refinement
- Suitable for development/testing

### Fair (50-69%)
- Basic functionality present
- Significant improvements needed
- Review prompt engineering and examples
- Consider additional training data

### Poor (0-49%)
- Major issues with LLM integration
- Check prompt formatting and schema
- Verify LLM model capabilities
- Consider different approach

## Category Analysis

The function provides breakdown by category to identify specific weaknesses:

```
📋 CATEGORY BREAKDOWN:
  Basic Queries: 5/5 (100.0%)      ← Simple hotel/review queries
  Review Queries: 4/5 (80.0%)      ← Review-specific filters
  User Queries: 5/5 (100.0%)       ← Guest/reviewer queries  
  Aspect Analysis: 3/5 (60.0%)     ← Complex aspect traversals
  Complex Multi-hop: 2/5 (40.0%)   ← Multi-step graph traversals
  Turkish Language: 1/5 (20.0%)    ← Non-English queries
  Advanced Logic: 1/5 (20.0%)      ← Complex business logic
```

This helps identify areas for improvement (e.g., "Turkish language support needs work").

## Integration with Your Codebase

The validation function is already implemented in your codebase:

1. **Location**: `test_llm_gremlin_validation.py`
2. **Dependencies**: Uses similarity calculation and syntax validation helpers
3. **Import**: `from test_llm_gremlin_validation import test_llm_to_gremlin`

## Demo Scripts Available

1. **`demo_test_validation.py`** - Full comprehensive demo
2. **`quick_test_demo.py`** - Quick 5-case validation
3. **`test_llm_gremlin_validation.py`** - Main implementation with 35-case demo

## Running the Tests

```bash
# Run full demo with mock LLM
python demo_test_validation.py

# Run quick 5-case demo  
python quick_test_demo.py

# Run main validation script
python test_llm_gremlin_validation.py
```

## Key Features

✅ **Comprehensive Coverage**: 35 test cases across 7 categories  
✅ **Syntax Validation**: Checks for valid Gremlin structure  
✅ **Similarity Analysis**: Compares output to expected results  
✅ **Error Handling**: Gracefully handles LLM failures  
✅ **Detailed Reporting**: Category breakdowns and recommendations  
✅ **Flexible Integration**: Works with any callable function  
✅ **Multi-language Support**: Includes Turkish test cases  
✅ **Domain-Specific**: Tailored for hotel review graph database  

The `test_llm_to_gremlin` function provides everything needed to validate and improve LLM-to-Gremlin conversion quality!
