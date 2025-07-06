# Complete FastAPI Graph RAG Backend

A comprehensive FastAPI backend system implementing both traditional analytics and intelligent Graph RAG capabilities for hotel reviews.

## 🏗️ Architecture Overview

The system is organized into two logical sections:

### Section 1: Traditional Analytics (`/api/v1/average` & `/api/v1/reviews`)
REST-based classical analytics endpoints for dashboard integration and traditional data analysis.

### Section 2: Semantic RAG Intelligence (`/api/v1/semantic`)
AI-powered endpoints using LLM + Gremlin + Vector Search for intelligent query processing.

## 📋 Complete API Reference

### 🏢 Traditional Analytics Endpoints

#### Group-Level Analytics
- **`GET /api/v1/average/groups`** - Hotel group statistics and averages
- **`GET /api/v1/average/hotels`** - Hotel-level statistics with filtering
- **`GET /api/v1/average/{hotel_name}`** - Detailed hotel analysis

#### Hotel-Specific Analytics  
- **`GET /api/v1/average/{hotel_id}/languages`** - Language distribution per hotel
- **`GET /api/v1/average/{hotel_name}/sources`** - Review source breakdown
- **`GET /api/v1/average/{hotel_name}/accommodations`** - Room type metrics
- **`GET /api/v1/average/{hotel_name}/aspects`** - Aspect score breakdown

#### Review Data Access
- **`GET /api/v1/reviews`** - Query reviews with comprehensive filtering
  - Filter by: language, source, aspect, sentiment, hotel, date range, rating

### 🤖 Semantic RAG Intelligence Endpoints

#### Natural Language Processing
- **`POST /api/v1/semantic/ask`** - Full RAG pipeline with natural language queries
- **`POST /api/v1/semantic/filter`** - Convert structured filters to Gremlin queries
- **`POST /api/v1/semantic/gremlin`** - Natural language to Gremlin translation
- **`POST /api/v1/semantic/vector`** - Pure semantic vector search
- **`GET /api/v1/semantic/models`** - Active model information and stats

### ❤️ System Health & Monitoring
- **`GET /api/v1/health`** - Basic system health check
- **`GET /api/v1/health/detailed`** - Comprehensive system diagnostics
- **`GET /api/v1/statistics`** - Performance metrics and usage statistics

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment variables
cp .env.example .env

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server
```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access Documentation
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 💡 Usage Examples

### Traditional Analytics Examples

#### Get Hotel Group Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/average/groups"
```

#### Get Top Hotels with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/average/hotels?limit=10&min_rating=8.0&group_name=Marriott"
```

#### Query Reviews with Multiple Filters
```bash
curl -X GET "http://localhost:8000/api/v1/reviews?language=en&sentiment=negative&aspect=cleanliness&limit=50"
```

### Semantic RAG Examples

#### Ask Natural Language Questions
```bash
curl -X POST "http://localhost:8000/api/v1/semantic/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Why are guests complaining about room cleanliness in luxury hotels?",
       "filters": {
         "hotel_type": "luxury",
         "aspect": "cleanliness",
         "sentiment": "negative"
       },
       "include_gremlin_query": true,
       "include_semantic_chunks": true
     }'
```

#### Convert Structured Filters to Gremlin
```bash
curl -X POST "http://localhost:8000/api/v1/semantic/filter" \
     -H "Content-Type: application/json" \
     -d '{
       "filters": {
         "hotel_group": "Marriott",
         "aspect_score": {"service": ">= 8", "location": ">= 7"},
         "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
       },
       "summarize_with_llm": true,
       "max_results": 20
     }'
```

#### Generate Gremlin from Natural Language
```bash
curl -X POST "http://localhost:8000/api/v1/semantic/gremlin" \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Find hotels with excellent service but poor location ratings",
       "include_explanation": true
     }'
```

#### Perform Semantic Vector Search
```bash
curl -X POST "http://localhost:8000/api/v1/semantic/vector" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "hotel room maintenance issues bathroom problems",
       "top_k": 15,
       "min_score": 0.7
     }'
```

## 🔧 Configuration

### Required Environment Variables
```env
# Application
DEBUG=true
DEVELOPMENT_MODE=true

# Gemini LLM
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# Hugging Face Embeddings
HUGGINGFACE_API_TOKEN=your_hf_token
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Azure Cosmos DB Gremlin
GREMLIN_URL=wss://your-account.gremlin.cosmos.azure.com:443/
GREMLIN_DATABASE=reviewdb
GREMLIN_GRAPH=review6
GREMLIN_KEY=your_gremlin_key
GREMLIN_USERNAME=your_account_name

