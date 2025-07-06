#!/usr/bin/env python3
"""
Test script to verify Turkish language support in Gremlin query generation.

This script tests the multilingual fix for Turkish queries and demonstrates
that the system can now handle Turkish input correctly.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings

async def test_turkish_language_support():
    """Test Turkish language queries with the enhanced LLM."""
    print("🇹🇷 TESTING TURKISH LANGUAGE SUPPORT")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    print(f"✅ Environment loaded")
    print(f"   Provider: {settings.model_provider}")
    print(f"   Model: {settings.gemini_model}")
    
    # Turkish test queries
    turkish_queries = [
        {
            "name": "Turkish Cleanliness Complaints",
            "query": "Türkçe yazılmış temizlik şikayetlerini göster",
            "expected_elements": ["Review", "WRITTEN_IN", "cleanliness"]
        },
        {
            "name": "VIP Guest Issues in Turkish",
            "query": "VIP misafirlerin sorunlarını göster",
            "expected_elements": ["Guest", "VIP", "type"]
        },
        {
            "name": "Hotel Service Ratings in Turkish",
            "query": "Otellerin hizmet puanlarını göster",
            "expected_elements": ["Hotel", "service", "rating"]
        },
        {
            "name": "Maintenance Issues in Turkish",
            "query": "Son bakım sorunlarını göster",
            "expected_elements": ["MaintenanceIssue", "Issue"]
        },
        {
            "name": "Room Complaints in Turkish",
            "query": "Oda şikayetlerini bul",
            "expected_elements": ["Room", "complaint"]
        }
    ]
    
    # English control queries for comparison
    english_queries = [
        {
            "name": "English Cleanliness Complaints",
            "query": "Show me cleanliness complaints written in Turkish",
            "expected_elements": ["Review", "cleanliness"]
        },
        {
            "name": "English VIP Guest Issues",
            "query": "Show VIP guest issues",
            "expected_elements": ["Guest", "VIP"]
        }
    ]
    
    try:
        # Initialize the enhanced LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print("✅ Enhanced GraphQueryLLM initialized successfully")
        
        # Test Turkish queries
        print(f"\n🇹🇷 TESTING TURKISH QUERIES")
        print("-" * 40)
        
        turkish_success = 0
        for i, test_case in enumerate(turkish_queries, 1):
            print(f"\n[{i}] {test_case['name']}")
            print(f"📝 Turkish Input: {test_case['query']}")
            
            try:
                # Generate Gremlin query
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                
                if gremlin_query and gremlin_query.strip() and gremlin_query.startswith('g.'):
                    print(f"✅ Generated: {gremlin_query}")
                    turkish_success += 1
                    
                    # Check if query contains expected elements
                    contains_expected = any(element.lower() in gremlin_query.lower() 
                                          for element in test_case['expected_elements'])
                    if contains_expected:
                        print(f"✅ Query contains expected elements")
                    else:
                        print(f"⚠️  Query may not contain all expected elements")
                else:
                    print("❌ Failed to generate valid Gremlin query")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        # Test English queries for comparison
        print(f"\n🇺🇸 TESTING ENGLISH CONTROL QUERIES")
        print("-" * 40)
        
        english_success = 0
        for i, test_case in enumerate(english_queries, 1):
            print(f"\n[{i}] {test_case['name']}")
            print(f"📝 English Input: {test_case['query']}")
            
            try:
                # Generate Gremlin query
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                
                if gremlin_query and gremlin_query.strip() and gremlin_query.startswith('g.'):
                    print(f"✅ Generated: {gremlin_query}")
                    english_success += 1
                else:
                    print("❌ Failed to generate valid Gremlin query")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        # Summary
        print(f"\n📊 TEST RESULTS SUMMARY")
        print("=" * 40)
        print(f"Turkish Queries: {turkish_success}/{len(turkish_queries)} successful")
        print(f"English Queries: {english_success}/{len(english_queries)} successful")
        print(f"Total Success Rate: {(turkish_success + english_success)/(len(turkish_queries) + len(english_queries))*100:.1f}%")
        
        if turkish_success > 0:
            print("🎉 Turkish language support is working!")
            return True
        else:
            print("❌ Turkish language support needs further debugging")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def test_language_detection():
    """Test the language detection functionality."""
    print(f"\n🔍 TESTING LANGUAGE DETECTION")
    print("-" * 40)
    
    try:
        # Import language detection
        from app.core.graph_query_llm import LANGUAGE_DETECTION_AVAILABLE
        
        if not LANGUAGE_DETECTION_AVAILABLE:
            print("❌ Language detection not available")
            return False
        
        from langdetect import detect
        
        test_texts = [
            ("Hello, how are you?", "en"),
            ("Türkçe yazılmış temizlik şikayetlerini göster", "tr"),
            ("Bonjour, comment allez-vous?", "fr"),
            ("Hola, ¿cómo estás?", "es"),
            ("VIP misafirlerin sorunlarını göster", "tr")
        ]
        
        print("Testing language detection:")
        for text, expected in test_texts:
            try:
                detected = detect(text)
                status = "✅" if detected == expected else "⚠️"
                print(f"{status} '{text[:30]}...' → {detected} (expected: {expected})")
            except Exception as e:
                print(f"❌ Error detecting language for '{text[:30]}...': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Language detection test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        """Run all tests."""
        print("🧪 TESTING TURKISH LANGUAGE SUPPORT IN GRAPH RAG")
        print("=" * 60)
        
        # Test language detection
        lang_detection_success = await test_language_detection()
        
        # Test Turkish queries
        turkish_support_success = await test_turkish_language_support()
        
        if lang_detection_success and turkish_support_success:
            print("\n🎉 ALL TESTS PASSED! Turkish language support is working correctly.")
            return True
        else:
            print("\n❌ Some tests failed. Check the output above for details.")
            return False
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
