"""
Configuration settings module.
Loads and validates environment variables using Pydantic.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini/LLM Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    llm_model_name: str = Field(default="gemini-2.0-flash", env="LLM_MODEL_NAME")
    model_provider: str = Field(default="gemini", env="MODEL_PROVIDER")
    
    # Azure Gremlin Configuration
    gremlin_url: str = Field(..., env="GREMLIN_URL")
    gremlin_database: str = Field(..., env="GREMLIN_DATABASE")
    gremlin_graph: str = Field(..., env="GREMLIN_GRAPH")
    gremlin_key: str = Field(..., env="GREMLIN_KEY")
    gremlin_username: str = Field(..., env="GREMLIN_USERNAME")
    gremlin_traversal_source: str = Field(default="g", env="GREMLIN_TRAVERSAL_SOURCE")
    
    # Hugging Face Embeddings Configuration
    huggingface_embedding_model: str = Field(default="all-MiniLM-L6-v2", env="HUGGINGFACE_EMBEDDING_MODEL")
    huggingface_api_token: str = Field(..., env="HUGGINGFACE_API_TOKEN")
    embedding_model_name: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL_NAME")
    
    # Vector Store Configuration
    vector_store_type: str = Field(default="huggingface", env="VECTOR_STORE_TYPE")
    vector_db_uri: str = Field(default="hf_faiss_index", env="VECTOR_DB_URI")
    vector_index: str = Field(default="hotel_reviews", env="VECTOR_INDEX")
    
    # RAG Pipeline Configuration
    max_graph_results: int = Field(default=10, env="MAX_GRAPH_RESULTS")
    max_semantic_results: int = Field(default=5, env="MAX_SEMANTIC_RESULTS")
    
    # Application Configuration
    debug: bool = Field(default=False, env="DEBUG")
    development_mode: bool = Field(default=False, env="DEVELOPMENT_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Connection Timeouts and Retries
    gremlin_timeout: int = Field(default=30, env="GREMLIN_TIMEOUT")
    gremlin_max_retries: int = Field(default=3, env="GREMLIN_MAX_RETRIES")
    vector_search_timeout: int = Field(default=30, env="VECTOR_SEARCH_TIMEOUT")
    
    @field_validator("gremlin_url")
    @classmethod
    def validate_gremlin_url(cls, v):
        """Validate Gremlin URL format."""
        if not v.startswith(("ws://", "wss://")):
            raise ValueError("Gremlin URL must start with ws:// or wss://")
        return v
    
    @field_validator("max_graph_results", "max_semantic_results")
    @classmethod
    def validate_positive_integers(cls, v):
        """Validate that result limits are positive integers."""
        if v <= 0:
            raise ValueError("Result limits must be positive integers")
        return v
    
    @field_validator("model_provider")
    @classmethod
    def validate_model_provider(cls, v):
        """Validate model provider."""
        allowed_providers = ["gemini", "openai", "huggingface"]
        if v not in allowed_providers:
            raise ValueError(f"Model provider must be one of: {allowed_providers}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        protected_namespaces = ('settings_',)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses LRU cache to avoid reloading settings on every request.
    """
    return Settings()
