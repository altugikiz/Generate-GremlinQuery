#!/usr/bin/env python3
"""
Debug script to test Turkish language functionality and fix syntax errors.
"""

import asyncio
import sys
import os
import time
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Load environment variables
load_dotenv()

def test_basic_syntax():
    """Test basic syntax patterns that might cause issues."""
    print("🔍 Testing basic syntax patterns...")
    
    # Test dictionary access patterns
    payload = {
        "query": "Test query",
        "filters": {"language": "tr"}
    }
    
    # CORRECT syntax
    print(f"Query: {payload['query']}")  # Correct: using single quotes
    print(f"Language: {payload['filters']['language']}")
    
    # The error was likely caused by using incorrect quotes in f-strings
    # INCORRECT (this would cause syntax error):
    # print(f"Query: {payload[" query"]}")  # Wrong: space and wrong quotes
    
    print("✅ Basic syntax test passed")

def test_api_request():
    """Test a simple API request with proper syntax."""
    BASE_URL = "http://localhost:8000"
    
    try:
        # Check server status
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print(f"✅ Server status: {response.status_code}")
        
        if response.status_code == 200:
            # Test Turkish query with correct syntax
            test_payload = {
                "query": "Türkçe yazılmış temizlik şikayetlerini göster",
                "include_gremlin_query": True,
                "include_semantic_chunks": False,
                "use_llm_summary": True
            }
            
            print(f"📝 Testing query: {test_payload['query']}")
            
            response = requests.post(
                f"{BASE_URL}/api/v1/ask",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Turkish query test successful!")
                
                # Safely access response data
                if 'answer' in data:
                    print(f"💬 Answer: {data['answer'][:100]}...")
                
                if 'gremlin_query' in data and data['gremlin_query']:
                    print(f"🔍 Gremlin: {data['gremlin_query']}")
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the API server is running.")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main test function."""
    print("🎯 Debug Script for Turkish Language Support")
    print("=" * 60)
    
    test_basic_syntax()
    print()
    test_api_request()
    
    print("\n🎉 Debug script completed!")

if __name__ == "__main__":
    main()
