#!/usr/bin/env python3
"""
Usage Examples for LLM-to-Gremlin Validation

This file shows different ways to use the validation test suite with various
LLM integration patterns.
"""

import asyncio
from tests.test_llm_gremlin_validation import test_llm_to_gremlin, GREMLIN_TEST_CASES


# Example 1: Simple synchronous LLM function
def example_sync_llm(natural_language_query: str) -> str:
    """
    Example synchronous LLM function.
    Replace this with your actual LLM integration.
    """
    # Your LLM integration code here
    # This is just a mock example
    
    if "hotels" in natural_language_query.lower():
        return "g.V().hasLabel('Hotel').valueMap()"
    elif "reviews" in natural_language_query.lower():
        return "g.V().hasLabel('Review').valueMap()"
    else:
        return "g.V().limit(10).valueMap()"


# Example 2: Async LLM with wrapper
class AsyncLLMExample:
    """Example async LLM wrapper."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize your async LLM client here
    
    async def generate_gremlin_query(self, query: str) -> str:
        """Async method to generate Gremlin query."""
        # Your async LLM call here
        # For example: result = await self.llm_client.generate(query)
        return f"g.V().hasLabel('Hotel').has('name', '{query}').valueMap()"
    
    def sync_wrapper(self, query: str) -> str:
        """Synchronous wrapper for the async method."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.generate_gremlin_query(query))
            return result
        finally:
            loop.close()


# Example 3: OpenAI integration example
def openai_llm_example(natural_language_query: str) -> str:
    """
    Example OpenAI integration.
    Uncomment and modify for actual use.
    """
    # import openai
    # 
    # try:
    #     response = openai.ChatCompletion.create(
    #         model="gpt-4",
    #         messages=[
    #             {"role": "system", "content": "You are a Gremlin query expert..."},
    #             {"role": "user", "content": natural_language_query}
    #         ]
    #     )
    #     return response.choices[0].message.content.strip()
    # except Exception as e:
    #     return f"ERROR: {str(e)}"
    
    # Mock implementation
    return "g.V().hasLabel('Hotel').valueMap()"


# Example 4: Gemini integration example  
def gemini_llm_example(natural_language_query: str) -> str:
    """
    Example Google Gemini integration.
    Uncomment and modify for actual use.
    """
    # import google.generativeai as genai
    # 
    # try:
    #     genai.configure(api_key="your_api_key_here")
    #     model = genai.GenerativeModel('gemini-pro')
    #     
    #     prompt = f"""Convert this natural language query to Gremlin:
    #     {natural_language_query}
    #     
    #     Return only the Gremlin query."""
    #     
    #     response = model.generate_content(prompt)
    #     return response.text.strip()
    # except Exception as e:
    #     return f"ERROR: {str(e)}"
    
    # Mock implementation
    return "g.V().hasLabel('Review').valueMap()"


# Example 5: Custom LLM with preprocessing
class CustomLLMExample:
    """Example custom LLM with query preprocessing."""
    
    def __init__(self):
        self.schema_info = {
            "vertices": ["Hotel", "Review", "Reviewer", "Aspect"],
            "edges": ["HAS_REVIEW", "ANALYZES_ASPECT", "WRITTEN_IN"],
            "properties": {
                "Hotel": ["name", "city", "star_rating"],
                "Review": ["score", "text", "created_at"],
                "Reviewer": ["traveler_type"],
                "Aspect": ["name", "aspect_score"]
            }
        }
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess the natural language query."""
        # Add domain-specific preprocessing
        query = query.lower()
        
        # Map common terms
        if "vip" in query:
            query = query.replace("vip", "traveler_type='VIP'")
        if "cleanliness" in query:
            query = query.replace("cleanliness", "aspect='cleanliness'")
        
        return query
    
    def generate_gremlin_query(self, natural_language_query: str) -> str:
        """Generate Gremlin query with preprocessing."""
        processed_query = self.preprocess_query(natural_language_query)
        
        # Your LLM integration with the processed query
        # This is mock implementation
        if "hotel" in processed_query:
            return "g.V().hasLabel('Hotel').valueMap()"
        elif "review" in processed_query:
            return "g.V().hasLabel('Review').valueMap()"
        else:
            return "g.V().limit(10).valueMap()"


def run_validation_examples():
    """Run validation with different LLM examples."""
    print("🧪 LLM-TO-GREMLIN VALIDATION EXAMPLES")
    print("=" * 60)
    
    examples = [
        ("Simple Sync LLM", example_sync_llm),
        ("OpenAI Example", openai_llm_example),
        ("Gemini Example", gemini_llm_example),
        ("Custom LLM", CustomLLMExample().generate_gremlin_query)
    ]
    
    for name, llm_function in examples:
        print(f"\n🔍 Testing {name}")
        print("-" * 40)
        
        # Run a subset of tests for demonstration
        sample_tests = GREMLIN_TEST_CASES[:5]  # First 5 tests
        
        passed = 0
        for i, test_case in enumerate(sample_tests, 1):
            try:
                result = llm_function(test_case["input"])
                syntax_valid = result.startswith("g.") and "hasLabel(" in result
                
                if syntax_valid:
                    passed += 1
                    print(f"  [{i}] ✅ {test_case['input'][:30]}...")
                else:
                    print(f"  [{i}] ❌ {test_case['input'][:30]}...")
                    
            except Exception as e:
                print(f"  [{i}] ❌ {test_case['input'][:30]}... (ERROR: {e})")
        
        print(f"  Result: {passed}/{len(sample_tests)} passed")
    
    print(f"\n💡 To run full validation on your LLM:")
    print("results = test_llm_to_gremlin(your_llm_function)")


def run_async_example():
    """Example of testing an async LLM."""
    print("\n🔄 ASYNC LLM EXAMPLE")
    print("-" * 30)
    
    async def test_async():
        # Initialize async LLM
        async_llm = AsyncLLMExample("your-api-key")
        
        # Test a few queries
        test_queries = [
            "Show me all hotels",
            "Find VIP guests", 
            "Show me reviews"
        ]
        
        for query in test_queries:
            result = await async_llm.generate_gremlin_query(query)
            print(f"Query: {query}")
            print(f"Result: {result}")
            print()
    
    # Run async test
    asyncio.run(test_async())
    
    # Show how to use with validation suite
    print("To use with validation suite:")
    print("async_llm = AsyncLLMExample('your-api-key')")
    print("results = test_llm_to_gremlin(async_llm.sync_wrapper)")


if __name__ == "__main__":
    # Run examples
    run_validation_examples()
    
    # Show async example
    run_async_example()
    
    print("\n🎯 INTEGRATION GUIDE:")
    print("=" * 60)
    print("1. Replace example functions with your actual LLM integration")
    print("2. Ensure your function takes a string and returns a string")
    print("3. Handle errors gracefully (return error message as string)")
    print("4. Run: test_llm_to_gremlin(your_function)")
    print("5. Analyze results and improve your LLM prompts/logic")
    print("\nFor detailed testing, use the comprehensive test suite:")
    print("python test_llm_gremlin_validation.py")
