#!/usr/bin/env python3
"""
Quick API Test
"""

import asyncio
import aiohttp

async def test_api():
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": "otel temizliği",
            "top_k": 3,
            "min_score": 0.0
        }
        
        async with session.post(
            "http://localhost:8000/api/v1/semantic/vector",
            json=payload
        ) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            results = data.get('results', [])
            print(f"Results count: {len(results)}")
            print(f"Total documents: {data.get('total_documents', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(test_api())
