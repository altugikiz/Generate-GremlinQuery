# Graph RAG Pipeline API

A comprehensive FastAPI backend system implementing Graph RAG (Retrieval-Augmented Generation) using Gremlin queries and vector search for enhanced information retrieval and generation.

## 🌟 Features

- **Graph Database Integration**: Connect to Azure Cosmos DB Gremlin API for graph-based queries
- **Vector Search**: Semantic search using Hugging Face embeddings and FAISS index
- **Hybrid Search**: Combine graph and semantic search for enhanced results
- **LLM Integration**: Generate responses using Google Gemini AI
- **RESTful API**: FastAPI-based endpoints with automatic documentation
- **Health Monitoring**: Comprehensive health checks and performance metrics
- **Modular Design**: Clean, extensible architecture with proper separation of concerns

## 🏗️ Architecture

```
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── health.py      # Health check endpoints
│   │       └── search.py      # Search and retrieval endpoints
│   ├── core/
│   │   ├── gremlin_client.py  # Gremlin database client
│   │   ├── vector_store.py    # Vector store implementation
│   │   └── rag_pipeline.py    # RAG pipeline orchestration
│   ├── models/
│   │   └── dto.py             # Data Transfer Objects
│   └── config/
│       └── settings.py        # Configuration management
├── logs/                      # Application logs
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Azure Cosmos DB with Gremlin API
- Hugging Face API token
- Google Gemini API key

### Installation

1. **Clone or extract the project**:
   ```bash
   cd newGraph
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   The `.env` file is already configured with your credentials.

4. **Start the server**:

   **Option 1 - Python script:**
   ```bash
   python run.py
   ```

   **Option 2 - PowerShell (Windows):**
   ```powershell
   .\start.ps1
   ```

   **Option 3 - Batch file (Windows):**
   ```cmd
   start.bat
   ```

   **Option 4 - Direct command:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**:
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Documentation**: http://localhost:8000/redoc
   - **Health Check**: http://localhost:8000/api/v1/health

## 📖 API Endpoints

### Health Endpoints

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health information
- `GET /api/v1/health/readiness` - Kubernetes-style readiness check
- `GET /api/v1/health/liveness` - Kubernetes-style liveness check

### Search Endpoints

- `POST /api/v1/search` - Hybrid search (graph + semantic)
- `GET /api/v1/search/simple` - Simple search with query parameters
- `POST /api/v1/index` - Index documents for semantic search
- `GET /api/v1/graph/nodes/{node_id}/relationships` - Get node relationships
- `GET /api/v1/graph/search` - Search graph by properties
- `GET /api/v1/semantic/search` - Semantic search only
- `GET /api/v1/statistics` - Pipeline performance statistics
- `DELETE /api/v1/index/clear` - Clear vector index

## 🔧 Configuration

All configuration is managed through environment variables in the `.env` file:

### LLM Configuration
```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
LLM_MODEL_NAME=gemini-2.0-flash
MODEL_PROVIDER=gemini
```

### Gremlin Database Configuration
```env
GREMLIN_URL=wss://your-cosmos-account.gremlin.cosmos.azure.com:443/
GREMLIN_DATABASE=your_database_name
GREMLIN_GRAPH=your_graph_name
GREMLIN_KEY=your_cosmos_db_key
GREMLIN_USERNAME=your_cosmos_account_name
GREMLIN_TRAVERSAL_SOURCE=g
```

### Vector Store Configuration
```env
HUGGINGFACE_EMBEDDING_MODEL=all-MiniLM-L6-v2
HUGGINGFACE_API_TOKEN=your_huggingface_token
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=huggingface
VECTOR_DB_URI=hf_faiss_index
VECTOR_INDEX=hotel_reviews
```

### Pipeline Configuration
```env
MAX_GRAPH_RESULTS=10
MAX_SEMANTIC_RESULTS=5
```

## 💡 Usage Examples

### 1. Hybrid Search
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "best hotels in New York",
       "search_type": "hybrid",
       "max_results": 10
     }'
```

### 2. Simple Search
```bash
curl "http://localhost:8000/api/v1/search/simple?q=luxury+hotels&search_type=hybrid&max_results=5"
```

### 3. Index Documents
```bash
curl -X POST "http://localhost:8000/api/v1/index" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": [
         {
           "content": "This hotel offers excellent amenities...",
           "metadata": {"hotel_id": "hotel_123", "rating": 5}
         }
       ]
     }'
```

### 4. Graph Search
```bash
curl "http://localhost:8000/api/v1/graph/search?label=Hotel&property_name=name&property_value=Grand+Hotel&limit=10"
```

### 5. Health Check
```bash
curl "http://localhost:8000/api/v1/health"
```

## 🔍 Search Types

1. **Graph Search** (`"graph"`): Searches the graph database using Gremlin queries
2. **Semantic Search** (`"semantic"`): Searches using vector embeddings for semantic similarity
3. **Hybrid Search** (`"hybrid"`): Combines both graph and semantic search results

## 🧪 Testing

Test the API endpoints using the interactive documentation at `http://localhost:8000/docs` or use curl/Postman with the examples above.

## 📊 Monitoring

The application provides comprehensive monitoring through:

- **Health endpoints** for service status
- **Performance metrics** for search operations
- **Statistics endpoints** for usage analytics
- **Structured logging** with Loguru

## 🛠️ Development

### Project Structure
- **Modular Design**: Clean separation between API, core logic, and configuration
- **Type Safety**: Full type hints with Pydantic models
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Async Support**: Fully asynchronous for high performance
- **Dependency Injection**: FastAPI's dependency system for clean architecture

### Adding New Features
1. Define DTOs in `app/models/dto.py`
2. Implement business logic in `app/core/`
3. Create API endpoints in `app/api/routes/`
4. Update configuration in `app/config/settings.py`

## 📝 Logging

Logs are written to:
- Console (for development)
- `logs/app.log` (rotating file)

## 🔒 Security Considerations

- Configure CORS appropriately for production
- Use environment variables for sensitive configuration
- Implement authentication/authorization as needed
- Validate input data using Pydantic models

## 🚀 Production Deployment

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Configure appropriate CORS origins
3. Use a production WSGI server (Gunicorn)
4. Set up proper logging and monitoring
5. Secure environment variable management

## 📚 Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **Gremlin Python**: Graph database client
- **Sentence Transformers**: Text embeddings
- **FAISS**: Vector similarity search
- **Google GenerativeAI**: LLM integration
- **Loguru**: Structured logging

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Include proper error handling
4. Update documentation for new features
5. Test endpoints thoroughly

## 📄 License

This project is proprietary. All rights reserved.

---

**Happy coding! 🎉**

For questions or support, please check the health endpoints and logs for debugging information.
