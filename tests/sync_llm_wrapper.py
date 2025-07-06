#!/usr/bin/env python3
"""
Sync Wrapper for Async GraphQueryLLM

This module provides a synchronous wrapper for the async GraphQueryLLM class
that safely handles event loops to avoid "RuntimeError: Cannot run the event loop 
while another loop is running" errors.

Usage:
    from sync_llm_wrapper import create_sync_wrapper
    
    # Create the sync wrapper
    sync_generator = create_sync_wrapper()
    
    # Use in synchronous test functions
    result = sync_generator("Find all hotels")
"""

import asyncio
import sys
import os
import threading
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app.core.graph_query_llm import GraphQueryLLM
from app.config.settings import get_settings


class SafeAsyncWrapper:
    """Safe wrapper that handles async LLM calls in sync context."""
    
    def __init__(self):
        """Initialize the wrapper with GraphQueryLLM."""
        self.llm = None
        self._initialized = False
        self._executor = ThreadPoolExecutor(max_workers=1)
        
    def _initialize_llm(self) -> None:
        """Initialize the GraphQueryLLM in a separate thread."""
        def init_in_thread():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Load environment
                load_dotenv()
                settings = get_settings()
                
                if not settings.gemini_api_key:
                    raise ValueError("GEMINI_API_KEY not found in .env file")
                
                # Initialize the LLM
                self.llm = GraphQueryLLM(
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model
                )
                
                # Initialize in the async context
                result = loop.run_until_complete(self.llm.initialize())
                self._initialized = True
                print(f"✅ GraphQueryLLM initialized: {settings.gemini_model}")
                
            except Exception as e:
                print(f"❌ Failed to initialize GraphQueryLLM: {e}")
                raise
            finally:
                loop.close()
        
        # Run initialization in thread
        future = self._executor.submit(init_in_thread)
        future.result()  # Wait for completion
    
    def generate_gremlin_query(self, natural_language_query: str) -> str:
        """
        Generate Gremlin query from natural language in sync context.
        
        Args:
            natural_language_query: Natural language input
            
        Returns:
            Generated Gremlin query string
        """
        if not self._initialized:
            self._initialize_llm()
        
        def async_call_in_thread():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Call the async method
                result = loop.run_until_complete(
                    self.llm.generate_gremlin_query(natural_language_query)
                )
                return result if result else "g.V().hasLabel('Hotel').limit(10).valueMap()"
                
            except Exception as e:
                return f"ERROR: {str(e)}"
            finally:
                loop.close()
        
        # Execute in thread to avoid event loop conflicts
        future = self._executor.submit(async_call_in_thread)
        return future.result()
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)


def create_sync_wrapper() -> Callable[[str], str]:
    """
    Create a synchronous wrapper function for async GraphQueryLLM.
    
    This function returns a callable that can be used in synchronous test
    contexts without event loop conflicts.
    
    Returns:
        Callable that takes natural language string and returns Gremlin query
        
    Example:
        sync_generator = create_sync_wrapper()
        result = sync_generator("Find all hotels")
    """
    wrapper = SafeAsyncWrapper()
    return wrapper.generate_gremlin_query


def simple_sync_wrapper(natural_language_query: str) -> str:
    """
    Simple one-shot sync wrapper for testing.
    
    Creates a new LLM instance for each call. Less efficient but simpler
    for quick testing or when you only need a few calls.
    
    Args:
        natural_language_query: Natural language input
        
    Returns:
        Generated Gremlin query string
    """
    def run_in_thread():
        # Create new event loop in thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Load environment
            load_dotenv()
            settings = get_settings()
            
            if not settings.gemini_api_key:
                return "ERROR: GEMINI_API_KEY not found"
            
            # Initialize and use LLM
            async def async_generate():
                llm = GraphQueryLLM(
                    api_key=settings.gemini_api_key,
                    model_name=settings.gemini_model
                )
                await llm.initialize()
                return await llm.generate_gremlin_query(natural_language_query)
            
            result = loop.run_until_complete(async_generate())
            return result if result else "g.V().hasLabel('Hotel').limit(10).valueMap()"
            
        except Exception as e:
            return f"ERROR: {str(e)}"
        finally:
            loop.close()
    
    # Use ThreadPoolExecutor for clean thread management
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_in_thread)
        return future.result()


# Alternative approach using threading directly
class ThreadSafeAsyncWrapper:
    """Thread-safe wrapper using direct threading approach."""
    
    def __init__(self):
        self.llm = None
        self._lock = threading.Lock()
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure LLM is initialized in thread-safe manner."""
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:  # Double-check pattern
                return
                
            def init_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    load_dotenv()
                    settings = get_settings()
                    
                    if not settings.gemini_api_key:
                        raise ValueError("GEMINI_API_KEY not found")
                    
                    self.llm = GraphQueryLLM(
                        api_key=settings.gemini_api_key,
                        model_name=settings.gemini_model
                    )
                    
                    loop.run_until_complete(self.llm.initialize())
                    
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize LLM: {e}")
                finally:
                    loop.close()
            
            # Run in separate thread
            thread = threading.Thread(target=init_thread)
            thread.start()
            thread.join()
            
            self._initialized = True
    
    def generate_sync(self, query: str) -> str:
        """Generate query synchronously."""
        self._ensure_initialized()
        
        result_container = [None]
        exception_container = [None]
        
        def async_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.llm.generate_gremlin_query(query)
                )
                result_container[0] = result
                
            except Exception as e:
                exception_container[0] = e
            finally:
                loop.close()
        
        thread = threading.Thread(target=async_thread)
        thread.start()
        thread.join()
        
        if exception_container[0]:
            return f"ERROR: {str(exception_container[0])}"
        
        return result_container[0] or "g.V().hasLabel('Hotel').limit(10).valueMap()"


def demo_sync_wrapper():
    """Demonstrate the sync wrapper usage."""
    print("🧪 SYNC WRAPPER DEMO")
    print("=" * 50)
    
    # Method 1: Reusable wrapper (recommended for multiple calls)
    print("\n1️⃣ Using reusable sync wrapper:")
    sync_generator = create_sync_wrapper()
    
    test_queries = [
        "Find all hotels",
        "Show VIP guests", 
        "Türkçe yazılmış temizlik şikayetlerini göster"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: {query}")
        result = sync_generator(query)
        print(f"    Result: {result}")
    
    # Method 2: Simple one-shot wrapper
    print("\n\n2️⃣ Using simple one-shot wrapper:")
    result = simple_sync_wrapper("Find maintenance issues")
    print(f"Result: {result}")
    
    # Method 3: Thread-safe wrapper
    print("\n\n3️⃣ Using thread-safe wrapper:")
    wrapper = ThreadSafeAsyncWrapper()
    result = wrapper.generate_sync("Show me recent reviews")
    print(f"Result: {result}")


def sync_wrapper(prompt: str) -> str:
    """
    Sync wrapper function that safely calls async generate_gremlin_query.
    
    This function provides a clean interface for synchronous test loops
    that need to call the async GraphQueryLLM.generate_gremlin_query method.
    
    Args:
        prompt: Natural language query string
        
    Returns:
        Generated Gremlin query string
        
    Example:
        # Use in synchronous test loops
        result = sync_wrapper("Find all hotels")
        print(f"Generated: {result}")
    """
    # Use the existing create_sync_wrapper function
    sync_generator = create_sync_wrapper()
    return sync_generator(prompt)


if __name__ == "__main__":
    demo_sync_wrapper()
