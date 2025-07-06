#!/usr/bin/env python3
"""
Single Query Test - Example from User Request

Tests the specific query: "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks."
"""

import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv


async def test_specific_query():
    """Test the specific query from the user's example."""
    print("🎯 TESTING SPECIFIC QUERY FROM USER REQUEST")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return
    
    # Initialize Gemini
    genai.configure(api_key=gemini_api_key)
    llm = genai.GenerativeModel(gemini_model)
    print(f"✅ Initialized {gemini_model}")
    
    # The exact query from the user's request
    user_query = "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks."
    
    print(f"\n📝 User Query:")
    print(f"   '{user_query}'")
    
    # Enhanced prompt with hotel domain context
    prompt = """You are an expert in Gremlin graph database queries for hotel management systems.

HOTEL GRAPH SCHEMA:
Vertices:
- Guest: name, type(VIP/regular), member_since
- Room: number, type(standard/suite/vip), floor
- Hotel: name, city, rating
- MaintenanceIssue: description, severity, date_reported, status

Edges:
- STAYED_IN: Guest -> Room (with check_in_date, check_out_date)
- LOCATED_IN: Room -> Hotel
- HAS_MAINTENANCE_ISSUE: Room -> MaintenanceIssue
- REPORTED_BY: MaintenanceIssue -> Guest

GREMLIN SYNTAX RULES:
- Start with g.V() for vertices
- Use hasLabel('VertexType') to filter vertex types
- Use has('property', value) for property filtering
- Use has('property', gte(date)) for date comparisons
- Use out('EdgeLabel') to traverse outgoing edges
- Use in('EdgeLabel') to traverse incoming edges
- For date filtering: has('date', gte('2024-06-21')) format

TASK: Convert this natural language request to a valid Gremlin query:

"{user_query}"

Requirements:
1. Find VIP guests
2. Get rooms they stayed in recently (last 2 weeks)
3. Find maintenance issues for those rooms
4. Return maintenance issue details

Generate ONLY the Gremlin query:"""

    print(f"\n🤖 Sending to Gemini {gemini_model}...")
    print("📋 Prompt includes:")
    print("   • Hotel domain schema")
    print("   • Gremlin syntax rules")
    print("   • Step-by-step requirements")
    
    try:
        response = await asyncio.to_thread(llm.generate_content, prompt)
        generated_query = response.text.strip()
        
        print(f"\n✨ Generated Gremlin Query:")
        print(f"   {generated_query}")
        
        # Analyze the query
        print(f"\n🔍 Query Analysis:")
        
        if generated_query.startswith('g.'):
            print("   ✅ Valid Gremlin syntax (starts with 'g.')")
        else:
            print("   ❌ Invalid syntax (doesn't start with 'g.')")
        
        if 'VIP' in generated_query:
            print("   ✅ Filters for VIP guests")
        else:
            print("   ⚠️ Missing VIP guest filter")
        
        if 'MaintenanceIssue' in generated_query:
            print("   ✅ Targets maintenance issues")
        else:
            print("   ⚠️ Missing maintenance issue traversal")
        
        if any(date_term in generated_query for date_term in ['gte(', 'date', 'week', 'day']):
            print("   ✅ Includes date/time filtering")
        else:
            print("   ⚠️ Missing time period filtering")
        
        if any(traverse in generated_query for traverse in ['out(', 'in(']):
            print("   ✅ Uses graph traversal")
        else:
            print("   ⚠️ Missing graph traversal")
        
        # Expected query structure explanation
        print(f"\n💡 Expected Query Structure:")
        print("   1. g.V().hasLabel('Guest').has('type', 'VIP')")
        print("   2. .out('STAYED_IN')  // get rooms they stayed in")
        print("   3. .has('check_out_date', gte('recent_date'))  // recent stays")
        print("   4. .out('HAS_MAINTENANCE_ISSUE')  // get maintenance issues")
        print("   5. .valueMap()  // return issue details")
        
        print(f"\n🎉 Test Complete!")
        print(f"   Original Query: {user_query}")
        print(f"   Generated Result: {generated_query}")
        
        return generated_query
        
    except Exception as e:
        print(f"❌ Error generating query: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(test_specific_query())
