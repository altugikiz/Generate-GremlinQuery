#!/usr/bin/env python3
"""
Simple test script to verify the Graph RAG Pipeline components.
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from app.config.settings import get_settings
        print("✅ Settings import successful")
        
        from app.models.dto import SearchRequest, GraphResult
        print("✅ DTOs import successful")
        
        from app.core.domain_schema import VERTICES, EDGES
        print(f"✅ Domain schema import successful - {len(VERTICES)} vertices, {len(EDGES)} edges")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_configuration():
    """Test that configuration loads properly."""
    print("🧪 Testing configuration...")
    
    try:
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"✅ Configuration loaded - Model: {settings.gemini_model}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_schema_validation():
    """Test schema validation."""
    print("🧪 Testing schema validation...")
    
    try:
        from app.core.domain_schema import validate_schema, get_schema_summary
        
        # Validate schema
        validate_schema()
        print("✅ Schema validation passed")
        
        # Get summary
        summary = get_schema_summary()
        print(f"✅ Schema summary: {summary['vertices']['count']} vertices, {summary['edges']['count']} edges")
        
        return True
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

async def test_dto_creation():
    """Test DTO creation and validation."""
    print("🧪 Testing DTO creation...")
    
    try:
        from app.models.dto import SearchRequest, GraphNode, GraphEdge
        
        # Test SearchRequest
        request = SearchRequest(query="test hotel", search_type="hybrid")
        print(f"✅ SearchRequest created: {request.query}")
        
        # Test GraphNode
        node = GraphNode(id="test_1", label="Hotel", properties={"name": "Test Hotel"})
        print(f"✅ GraphNode created: {node.label}")
        
        return True
    except Exception as e:
        print(f"❌ DTO creation failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🏁 Graph RAG Pipeline Component Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Schema Validation Test", test_schema_validation),
        ("DTO Creation Test", test_dto_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
