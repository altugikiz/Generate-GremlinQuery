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
from app.core.sync_gremlin_client import SyncGremlinClient
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
    """
    Application lifespan manager for startup and shutdown events.
    
    This function ensures robust initialization of critical services:
    - Fails fast if essential services cannot be initialized
    - Provides clear error messages and logging
    - Prevents silent failures that lead to runtime errors
    - Follows Azure best practices for service initialization
    """
    global gremlin_client, vector_store, rag_pipeline
    
    settings = get_settings()
    logger.info("🚀 Starting Graph RAG Pipeline application...")
    
    # Track initialized components for cleanup
    initialized_components = []
    
    try:
        # === CRITICAL SERVICE INITIALIZATION ===
        # These services are essential - startup should fail if they're unavailable
        
        # 1. Initialize Sync Gremlin client
        logger.info("🔌 Initializing Sync Gremlin client...")
        gremlin_client = SyncGremlinClient(
            url=settings.gremlin_url,
            database=settings.gremlin_database,
            graph=settings.gremlin_graph,
            username=settings.gremlin_username,
            password=settings.gremlin_key,
            traversal_source=settings.gremlin_traversal_source
        )
        
        # Test connection - PRODUCTION MODE: FAIL FAST
        try:
            await gremlin_client.connect()
            logger.info("✅ Gremlin client connected successfully")
            initialized_components.append(("gremlin_client", gremlin_client))
        except Exception as e:
            logger.error(f"❌ PRODUCTION MODE: Gremlin connection REQUIRED but failed: {e}")
            logger.error("   📋 Check: GREMLIN_URL, GREMLIN_KEY, network connectivity")
            logger.error("   💡 Suggestion: Verify Cosmos DB Gremlin API is accessible")
            logger.error("   🚨 PRODUCTION MODE: Application startup will FAIL")
            # In production mode, ALWAYS fail fast - no development mode fallback allowed
            raise RuntimeError(f"PRODUCTION MODE: Critical service failure - Gremlin connection failed: {e}")
        
        # 2. Initialize Graph Query LLM (critical for graph operations)
        logger.info("🤖 Initializing Graph Query LLM...")
        graph_query_llm = GraphQueryLLM(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model
        )
        
        try:
            await graph_query_llm.initialize()
            logger.info("✅ Graph Query LLM initialized successfully")
            initialized_components.append(("graph_query_llm", graph_query_llm))
        except Exception as e:
            logger.error(f"❌ PRODUCTION MODE: Graph Query LLM initialization REQUIRED but failed: {e}")
            logger.error("   📋 Check: GEMINI_API_KEY, GEMINI_MODEL, API quota")
            logger.error("   💡 Suggestion: Verify Gemini API access and model availability")
            logger.error("   � PRODUCTION MODE: Application startup will FAIL")
            raise RuntimeError(f"PRODUCTION MODE: Critical service failure - Graph Query LLM initialization failed: {e}")
        
        # === REQUIRED SERVICE INITIALIZATION ===
        # In production mode, ALL services are required
        
        # 3. Initialize vector store (REQUIRED in production mode)
        logger.info("📊 Initializing Vector Store...")
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
            initialized_components.append(("vector_store", vector_store))
        except Exception as e:
            logger.error(f"❌ PRODUCTION MODE: Vector store initialization REQUIRED but failed: {e}")
            logger.error("   � Check: HUGGINGFACE_API_TOKEN, vector store files")
            logger.error("   � PRODUCTION MODE: Application startup will FAIL")
            raise RuntimeError(f"PRODUCTION MODE: Vector store initialization failed: {e}")
        
        # 4. Initialize Vector Retriever (REQUIRED in production mode)
        logger.info("🔍 Initializing Vector Retriever...")
        vector_retriever = VectorRetriever(
            embedding_model=settings.huggingface_embedding_model,
            store_path=settings.vector_db_uri,
            index_name=settings.vector_index,
            api_token=settings.huggingface_api_token
        )
        
        try:
            await vector_retriever.initialize()
            logger.info("✅ Vector retriever initialized successfully")
            initialized_components.append(("vector_retriever", vector_retriever))
        except Exception as e:
            logger.error(f"❌ PRODUCTION MODE: Vector retriever initialization REQUIRED but failed: {e}")
            logger.error("   � PRODUCTION MODE: Application startup will FAIL")
            raise RuntimeError(f"PRODUCTION MODE: Vector retriever initialization failed: {e}")
        
        # 5. Initialize Enhanced RAG pipeline
        logger.info("🔗 Initializing RAG Pipeline...")
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
            development_mode=False  # PRODUCTION MODE: Always False, no development fallbacks
        )
        logger.info("✅ RAG pipeline initialized successfully - PRODUCTION MODE")
        initialized_components.append(("rag_pipeline", rag_pipeline))
        
        # Store instances in app state
        app.state.gremlin_client = gremlin_client
        app.state.vector_store = vector_store
        app.state.graph_query_llm = graph_query_llm
        app.state.vector_retriever = vector_retriever
        app.state.rag_pipeline = rag_pipeline
        app.state.development_mode = False  # PRODUCTION MODE: Always False
        
        # Log initialization summary
        logger.info("🎯 PRODUCTION MODE: All critical services initialized successfully")
        
        all_services = ["gremlin_client", "graph_query_llm", "vector_store", "vector_retriever", "rag_pipeline"]
        initialized_service_names = [name for name, _ in initialized_components]
        
        logger.info(f"✅ All services operational: {', '.join(initialized_service_names)}")
        logger.info("🚀 PRODUCTION MODE: Real Gremlin execution enabled - No development fallbacks")
        
        logger.info("🎉 PRODUCTION MODE: Application startup completed successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"💥 STARTUP FAILED: {e}")
        logger.error("🔧 Application will not start - fix the above errors and restart")
        
        # Clean up any partially initialized components
        for name, component in initialized_components:
            try:
                if hasattr(component, 'close'):
                    await component.close()
                    logger.info(f"🧹 Cleaned up {name}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error cleaning up {name}: {cleanup_error}")
        
        # Re-raise to prevent application from starting
        raise
        
    finally:
        # === GRACEFUL SHUTDOWN ===
        logger.info("🔄 Shutting down Graph RAG Pipeline application...")
        
        # Clean up in reverse order of initialization (using locals to avoid UnboundLocalError)
        cleanup_tasks = []
        for name, var in [
            ("rag_pipeline", locals().get("rag_pipeline")),
            ("vector_retriever", locals().get("vector_retriever")),
            ("vector_store", locals().get("vector_store")),
            ("graph_query_llm", locals().get("graph_query_llm")),
            ("gremlin_client", locals().get("gremlin_client"))
        ]:
            if var is not None:
                cleanup_tasks.append((name, var))
        
        for name, component in cleanup_tasks:
            if component and hasattr(component, 'close'):
                try:
                    await component.close()
                    logger.info(f"✅ {name} shutdown complete")
                except Exception as e:
                    logger.warning(f"⚠️ Error during {name} shutdown: {e}")
        
        logger.info("👋 Application shutdown complete")


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
