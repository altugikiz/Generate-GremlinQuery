"""
Sample data loader for the Hotel Review Graph RAG system.

This script creates sample data that follows the defined domain schema
to demonstrate the system's capabilities.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.config.settings import get_settings


class SampleDataLoader:
    """Loads sample data into the graph database following the domain schema."""
    
    def __init__(self, gremlin_client: SchemaAwareGremlinClient):
        self.client = gremlin_client
        self.created_entities = {
            "hotels": [],
            "reviews": [],
            "aspects": [],
            "languages": [],
            "sources": [],
            "hotel_groups": []
        }
    
    async def load_all_sample_data(self):
        """Load all sample data in the correct order."""
        print("🏁 Loading sample data for Graph RAG Pipeline...")
        
        try:
            # Clear existing data (optional)
            # await self.clear_existing_data()
            
            # Load reference data first
            await self.load_languages()
            await self.load_sources()
            await self.load_aspects()
            await self.load_hotel_groups()
            
            # Load main entities
            await self.load_hotels()
            await self.load_reviews()
            await self.load_analyses()
            
            # Create relationships
            await self.create_relationships()
            
            print("✅ Sample data loading completed successfully!")
            
        except Exception as e:
            print(f"❌ Sample data loading failed: {e}")
            raise
    
    async def load_languages(self):
        """Load language entities."""
        print("📚 Loading languages...")
        
        languages = [
            {"code": "en", "name": "English", "family": "Germanic", "script": "Latin"},
            {"code": "es", "name": "Spanish", "family": "Romance", "script": "Latin"},
            {"code": "fr", "name": "French", "family": "Romance", "script": "Latin"},
            {"code": "de", "name": "German", "family": "Germanic", "script": "Latin"},
            {"code": "it", "name": "Italian", "family": "Romance", "script": "Latin"},
            {"code": "pt", "name": "Portuguese", "family": "Romance", "script": "Latin"},
            {"code": "zh", "name": "Chinese", "family": "Sino-Tibetan", "script": "Chinese"},
            {"code": "ja", "name": "Japanese", "family": "Japonic", "script": "Japanese"},
        ]
        
        for lang in languages:
            vertex_id = f"lang_{lang['code']}"
            query = f"""
            g.addV('Language')
             .property(id, '{vertex_id}')
             .property('code', '{lang['code']}')
             .property('name', '{lang['name']}')
             .property('family', '{lang['family']}')
             .property('script', '{lang['script']}')
            """
            await self.client.execute_query(query)
        
        print(f"✅ Loaded {len(languages)} languages")
    
    async def load_sources(self):
        """Load source platform entities."""
        print("🌐 Loading sources...")
        
        sources = [
            {"name": "Booking.com", "type": "OTA", "url": "https://booking.com", "reliability_score": 0.9},
            {"name": "Expedia", "type": "OTA", "url": "https://expedia.com", "reliability_score": 0.85},
            {"name": "TripAdvisor", "type": "Review Site", "url": "https://tripadvisor.com", "reliability_score": 0.8},
            {"name": "Hotels.com", "type": "OTA", "url": "https://hotels.com", "reliability_score": 0.85},
            {"name": "Airbnb", "type": "Alternative Accommodation", "url": "https://airbnb.com", "reliability_score": 0.75},
            {"name": "Google Reviews", "type": "Review Platform", "url": "https://google.com", "reliability_score": 0.7},
        ]
        
        for source in sources:
            vertex_id = f"source_{source['name'].lower().replace('.', '').replace(' ', '_')}"
            query = f"""
            g.addV('Source')
             .property(id, '{vertex_id}')
             .property('name', '{source['name']}')
             .property('type', '{source['type']}')
             .property('url', '{source['url']}')
             .property('reliability_score', {source['reliability_score']})
            """
            await self.client.execute_query(query)
            self.created_entities["sources"].append(vertex_id)
        
        print(f"✅ Loaded {len(sources)} sources")
    
    async def load_aspects(self):
        """Load aspect entities."""
        print("🎯 Loading aspects...")
        
        aspects = [
            {"name": "cleanliness", "category": "facility", "description": "Overall cleanliness of rooms and common areas", "weight": 0.9},
            {"name": "service", "category": "staff", "description": "Quality of customer service and staff interactions", "weight": 1.0},
            {"name": "location", "category": "geography", "description": "Convenience and attractiveness of hotel location", "weight": 0.8},
            {"name": "comfort", "category": "accommodation", "description": "Comfort of beds, rooms, and amenities", "weight": 0.9},
            {"name": "facilities", "category": "amenities", "description": "Quality and availability of hotel facilities", "weight": 0.7},
            {"name": "value", "category": "pricing", "description": "Value for money and overall pricing satisfaction", "weight": 0.8},
            {"name": "food", "category": "dining", "description": "Quality of restaurant, breakfast, and dining options", "weight": 0.6},
            {"name": "wifi", "category": "technology", "description": "Quality and reliability of internet connection", "weight": 0.5},
            {"name": "noise", "category": "environment", "description": "Noise levels and sound insulation", "weight": 0.6},
            {"name": "checkin", "category": "process", "description": "Check-in and check-out process efficiency", "weight": 0.4},
        ]
        
        for aspect in aspects:
            vertex_id = f"aspect_{aspect['name']}"
            query = f"""
            g.addV('Aspect')
             .property(id, '{vertex_id}')
             .property('name', '{aspect['name']}')
             .property('category', '{aspect['category']}')
             .property('description', '{aspect['description']}')
             .property('weight', {aspect['weight']})
            """
            await self.client.execute_query(query)
            self.created_entities["aspects"].append(vertex_id)
        
        print(f"✅ Loaded {len(aspects)} aspects")
    
    async def load_hotel_groups(self):
        """Load hotel group entities."""
        print("🏨 Loading hotel groups...")
        
        hotel_groups = [
            {"name": "Marriott International", "headquarters": "Bethesda, MD, USA", "founded": 1927},
            {"name": "Hilton Worldwide", "headquarters": "McLean, VA, USA", "founded": 1919},
            {"name": "Hyatt Hotels Corporation", "headquarters": "Chicago, IL, USA", "founded": 1957},
            {"name": "InterContinental Hotels Group", "headquarters": "Denham, UK", "founded": 1777},
            {"name": "Accor", "headquarters": "Issy-les-Moulineaux, France", "founded": 1967},
        ]
        
        for group in hotel_groups:
            vertex_id = f"group_{group['name'].lower().replace(' ', '_').replace(',', '')}"
            query = f"""
            g.addV('HotelGroup')
             .property(id, '{vertex_id}')
             .property('name', '{group['name']}')
             .property('headquarters', '{group['headquarters']}')
             .property('founded', {group['founded']})
             .property('website', 'https://{group['name'].split()[0].lower()}.com')
            """
            await self.client.execute_query(query)
            self.created_entities["hotel_groups"].append(vertex_id)
        
        print(f"✅ Loaded {len(hotel_groups)} hotel groups")
    
    async def load_hotels(self):
        """Load hotel entities."""
        print("🏢 Loading hotels...")
        
        hotels = [
            {
                "name": "Grand Marriott Times Square",
                "city": "New York",
                "country": "USA",
                "star_rating": 4,
                "latitude": 40.7589,
                "longitude": -73.9851,
                "group": "group_marriott_international"
            },
            {
                "name": "Hilton Garden Inn Downtown",
                "city": "Chicago",
                "country": "USA", 
                "star_rating": 3,
                "latitude": 41.8781,
                "longitude": -87.6298,
                "group": "group_hilton_worldwide"
            },
            {
                "name": "Hyatt Regency London",
                "city": "London",
                "country": "UK",
                "star_rating": 5,
                "latitude": 51.5074,
                "longitude": -0.1278,
                "group": "group_hyatt_hotels_corporation"
            },
            {
                "name": "InterContinental Paris Le Grand",
                "city": "Paris",
                "country": "France",
                "star_rating": 5,
                "latitude": 48.8566,
                "longitude": 2.3522,
                "group": "group_intercontinental_hotels_group"
            },
            {
                "name": "Novotel Berlin Mitte",
                "city": "Berlin",
                "country": "Germany",
                "star_rating": 4,
                "latitude": 52.5200,
                "longitude": 13.4050,
                "group": "group_accor"
            },
        ]
        
        for hotel in hotels:
            vertex_id = f"hotel_{hotel['name'].lower().replace(' ', '_').replace(',', '')}"
            query = f"""
            g.addV('Hotel')
             .property(id, '{vertex_id}')
             .property('name', '{hotel['name']}')
             .property('city', '{hotel['city']}')
             .property('country', '{hotel['country']}')
             .property('star_rating', {hotel['star_rating']})
             .property('latitude', {hotel['latitude']})
             .property('longitude', {hotel['longitude']})
             .property('phone', '+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}')
             .property('check_in', '15:00')
             .property('check_out', '11:00')
            """
            await self.client.execute_query(query)
            self.created_entities["hotels"].append({"id": vertex_id, "group": hotel["group"]})
        
        print(f"✅ Loaded {len(hotels)} hotels")
    
    async def load_reviews(self):
        """Load review entities."""
        print("📝 Loading reviews...")
        
        review_templates = [
            {"title": "Excellent stay", "text": "The hotel was fantastic. Great service, clean rooms, and perfect location. Highly recommended!", "score": 9},
            {"title": "Good value", "text": "Nice hotel for the price. Room was clean and staff was helpful. Location could be better.", "score": 7},
            {"title": "Outstanding service", "text": "The staff went above and beyond. The concierge was particularly helpful with restaurant recommendations.", "score": 10},
            {"title": "Disappointing experience", "text": "Room was not clean upon arrival. Had to wait 30 minutes for someone to fix it. Service was slow.", "score": 4},
            {"title": "Perfect location", "text": "Could not ask for a better location. Walking distance to everything. Hotel facilities were good too.", "score": 8},
            {"title": "Mixed feelings", "text": "The room was nice but the WiFi was terrible. Food at the restaurant was excellent though.", "score": 6},
            {"title": "Great facilities", "text": "The gym and pool were excellent. Room was comfortable and quiet. Check-in was smooth.", "score": 8},
            {"title": "Poor value for money", "text": "Way too expensive for what you get. Room was small and breakfast was mediocre.", "score": 3},
        ]
        
        for hotel in self.created_entities["hotels"]:
            # Generate 3-5 reviews per hotel
            num_reviews = random.randint(3, 5)
            for i in range(num_reviews):
                template = random.choice(review_templates)
                review_id = f"review_{hotel['id']}_{i+1}"
                
                # Random date in the last 6 months
                days_ago = random.randint(1, 180)
                review_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
                
                query = f"""
                g.addV('Review')
                 .property(id, '{review_id}')
                 .property('title', '{template['title']}')
                 .property('text', '{template['text']}')
                 .property('score', {template['score']})
                 .property('created_at', '{review_date}')
                 .property('verified', {random.choice(['true', 'false'])})
                 .property('helpful_votes', {random.randint(0, 15)})
                 .property('author_name', 'Guest_{random.randint(1000, 9999)}')
                """
                await self.client.execute_query(query)
                self.created_entities["reviews"].append({
                    "id": review_id, 
                    "hotel_id": hotel['id'],
                    "score": template['score']
                })
        
        print(f"✅ Loaded {len(self.created_entities['reviews'])} reviews")
    
    async def load_analyses(self):
        """Load analysis entities for reviews."""
        print("🤖 Loading analyses...")
        
        analyses_created = 0
        for review in self.created_entities["reviews"]:
            # Create 2-3 analyses per review (different aspects)
            aspects_to_analyze = random.sample(self.created_entities["aspects"], random.randint(2, 3))
            
            for aspect_id in aspects_to_analyze:
                analysis_id = f"analysis_{review['id']}_{aspect_id}"
                
                # Generate sentiment score based on review score
                base_sentiment = (review['score'] - 5.5) / 4.5  # Convert 1-10 to roughly -1 to 1
                sentiment_score = max(-1, min(1, base_sentiment + random.uniform(-0.2, 0.2)))
                
                # Generate aspect score based on review score with some variation
                aspect_score = max(0, min(5, review['score'] / 2 + random.uniform(-0.5, 0.5)))
                
                query = f"""
                g.addV('Analysis')
                 .property(id, '{analysis_id}')
                 .property('sentiment_score', {sentiment_score:.3f})
                 .property('confidence', {random.uniform(0.7, 0.95):.3f})
                 .property('aspect_score', {aspect_score:.2f})
                 .property('explanation', 'AI-generated analysis of {aspect_id.replace('aspect_', '')} aspect')
                 .property('model_version', 'v1.0')
                 .property('analyzed_at', '{datetime.now().isoformat()}')
                """
                await self.client.execute_query(query)
                analyses_created += 1
        
        print(f"✅ Loaded {analyses_created} analyses")
    
    async def create_relationships(self):
        """Create relationships between entities."""
        print("🔗 Creating relationships...")
        
        # Hotel group owns hotels
        for hotel in self.created_entities["hotels"]:
            query = f"""
            g.V('{hotel['group']}').addE('OWNS').to(g.V('{hotel['id']}'))
             .property('since', {random.randint(1990, 2020)})
             .property('ownership_type', 'owned')
            """
            await self.client.execute_query(query)
        
        # Hotel has reviews  
        for review in self.created_entities["reviews"]:
            query = f"""
            g.V('{review['hotel_id']}').addE('HAS_REVIEW').to(g.V('{review['id']}'))
             .property('featured', {random.choice(['true', 'false'])})
            """
            await self.client.execute_query(query)
        
        print("✅ Created relationships")
    
    async def get_loading_summary(self):
        """Get summary of loaded data."""
        stats = await self.client.get_schema_statistics()
        
        print("\n📊 Data Loading Summary:")
        print("=" * 40)
        for vertex_type, count in stats["vertex_counts"].items():
            if count > 0:
                print(f"  {vertex_type}: {count}")
        
        print("\nEdges:")
        for edge_type, count in stats["edge_counts"].items():
            if count > 0:
                print(f"  {edge_type}: {count}")
        
        print(f"\nTotal: {stats['total_vertices']} vertices, {stats['total_edges']} edges")


async def main():
    """Main function to run the data loader."""
    # Initialize settings and client
    settings = get_settings()
    
    gremlin_client = SchemaAwareGremlinClient(
        url=settings.gremlin_url,
        database=settings.gremlin_database,
        graph=settings.gremlin_graph,
        username=settings.gremlin_username,
        password=settings.gremlin_key,
        traversal_source=settings.gremlin_traversal_source
    )
    
    try:
        await gremlin_client.connect()
        
        loader = SampleDataLoader(gremlin_client)
        await loader.load_all_sample_data()
        await loader.get_loading_summary()
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
    finally:
        await gremlin_client.close()


if __name__ == "__main__":
    asyncio.run(main())
