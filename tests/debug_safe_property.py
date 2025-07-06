#!/usr/bin/env python3
"""Debug script for safe property access function."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.routes.analytics import safe_extract_property

def test_safe_property_access():
    """Test safe property access function."""
    
    test_cases = [
        ({"prop": ["value"]}, "prop", "default", "value"),  # Normal valueMap case
        ({"prop": "direct_value"}, "prop", "default", "direct_value"),  # Direct value
        ({}, "missing_prop", "default", "default"),  # Missing property
        ({"prop": []}, "prop", "default", "default"),  # Empty array
        (None, "prop", "default", "default"),  # None input
    ]
    
    print("🧪 Testing safe_extract_property function")
    print("=" * 50)
    
    for i, (test_data, prop, default, expected) in enumerate(test_cases, 1):
        result = safe_extract_property(test_data, prop, default)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"Test {i}: {status}")
        print(f"  Input: {test_data}")
        print(f"  Property: '{prop}', Default: '{default}'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print()
        
        if result != expected:
            print(f"❌ Test {i} failed!")
            print(f"   Expected: {expected} (type: {type(expected)})")
            print(f"   Got: {result} (type: {type(result)})")
            return False
    
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    test_safe_property_access()
