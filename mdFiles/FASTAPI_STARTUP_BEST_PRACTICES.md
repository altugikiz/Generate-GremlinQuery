# FastAPI Startup Error Handling Best Practices

## Overview

This document outlines the improvements made to the FastAPI application startup process to ensure robust error handling, particularly for critical services like the Gremlin database connection.

## Problem Statement

The original implementation had several critical issues:

1. **Silent Failures**: Connection errors were swallowed in development mode, leading to runtime failures
2. **Poor Error Visibility**: No clear indication of what failed during startup
3. **Inconsistent State**: Global variables set to `None` when services failed
4. **Hard to Debug**: Limited information about why services couldn't initialize
5. **No Fail-Fast Pattern**: Application would start even with critical services unavailable

## Solution Architecture

### 1. Service Classification

Services are now classified into two categories:

#### Critical Services (Must Work)
- **Gremlin Client**: Essential for graph operations
- **Graph Query LLM**: Required for query generation

These services **must** initialize successfully or the application **will not start**.

#### Optional Services (Graceful Degradation)
- **Vector Store**: Can be unavailable in development mode
- **Vector Retriever**: Depends on vector store

These services can fail in development mode, but the application will log warnings and continue with limited functionality.

### 2. Fail-Fast Pattern

```python
# Always test critical service connections immediately
try:
    await gremlin_client.connect()
    logger.info("✅ Gremlin client connected successfully")
except Exception as e:
    logger.error(f"❌ Gremlin connection failed: {e}")
    # Always re-raise - no silent failures
    raise RuntimeError(f"Critical service failure: Gremlin connection failed: {e}")
```

### 3. Comprehensive Error Reporting

Each service initialization now includes:

- **Clear status logging** with emojis for visual scanning
- **Specific error messages** with context and suggestions
- **Troubleshooting hints** for common issues
- **Duration tracking** for performance monitoring

### 4. Graceful Cleanup

The lifespan function now:

- **Tracks initialized components** for proper cleanup
- **Cleans up in reverse order** of initialization
- **Handles cleanup errors gracefully** without stopping the shutdown process
- **Provides detailed shutdown logging**

## Key Improvements

### Before (Problematic)
```python
try:
    await gremlin_client.connect()
    logger.info("✅ Gremlin client connected successfully")
except Exception as e:
    if settings.development_mode:
        logger.warning(f"⚠️ Gremlin connection failed (development mode): {e}")
        gremlin_client = None  # Silent failure!
    else:
        raise
```

### After (Robust)
```python
try:
    await gremlin_client.connect()
    logger.info("✅ Gremlin client connected successfully")
    initialized_components.append(("gremlin_client", gremlin_client))
except Exception as e:
    logger.error(f"❌ Gremlin connection failed: {e}")
    logger.error("   📋 Check: GREMLIN_URL, GREMLIN_KEY, network connectivity")
    logger.error("   💡 Suggestion: Verify Cosmos DB Gremlin API is accessible")
    # Always re-raise - no silent failures
    raise RuntimeError(f"Critical service failure: Gremlin connection failed: {e}")
```

## Error Handling Patterns

### 1. Structured Error Messages

```python
logger.error(f"❌ Service initialization failed: {e}")
logger.error("   📋 Check: [specific items to verify]")
logger.error("   💡 Suggestion: [actionable advice]")
```

### 2. Component Tracking

```python
initialized_components = []
# ... after successful initialization
initialized_components.append(("service_name", service_instance))
```

### 3. Cleanup on Failure

```python
except Exception as e:
    # Clean up any partially initialized components
    for name, component in initialized_components:
        try:
            if hasattr(component, 'close'):
                await component.close()
        except Exception as cleanup_error:
            logger.warning(f"⚠️ Error cleaning up {name}: {cleanup_error}")
    raise
```

## Logging Strategy

### Log Levels and Emojis

- `🚀` Application startup
- `🔌` Service initialization starting
- `✅` Successful initialization
- `❌` Critical failure
- `⚠️` Warning (non-critical)
- `🔧` Development mode notice
- `💡` Suggestion/hint
- `📋` Checklist item
- `🎯` Summary of critical services
- `📈` Summary of optional services
- `🎉` Startup completion
- `💥` Startup failure
- `🔄` Shutdown starting
- `🧹` Cleanup action
- `👋` Shutdown complete

### Startup Summary

The improved lifespan function provides a clear summary:

