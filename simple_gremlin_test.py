#!/usr/bin/env python3
"""
Simple Gremlin Query Generation Test

This script demonstrates natural language to Gremlin query translation
using the configured LLM from your .env file.
"""

import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv


class SimpleGremlinTester:
    """Simple tester for Gremlin query generation."""
    
    def __init__(self):
        """Initialize with environment variables."""
        load_dotenv()
        
        # Get configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        
        # Initialize Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.llm = genai.GenerativeModel(self.gemini_model)
            print(f"✅ Initialized Gemini: {self.gemini_model}")
        else:
            raise ValueError("GEMINI_API_KEY not found in .env file")
    
    async def generate_query(self, user_query: str) -> str:
        """Generate Gremlin query from natural language."""
        
        # Simple schema prompt based on hotel reviews
        schema_prompt = """
You are a Gremlin query expert for hotel review databases.

GRAPH SCHEMA:
- Hotel: properties include name, city, rating
- Review: properties include content, score, date  
- Guest: properties include name, type (VIP, regular)
- Room: properties include number, type, floor
- Aspect: properties include name (service, cleanliness, location)
- MaintenanceIssue: properties include description, severity, date

RELATIONSHIPS:
- HAS_REVIEW: Hotel -> Review
- WROTE_REVIEW: Guest -> Review  
- STAYED_IN: Guest -> Room
- HAS_MAINTENANCE_ISSUE: Room -> MaintenanceIssue
- ANALYZES_ASPECT: Review -> Aspect

GREMLIN EXAMPLES:
- Find all hotels: g.V().hasLabel('Hotel')
- Find VIP guests: g.V().hasLabel('Guest').has('type', 'VIP')
- Find recent reviews: g.V().hasLabel('Review').has('date', gte('2024-01-01'))
- Find maintenance issues: g.V().hasLabel('Room').out('HAS_MAINTENANCE_ISSUE')

Generate ONLY the Gremlin query for this request (no explanations):
"""
        
        prompt = schema_prompt + f"\nRequest: {user_query}\nGremlin Query:"
        
        print(f"\n📝 Query: {user_query}")
        print("🤖 Generating...")
        
        try:
            response = await asyncio.to_thread(self.llm.generate_content, prompt)
            gremlin_query = response.text.strip()
            
            # Clean up response
            if gremlin_query.startswith('```'):
                gremlin_query = gremlin_query.split('\n')[1]
            if not gremlin_query.startswith('g.'):
                # Try to extract the query
                lines = gremlin_query.split('\n')
                for line in lines:
                    if line.strip().startswith('g.'):
                        gremlin_query = line.strip()
                        break
            
            print(f"✨ Generated: {gremlin_query}")
            return gremlin_query
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""


async def main():
    """Test multiple query types."""
    print("🧪 SIMPLE GREMLIN QUERY GENERATION TEST")
    print("=" * 50)
    
    try:
        tester = SimpleGremlinTester()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test queries
    test_queries = [
        "Show me all hotels",
        "Find hotels with high ratings",
        "What are VIP guest reviews?",
        "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
        "Find hotels with excellent service but poor location ratings",
        "What rooms have had maintenance issues?",
        "Find reviews that mention cleanliness",
        "Show me luxury hotels in New York"
    ]
    
    print(f"\n🏃 Testing {len(test_queries)} queries...\n")
    
    results = []
    for i, query in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}]", end=" ")
        result = await tester.generate_query(query)
        results.append((query, result))
        print()  # Add spacing
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    
    for i, (query, result) in enumerate(results, 1):
        status = "✅" if result.startswith("g.") else "❌"
        print(f"{status} Query {i}: {query}")
        print(f"   → {result}")
        print()
    
    successful = sum(1 for _, result in results if result.startswith("g."))
    print(f"🎯 Success Rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
