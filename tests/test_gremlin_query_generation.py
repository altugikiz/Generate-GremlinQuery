#!/usr/bin/env python3
"""
Gremlin Query Generation Test Script

This script tests natural language to Gremlin query translation using the configured LLM.
It demonstrates the query generation capability without executing the queries.

Usage:
    python test_gremlin_query_generation.py

Features:
- Loads configuration from .env file
- Uses the configured LLM provider (Gemini/OpenAI)
- Includes hotel review domain schema in prompts
- Tests various query types and complexity levels
- Provides detailed debugging output
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Import domain schema
try:
    import sys
    sys.path.append('.')
    from app.core.domain_schema import VERTICES, EDGES, get_vertex_labels, get_edge_labels
    from app.config.settings import get_settings
    SCHEMA_AVAILABLE = True
    print("✅ Domain schema loaded successfully")
except ImportError as e:
    print(f"⚠️ Warning: Could not import domain schema ({e}). Using basic schema.")
    SCHEMA_AVAILABLE = False
except Exception as e:
    print(f"⚠️ Warning: Error loading domain schema ({e}). Using basic schema.")
    SCHEMA_AVAILABLE = False


class GremlinQueryTester:
    """Test class for natural language to Gremlin query generation."""
    
    def __init__(self):
        """Initialize the tester with configuration from .env file."""
        # Load environment variables
        load_dotenv()
        
        self.model_provider = os.getenv('MODEL_PROVIDER', 'gemini')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize the LLM
        self.llm = None
        self._initialize_llm()
        
        # Build schema prompt
        self.schema_prompt = self._build_schema_prompt()
    
    def _initialize_llm(self):
        """Initialize the LLM based on MODEL_PROVIDER."""
        try:
            if self.model_provider.lower() == 'gemini':
                if not self.gemini_api_key:
                    raise ValueError("GEMINI_API_KEY not found in environment variables")
                
                genai.configure(api_key=self.gemini_api_key)
                self.llm = genai.GenerativeModel(self.gemini_model)
                print(f"✅ Initialized Gemini model: {self.gemini_model}")
                
            elif self.model_provider.lower() == 'openai':
                if not self.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                
                # Would initialize OpenAI client here
                print("⚠️ OpenAI integration not implemented in this test script")
                print("   Please use Gemini or implement OpenAI support")
                
            else:
                raise ValueError(f"Unsupported MODEL_PROVIDER: {self.model_provider}")
                
        except Exception as e:
            print(f"❌ Failed to initialize LLM: {e}")
            raise
    
    def _build_schema_prompt(self) -> str:
        """Build the domain schema description for the prompt."""
        if not SCHEMA_AVAILABLE:
            return """
Basic Hotel Review Graph Schema:

VERTICES (Nodes):
- Hotel: Properties include name, address, city, rating
- Review: Properties include content, score, date
- Guest: Properties include name, type (VIP, regular)
- Room: Properties include number, type, floor
- Aspect: Properties include name (service, cleanliness, location, etc.)

EDGES (Relationships):
- HAS_REVIEW: Hotel -> Review
- WROTE_REVIEW: Guest -> Review
- BOOKED_ROOM: Guest -> Room
- HAS_MAINTENANCE_ISSUE: Room -> MaintenanceIssue
- ANALYZES_ASPECT: Analysis -> Aspect
"""
        
        schema_description = """
Hotel Review Graph Schema:

VERTICES (Nodes):
"""
        
        # Add vertex information from domain schema
        if SCHEMA_AVAILABLE:
            try:
                vertex_labels = get_vertex_labels()
                edge_labels = get_edge_labels()
                
                for vertex in VERTICES:
                    # Get first 3 properties safely
                    properties = []
                    if hasattr(vertex, 'properties') and vertex.properties:
                        for i, prop in enumerate(vertex.properties):
                            if i >= 3:  # Limit to first 3
                                break
                            prop_type = getattr(prop, 'type', 'unknown')
                            if hasattr(prop_type, 'value'):
                                prop_type = prop_type.value
                            properties.append(f"{prop.name}({prop_type})")
                    
                    schema_description += f"- {vertex.label}: {vertex.description}\n"
                    if properties:
                        schema_description += f"  Properties: {', '.join(properties)}\n"
                
                schema_description += "\nEDGES (Relationships):\n"
                
                for edge in EDGES:
                    schema_description += f"- {edge.label}: {edge.from_vertex} -> {edge.to_vertex}\n"
                    schema_description += f"  Description: {edge.description}\n"
            except Exception as e:
                print(f"⚠️ Warning: Error loading schema details: {e}")
                # Fall back to basic schema
                pass
        
        schema_description += """
