#!/usr/bin/env python3
"""
Final Gremlin Query Generation Demo

This script demonstrates the complete natural language to Gremlin query translation
workflow using your configured Gemini LLM.
"""

import os
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv
import re


class GremlinQueryGenerator:
    """Production-ready Gremlin query generator."""
    
    def __init__(self):
        load_dotenv()
        
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=self.gemini_api_key)
        self.llm = genai.GenerativeModel(self.gemini_model)
    
    def clean_gremlin_query(self, response: str) -> str:
        """Clean the LLM response to extract valid Gremlin query."""
        # Remove markdown code blocks
        response = re.sub(r'```(?:gremlin)?\n?(.*?)\n?```', r'\1', response, flags=re.DOTALL)
        
        # Split into lines and find the query
        lines = response.strip().split('\n')
        query_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('g.') or (query_lines and line.startswith('.')):
                query_lines.append(line)
            elif query_lines:
                # Stop when we hit explanatory text after the query
                break
        
        # Join multi-line queries
        query = ' '.join(query_lines).strip()
        
        # Remove any trailing periods or semicolons
        query = re.sub(r'[.;]+$', '', query)
        
        return query
    
    async def generate_gremlin_query(self, user_query: str) -> str:
        """Generate Gremlin query from natural language."""
        
        prompt = f"""You are a Gremlin query expert for hotel management graph databases.

SCHEMA:
Vertices: Guest(name,type), Room(number,type,floor), Hotel(name,city), MaintenanceIssue(description,date,severity)
Edges: STAYED_IN(Guest->Room), HAS_MAINTENANCE_ISSUE(Room->MaintenanceIssue), LOCATED_IN(Room->Hotel)

RULES:
- Start with g.V()
- Use hasLabel('Type') for vertex types
- Use has('property', value) for filtering
- Use out('EDGE') for outgoing edges
- Use in('EDGE') for incoming edges
- For dates: has('date', gte('2024-06-21'))
- End with valueMap() for full results

Convert to Gremlin query (return ONLY the query):

"{user_query}"

Query:"""

        try:
            response = await asyncio.to_thread(self.llm.generate_content, prompt)
            raw_response = response.text
            cleaned_query = self.clean_gremlin_query(raw_response)
            
            return cleaned_query
            
        except Exception as e:
            return f"Error: {e}"


async def demo():
    """Demonstrate the query generation."""
    print("🎯 GREMLIN QUERY GENERATION DEMO")
    print("=" * 50)
    
    generator = GremlinQueryGenerator()
    print(f"✅ Initialized Gemini: {generator.gemini_model}")
    
    # Test queries
    queries = [
        "Show me all hotels",
        "Find VIP guests",
        "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
        "What rooms had maintenance issues this month?",
        "Find hotels with recent guest complaints"
    ]
    
    print(f"\n🧪 Testing {len(queries)} queries:\n")
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}] 📝 Input: '{query}'")
        
        result = await generator.generate_gremlin_query(query)
        
        if result.startswith('g.'):
            print(f"    ✅ Output: {result}")
        else:
            print(f"    ❌ Error: {result}")
        print()
    
    print("🎉 Demo Complete!")
    
    # Interactive mode
    print("\n💬 Interactive Mode (type 'quit' to exit):")
    while True:
        try:
            user_input = input("\n📝 Enter query: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            if user_input:
                result = await generator.generate_gremlin_query(user_input)
                print(f"✨ Gremlin: {result}")
        except KeyboardInterrupt:
            break
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(demo())
