"""
Health check endpoints for monitoring system status.
"""

from fastapi import APIRouter, Depends, Request
from datetime import datetime
import time
import psutil
import os
from typing import Dict, Any

from app.models.dto import HealthResponse
from app.core.gremlin_client import GremlinClient
from app.core.vector_store import VectorStore
from app.core.rag_pipeline import RAGPipeline

router = APIRouter()

# Application start time for uptime calculation
_start_time = time.time()


def get_gremlin_client(request: Request) -> GremlinClient:
    """Dependency to get Gremlin client from app state."""
    return getattr(request.app.state, 'gremlin_client', None)


def get_vector_store(request: Request) -> VectorStore:
    """Dependency to get vector store from app state."""
    return getattr(request.app.state, 'vector_store', None)


def get_rag_pipeline(request: Request) -> RAGPipeline:
    """Dependency to get RAG pipeline from app state."""
    return getattr(request.app.state, 'rag_pipeline', None)


def get_development_mode(request: Request) -> bool:
    """Dependency to get development mode status."""
    return getattr(request.app.state, 'development_mode', False)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    gremlin_client: GremlinClient = Depends(get_gremlin_client),
    vector_store: VectorStore = Depends(get_vector_store),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
    development_mode: bool = Depends(get_development_mode)
):
    """
    Comprehensive health check endpoint.
    
    Returns the status of all system components:
    - Overall system status
    - Individual service statuses
    - System metrics
    - Application version and uptime
    """
    components = {}
    overall_status = "healthy"
    
    # In development mode, adjust expectations
    if development_mode:
        overall_status = "development"
    
    try:
        # Check Gremlin connection
        if gremlin_client and gremlin_client.is_connected:
            components["gremlin"] = "healthy"
        elif development_mode:
            components["gremlin"] = "unavailable_dev_mode"
        else:
            components["gremlin"] = "unhealthy"
            if not development_mode:
                overall_status = "degraded"
    except Exception:
        components["gremlin"] = "error"
        if not development_mode:
            overall_status = "unhealthy"
    
    try:
        # Check vector store
        if vector_store and hasattr(vector_store, '_is_initialized') and vector_store._is_initialized:
            components["vector_store"] = "healthy"
        elif development_mode:
            components["vector_store"] = "unavailable_dev_mode"
        else:
            components["vector_store"] = "unhealthy"
            if not development_mode:
                overall_status = "degraded"
    except Exception:
        components["vector_store"] = "error"
        if not development_mode:
            overall_status = "unhealthy"
    
    try:
        # Check RAG pipeline
        if rag_pipeline:
            components["rag_pipeline"] = "healthy"
        else:
            components["rag_pipeline"] = "unhealthy"
            if not development_mode:
                overall_status = "degraded"
    except Exception:
        components["rag_pipeline"] = "error"
        if not development_mode:
            overall_status = "unhealthy"
    
    # Calculate uptime
    uptime_seconds = time.time() - _start_time
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        components=components,
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        development_mode=development_mode
    )


@router.get("/health/detailed")
async def detailed_health_check(
    gremlin_client: GremlinClient = Depends(get_gremlin_client),
    vector_store: VectorStore = Depends(get_vector_store),
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
) -> Dict[str, Any]:
    """
    Detailed health check with performance metrics and statistics.
    
    Returns comprehensive information about:
    - Service statuses and connection details
    - Performance metrics and statistics
    - System resource usage
    - Configuration information
    """
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - _start_time,
        "services": {},
        "system": {},
        "performance": {}
    }
    
    # Gremlin client health
    try:
        if gremlin_client:
            gremlin_stats = await gremlin_client.get_statistics()
            health_data["services"]["gremlin"] = {
                "status": "connected" if gremlin_client.is_connected else "disconnected",
                "statistics": gremlin_stats
            }
        else:
            health_data["services"]["gremlin"] = {"status": "not_initialized"}
    except Exception as e:
        health_data["services"]["gremlin"] = {"status": "error", "error": str(e)}
    
    # Vector store health
    try:
        if vector_store:
            vector_stats = await vector_store.get_statistics()
            health_data["services"]["vector_store"] = {
                "status": "ready" if vector_store.is_initialized else "not_ready",
                "statistics": vector_stats
            }
        else:
            health_data["services"]["vector_store"] = {"status": "not_initialized"}
    except Exception as e:
        health_data["services"]["vector_store"] = {"status": "error", "error": str(e)}
    
    # RAG pipeline health
    try:
        if rag_pipeline:
            pipeline_stats = await rag_pipeline.get_statistics()
            health_data["services"]["rag_pipeline"] = {
                "status": "ready",
                "statistics": pipeline_stats
            }
        else:
            health_data["services"]["rag_pipeline"] = {"status": "not_initialized"}
    except Exception as e:
        health_data["services"]["rag_pipeline"] = {"status": "error", "error": str(e)}
    
    # System metrics
    try:
        process = psutil.Process(os.getpid())
        health_data["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "process_memory_mb": process.memory_info().rss / 1024 / 1024,
            "process_cpu_percent": process.cpu_percent(),
            "disk_usage_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
        }
    except Exception as e:
        health_data["system"] = {"error": str(e)}
    
    return health_data


@router.get("/health/readiness")
async def readiness_check(
    gremlin_client: GremlinClient = Depends(get_gremlin_client),
    vector_store: VectorStore = Depends(get_vector_store)
) -> Dict[str, Any]:
    """
    Kubernetes-style readiness check.
    
    Returns 200 if all critical services are ready to serve requests,
    otherwise returns 503.
    """
    ready = True
    services = {}
    
    # Check critical dependencies
    if not gremlin_client or not gremlin_client.is_connected:
        ready = False
        services["gremlin"] = "not_ready"
    else:
        services["gremlin"] = "ready"
    
    if not vector_store or not vector_store.is_initialized:
        ready = False
        services["vector_store"] = "not_ready"
    else:
        services["vector_store"] = "ready"
    
    return {
        "ready": ready,
        "services": services,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness check.
    
    Returns 200 if the application is running and responsive.
    This is a lightweight check that doesn't test external dependencies.
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - _start_time
    }
