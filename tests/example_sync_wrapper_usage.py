#!/usr/bin/env python3
"""
Example: Using Sync Wrapper to Fix Async/Await Issues

This example demonstrates how to properly use the sync wrapper to avoid
"RuntimeWarning: coroutine was never awaited" and "event loop already running" errors
when testing async LLM functions in synchronous test loops.

SOLUTION: Option B - Wrap async method into sync function using safe event loop handler
"""

import sys
import os
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.getcwd())

from tests.sync_llm_wrapper import sync_wrapper, create_sync_wrapper, ThreadSafeAsyncWrapper
from tests.test_llm_gremlin_validation import test_llm_to_gremlin


def example_sync_test_loop():
    """
    Example of using sync wrapper in a test loop.
    
    This demonstrates how to fix the original error:
    RuntimeWarning: coroutine 'generate_gremlin_query' was never awaited
    """
    print("🔧 EXAMPLE: Using sync_wrapper in test loops")
    print("=" * 60)
    
    # ❌ ORIGINAL PROBLEM (this would cause the error):
    # from app.core.graph_query_llm import GraphQueryLLM
    # llm = GraphQueryLLM(api_key, model)
    # result = llm.generate_gremlin_query(prompt)  # ❌ Error: coroutine never awaited
    
    # ✅ SOLUTION: Use sync wrapper
    test_queries = [
        "Find all hotels",
        "Show VIP guests",
        "Türkçe yazılmış temizlik şikayetlerini göster",
        "Find maintenance issues"
    ]
    
    print("🧪 Testing queries in synchronous loop:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query[:40]}...")
        
        # ✅ This works! No async/await needed
        result = sync_wrapper(query)
        
        if result.startswith("ERROR:"):
            print(f"    ❌ {result}")
        else:
            print(f"    ✅ Generated: {result[:50]}...")


def example_reusable_wrapper():
    """
    Example using reusable wrapper for better performance.
    
    When you need to make many calls, create the wrapper once
    and reuse it to avoid initialization overhead.
    """
    print("\n🚀 EXAMPLE: Using reusable wrapper for multiple calls")
    print("=" * 60)
    
    # Create wrapper once
    sync_generator = create_sync_wrapper()
    
    test_queries = [
        "Show all hotels in New York",
        "Find reviews with poor cleanliness scores",
        "VIP misafirlerinin şikayetlerini göster"
    ]
    
    print("🧪 Testing with reusable wrapper:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query}")
        
        # ✅ Use the same wrapper instance for all calls
        result = sync_generator(query)
        
        if result.startswith("ERROR:"):
            print(f"    ❌ {result}")
        else:
            print(f"    ✅ Generated: {result[:60]}...")


def example_validation_suite():
    """
    Example running the full validation suite with sync wrapper.
    
    This shows how to integrate with existing test frameworks
    that expect synchronous function calls.
    """
    print("\n🧪 EXAMPLE: Running validation suite with sync wrapper")
    print("=" * 60)
    
    # Create sync wrapper
    sync_generator = create_sync_wrapper()
    
    print("🚀 Running LLM validation tests...")
    
    # Run the validation suite (this expects a sync function)
    results = test_llm_to_gremlin(sync_generator)
    
    # Display results
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"   Pass Rate: {results['pass_rate']:.1f}%")
    print(f"   Passed Tests: {results['passed_tests']}/{results['total_tests']}")
    print(f"   Syntax Valid: {results['syntax_valid']}/{results['total_tests']}")
    print(f"   Average Similarity: {results['average_similarity']:.3f}")
    
    if results['pass_rate'] >= 70:
        print("✅ Validation passed!")
        return True
    else:
        print("⚠️ Validation needs improvement")
        return False


def example_thread_safe_approach():
    """
    Example using thread-safe wrapper approach.
    
    Alternative method using direct threading for specific use cases.
    """
    print("\n🔒 EXAMPLE: Using thread-safe wrapper")
    print("=" * 60)
    
    wrapper = ThreadSafeAsyncWrapper()
    
    test_queries = [
        "Find hotels with good ratings",
        "Show maintenance problems"
    ]
    
    print("🧪 Testing with thread-safe wrapper:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query}")
        
        # ✅ Thread-safe async handling
        result = wrapper.generate_sync(query)
        
        if result.startswith("ERROR:"):
            print(f"    ❌ {result}")
        else:
            print(f"    ✅ Generated: {result[:50]}...")


def compare_approaches():
    """
    Compare different sync wrapper approaches.
    """
    print("\n📊 COMPARISON: Different Sync Wrapper Approaches")
    print("=" * 60)
    
    test_query = "Find all hotels with VIP guests"
    
    approaches = [
        ("Simple sync_wrapper", lambda: sync_wrapper(test_query)),
        ("Reusable wrapper", lambda: create_sync_wrapper()(test_query)),
        ("Thread-safe wrapper", lambda: ThreadSafeAsyncWrapper().generate_sync(test_query))
    ]
    
    for name, func in approaches:
        print(f"\n🔧 Testing {name}:")
        try:
            result = func()
            status = "✅ Success" if not result.startswith("ERROR:") else "❌ Error"
            print(f"   {status}: {result[:50]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")


def main():
    """
    Main demonstration function.
    
    Shows all the different ways to use sync wrappers to fix
    async/await issues in synchronous test environments.
    """
    print("🎯 SYNC WRAPPER SOLUTIONS FOR ASYNC LLM TESTING")
    print("=" * 80)
    print("Demonstrates how to fix 'coroutine never awaited' and")
    print("'event loop already running' errors in test suites.")
    print("=" * 80)
    
    try:
        # Example 1: Basic sync wrapper usage
        example_sync_test_loop()
        
        # Example 2: Reusable wrapper for performance
        example_reusable_wrapper()
        
        # Example 3: Full validation suite integration
        validation_success = example_validation_suite()
        
        # Example 4: Thread-safe approach
        example_thread_safe_approach()
        
        # Example 5: Compare different approaches
        compare_approaches()
        
        # Summary
        print("\n🎉 SUMMARY: Sync Wrapper Solutions")
        print("=" * 60)
        print("✅ Fixed 'coroutine never awaited' errors")
        print("✅ Fixed 'event loop already running' errors")
        print("✅ Enabled async LLM calls in sync test loops")
        print("✅ Provided multiple approaches for different use cases")
        
        if validation_success:
            print("✅ LLM validation tests passed")
            
        print("\n💡 RECOMMENDATIONS:")
        print("   • Use sync_wrapper() for simple one-off calls")
        print("   • Use create_sync_wrapper() for multiple calls (better performance)")
        print("   • Use ThreadSafeAsyncWrapper for thread-safe scenarios")
        print("   • All approaches avoid event loop conflicts")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\n{'🎯 DEMO COMPLETED SUCCESSFULLY' if success else '❌ DEMO COMPLETED WITH ERRORS'}")
    sys.exit(0 if success else 1)
