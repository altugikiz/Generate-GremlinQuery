"""
FastAPI Graph RAG Pipeline
A comprehensive backend system implementing Graph RAG using Gremlin queries and vector search.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
from loguru import logger

from app.config.settings import get_settings
from app.api.routes import search, health, schema, ask, analytics, semantic, graph_rag_endpoints
from app.core.schema_gremlin_client import SchemaAwareGremlinClient
from app.core.vector_store import VectorStore
from app.core.rag_pipeline import EnhancedRAGPipeline
from app.core.graph_query_llm import GraphQueryLLM
from app.core.vector_retriever import VectorRetriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.add("logs/app.log", rotation="500 MB", level="INFO")

# Global instances
gremlin_client = None
vector_store = None
rag_pipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global gremlin_client, vector_store, rag_pipeline
    
    settings = get_settings()
    logger.info("Starting Graph RAG Pipeline application...")
    
    try:
        # Initialize Schema-aware Gremlin client
        gremlin_client = SchemaAwareGremlinClient(
            url=settings.gremlin_url,
            database=settings.gremlin_database,
            graph=settings.gremlin_graph,
            username=settings.gremlin_username,
            password=settings.gremlin_key,
            traversal_source=settings.gremlin_traversal_source
        )
        
        # Try to connect, but don't fail in development mode
        try:
            await gremlin_client.connect()
            logger.info("✅ Gremlin client connected successfully")
        except Exception as e:
            if settings.development_mode:
                logger.warning(f"⚠️ Gremlin connection failed (development mode): {e}")
                gremlin_client = None  # Will create a mock client later
            else:
                raise
        
        # Initialize vector store
        vector_store = VectorStore(
            store_type=settings.vector_store_type,
            db_uri=settings.vector_db_uri,
            index_name=settings.vector_index,
            embedding_model=settings.huggingface_embedding_model,
            api_token=settings.huggingface_api_token
        )
        
        try:
            await vector_store.initialize()
            logger.info("✅ Vector store initialized successfully")
        except Exception as e:
            if settings.development_mode:
                logger.warning(f"⚠️ Vector store initialization failed (development mode): {e}")
                vector_store = None  # Will create a mock store later
            else:
                raise
        
        # Initialize Graph Query LLM
        graph_query_llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        
        try:
            await graph_query_llm.initialize()
            logger.info("✅ Graph Query LLM initialized successfully")
        except Exception as e:
            if settings.development_mode:
                logger.warning(f"⚠️ Graph Query LLM initialization failed (development mode): {e}")
                graph_query_llm = None
            else:
                raise
        
        # Initialize Vector Retriever
        vector_retriever = VectorRetriever(
            embedding_model=settings.huggingface_embedding_model,
            store_path=settings.vector_db_uri,
            index_name=settings.vector_index,
            api_token=settings.huggingface_api_token
        )
        
        try:
            await vector_retriever.initialize()
            logger.info("✅ Vector retriever initialized successfully")
        except Exception as e:
            if settings.development_mode:
                logger.warning(f"⚠️ Vector retriever initialization failed (development mode): {e}")
                vector_retriever = None
            else:
                raise
        
        # Initialize Enhanced RAG pipeline
        rag_pipeline = EnhancedRAGPipeline(
            gremlin_client=gremlin_client,
            vector_store=vector_store,
            graph_query_llm=graph_query_llm,
            vector_retriever=vector_retriever,
            model_provider=settings.model_provider,
            gemini_api_key=settings.gemini_api_key,
            gemini_model=settings.gemini_model,
            max_graph_results=settings.max_graph_results,
            max_semantic_results=settings.max_semantic_results,
            development_mode=settings.development_mode
        )
        logger.info("✅ RAG pipeline initialized successfully")
        
        # Store instances in app state
        app.state.gremlin_client = gremlin_client
        app.state.vector_store = vector_store
        app.state.graph_query_llm = graph_query_llm
        app.state.vector_retriever = vector_retriever
        app.state.rag_pipeline = rag_pipeline
        app.state.development_mode = settings.development_mode
        
        if settings.development_mode:
            logger.info("🔧 Running in development mode - some features may be limited")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down Graph RAG Pipeline application...")
        if gremlin_client:
            await gremlin_client.close()
        if vector_store:
            await vector_store.close()
        if vector_retriever:
            await vector_retriever.close()
        logger.info("✅ Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Graph RAG Pipeline API",
        description="A comprehensive backend system implementing Graph RAG using Gremlin queries and vector search",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(search.router, prefix="/api/v1", tags=["Search"])
    app.include_router(schema.router, prefix="/api/v1", tags=["Schema"])
    app.include_router(ask.router, tags=["Ask"])
    app.include_router(analytics.router, tags=["Analytics"])
    app.include_router(semantic.router, tags=["Semantic RAG"])
    app.include_router(graph_rag_endpoints.router, tags=["Graph RAG Enhanced"])
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