```
🎯 Critical services initialized: gremlin_client, graph_query_llm
📈 Optional services initialized: vector_store, vector_retriever
⚠️ Optional services not available: (none)
🎉 Application startup completed successfully!
```

## Standalone Testing

A comprehensive standalone test script (`test_gremlin_standalone.py`) is provided to:

1. **Test environment variables** are properly set
2. **Test client creation** without connection
3. **Test actual connection** to Cosmos DB
4. **Test basic queries** to verify functionality
5. **Test schema methods** for full validation

### Usage

```bash
python test_gremlin_standalone.py
```

The script provides detailed output:

```
🔍 Environment Configuration:
   GREMLIN_URL: wss://...
   GREMLIN_DATABASE: graphdb
   ...

✅ PASS Environment Variables: All required environment variables are set (0.01s)
✅ PASS Client Creation: SchemaAwareGremlinClient created successfully (0.02s)
✅ PASS Connection Test: Connected to wss://... (1.23s)
✅ PASS Basic Query Test: Query successful - found 1250 vertices (0.45s)
✅ PASS Schema Methods Test: Retrieved 3 vertex labels: ['hotel', 'review', 'user'] (0.32s)

📊 GREMLIN CONNECTION TEST SUMMARY
Total Tests: 5
Passed: 5
Failed: 0
Success Rate: 100.0%

🎉 All tests passed! Your Gremlin connection is working properly.
```

## Best Practices for FastAPI Startup

### 1. Use @asynccontextmanager for Lifespan

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        # Initialize services
        yield
    except Exception:
        # Cleanup on failure
        raise
    finally:
        # Cleanup on shutdown
```

### 2. Classify Services by Criticality

- **Critical**: Must work for application to function
- **Optional**: Can gracefully degrade

### 3. Always Test Connections

Don't just create clients - test that they can actually connect:

```python
client = create_client()
await client.connect()  # Test the connection!
```

### 4. Provide Actionable Error Messages

Include:
- What failed
- Why it might have failed
- How to fix it
- What to check

### 5. Implement Proper Cleanup

- Track what was initialized
- Clean up in reverse order
- Handle cleanup errors gracefully
- Don't let cleanup errors mask the original failure

### 6. Use Structured Logging

- Consistent format
- Visual indicators (emojis)
- Appropriate log levels
- Contextual information

## Environment Variables

Ensure these are set for Gremlin connectivity:

```bash
GREMLIN_URL=wss://your-cosmos-account.gremlin.cosmos.azure.com:443/
GREMLIN_DATABASE=your-database-name
GREMLIN_GRAPH=your-graph-name
GREMLIN_USERNAME=/dbs/your-database-name/colls/your-graph-name
GREMLIN_KEY=your-primary-or-secondary-key
GREMLIN_TRAVERSAL_SOURCE=g
DEVELOPMENT_MODE=false  # Set to true for graceful degradation
```

## Troubleshooting

### Common Issues

1. **"Connection failed"**
   - Check GREMLIN_URL format
   - Verify Cosmos DB is running
   - Check firewall settings

2. **"Authentication failed"**
   - Verify GREMLIN_KEY is correct
   - Check GREMLIN_USERNAME format
   - Ensure keys haven't been rotated

3. **"Database/Graph not found"**
   - Verify GREMLIN_DATABASE and GREMLIN_GRAPH names
   - Check that resources exist in Azure Portal

4. **"Timeout"**
   - Check network connectivity
   - Verify Azure region accessibility
   - Consider increasing timeout values

### Using the Standalone Test

Run the standalone test script first to isolate connection issues:

```bash
python test_gremlin_standalone.py
```

This will help determine if the issue is with:
- Environment configuration
- Network connectivity
- Authentication
- Service availability

## Monitoring and Alerting

Consider adding:

1. **Health check endpoints** that test critical services
2. **Metrics collection** for startup times and failure rates
3. **Alerting** on startup failures
4. **Dashboard** showing service health status

## Security Considerations

1. **Never log sensitive data** (keys, passwords)
2. **Use Azure Key Vault** for secrets in production
3. **Implement proper RBAC** for Cosmos DB access
4. **Enable audit logging** for production systems
5. **Rotate keys regularly** and test the rotation process

## Performance Considerations

1. **Connection pooling** for high-throughput scenarios
2. **Timeout configuration** based on network latency
3. **Retry logic** with exponential backoff
4. **Circuit breaker patterns** for resilience
5. **Caching** for frequently accessed data

This implementation follows Azure best practices for:
- Error handling and reliability
- Security and authentication
- Performance and monitoring
- Operational excellence
