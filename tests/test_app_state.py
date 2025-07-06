#!/usr/bin/env python3
"""
Test API with State Check
"""

import asyncio
import aiohttp
import json

async def test_app_state():
    """Test the app state through a new endpoint."""
    
    print("🧪 Testing App State via API")
    
    # Test the health endpoint to see what it reports
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/api/v1/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Health endpoint response:")
                    print(json.dumps(health_data, indent=2))
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_app_state())