# Vector Store
VECTOR_STORE_TYPE=huggingface
VECTOR_DB_URI=hf_faiss_index
```

## 🧪 Testing

### Run Comprehensive Tests
```bash
# Test all endpoints
python test_complete_backend.py

# Test Gremlin query generation
python test_gremlin_generation.py

# Test individual components
python test_components.py
```

### Example Test Results
```
🚀 COMPREHENSIVE FASTAPI BACKEND TEST SUITE
===============================================
📊 Overall Results:
   • Total Tests: 16
   • Successful: 14  
   • Failed: 2
   • Success Rate: 87.5%
   • Total Execution Time: 45.32 seconds

📈 Section Breakdown:
   ✅ Health & Status: 3/3 (100.0%)
   ✅ Traditional Analytics: 6/8 (75.0%)
   ✅ Semantic RAG: 5/5 (100.0%)
```

## 🏗️ Architecture Details

### Technology Stack
- **Web Framework**: FastAPI with async support
- **Graph Database**: Azure Cosmos DB Gremlin API
- **Vector Database**: FAISS with Hugging Face embeddings
- **LLM Provider**: Google Gemini Pro
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2

### Domain Schema
```
Hotels ←→ HotelGroups
   ↓
Reviews ←→ Languages, Sources
   ↓
Analysis ←→ Aspects (cleanliness, service, location, etc.)
   ↓
AccommodationTypes ←→ Amenities
```

### Request Flow for Semantic Ask
```
1. Natural Language Query → LLM Translation → Gremlin Query
2. Execute Graph Search → Retrieve structured data
3. Semantic Vector Search → Retrieve relevant text chunks  
4. Context Fusion → Combine graph + semantic results
5. LLM Generation → Synthesize intelligent answer
```

## 📊 Response Formats

### Traditional Analytics Response
```json
{
  "hotel_id": "hotel_001",
  "hotel_name": "Grand Plaza Hotel",
  "total_reviews": 1247,
  "average_rating": 8.3,
  "aspect_breakdown": [
    {
      "aspect_name": "service",
      "average_score": 8.7,
      "review_count": 980,
      "positive_percentage": 85.2,
      "negative_percentage": 7.1,
      "trending": "up"
    }
  ]
}
```

### Semantic RAG Response
```json
{
  "answer": "Guests are complaining about room cleanliness primarily due to...",
  "query": "Why are guests complaining about room cleanliness?",
  "gremlin_query": "g.V().hasLabel('Hotel').where(...)",
  "semantic_chunks": [
    {
      "text": "The bathroom was not properly cleaned...",
      "similarity_score": 0.89,
      "metadata": {"hotel": "Grand Plaza", "date": "2024-01-15"}
    }
  ],
  "execution_time_ms": 1450.5,
  "component_times": {
    "query_translation": 234.1,
    "graph_search": 456.2, 
    "semantic_search": 398.7,
    "response_generation": 361.5
  }
}
```

## 🎯 Use Cases

### Dashboard Analytics
- Hotel performance monitoring
- Review sentiment analysis
- Operational insights and KPIs
- Competitive benchmarking

### Intelligent Query Interface
- Natural language business questions
- Automated insight generation
- Contextual recommendations
- Trend analysis and forecasting

### API Integration
- Customer service chatbots
- Business intelligence tools
- Review management systems
- Hospitality management platforms

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t graph-rag-backend .

# Run container
docker run -p 8000:8000 --env-file .env graph-rag-backend
```

### Performance Optimization
- Configure connection pooling
- Enable response caching for analytics
- Set up load balancing
- Monitor with APM tools

### Security Considerations
- Configure CORS for production domains
- Implement rate limiting
- Add authentication/authorization
- Secure environment variable management

## 📚 Documentation

- **API Reference**: Available at `/docs` when server is running
- **Schema Documentation**: Detailed graph schema in `app/core/domain_schema.py`
- **Development Guide**: See individual module docstrings
- **Testing Guide**: Comprehensive test examples in `test_*.py` files

## 🤝 Contributing

1. Follow the modular architecture patterns
2. Add comprehensive error handling
3. Include type hints for all functions
4. Update tests for new features
5. Document API changes in README

## 🎉 Features Summary

✅ **Complete Analytics Suite** - Traditional REST endpoints for all hotel metrics  
✅ **Intelligent RAG Pipeline** - Natural language to insights transformation  
✅ **Hybrid Search System** - Graph + semantic search combination  
✅ **Production Ready** - Health checks, monitoring, error handling  
✅ **Comprehensive Testing** - Automated test suite for all endpoints  
✅ **Developer Friendly** - Interactive docs, clear architecture, type safety  

This backend provides everything needed for both dashboard analytics and AI-powered smart queries in the hospitality domain!
