"""
Minimal FastAPI server for testing Turkish query functionality
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Graph RAG Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    gremlin_query: str = None
    execution_time_ms: float = 0
    development_mode: bool = True

@app.get("/api/v1/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "development_mode": True,
        "components": {
            "server": "running",
            "turkish_support": "enabled"
        }
    }

@app.post("/api/v1/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Test endpoint for processing queries"""
    logger.info(f"Received query: {request.query}")
    
    # Simple language detection
    turkish_keywords = ["otel", "temizlik", "göster", "olan", "düşük", "yüksek", "en", "iyi"]
    is_turkish = any(keyword in request.query.lower() for keyword in turkish_keywords)
    
    # Mock Gremlin query generation
    if is_turkish:
        gremlin_query = "g.V().hasLabel('hotel').has('cleanliness_rating', lt(3.0)).valueMap()"
        answer = f"Turkish query detected: '{request.query}'. Generated Gremlin query for low cleanliness hotels."
    else:
        gremlin_query = "g.V().hasLabel('hotel').valueMap()"
        answer = f"English query processed: '{request.query}'. Generated basic hotel query."
    
    return QueryResponse(
        query=request.query,
        answer=answer,
        gremlin_query=gremlin_query,
        execution_time_ms=100,
        development_mode=True
    )

if __name__ == "__main__":
    logger.info("Starting minimal test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
