#!/usr/bin/env python3
"""
Test App State Vector Retriever
"""

import asyncio
from unittest.mock import MagicMock
from app.api.routes.semantic import get_vector_retriever
from app.core.vector_retriever import VectorRetriever

def test_dependency_function():
    """Test the dependency injection function."""
    
    print("🧪 Testing get_vector_retriever dependency function")
    
    # Create a mock request with app state
    mock_request = MagicMock()
    mock_app_state = MagicMock()
    
    # Test 1: No vector retriever in app state
    mock_app_state.vector_retriever = None
    mock_request.app.state = mock_app_state
    
    result = get_vector_retriever(mock_request)
    print(f"✅ Test 1 - No vector retriever in state: {type(result)}")
    print(f"   Returns: {result}")
    
    # Test 2: Vector retriever exists in app state
    mock_vector_retriever = VectorRetriever()
    mock_app_state.vector_retriever = mock_vector_retriever
    
    result = get_vector_retriever(mock_request)
    print(f"✅ Test 2 - Vector retriever in state: {type(result)}")
    print(f"   Returns same instance: {result is mock_vector_retriever}")

if __name__ == "__main__":
    test_dependency_function()