GREMLIN SYNTAX EXAMPLES:
- Find all hotels: g.V().hasLabel('Hotel')
- Find hotel by name: g.V().hasLabel('Hotel').has('name', 'Hotel Name')
- Find reviews for a hotel: g.V().hasLabel('Hotel').has('name', 'Hotel Name').in('HAS_REVIEW')
- Find high-rated reviews: g.V().hasLabel('Review').has('score', gte(8))
- Find VIP guests: g.V().hasLabel('Guest').has('type', 'VIP')
- Find rooms with maintenance issues: g.V().hasLabel('Room').out('HAS_MAINTENANCE_ISSUE')
- Find recent reviews: g.V().hasLabel('Review').has('date', gte('2024-01-01'))
- Find hotels with good cleanliness: g.V().hasLabel('Hotel').in('HAS_REVIEW').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'cleanliness').in('ANALYZES_ASPECT').has('aspect_score', gte(4.0))

IMPORTANT GREMLIN RULES:
- Always start with g.V() for vertex queries
- Use hasLabel('VertexName') to filter by vertex type
- Use has('property', 'value') for exact matches
- Use has('property', gte(value)) for greater than or equal
- Use has('property', lte(value)) for less than or equal
- Use in('EdgeLabel') to traverse incoming edges
- Use out('EdgeLabel') to traverse outgoing edges
- Use valueMap() or values('property') to get results
- Use limit(n) to limit results
- For date comparisons, use proper date format
"""
        
        return schema_description
    
    async def generate_gremlin_query(self, user_query: str, verbose: bool = True) -> Optional[str]:
        """
        Generate a Gremlin query from natural language input.
        
        Args:
            user_query: Natural language query from user
            verbose: Whether to print detailed debugging information
            
        Returns:
            Generated Gremlin query string or None if failed
        """
        if not self.llm:
            print("❌ LLM not initialized")
            return None
        
        try:
            # Build the prompt
            prompt = f"""You are a Gremlin query expert specializing in hotel review graph databases.

{self.schema_prompt}

TASK: Convert the following natural language query into a valid Gremlin query.

User Query: "{user_query}"

Requirements:
1. Generate ONLY the Gremlin query, no explanations
2. Use the exact vertex and edge labels from the schema above
3. Ensure the query is syntactically correct
4. Use appropriate property names and data types
5. Include proper filtering and traversal steps
6. Return only the query string, no markdown formatting

