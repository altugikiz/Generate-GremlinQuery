#!/usr/bin/env python3
"""
Enhanced Gremlin Query Generation Test Script

Objective:
Tests LLM integration for converting natural language queries into Gremlin queries.
Supports both single queries and batch testing with detailed analysis.

Requirements:
- Reads user query from input() or uses predefined test strings
- Uses Gemini LLM (based on MODEL_PROVIDER from .env)
- Constructs domain-aware prompts for Gremlin query generation
- Prints original input, generated query, and analysis

Example:
    user_query = "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks."
    → LLM returns:
    "g.V().hasLabel('Guest').has('type', 'VIP').out('STAYED_IN').out('HAS_ISSUE').has('date', gte('now-14d')).valueMap()"
"""

import os
import sys
import time
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from loguru import logger
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure enhanced logging
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}", level="INFO")


class EnhancedGremlinTester:
    """Enhanced tester for Gremlin query generation with analysis and debugging."""
    
    def __init__(self):
        """Initialize with environment configuration."""
        self.env_config = self._load_environment()
        self.llm = self._setup_gemini_client()
        logger.info("🚀 Enhanced Gremlin Tester initialized successfully")
    
    def _load_environment(self) -> Dict[str, str]:
        """Load and validate environment configuration."""
        try:
            env_config = {
                'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
                'GEMINI_MODEL': os.getenv('GEMINI_MODEL', 'gemini-2.0-flash'),
                'MODEL_PROVIDER': os.getenv('MODEL_PROVIDER', 'gemini'),
                'LLM_MODEL_NAME': os.getenv('LLM_MODEL_NAME', 'gemini-2.0-flash')
            }
            
            if not env_config['GEMINI_API_KEY']:
                raise ValueError("GEMINI_API_KEY is required but not found in .env")
            
            logger.info(f"✅ Environment loaded - Provider: {env_config['MODEL_PROVIDER']}, Model: {env_config['GEMINI_MODEL']}")
            return env_config
            
        except Exception as e:
            logger.error(f"❌ Failed to load environment: {e}")
            raise

    def _setup_gemini_client(self):
        """Initialize and configure Gemini client."""
        try:
            genai.configure(api_key=self.env_config['GEMINI_API_KEY'])
            model = genai.GenerativeModel(self.env_config['GEMINI_MODEL'])
            logger.info(f"✅ Gemini client initialized - Model: {self.env_config['GEMINI_MODEL']}")
            return model
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {e}")
            raise

    def get_hotel_domain_schema(self) -> str:
        """Return the comprehensive hotel review domain schema."""
        return """
        Hotel Review Graph Database Schema:
        
        VERTICES:
        - Hotel: id, name, location, star_rating, amenities[]
        - HotelGroup: id, name, type, headquarters
        - Review: id, title, text, overall_score, date, author_name
        - Analysis: id, overall_sentiment, confidence_score
        - Aspect: id, name, category [cleanliness, service, location, value, amenities, staff, room, etc.]
        - Language: id, name, code [en, es, fr, de, etc.]
        - Source: id, name, type, url [TripAdvisor, Booking.com, Hotels.com, etc.]
        - Guest: id, name, type [VIP, regular, business, family], loyalty_level
        - Room: id, number, type, floor, features[], price_per_night
        - MaintenanceIssue: id, type, severity, status, date_reported, description
        - AccommodationType: id, type, features[], max_occupancy, price_range

        EDGES:
        - Hotel -[BELONGS_TO]-> HotelGroup
        - Review -[ABOUT]-> Hotel
        - Review -[HAS_ANALYSIS]-> Analysis
        - Analysis -[ANALYZES_ASPECT]-> Aspect
        - Review -[WRITTEN_IN]-> Language
        - Review -[FROM_SOURCE]-> Source
        - Guest -[WROTE]-> Review
        - Guest -[STAYED_IN]-> Room
        - Room -[BELONGS_TO]-> Hotel
        - Room -[HAS_ISSUE]-> MaintenanceIssue
        - Hotel -[OFFERS]-> AccommodationType
        - Analysis -[HAS_SCORE]-> Aspect (with aspect_score property)
        """

    def create_gremlin_prompt(self, user_query: str) -> str:
        """Create a comprehensive prompt for Gremlin query generation."""
        schema = self.get_hotel_domain_schema()
        
        prompt = f"""
        You are a Gremlin query expert specializing in hotel review graph databases.
        
        {schema}
        
        User Query: "{user_query}"
        
        Convert this natural language query into a valid Gremlin traversal query.
        
        GREMLIN RULES:
        1. Always start with g.V() for vertex queries
        2. Use hasLabel('VertexType') to filter by vertex type
        3. Use has('property', value) for property filtering
        4. Use out('EDGE_NAME') and in('EDGE_NAME') for edge traversal
        5. Use where() for complex filtering conditions
        6. Use valueMap() or values('property') to return data
        7. Always add .limit(10) for performance unless otherwise specified
        8. For date comparisons, use gte(), lte(), gt(), lt()
        9. For text searches, consider using textContains() or regex()
        10. For score comparisons, use numeric operators

        QUERY PATTERNS:
        - "Find hotels" → g.V().hasLabel('Hotel').limit(10).valueMap()
        - "Hotels with poor service" → g.V().hasLabel('Hotel').where(__.in('ABOUT').in('HAS_ANALYSIS').out('ANALYZES_ASPECT').has('name', 'service').values('aspect_score').is(lt(5))).limit(10).valueMap()
        - "VIP guest issues" → g.V().hasLabel('Guest').has('type', 'VIP').out('STAYED_IN').out('HAS_ISSUE').limit(10).valueMap()
        - "Recent maintenance" → g.V().hasLabel('MaintenanceIssue').has('date_reported', gte('2024-01-01')).limit(10).valueMap()
        
        Return ONLY the Gremlin query, no explanations or markdown.
        """
        
        return prompt

    def clean_gremlin_query(self, raw_response: str) -> str:
        """Clean and extract Gremlin query from LLM response."""
        cleaned = raw_response.strip()
        
        # Remove markdown formatting
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            # Find the actual query line
            for line in lines:
                line = line.strip()
                if line.startswith('g.') and not line.startswith('//') and not line.startswith('#'):
                    return line
        
        # Remove language markers
        cleaned = cleaned.replace('```gremlin', '').replace('```', '')
        
        # Extract query line
        lines = cleaned.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('g.') and not line.startswith('//') and not line.startswith('#'):
                return line
        
        return cleaned.strip()

    def analyze_gremlin_query(self, query: str) -> Dict[str, Any]:
        """Analyze the generated Gremlin query for correctness and completeness."""
        analysis = {
            "valid_syntax": False,
            "starts_with_g": False,
            "has_vertex_filter": False,
            "has_property_filter": False,
            "has_edge_traversal": False,
            "has_result_projection": False,
            "has_limit": False,
            "estimated_complexity": "simple",
            "potential_issues": [],
            "query_type": "unknown",
            "performance_score": 0
        }
        
        # Basic syntax validation
        if query.startswith('g.'):
            analysis["starts_with_g"] = True
            analysis["performance_score"] += 20
        
        if '.hasLabel(' in query:
            analysis["has_vertex_filter"] = True
            analysis["performance_score"] += 20
        
        if '.has(' in query:
            analysis["has_property_filter"] = True
            analysis["performance_score"] += 15
        
        if any(edge in query for edge in ['.out(', '.in(', '.both(']):
            analysis["has_edge_traversal"] = True
            analysis["performance_score"] += 15
        
        if any(proj in query for proj in ['.valueMap(', '.values(', '.project(']):
            analysis["has_result_projection"] = True
            analysis["performance_score"] += 15
        
        if '.limit(' in query:
            analysis["has_limit"] = True
            analysis["performance_score"] += 15
        
        # Determine query type
        if 'Hotel' in query:
            analysis["query_type"] = "hotel_search"
        elif 'Review' in query:
            analysis["query_type"] = "review_analysis" 
        elif 'MaintenanceIssue' in query:
            analysis["query_type"] = "maintenance_query"
        elif 'Guest' in query:
            analysis["query_type"] = "guest_analysis"
        
        # Complexity estimation
        complexity_indicators = (
            query.count('.') + 
            query.count('where') + 
            query.count('group') + 
            query.count('project')
        )
        
        if complexity_indicators > 15:
            analysis["estimated_complexity"] = "complex"
        elif complexity_indicators > 8:
            analysis["estimated_complexity"] = "medium"
        
        # Issue detection
        if not analysis["has_result_projection"]:
            analysis["potential_issues"].append("Missing result projection (valueMap/values)")
        
        if not analysis["has_limit"]:
            analysis["potential_issues"].append("No result limit - may impact performance")
        
        if not analysis["has_vertex_filter"]:
            analysis["potential_issues"].append("No vertex type filtering - inefficient")
        
        # Overall validity
        analysis["valid_syntax"] = (
            analysis["starts_with_g"] and 
            analysis["has_vertex_filter"] and 
            analysis["has_result_projection"]
        )
        
        return analysis

    def generate_query(self, user_query: str) -> Dict[str, Any]:
        """Generate and analyze a Gremlin query from natural language."""
        logger.info(f"🎯 Processing query: '{user_query}'")
        
        try:
            # Create prompt
            prompt = self.create_gremlin_prompt(user_query)
            
            # Generate query
            start_time = time.time()
            response = self.llm.generate_content(prompt)
            generation_time = (time.time() - start_time) * 1000
            
            # Extract and clean query
            raw_response = response.text
            gremlin_query = self.clean_gremlin_query(raw_response)
            
            # Analyze query
            analysis = self.analyze_gremlin_query(gremlin_query)
            
            return {
                "user_query": user_query,
                "gremlin_query": gremlin_query,
                "raw_response": raw_response,
                "generation_time_ms": generation_time,
                "analysis": analysis,
                "model_info": {
                    "provider": self.env_config['MODEL_PROVIDER'],
                    "model": self.env_config['GEMINI_MODEL']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Query generation failed: {e}")
            raise

    def print_results(self, result: Dict[str, Any]) -> None:
        """Print detailed results of query generation and analysis."""
        print("\n" + "="*80)
        print("🔍 GREMLIN QUERY GENERATION RESULTS")
        print("="*80)
        
        # Basic info
        print(f"📝 Original Query: {result['user_query']}")
        print(f"⚡ Generation Time: {result['generation_time_ms']:.2f}ms")
        print(f"🤖 Model: {result['model_info']['provider']} ({result['model_info']['model']})")
        
        # Generated query
        print(f"\n🔍 Generated Gremlin Query:")
        print("─" * 60)
        print(result['gremlin_query'])
        print("─" * 60)
        
        # Analysis
        analysis = result['analysis']
        print(f"\n📊 Query Analysis:")
        print(f"✅ Valid Syntax: {analysis['valid_syntax']}")
        print(f"🎯 Query Type: {analysis['query_type']}")
        print(f"⚖️  Complexity: {analysis['estimated_complexity']}")
        print(f"🏆 Performance Score: {analysis['performance_score']}/100")
        
        print(f"\n🔧 Technical Details:")
        print(f"   • Starts with g.: {analysis['starts_with_g']}")
        print(f"   • Has vertex filter: {analysis['has_vertex_filter']}")
        print(f"   • Has property filter: {analysis['has_property_filter']}")
        print(f"   • Has edge traversal: {analysis['has_edge_traversal']}")
        print(f"   • Has result projection: {analysis['has_result_projection']}")
        print(f"   • Has result limit: {analysis['has_limit']}")
        
        if analysis['potential_issues']:
            print(f"\n⚠️  Potential Issues:")
            for issue in analysis['potential_issues']:
                print(f"   • {issue}")
        
        # Query explanation
        self.explain_query_logic(result['user_query'], result['gremlin_query'])

    def explain_query_logic(self, user_query: str, gremlin_query: str) -> None:
        """Provide human-readable explanation of the query logic."""
        print(f"\n💡 Query Logic Explanation:")
        print("This query executes the following steps:")
        
        # Extract query components for explanation
        if 'VIP' in user_query.upper() and 'maintenance' in user_query.lower():
            print("1. 🎯 Start with Guest vertices filtered by type='VIP'")
            print("2. 🏠 Traverse to rooms they stayed in (STAYED_IN edge)")
            print("3. 🔧 Find maintenance issues for those rooms (HAS_ISSUE edge)")
            print("4. 📅 Filter by recent dates (last 2 weeks)")
            print("5. 📋 Return maintenance issue details")
        elif 'hotel' in user_query.lower() and 'rating' in user_query.lower():
            print("1. 🏨 Start with Hotel vertices") 
            print("2. 🔍 Filter by rating criteria")
            print("3. 📊 Return hotel properties and scores")
        elif 'review' in user_query.lower():
            print("1. 📝 Start with Review vertices")
            print("2. 🔍 Apply filters for sentiment, aspect, or content")
            print("3. 🔗 Traverse to related entities as needed")
            print("4. 📋 Return review data and analysis")
        else:
            print("1. 🎯 Start from the appropriate vertex type")
            print("2. 🔍 Apply filters based on query criteria")
            print("3. 🔗 Traverse relationships to gather related data")
            print("4. 📋 Return relevant properties")


def get_test_queries() -> List[str]:
    """Return a list of test queries for batch testing."""
    return [
        "Find all hotels",
        "Show me hotels with poor cleanliness ratings",
        "What are the top-rated hotels for service?",
        "Find VIP guest rooms with maintenance issues in the last 2 weeks",
        "Show me negative reviews about location",
        "Which hotels have the most complaints about amenities?",
        "Find hotels in the Marriott group with high ratings",
        "Show me reviews written in English about service",
        "What maintenance issues are reported most frequently?",
        "Find luxury hotels with excellent staff ratings",
        "Show me business travelers' reviews about room quality",
        "Which hotels have bathroom maintenance problems?"
    ]


def test_generate_gremlin_query(user_query: Optional[str] = None) -> Dict[str, Any]:
    """
    Main test function that:
    1. Takes a user query (input or predefined)
    2. Sends it to LLM (Gemini)
    3. Receives and cleans the Gremlin query
    4. Prints results for debugging
    5. Returns the result for further use
    """
    
    tester = EnhancedGremlinTester()
    
    # Get user query
    if not user_query:
        print("\n" + "="*70)
        print("🔍 GREMLIN QUERY GENERATION TEST")
        print("="*70)
        user_query = input("\n📝 Enter your natural language query (or press Enter for default): ").strip()
    
    # Use default query if none provided
    if not user_query:
        user_query = "Show me all maintenance issues related to VIP guest rooms in the last 2 weeks."
    
    # Generate and analyze query
    result = tester.generate_query(user_query)
    
    # Print results
    tester.print_results(result)
    
    return result


def run_multiple_test_queries() -> List[Dict[str, Any]]:
    """Run multiple test queries to validate different scenarios."""
    test_queries = get_test_queries()
    
    print("\n🔄 RUNNING MULTIPLE TEST SCENARIOS")
    print("="*80)
    
    tester = EnhancedGremlinTester()
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}/{len(test_queries)}")
        print(f"Query: {query}")
        print("-" * 70)
        
        try:
            result = tester.generate_query(query)
            result["status"] = "✅ SUCCESS"
            results.append(result)
            
            # Print condensed results
            analysis = result['analysis']
            print(f"✅ Generated: {result['gremlin_query'][:80]}...")
            print(f"   Performance: {analysis['performance_score']}/100, Type: {analysis['query_type']}")
            
        except Exception as e:
            error_result = {
                "user_query": query,
                "gremlin_query": None,
                "status": f"❌ FAILED: {str(e)}",
                "error": str(e)
            }
            results.append(error_result)
            print(f"❌ Failed: {str(e)}")
        
        print("─" * 70)
    
    # Summary
    success_count = sum(1 for r in results if "SUCCESS" in r.get("status", ""))
    print(f"\n📊 SUMMARY: {success_count}/{len(test_queries)} queries successful")
    print(f"Success Rate: {(success_count/len(test_queries)*100):.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if "SUCCESS" in result.get("status", "") else "❌"
        query_preview = result['user_query'][:60] + "..." if len(result['user_query']) > 60 else result['user_query']
        print(f"{i:2d}. {status_icon} {query_preview}")
        
        if "SUCCESS" in result.get("status", ""):
            score = result['analysis']['performance_score']
            complexity = result['analysis']['estimated_complexity']
            print(f"     Score: {score}/100, Complexity: {complexity}")
    
    return results


def interactive_mode():
    """Run in interactive mode for continuous testing."""
    print("\n🎮 INTERACTIVE GREMLIN QUERY GENERATOR")
    print("="*70)
    print("Enter natural language queries to convert to Gremlin.")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("Type 'batch' to run all test scenarios.")
    print("="*70)
    
    while True:
        try:
            user_input = input("\n🤔 Your query: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'batch':
                run_multiple_test_queries()
                continue
            elif not user_input:
                print("⚠️  Please enter a query or 'quit' to exit.")
                continue
            
            # Process the query
            result = test_generate_gremlin_query(user_input)
            
            # Ask if user wants to save results
            save_choice = input("\n💾 Save this result to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                save_result_to_file(result)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Interactive mode error: {e}")


def save_result_to_file(result: Dict[str, Any], filename: Optional[str] = None):
    """Save test result to a JSON file."""
    if not filename:
        timestamp = int(time.time())
        filename = f"gremlin_test_result_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Result saved to: {filename}")
    except Exception as e:
        print(f"❌ Failed to save result: {e}")


def analyze_batch_results(results: List[Dict[str, Any]]):
    """Analyze batch test results and provide insights."""
    if not results:
        return
    
    successful_results = [r for r in results if "SUCCESS" in r.get("status", "")]
    
    if not successful_results:
        print("⚠️  No successful queries to analyze.")
        return
    
    print(f"\n📈 BATCH ANALYSIS ({len(successful_results)} successful queries)")
    print("="*70)
    
    # Performance scores
    scores = [r['analysis']['performance_score'] for r in successful_results]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    print(f"🏆 Performance Scores:")
    print(f"   Average: {avg_score:.1f}/100")
    print(f"   Best: {max_score}/100")
    print(f"   Worst: {min_score}/100")
    
    # Query types
    query_types = [r['analysis']['query_type'] for r in successful_results]
    type_counts = {}
    for qtype in query_types:
        type_counts[qtype] = type_counts.get(qtype, 0) + 1
    
    print(f"\n🎯 Query Type Distribution:")
    for qtype, count in sorted(type_counts.items()):
        percentage = (count / len(successful_results)) * 100
        print(f"   {qtype}: {count} ({percentage:.1f}%)")
    
    # Generation times
    times = [r['generation_time_ms'] for r in successful_results]
    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)
    
    print(f"\n⚡ Generation Performance:")
    print(f"   Average time: {avg_time:.1f}ms")
    print(f"   Slowest: {max_time:.1f}ms")
    print(f"   Fastest: {min_time:.1f}ms")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test Gremlin query generation from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_gremlin_generation.py --query "Find hotels with poor service"
  python test_gremlin_generation.py --multiple
  python test_gremlin_generation.py --interactive
  python test_gremlin_generation.py -q "VIP maintenance issues" --save
        """
    )
    
    parser.add_argument("--query", "-q", type=str, help="Specific query to test")
    parser.add_argument("--multiple", "-m", action="store_true", help="Run multiple test scenarios")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--save", "-s", action="store_true", help="Save results to file")
    parser.add_argument("--analyze", "-a", action="store_true", help="Include batch analysis")
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_mode()
        elif args.multiple:
            results = run_multiple_test_queries()
            if args.analyze:
                analyze_batch_results(results)
            if args.save:
                timestamp = int(time.time())
                filename = f"batch_gremlin_test_results_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Batch results saved to: {filename}")
        elif args.query:
            result = test_generate_gremlin_query(args.query)
            if args.save:
                save_result_to_file(result)
        else:
            # Default: single query with user input
            result = test_generate_gremlin_query()
            if args.save:
                save_result_to_file(result)
                
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Application error: {e}")
        sys.exit(1)
