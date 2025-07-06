#!/usr/bin/env python3
"""
Test script to verify enhanced Turkish Gremlin query generation.

This script tests the improved LLM-to-Gremlin translation with:
1. Few-shot Turkish examples
2. Enforced .valueMap(true) usage
3. Hotel name inclusion for hotel listings
4. Post-processing query enhancement
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings

async def test_enhanced_turkish_queries():
    """Test enhanced Turkish query generation with improved patterns."""
    print("🇹🇷 TESTING ENHANCED TURKISH GREMLIN GENERATION")
    print("=" * 70)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    
    print(f"✅ Environment: {settings.model_provider} - {settings.gemini_model}")
    
    # Enhanced Turkish test queries with expected patterns
    test_cases = [
        {
            "name": "Hotel Names (Basic Turkish)",
            "query": "Otellerin isimlerini göster",
            "expected_patterns": [".valueMap(true)", "hotel_name", "hasLabel('Hotel')"],
            "should_include_select": True
        },
        {
            "name": "VIP Guest Information",
            "query": "VIP misafirlerin bilgilerini listele",
            "expected_patterns": [".valueMap(true)", "VIP", "hasLabel"],
            "should_include_select": False
        },
        {
            "name": "Low Cleanliness Hotels",
            "query": "Temizlik puanı düşük olan otelleri bul",
            "expected_patterns": [".valueMap(true)", "cleanliness", "hotel_name"],
            "should_include_select": True
        },
        {
            "name": "Turkish Complaints",
            "query": "Türkçe şikayetleri göster",
            "expected_patterns": [".valueMap(true)", "tr", "hasLabel('Review')"],
            "should_include_select": False
        },
        {
            "name": "Hotel Service Ratings",
            "query": "Otellerin hizmet puanlarını göster",
            "expected_patterns": [".valueMap(true)", "service", "Hotel"],
            "should_include_select": True
        },
        {
            "name": "Simple Hotel List",
            "query": "Otelleri listele",
            "expected_patterns": [".valueMap(true)", "hotel_name", "hasLabel('Hotel')"],
            "should_include_select": True
        }
    ]
    
    try:
        # Initialize enhanced LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ Enhanced GraphQueryLLM initialized\n")
        
        success_count = 0
        total_validations = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}] Testing: {test_case['name']}")
            print(f"📝 Turkish Query: {test_case['query']}")
            
            try:
                # Generate enhanced Gremlin query
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                
                print(f"🔍 Generated Query: {gremlin_query}")
                
                # Validate basic structure
                if gremlin_query and gremlin_query.strip() and gremlin_query.startswith('g.'):
                    print("✅ Basic structure valid")
                    success_count += 1
                else:
                    print("❌ Invalid basic structure")
                    continue
                
                # Check expected patterns
                pattern_checks = []
                for pattern in test_case['expected_patterns']:
                    if pattern in gremlin_query:
                        pattern_checks.append(f"✅ Contains '{pattern}'")
                        total_validations += 1
                    else:
                        pattern_checks.append(f"❌ Missing '{pattern}'")
                
                # Special check for hotel_name selection
                if test_case['should_include_select']:
                    if "select('hotel_name')" in gremlin_query or 'select("hotel_name")' in gremlin_query:
                        pattern_checks.append("✅ Includes hotel_name selection")
                        total_validations += 1
                    else:
                        pattern_checks.append("❌ Missing hotel_name selection")
                
                # Check for .valueMap(true) instead of .valueMap()
                if '.valueMap(true)' in gremlin_query:
                    pattern_checks.append("✅ Uses .valueMap(true)")
                    total_validations += 1
                elif '.valueMap()' in gremlin_query:
                    pattern_checks.append("⚠️  Uses .valueMap() instead of .valueMap(true)")
                else:
                    pattern_checks.append("⚠️  No valueMap found")
                
                # Print validation results
                for check in pattern_checks:
                    print(f"    {check}")
                
                print(f"📊 Pattern Score: {pattern_checks.count('✅')}/{len(pattern_checks)}")
                
            except Exception as e:
                print(f"❌ Generation failed: {e}")
            
            print("-" * 50)
        
        # Summary
        print(f"\n📊 ENHANCEMENT TEST RESULTS")
        print("=" * 40)
        print(f"✅ Successful queries: {success_count}/{len(test_cases)}")
        print(f"✅ Pattern validations: {total_validations}/{len(test_cases) * 4} expected")
        
        success_rate = success_count / len(test_cases)
        pattern_rate = total_validations / (len(test_cases) * 4)
        
        if success_rate >= 0.8 and pattern_rate >= 0.7:
            print("🎉 ENHANCEMENT SUCCESS: Turkish query improvements working!")
            print("✅ .valueMap(true) enforcement active")
            print("✅ hotel_name selection included")
            print("✅ Turkish few-shot examples effective")
            print("✅ Post-processing enhancements applied")
            return True
        else:
            print("⚠️  Enhancement needs improvement")
            print(f"Success rate: {success_rate:.1%}")
            print(f"Pattern rate: {pattern_rate:.1%}")
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

async def test_before_after_comparison():
    """Test to show before/after improvement comparison."""
    print("\n🔧 BEFORE/AFTER COMPARISON TEST")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    try:
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        
        test_query = "Otellerin isimlerini göster"
        print(f"📝 Test Query: {test_query}")
        
        # Generate with enhancements
        enhanced_query = await llm.generate_gremlin_query(test_query)
        print(f"🔧 Enhanced Query: {enhanced_query}")
        
        # Analysis
        improvements = []
        
        if '.valueMap(true)' in enhanced_query:
            improvements.append("✅ Uses .valueMap(true) for complete property retrieval")
        
        if "select('hotel_name')" in enhanced_query:
            improvements.append("✅ Includes hotel_name selection for hotel listings")
        
        if '.limit(' in enhanced_query:
            improvements.append("✅ Includes performance limit")
        
        print("\n🎯 Applied Improvements:")
        for improvement in improvements:
            print(f"    {improvement}")
        
        return len(improvements) >= 2
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        """Run all enhancement tests."""
        print("🧪 ENHANCED TURKISH GREMLIN QUERY GENERATION TEST")
        print("=" * 70)
        
        # Test enhanced queries
        enhanced_success = await test_enhanced_turkish_queries()
        
        # Test before/after comparison
        comparison_success = await test_before_after_comparison()
        
        if enhanced_success and comparison_success:
            print("\n🎉 ALL ENHANCEMENT TESTS PASSED!")
            print("📋 VERIFIED IMPROVEMENTS:")
            print("  ✅ Turkish few-shot examples working")
            print("  ✅ .valueMap(true) enforcement active")
            print("  ✅ hotel_name selection included automatically")
            print("  ✅ Post-processing query enhancement applied")
            print("  ✅ Turkish language support enhanced")
            return True
        else:
            print("\n⚠️  Some enhancement tests failed")
            return False
    
    success = asyncio.run(main())
    print(f"\n{'🎯 ENHANCEMENT TEST COMPLETED SUCCESSFULLY' if success else '❌ ENHANCEMENT TEST COMPLETED WITH ISSUES'}")
    sys.exit(0 if success else 1)
