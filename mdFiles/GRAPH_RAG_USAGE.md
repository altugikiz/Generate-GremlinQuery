# Graph RAG Enhanced Usage Guide

## 🎯 Overview

Your Graph RAG system now provides powerful natural language query capabilities that combine:

1. **LLM-powered Query Translation** (Gemini) → Converts natural language to Gremlin queries
2. **Graph Database Search** (Azure Cosmos DB) → Retrieves structured relationship data  
3. **Semantic Vector Search** (Hugging Face + FAISS) → Finds semantically similar content
4. **Intelligent Response Generation** (Gemini) → Synthesizes answers from combined context

## 🚀 Quick Start

### 1. Start the Server
```bash
# Using Python directly
python main.py

# Or using the startup scripts
.\start.ps1        # PowerShell
start.bat          # Batch
python run.py      # Python script
```

### 2. Test the Natural Language Interface
```bash
# Basic ask query
curl -X POST "http://localhost:8000/api/v1/ask" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What are the best hotels in New York?",
       "include_context": true,
       "include_query_translation": true
     }'

# Response will include:
# - Generated answer
# - Original query  
# - Gremlin query (if requested)
# - Execution time
# - Development mode status
```

## 📋 API Endpoints

### Natural Language Query Interface

#### `POST /api/v1/ask`
Ask questions in natural language and get intelligent answers.

**Request:**
```json
{
  "query": "Find hotels with excellent service but poor location",
  "include_context": false,
  "include_query_translation": true
}
```

**Response:**
```json
{
  "answer": "Based on the graph analysis, I found several hotels...",
  "query": "Find hotels with excellent service but poor location",
  "gremlin_query": "g.V().hasLabel('Hotel').where(__.in('HAS_REVIEW')...)",
  "execution_time_ms": 1250.5,
  "development_mode": true
}
```

#### `GET /api/v1/ask/examples`
Get example queries organized by category.

#### `GET /api/v1/ask/suggestions/{query}`
Get suggested related queries based on input.

#### `GET /api/v1/ask/explain/{gremlin_query}`
Get human-readable explanation of a Gremlin query.

## 🎨 Example Queries

### Hotel Search
```
"What are the best hotels in New York?"
"Find luxury hotels with high ratings"
"Show me hotels in Paris with good location scores"
```

### Review Analysis
```
"What are the most common complaints about hotel service?"
"Find reviews that mention cleanliness issues"
"Show me positive reviews about hotel amenities"
```

### Aspect Analysis
```
"Which hotels have the best cleanliness ratings?"
"Find hotels with excellent service but poor location"
"Show me hotels with consistent high ratings across all aspects"
```

### Comparative Analysis
```
"Compare Marriott and Hilton hotels based on guest reviews"
"Which hotel chain has the best customer service?"
"Find hotels that compete with luxury brands"
```

### Trend Analysis
```
"How have hotel ratings changed over the past year?"
"Show me trending issues in recent hotel reviews"
"Find hotels with improving or declining reputation"
```

## 🛠️ Technical Architecture

### Query Processing Flow

```
User Query → LLM Translation → Gremlin Query → Graph Search
     ↓                                              ↓
Semantic Search ← Vector Embeddings         Graph Results
     ↓                                              ↓
Combined Context ← Merge Results → LLM Generation → Answer
```

### Key Components

1. **GraphQueryLLM** (`app/core/graph_query_llm.py`)
   - Translates natural language to Gremlin queries
   - Uses Gemini with domain schema awareness
   - Provides query suggestions and explanations

2. **VectorRetriever** (`app/core/vector_retriever.py`)
   - Hugging Face embeddings (all-MiniLM-L6-v2)
   - FAISS vector index for fast similarity search
   - Metadata filtering and scoring

3. **EnhancedRAGPipeline** (`app/core/rag_pipeline.py`)
   - Orchestrates the entire workflow
   - Combines graph and semantic results
   - Generates intelligent responses

## 🔧 Configuration

Key environment variables in `.env`:

```env
# LLM Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# Hugging Face Configuration  
HUGGINGFACE_EMBEDDING_MODEL=all-MiniLM-L6-v2
HUGGINGFACE_API_TOKEN=your_hf_token

# Vector Store Configuration
VECTOR_STORE_TYPE=huggingface
VECTOR_DB_URI=hf_faiss_index
VECTOR_INDEX=hotel_reviews

# Development Mode
DEVELOPMENT_MODE=true  # Set to false for production
```

## 🧪 Testing

### Automated Testing
```bash
# Run the comprehensive test suite
python test_graph_rag.py

# Test specific components
python test_components.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get examples
curl http://localhost:8000/api/v1/ask/examples

# Test ask endpoint
curl -X POST http://localhost:8000/api/v1/ask \
     -H "Content-Type: application/json" \
     -d '{"query": "Find the best hotels"}'
```

## 🚨 Development Mode

When `DEVELOPMENT_MODE=true`:
- System gracefully handles missing database connections
- Provides informative fallback responses
- Shows what components are available/unavailable
- Includes debugging information in responses

## 📊 Performance Monitoring

### Available Statistics Endpoints
- `GET /api/v1/health` - System health and component status
- `GET /api/v1/statistics` - Pipeline performance metrics
- Response times included in all ask responses

### Key Metrics
- Query translation time
- Graph search execution time  
- Semantic search time
- Total response generation time
- Success/failure rates

## 🎯 Best Practices

### Query Formulation
1. **Be specific**: Mention locations, hotel names, or aspects when relevant
2. **Ask about relationships**: "Hotels with good service but poor location"
3. **Use natural language**: The system translates to technical queries
4. **Request comparisons**: "Compare hotel chains by aspect scores"

### System Optimization
1. **Index documents**: Use `/api/v1/index` to add semantic content
2. **Monitor performance**: Check statistics endpoints regularly
3. **Tune parameters**: Adjust `MAX_GRAPH_RESULTS` and `MAX_SEMANTIC_RESULTS`
4. **Use development mode**: For testing and debugging

## 🔗 Integration Examples

### Python Client
```python
import httpx
import asyncio

async def ask_question(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/ask",
            json={"query": query}
        )
        return response.json()

# Usage
answer = await ask_question("What are the best hotels in Tokyo?")
print(answer["answer"])
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

async function askQuestion(query) {
  const response = await axios.post('http://localhost:8000/api/v1/ask', {
    query: query,
    include_query_translation: true
  });
  return response.data;
}

// Usage
askQuestion("Find hotels with spa amenities")
  .then(result => console.log(result.answer));
```

## 🚀 Production Deployment

### Environment Setup
```env
DEBUG=false
DEVELOPMENT_MODE=false
# Add production database credentials
# Configure appropriate CORS origins
# Set up monitoring and logging
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t graph-rag-api .
docker run -p 8000:8000 --env-file .env graph-rag-api
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Schema Documentation**: http://localhost:8000/api/v1/schema/
- **Health Monitoring**: http://localhost:8000/api/v1/health
- **Query Examples**: http://localhost:8000/api/v1/ask/examples

This enhanced system provides a powerful, production-ready Graph RAG pipeline with natural language capabilities!
