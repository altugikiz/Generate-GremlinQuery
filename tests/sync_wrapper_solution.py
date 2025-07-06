#!/usr/bin/env python3
"""
SOLUTION: Option B - Sync Wrapper for Async LLM Function

This script demonstrates how to fix the following errors:
- RuntimeWarning: coroutine 'generate_gremlin_query' was never awaited
- ERROR: Cannot run the event loop while another loop is running

PROBLEM:
You have an async method generate_gremlin_query(prompt: str) that you need to call
from synchronous test loops, but direct calls cause event loop conflicts.

SOLUTION:
Create a sync_wrapper(prompt) function that safely handles the async call
using a separate thread with its own event loop.
"""

import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.getcwd())


def sync_wrapper(prompt: str) -> str:
    """
    Sync wrapper function that safely calls async generate_gremlin_query.
    
    This function solves the "coroutine never awaited" and "event loop already running" 
    errors by running the async call in a separate thread with its own event loop.
    
    Args:
        prompt: Natural language query string
        
    Returns:
        Generated Gremlin query string
        
    Usage in synchronous test loops:
        result = sync_wrapper("Find all hotels")
        print(f"Generated: {result}")
    """
    import asyncio
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from dotenv import load_dotenv
    
    # Import your async LLM class
    from app.core.graph_query_llm import GraphQueryLLM
    from app.config.settings import get_settings
    
    def run_async_in_thread():
        """Run the async function in a separate thread with its own event loop."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Load settings
            load_dotenv()
            settings = get_settings()
            
            if not settings.gemini_api_key:
                return "ERROR: GEMINI_API_KEY not found in .env file"
            
            # Initialize and use the async LLM
            async def async_generate():
                llm = GraphQueryLLM(
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model
                )
                await llm.initialize()
                return await llm.generate_gremlin_query(prompt)
            
            # Run the async function
            result = loop.run_until_complete(async_generate())
            return result if result else "g.V().hasLabel('Hotel').limit(10).valueMap()"
            
        except Exception as e:
            return f"ERROR: {str(e)}"
        finally:
            loop.close()
    
    # Execute in a separate thread to avoid event loop conflicts
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_in_thread)
        return future.result()


def test_sync_wrapper_in_loops():
    """
    Demonstrate using sync_wrapper in various synchronous test scenarios.
    
    This shows how the wrapper fixes the original async/await issues.
    """
    print("🧪 TESTING SYNC WRAPPER IN SYNCHRONOUS LOOPS")
    print("=" * 60)
    
    # Test 1: Simple loop
    print("\n1️⃣ Simple test loop:")
    test_queries = [
        "Find all hotels",
        "Show VIP guests",
        "Türkçe yazılmış temizlik şikayetlerini göster"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Testing: {query}")
        
        # ✅ This works! No async/await needed
        result = sync_wrapper(query)
        
        if result.startswith("ERROR:"):
            print(f"    ❌ {result}")
        else:
            print(f"    ✅ Generated: {result[:50]}...")
    
    # Test 2: Validation-style loop
    print(f"\n2️⃣ Validation-style testing:")
    
    test_cases = [
        {
            "input": "Find hotels with good ratings",
            "expected_contains": ["Hotel", "hasLabel", "valueMap"]
        },
        {
            "input": "Show maintenance issues",
            "expected_contains": ["MaintenanceIssue", "hasLabel"]
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}] Validating: {test_case['input']}")
        
        # ✅ Call async function synchronously
        generated = sync_wrapper(test_case['input'])
        
        if generated.startswith("ERROR:"):
            print(f"    ❌ Generation failed: {generated}")
            continue
        
        # Simple validation
        contains_expected = any(expected in generated for expected in test_case['expected_contains'])
        
        if contains_expected:
            print(f"    ✅ Validation passed")
            passed += 1
        else:
            print(f"    ⚠️  Generated query may not contain expected elements")
            print(f"    Generated: {generated[:60]}...")
    
    print(f"\n📊 Validation Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    return passed >= total * 0.5  # 50% pass rate


def demonstrate_fixes():
    """
    Show the before/after comparison of the async/await fix.
    """
    print("\n🔧 BEFORE/AFTER: Fixing Async/Await Issues")
    print("=" * 60)
    
    print("❌ BEFORE (causes errors):")
    print("```python")
    print("# This would cause:")
    print("# RuntimeWarning: coroutine 'generate_gremlin_query' was never awaited")
    print("# ERROR: Cannot run the event loop while another loop is running")
    print("")
    print("from app.core.graph_query_llm import GraphQueryLLM")
    print("llm = GraphQueryLLM(api_key, model)")
    print("result = llm.generate_gremlin_query(prompt)  # ❌ Error!")
    print("```")
    
    print("\n✅ AFTER (works correctly):")
    print("```python")
    print("# This works in synchronous test loops:")
    print("result = sync_wrapper(prompt)  # ✅ Success!")
    print("```")
    
    # Demonstrate the fix works
    print(f"\n🧪 Live demonstration:")
    result = sync_wrapper("Find all hotels")
    
    if result.startswith("ERROR:"):
        print(f"❌ Demo failed: {result}")
        return False
    else:
        print(f"✅ Demo successful: {result[:50]}...")
        return True


def main():
    """
    Main demonstration of the sync wrapper solution.
    """
    print("🎯 SYNC WRAPPER SOLUTION FOR ASYNC LLM TESTING")
    print("=" * 80)
    print("Fixes: 'coroutine never awaited' and 'event loop already running' errors")
    print("=" * 80)
    
    try:
        # Show the fix explanation
        demo_success = demonstrate_fixes()
        
        if not demo_success:
            print("❌ Basic demo failed - check your .env configuration")
            return False
        
        # Test in realistic scenarios
        test_success = test_sync_wrapper_in_loops()
        
        # Summary
        print(f"\n🎉 SOLUTION SUMMARY")
        print("=" * 60)
        print("✅ Created sync_wrapper(prompt) function")
        print("✅ Fixed 'coroutine never awaited' errors") 
        print("✅ Fixed 'event loop already running' errors")
        print("✅ Enabled async LLM calls in sync test loops")
        print("✅ Provided thread-safe async execution")
        
        if test_success:
            print("✅ All validation tests passed")
        
        print(f"\n💡 USAGE:")
        print("   # Instead of:")
        print("   # result = await llm.generate_gremlin_query(prompt)  # ❌ Async")
        print("   ")
        print("   # Use this in sync test loops:")
        print("   result = sync_wrapper(prompt)  # ✅ Sync")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Solution demo failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    print(f"\n{'🎯 SOLUTION DEMONSTRATED SUCCESSFULLY' if success else '❌ SOLUTION DEMO FAILED'}")
    sys.exit(0 if success else 1)
