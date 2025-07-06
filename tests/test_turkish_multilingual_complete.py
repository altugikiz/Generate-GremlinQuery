#!/usr/bin/env python3
"""
Complete Test Script for Turkish/Multilingual Graph RAG System

This script tests:
1. Turkish language detection and processing
2. Natural language to Gremlin query conversion
3. End-to-end functionality through API endpoints
4. Database query capabilities and responses

Fixes the original syntax error and provides comprehensive testing.
"""

import asyncio
import sys
import os
import time
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings

# API Base URL
BASE_URL = "http://localhost:8000"

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'=' * 80}")
    print(f"🎯 {title}")
    print('=' * 80)

def print_section(title: str):
    """Print a formatted section."""
    print(f"\n{'-' * 60}")
    print(f"📋 {title}")
    print('-' * 60)

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with formatting."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n[{status}] {test_name}")
    if details:
        print(f"    {details}")

async def test_language_detection():
    """Test language detection functionality."""
    print_section("Testing Language Detection")
    
    try:
        # Import language detection
        from app.core.graph_query_llm import LANGUAGE_DETECTION_AVAILABLE
        
        if not LANGUAGE_DETECTION_AVAILABLE:
            print_test_result("Language Detection Available", False, "langdetect not installed")
            return False
        
        from langdetect import detect
        
        test_texts = [
            ("Hello, how are you?", "en"),
            ("Türkçe yazılmış temizlik şikayetlerini göster", "tr"),
            ("VIP misafirlerin sorunlarını göster", "tr"),
            ("Show me hotel reviews", "en"),
            ("Otellerin hizmet puanlarını göster", "tr")
        ]
        
        success_count = 0
        for text, expected in test_texts:
            try:
                detected = detect(text)
                success = detected == expected
                success_count += success
                print_test_result(f"Language Detection: '{text[:30]}...'", success, f"Expected: {expected}, Got: {detected}")
            except Exception as e:
                print_test_result(f"Language Detection: '{text[:30]}...'", False, f"Error: {e}")
        
        overall_success = success_count >= len(test_texts) * 0.8  # 80% success rate
        print_test_result("Overall Language Detection", overall_success, f"{success_count}/{len(test_texts)} successful")
        return overall_success
        
    except Exception as e:
        print_test_result("Language Detection Test", False, f"Test setup failed: {e}")
        return False