Gremlin Query:"""

            if verbose:
                print("\n" + "="*80)
                print("🔍 GENERATING GREMLIN QUERY")
                print("="*80)
                print(f"📝 User Query: {user_query}")
                print(f"🤖 LLM Provider: {self.model_provider}")
                print(f"🧠 Model: {self.gemini_model}")
                print("\n📋 Prompt Preview:")
                print("-" * 40)
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
                print("-" * 40)
            
            # Call the LLM
            if self.model_provider.lower() == 'gemini':
                response = await asyncio.to_thread(self.llm.generate_content, prompt)
                generated_query = response.text if hasattr(response, 'text') else str(response)
            else:
                # Placeholder for other providers
                generated_query = "# OpenAI integration not implemented"
            
            # Clean up the response
            generated_query = self._clean_gremlin_query(generated_query)
            
            if verbose:
                print(f"\n✨ Generated Gremlin Query:")
                print(f"   {generated_query}")
                print(f"\n🔧 Query Analysis:")
                self._analyze_query(generated_query)
            
            return generated_query
            
        except Exception as e:
            print(f"❌ Failed to generate query: {e}")
            return None
    
    def _clean_gremlin_query(self, response: str) -> str:
        """Clean and extract the Gremlin query from LLM response."""
        # Remove markdown formatting
        query = response.strip()
        if query.startswith("```"):
            lines = query.split('\n')
            query = '\n'.join(lines[1:-1]) if len(lines) > 2 else query
        
        # Remove any trailing explanations (take first line if multi-line)
        if '\n' in query:
            query = query.split('\n')[0]
        
        # Ensure query starts with 'g.'
        if not query.startswith('g.'):
            # Try to find the query in the response
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('g.'):
                    query = line
                    break
        
        return query.strip()
    
    def _analyze_query(self, query: str):
        """Analyze the generated query and provide insights."""
        if not query or not query.startswith('g.'):
            print("   ⚠️ Invalid query format")
            return
        
        analysis = []
        
        # Check for vertex labels
        if 'hasLabel(' in query:
            import re
            labels = re.findall(r"hasLabel\('([^']+)'\)", query)
            analysis.append(f"Targets vertex labels: {', '.join(labels)}")
        
        # Check for properties
        if 'has(' in query:
            analysis.append("Uses property filtering")
        
        # Check for traversals
        if '.in(' in query or '.out(' in query:
            analysis.append("Includes graph traversal")
        
        # Check for result operations
        if 'valueMap()' in query:
            analysis.append("Returns full property maps")
        elif 'values(' in query:
            analysis.append("Returns specific property values")
        
        # Check for limits
        if 'limit(' in query:
            analysis.append("Includes result limiting")
        
        for item in analysis:
            print(f"   ✓ {item}")
        
        if not analysis:
            print("   ℹ️ Basic vertex query")


def main():
    """Main test function."""
    print("🧪 GREMLIN QUERY GENERATION TEST")
    print("=" * 50)
    
    # Initialize tester
    try:
        tester = GremlinQueryTester()
    except Exception as e:
        print(f"❌ Failed to initialize tester: {e}")
        return
    
    # Define test queries
    test_queries = [
        # Basic queries
        "Show me all hotels",
        "Find hotels in New York",
        "What are the high-rated reviews?",
        
        # Complex queries
        "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks",
        "Find hotels with excellent service but poor location ratings",
        "What are the most common complaints about cleanliness?",
        "Show me reviews from VIP guests about luxury hotels",
        
        # Advanced queries
        "Find rooms that had maintenance issues and were booked by VIP guests",
        "Compare service ratings between different hotel chains",
        "Show me trending issues in recent hotel reviews"
    ]
    
    # Interactive mode option
    print("Choose test mode:")
    print("1. Run predefined test queries")
    print("2. Interactive mode (enter your own queries)")
    print("3. Single test query")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            # Run predefined tests
            print(f"\n🏃 Running {len(test_queries)} predefined test queries...")
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n{'='*20} TEST {i}/{len(test_queries)} {'='*20}")
                result = asyncio.run(tester.generate_gremlin_query(query, verbose=True))
                
                if result:
                    print(f"✅ Query {i} generated successfully")
                else:
                    print(f"❌ Query {i} failed to generate")
                
                if i < len(test_queries):
                    input("\nPress Enter to continue to next query...")
        
        elif choice == "2":
            # Interactive mode
            print("\n💬 Interactive Mode - Enter 'quit' to exit")
            
            while True:
                user_query = input("\n📝 Enter your query: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_query:
                    result = asyncio.run(tester.generate_gremlin_query(user_query, verbose=True))
                    
                    if result:
                        print(f"\n📋 Final Query: {result}")
                    else:
                        print("\n❌ Failed to generate query")
        
        elif choice == "3":
            # Single test
            test_query = "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks"
            print(f"\n🎯 Testing single query: '{test_query}'")
            
            result = asyncio.run(tester.generate_gremlin_query(test_query, verbose=True))
            
            if result:
                print(f"\n🎉 SUCCESS! Generated query:")
                print(f"   {result}")
                
                print(f"\n💡 Explanation:")
                print(f"   This query should find VIP guests, traverse to their room bookings,")
                print(f"   then find maintenance issues for those rooms within the last 2 weeks.")
            else:
                print(f"\n❌ FAILED to generate query")
        
        else:
            print("❌ Invalid choice")
            return
    
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("\n🏁 Test completed!")


if __name__ == "__main__":
    main()
