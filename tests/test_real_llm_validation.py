#!/usr/bin/env python3
"""
Integration Example: Testing GraphQueryLLM with Validation Suite

This script demonstrates how to integrate the LLM-to-Gremlin validation suite
with the actual GraphQueryLLM from the Graph RAG system using the improved
sync wrapper that avoids event loop conflicts.
"""

import asyncio
import sys
import os
from typing import Optional
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from tests.sync_llm_wrapper import create_sync_wrapper, ThreadSafeAsyncWrapper
from tests.test_llm_gremlin_validation import test_llm_to_gremlin


def main():
    """Main test function demonstrating improved sync wrapper."""
    print("🧪 TESTING GRAPH RAG LLM WITH VALIDATION SUITE")
    print("=" * 70)
    print("Using improved sync wrapper to avoid event loop conflicts")
    print("=" * 70)
    
    try:
        print("🚀 Creating sync wrapper...")
        
        # Method 1: Use the reusable sync wrapper (recommended)
        sync_generator = create_sync_wrapper()
        
        print("✅ Sync wrapper created successfully")
        print("🧪 Running comprehensive validation tests...\n")
        
        # Run the validation suite
        results = test_llm_to_gremlin(sync_generator)
        
        # Test the simple sync wrapper as well
        test_with_simple_sync_wrapper()
        
        # Additional analysis
        print("\n🔍 DETAILED ANALYSIS:")
        print("=" * 70)
        
        # Show some example successful conversions
        successful_tests = [test for test in results["test_details"] if test["test_passed"]]
        failed_tests = [test for test in results["test_details"] if not test["test_passed"]]
        
        if successful_tests:
            print(f"\n✅ SUCCESSFUL CONVERSIONS (showing first 3):")
            for i, test in enumerate(successful_tests[:3], 1):
                print(f"{i}. Input: {test['input'][:50]}...")
                print(f"   Generated: {test['generated'][:60]}...")
                print(f"   Similarity: {test['similarity']:.2f}")
        
        if failed_tests:
            print(f"\n❌ FAILED CONVERSIONS (showing first 2):")
            for i, test in enumerate(failed_tests[:2], 1):
                print(f"{i}. Input: {test['input'][:50]}...")
                print(f"   Generated: {test['generated'][:60]}...")
                print(f"   Expected: {test['expected'][:60]}...")
        
        # Performance recommendations
        print(f"\n💡 PERFORMANCE RECOMMENDATIONS:")
        print("=" * 70)
        
        if results["pass_rate"] >= 80:
            print("🎉 EXCELLENT: Your LLM is performing very well!")
            print("   • High accuracy in query generation")
            print("   • Good understanding of hotel domain")
            print("   • Minimal optimization needed")
        elif results["pass_rate"] >= 60:
            print("👍 GOOD: Solid performance with room for improvement")
            print("   • Consider refining domain prompts")
            print("   • Review failed test cases for patterns")
            print("   • May benefit from few-shot examples")
        else:
            print("⚠️  NEEDS IMPROVEMENT: Low pass rate detected")
            print("   • Review domain schema and prompts")
            print("   • Consider model fine-tuning")
            print("   • Add more training examples")
        
        # Component analysis
        if results["test_details"]:
            syntax_success_rate = (results["syntax_valid"] / results["total_tests"]) * 100
            print(f"\n📊 COMPONENT ANALYSIS:")
            print(f"   • Syntax Success Rate: {syntax_success_rate:.1f}%")
            print(f"   • Average Similarity: {results['average_similarity']:.3f}")
            print(f"   • Tests with Good Similarity (≥0.5): {len([t for t in results['test_details'] if t['similarity'] >= 0.5])}")
        
        print(f"\n📊 FINAL SCORE: {results['pass_rate']:.1f}% ({results['passed_tests']}/{results['total_tests']} tests passed)")
        
        return results["pass_rate"] >= 70  # Return success if 70%+ pass rate
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False


def demo_alternative_approaches():
    """Demonstrate alternative sync wrapper approaches."""
    print("\n🔧 ALTERNATIVE APPROACHES DEMO")
    print("=" * 70)
    
    # Method 2: Thread-safe wrapper
    print("2️⃣ Using Thread-Safe Wrapper:")
    try:
        wrapper = ThreadSafeAsyncWrapper()
        
        # Test with a few queries
        test_queries = [
            "Find all hotels",
            "Show VIP guests",
            "Türkçe yazılmış temizlik şikayetlerini göster"
        ]
        
        for query in test_queries:
            result = wrapper.generate_sync(query)
            print(f"   ✅ '{query[:30]}...' → {result[:40]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")


def test_with_simple_sync_wrapper():
    """
    Example: Testing with the simple sync_wrapper function.
    
    This demonstrates Option B: Using a sync wrapper to avoid async/await issues.
    """
    print("\n🔧 EXAMPLE: Using Simple sync_wrapper Function")
    print("=" * 70)
    
    # Import the sync wrapper
    from tests.sync_llm_wrapper import sync_wrapper
    
    # Test queries
    test_queries = [
        "Find all hotels",
        "Show VIP guests",
        "Türkçe yazılmış temizlik şikayetlerini göster"
    ]
    
    print("🧪 Testing individual queries:")
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query}")
        
        # ✅ This works! No async/await needed in test loops
        result = sync_wrapper(query)
        
        if result.startswith("ERROR:"):
            print(f"    ❌ {result}")
        else:
            print(f"    ✅ Generated: {result[:60]}...")
    
    print(f"\n✅ Simple sync wrapper test completed successfully!")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
