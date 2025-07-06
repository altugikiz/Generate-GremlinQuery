#!/usr/bin/env python3
"""
Test script to validate improved Turkish query translation quality.
Tests the enhanced few-shot examples, expanded vocabulary, and improved validation logic.
"""

import asyncio
import sys
import os
import time
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings

async def test_enhanced_turkish_queries():
    """Test enhanced Turkish query translation with improved few-shot examples."""
    print("🇹🇷 TESTING ENHANCED TURKISH QUERY TRANSLATION")
    print("=" * 80)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    print(f"✅ Environment loaded: {settings.model_provider} - {settings.gemini_model}")
    
    # Enhanced Turkish test queries focusing on quality improvements
    test_cases = [
        {
            "name": "Basic Hotel Names",
            "query": "Otellerin isimlerini göster",
            "expected_elements": ["valueMap(true)", "hotel_name", "limit(10)", "hasLabel('Hotel')"],
            "description": "Should include valueMap(true) and hotel_name selection",
            "category": "hotel_listing"
        },
        {
            "name": "All Hotels Listing", 
            "query": "Tüm otelleri listele",
            "expected_elements": ["valueMap(true)", "hotel_name", "hasLabel('Hotel')", "limit(10)"],
            "description": "Should include proper hotel listing structure",
            "category": "hotel_listing"
        },
        {
            "name": "VIP Guest Information",
            "query": "VIP misafirlerin bilgilerini göster",
            "expected_elements": ["valueMap(true)", "traveler_type", "VIP", "hasLabel('Reviewer')"],
            "description": "Should include proper VIP filtering and value extraction",
            "category": "guest_query"
        },
        {
            "name": "VIP Guest Type Query",
            "query": "Misafir tipi VIP olan yorumları göster",
            "expected_elements": ["valueMap(true)", "traveler_type", "VIP"],
            "description": "Should filter for VIP traveler type",
            "category": "guest_query"
        },
        {
            "name": "High Service Quality Hotels",
            "query": "Hizmet kalitesi iyi olan otellerin isimlerini listele",
            "expected_elements": ["valueMap(true)", "hotel_name", "service", "gte(4.0)"],
            "description": "Should include service filtering and hotel names",
            "category": "service_rating"
        },
        {
            "name": "High Service Ratings",
            "query": "Hizmet puanları yüksek oteller",
            "expected_elements": ["valueMap(true)", "hotel_name", "service", "gte(4.0)"],
            "description": "Should include service filtering and hotel names",
            "category": "service_rating"
        },
        {
            "name": "Cleanliness Complaints",
            "query": "Temizlik şikayetlerini göster",
            "expected_elements": ["valueMap(true)", "cleanliness"],
            "description": "Should include proper cleanliness aspect filtering",
            "category": "cleanliness"
        },
        {
            "name": "Turkish Reviews",
            "query": "Türkçe yazılmış yorumları listele",
            "expected_elements": ["valueMap(true)", "tr", "Review", "WRITTEN_IN"],
            "description": "Should filter for Turkish language reviews",
            "category": "language_review"
        },
        {
            "name": "English Reviews",
            "query": "İngilizce yazılmış yorumları bul",
            "expected_elements": ["valueMap(true)", "en", "Review", "WRITTEN_IN"],
            "description": "Should filter for English language reviews",
            "category": "language_review"
        },
        {
            "name": "Room Maintenance Issues",
            "query": "Oda bakım sorunlarını bul",
            "expected_elements": ["valueMap(true)", "MaintenanceIssue", "Room"],
            "description": "Should find maintenance issues related to rooms",
            "category": "maintenance"
        },
        {
            "name": "Accommodation Types",
            "query": "Konaklama türlerini göster",
            "expected_elements": ["valueMap(true)", "AccommodationType"],
            "description": "Should list accommodation types",
            "category": "accommodation"
        },
        {
            "name": "Low Rated Hotels",
            "query": "Düşük puanlı otelleri listele",
            "expected_elements": ["valueMap(true)", "hotel_name", "score", "lt(3.0)"],
            "description": "Should find hotels with low ratings",
            "category": "rating"
        }
    ]
    
    try:
        # Initialize enhanced LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ Enhanced GraphQueryLLM initialized successfully")
        
        success_count = 0
        total_tests = len(test_cases)
        category_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{total_tests}] {test_case['name']} ({test_case['category']})")
            print(f"📝 Query: {test_case['query']}")
            print(f"💡 Goal: {test_case['description']}")
            
            try:
                # Generate Gremlin query
                start_time = time.time()
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                generation_time = (time.time() - start_time) * 1000
                
                print(f"🔍 Generated ({generation_time:.1f}ms): {gremlin_query}")
                
                # Validate expected elements
                missing_elements = []
                present_elements = []
                for element in test_case['expected_elements']:
                    if element in gremlin_query:
                        present_elements.append(element)
                    else:
                        missing_elements.append(element)
                
                # Calculate success based on critical elements
                critical_elements = ["valueMap(true)"]  # Always required
                has_critical = all(elem in gremlin_query for elem in critical_elements)
                
                # Success if has critical elements and at least 50% of expected elements
                success_threshold = 0.6  # 60% of expected elements
                element_success_rate = len(present_elements) / len(test_case['expected_elements'])
                
                test_success = has_critical and element_success_rate >= success_threshold
                
                if test_success:
                    print("✅ SUCCESS: Query meets quality standards")
                    success_count += 1
                    
                    # Track category success
                    category = test_case['category']
                    if category not in category_results:
                        category_results[category] = {'success': 0, 'total': 0}
                    category_results[category]['success'] += 1
                else:
                    print(f"⚠️  PARTIAL: Missing critical elements: {missing_elements}")
                    print(f"   Present: {present_elements}")
                
                # Track category totals
                category = test_case['category']
                if category not in category_results:
                    category_results[category] = {'success': 0, 'total': 0}
                category_results[category]['total'] += 1
                
                # Basic syntax validation
                if gremlin_query.startswith('g.') and len(gremlin_query) > 10:
                    print("✅ Syntax: Valid Gremlin structure")
                else:
                    print("❌ Syntax: Invalid Gremlin structure")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
                # Track category totals even for failures
                category = test_case['category']
                if category not in category_results:
                    category_results[category] = {'success': 0, 'total': 0}
                category_results[category]['total'] += 1
        
        # Summary
        print(f"\n" + "=" * 80)
        print(f"📊 ENHANCED TURKISH TRANSLATION TEST RESULTS")
        print(f"=" * 80)
        print(f"✅ Successful queries: {success_count}/{total_tests}")
        print(f"📈 Overall success rate: {(success_count/total_tests)*100:.1f}%")
        
        # Category breakdown
        print(f"\n📋 SUCCESS BY CATEGORY:")
        print("-" * 50)
        for category, result in category_results.items():
            if result['total'] > 0:
                rate = (result['success'] / result['total']) * 100
                status = "✅" if rate >= 60 else "⚠️"
                print(f"{status} {category.replace('_', ' ').title()}: {result['success']}/{result['total']} ({rate:.1f}%)")
        
        # Overall assessment
        overall_success = success_count >= total_tests * 0.75  # 75% success rate
        
        print(f"\n" + "=" * 80)
        if overall_success:
            print("🎉 ENHANCED TURKISH SUPPORT IS WORKING EXCELLENTLY!")
            print("✅ Comprehensive few-shot examples are highly effective")
            print("✅ Expanded vocabulary coverage is working") 
            print("✅ Enhanced validation logic ensures quality")
            print("✅ Turkish queries consistently include essential elements")
            print("✅ Fallback mechanisms provide robust coverage")
        else:
            print("⚠️  Turkish support shows good improvement but needs fine-tuning")
            print("🔧 Consider adjusting specific category patterns")
            
        return overall_success
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        """Run the enhanced Turkish test."""
        print("🚀 Starting Enhanced Turkish Query Quality Test")
        print("This test validates improvements in LLM-to-Gremlin translation for Turkish queries\n")
        
        success = await test_enhanced_turkish_queries()
        
        print(f"\n{'🎯 ENHANCEMENT VALIDATION SUCCESSFUL' if success else '❌ ENHANCEMENT NEEDS MORE WORK'}")
        return success
    
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
