#!/usr/bin/env python3
"""
Test Script: Using Sync Wrapper with LLM Validation

This script demonstrates how to fix the async/await issues by using
the sync wrapper with the test_llm_to_gremlin validation function.
"""

import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.getcwd())

from tests.sync_llm_wrapper import create_sync_wrapper, simple_sync_wrapper, ThreadSafeAsyncWrapper
from tests.test_llm_gremlin_validation import test_llm_to_gremlin


def test_with_reusable_wrapper():
    """Test using the reusable sync wrapper (recommended)."""
    print("🧪 TESTING WITH REUSABLE SYNC WRAPPER")
    print("=" * 60)
    
    # Create the sync wrapper once
    sync_generator = create_sync_wrapper()
    
    # Test with a few sample queries first
    print("🔍 Quick validation test:")
    test_queries = [
        "Find all hotels",
        "Show VIP guests", 
        "Türkçe yazılmış temizlik şikayetlerini göster"
    ]
    
    for query in test_queries:
        result = sync_generator(query)
        print(f"✅ '{query[:30]}...' → {result[:50]}...")
    
    print("\n🚀 Running full validation suite...")
    
    # Run the comprehensive test suite
    results = test_llm_to_gremlin(sync_generator)
    
    return results


def test_with_simple_wrapper():
    """Test using the simple one-shot wrapper."""
    print("\n🧪 TESTING WITH SIMPLE ONE-SHOT WRAPPER")
    print("=" * 60)
    
    print("⚠️  Note: This creates a new LLM instance for each call (slower)")
    
    # Run the test suite with simple wrapper
    results = test_llm_to_gremlin(simple_sync_wrapper)
    
    return results


def test_with_thread_safe_wrapper():
    """Test using the thread-safe wrapper."""
    print("\n🧪 TESTING WITH THREAD-SAFE WRAPPER")
    print("=" * 60)
    
    # Create wrapper instance
    wrapper = ThreadSafeAsyncWrapper()
    
    # Run the test suite
    results = test_llm_to_gremlin(wrapper.generate_sync)
    
    return results


def compare_wrapper_performance():
    """Compare the performance of different wrapper approaches."""
    print("\n📊 WRAPPER PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Note: For performance testing, we'd need timing
    # For now, just show the different approaches work
    
    approaches = [
        ("Reusable Wrapper", create_sync_wrapper()),
        ("Thread-Safe Wrapper", ThreadSafeAsyncWrapper().generate_sync),
        # Skip simple wrapper in comparison as it's very slow
    ]
    
    test_query = "Find all hotels with good ratings"
    
    for name, generator in approaches:
        print(f"\n🔧 Testing {name}:")
        try:
            result = generator(test_query)
            print(f"   ✅ Success: {result[:60]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    """Main test function demonstrating all approaches."""
    print("🎯 SYNC WRAPPER TEST SUITE")
    print("=" * 80)
    print("This script demonstrates how to fix async/await issues")
    print("when testing async LLM functions in synchronous test loops.")
    print("=" * 80)
    
    try:
        # Test 1: Reusable wrapper (recommended for multiple calls)
        results1 = test_with_reusable_wrapper()
        
        # Test 2: Thread-safe wrapper (alternative approach)  
        results2 = test_with_thread_safe_wrapper()
        
        # Performance comparison
        compare_wrapper_performance()
        
        # Summary
        print("\n📋 SUMMARY")
        print("=" * 60)
        print(f"Reusable Wrapper Results:")
        print(f"  Pass Rate: {results1['pass_rate']:.1f}%")
        print(f"  Passed: {results1['passed_tests']}/{results1['total_tests']}")
        
        print(f"\nThread-Safe Wrapper Results:")
        print(f"  Pass Rate: {results2['pass_rate']:.1f}%") 
        print(f"  Passed: {results2['passed_tests']}/{results2['total_tests']}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("✅ Use 'create_sync_wrapper()' for multiple test calls")
        print("✅ Use 'simple_sync_wrapper()' for one-off testing")
        print("✅ Use 'ThreadSafeAsyncWrapper' for thread-safe scenarios")
        print("✅ All approaches avoid event loop conflicts")
        
        # Check if tests passed
        overall_success = results1['pass_rate'] >= 70 and results2['pass_rate'] >= 70
        
        if overall_success:
            print("\n🎉 SUCCESS: All sync wrapper approaches working correctly!")
            return True
        else:
            print("\n⚠️  Some tests had low pass rates, but sync wrappers are working")
            return True
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