async def test_turkish_gremlin_generation():
    """Test Turkish to Gremlin query generation."""
    print_section("Testing Turkish → Gremlin Query Generation")
    
    # Load environment
    load_dotenv()
    settings = get_settings()
    
    if not settings.gemini_api_key:
        print_test_result("Environment Setup", False, "GEMINI_API_KEY not found")
        return False
    
    print_test_result("Environment Setup", True, f"Using {settings.model_provider} - {settings.gemini_model}")
    
    # Turkish test queries
    turkish_queries = [
        {
            "name": "Turkish Cleanliness Complaints",
            "query": "Türkçe yazılmış temizlik şikayetlerini göster",
            "expected_elements": ["Review", "cleanliness", "hasLabel"]
        },
        {
            "name": "VIP Guest Issues",
            "query": "VIP misafirlerin sorunlarını göster",
            "expected_elements": ["Guest", "VIP", "type"]
        },
        {
            "name": "Hotel Service Ratings",
            "query": "Otellerin hizmet puanlarını göster",
            "expected_elements": ["Hotel", "service"]
        },
        {
            "name": "Room Maintenance Issues",
            "query": "Oda bakım sorunlarını bul",
            "expected_elements": ["Room", "maintenance", "Issue"]
        }
    ]
    
    try:
        # Initialize the LLM
        llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        await llm.initialize()
        print_test_result("LLM Initialization", True, "GraphQueryLLM ready")
        
        success_count = 0
        
        for i, test_case in enumerate(turkish_queries, 1):
            print(f"\n[{i}] Testing: {test_case['name']}")
            print(f"📝 Turkish Query: {test_case['query']}")
            
            try:
                # Generate Gremlin query
                start_time = time.time()
                gremlin_query = await llm.generate_gremlin_query(test_case['query'])
                generation_time = (time.time() - start_time) * 1000
                
                # Validate the query
                is_valid = (gremlin_query and 
                           gremlin_query.strip() and 
                           gremlin_query.startswith('g.') and
                           len(gremlin_query) > 10)
                
                if is_valid:
                    print(f"✅ Generated ({generation_time:.1f}ms): {gremlin_query}")
                    success_count += 1
                    
                    # Check for expected elements
                    contains_expected = any(element.lower() in gremlin_query.lower() 
                                          for element in test_case['expected_elements'])
                    if contains_expected:
                        print("✅ Contains expected elements")
                    else:
                        print("⚠️  May not contain all expected elements")
                else:
                    print(f"❌ Invalid query generated: {gremlin_query}")
                    
            except Exception as e:
                print(f"❌ Generation failed: {e}")
        
        overall_success = success_count >= len(turkish_queries) * 0.75  # 75% success rate
        print_test_result("Turkish Gremlin Generation", overall_success, 
                         f"{success_count}/{len(turkish_queries)} successful")
        return overall_success
        
    except Exception as e:
        print_test_result("Turkish Gremlin Generation", False, f"Test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints with Turkish queries."""
    print_section("Testing API Endpoints with Turkish Queries")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print_test_result("Server Status", False, f"Server returned {response.status_code}")
            return False
        print_test_result("Server Status", True, "API server is running")
    except Exception as e:
        print_test_result("Server Status", False, f"Cannot connect to server: {e}")
        return False
    
    # Test cases for API endpoints
    api_test_cases = [
        {
            "name": "Turkish Ask Endpoint",
            "endpoint": "/api/v1/ask",
            "payload": {
                "query": "Türkçe yazılmış temizlik şikayetlerini göster",
                "include_gremlin_query": True,
                "include_semantic_chunks": False,
                "use_llm_summary": True
            }
        },
        {
            "name": "Turkish Filter Endpoint",
            "endpoint": "/api/v1/filter",
            "payload": {
                "filters": {
                    "language": "tr",
                    "aspect": "cleanliness",
                    "sentiment": "negative"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True,
                "max_results": 10
            }
        },
        {
            "name": "Mixed Language Query",
            "endpoint": "/api/v1/ask",
            "payload": {
                "query": "VIP misafirlerin sorunlarını göster",
                "filters": {
                    "guest_type": "VIP"
                },
                "include_gremlin_query": True,
                "include_semantic_chunks": True
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(api_test_cases, 1):
        print(f"\n[{i}] Testing: {test_case['name']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}{test_case['endpoint']}",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code} ({response_time:.1f}ms)")
                
                # Check response structure
                if 'answer' in data or 'gremlin_query' in data or 'results' in data:
                    print("✅ Response has expected structure")
                    success_count += 1
                    
                    # Show key response elements
                    if 'gremlin_query' in data and data['gremlin_query']:
                        print(f"🔍 Gremlin: {data['gremlin_query'][:80]}...")
                    
                    if 'answer' in data and data['answer']:
                        print(f"💬 Answer: {data['answer'][:100]}...")
                        
                else:
                    print("⚠️  Response missing expected fields")
                    
            else:
                print(f"❌ Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    overall_success = success_count >= len(api_test_cases) * 0.67  # 67% success rate
    print_test_result("API Endpoint Tests", overall_success, 
                     f"{success_count}/{len(api_test_cases)} successful")
    return overall_success

def test_english_control_queries():
    """Test English queries as a control group."""
    print_section("Testing English Control Queries")
    
    english_test_cases = [
        {
            "name": "English Ask Query",
            "endpoint": "/api/v1/ask",
            "payload": {
                "query": "Show me hotels with excellent service",
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        },
        {
            "name": "English Filter Query",
            "endpoint": "/api/v1/filter",
            "payload": {
                "filters": {
                    "aspect": "service",
                    "sentiment": "positive"
                },
                "include_gremlin_query": True,
                "use_llm_summary": True
            }
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(english_test_cases, 1):
        print(f"\n[{i}] Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}{test_case['endpoint']}",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ English query successful")
                success_count += 1
                
                if 'gremlin_query' in data and data['gremlin_query']:
                    print(f"🔍 Generated Gremlin query successfully")
                    
            else:
                print(f"❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    overall_success = success_count == len(english_test_cases)
    print_test_result("English Control Tests", overall_success, 
                     f"{success_count}/{len(english_test_cases)} successful")
    return overall_success

async def main():
    """Run all tests and provide summary."""
    print_header("COMPLETE TURKISH/MULTILINGUAL GRAPH RAG SYSTEM TEST")
    
    # Run all test suites
    test_results = {}
    
    # Language detection test
    test_results['language_detection'] = await test_language_detection()
    
    # Turkish Gremlin generation test
    test_results['turkish_gremlin'] = await test_turkish_gremlin_generation()
    
    # API endpoint tests
    test_results['api_endpoints'] = test_api_endpoints()
    
    # English control tests
    test_results['english_control'] = test_english_control_queries()
    
    # Final summary
    print_header("TEST RESULTS SUMMARY")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Overall Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests >= total_tests * 0.75:  # 75% pass rate
        print("🎉 SYSTEM STATUS: Turkish multilingual support is working!")
        return True
    else:
        print("⚠️  SYSTEM STATUS: Issues detected, debugging needed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎯 TEST COMPLETED SUCCESSFULLY' if success else '❌ TEST COMPLETED WITH ISSUES'}")
    sys.exit(0 if success else 1)
