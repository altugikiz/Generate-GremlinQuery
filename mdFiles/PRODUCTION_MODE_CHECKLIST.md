# Production Mode Checklist

## 🎯 Graph RAG System Production Validation

This checklist ensures your Graph RAG system is properly configured for production deployment with full Gremlin execution and no development fallbacks.

---

## ✅ Environment Configuration

### 1. Environment Variables (.env file)
- [ ] `DEVELOPMENT_MODE=false` (CRITICAL - must be false)
- [ ] `GREMLIN_URL` - Valid Cosmos DB Gremlin API URL
- [ ] `GREMLIN_KEY` - Valid Cosmos DB primary key
- [ ] `GREMLIN_DATABASE` - Correct database name
- [ ] `GREMLIN_GRAPH` - Correct graph container name
- [ ] `GEMINI_API_KEY` - Valid Google AI API key
- [ ] `HUGGINGFACE_API_TOKEN` - Valid HuggingFace API token

### 2. Azure Cosmos DB Validation
- [ ] Cosmos DB account is accessible from deployment environment
- [ ] Gremlin API is enabled and configured
- [ ] Graph container exists and contains data
- [ ] Network connectivity allows WebSocket connections (port 443)
- [ ] Authentication credentials are valid and not expired

### 3. LLM Services
- [ ] Gemini API is accessible
- [ ] API quota is sufficient for expected load
- [ ] Model (gemini-2.0-flash) is available in your region

### 4. Vector Store
- [ ] FAISS index files exist and are accessible
- [ ] HuggingFace embedding model is available
- [ ] Vector store contains indexed documents

---

## 🚀 Application Configuration

### 1. Production Mode Enforcement
- [ ] `main.py` lifespan function requires successful Gremlin connection
- [ ] No development mode fallbacks in startup process
- [ ] All services must initialize successfully or startup fails

### 2. Endpoint Configuration
- [ ] `/semantic/ask` requires RAG pipeline initialization
- [ ] `/semantic/filter` requires Gremlin client connection
- [ ] `/semantic/gremlin` requires Graph Query LLM
- [ ] `/semantic/execute` allows raw query execution (with validation)

### 3. Error Handling
- [ ] Connection failures result in 503 Service Unavailable
- [ ] Gremlin execution errors are properly logged and returned
- [ ] LLM errors are handled gracefully
- [ ] No silent failures or fallback responses

---

## 🧪 Functional Validation

### 1. Server Startup Test
```bash
python main.py
```
**Expected Results:**
- [ ] Server starts successfully (no exceptions)
- [ ] All services initialize: Gremlin client, Graph Query LLM, Vector store, RAG pipeline
- [ ] Logs show "PRODUCTION MODE: Application startup completed successfully!"
- [ ] No development mode warnings

### 2. Gremlin Connection Test
```bash
python comprehensive_graph_rag_test.py
```
**Expected Results:**
- [ ] LLM → Gremlin translation works
- [ ] Real Gremlin queries execute against Cosmos DB
- [ ] Graph data is returned (not mock data)
- [ ] No "development mode" messages in responses

### 3. Full Pipeline Test
**Test Query:** "Show me hotels with cleanliness issues"

**Expected Behavior:**
- [ ] Natural language translated to valid Gremlin query
- [ ] Gremlin query executed against real Cosmos DB
- [ ] Real graph data retrieved and processed
- [ ] Semantic search performed on vector store
- [ ] LLM generates response using real data
- [ ] No fallback or mock responses

### 4. Error Handling Test
**Scenarios to Test:**
- [ ] Invalid Gremlin queries return 500 errors (not development messages)
- [ ] Database connection issues return 503 errors
- [ ] Malformed requests return 400 errors
- [ ] All errors are logged appropriately

---

## 📊 Performance & Monitoring

### 1. Response Times
- [ ] `/semantic/ask` responds within reasonable time (< 10 seconds typical)
- [ ] Gremlin queries execute efficiently
- [ ] Vector searches complete quickly
- [ ] No timeout errors under normal load

### 2. Logging & Observability
- [ ] Structured error logging enabled
- [ ] Performance metrics captured
- [ ] Database connection status monitored
- [ ] Component health checks available

---

## 🔒 Security & Production Readiness

### 1. Credentials Security
- [ ] No hardcoded credentials in code
- [ ] Environment variables properly secured
- [ ] API keys have appropriate permissions
- [ ] Database access follows least privilege

### 2. Query Validation
- [ ] Raw Gremlin execution includes basic safety checks
- [ ] Dangerous operations (drop, delete) are blocked
- [ ] Input validation prevents injection attacks
- [ ] Query complexity limits enforced

---

## 🎯 Production Deployment Verification

### Final Validation Commands

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **Run comprehensive tests:**
   ```bash
   python comprehensive_graph_rag_test.py
   ```

3. **Verify no development mode messages:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/semantic/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me hotels with poor service ratings"}'
   ```

### Success Criteria
- [ ] Server starts without errors
- [ ] All endpoints return real data (no development mode responses)
- [ ] Gremlin queries execute against actual Cosmos DB
- [ ] Response times are acceptable
- [ ] Error handling works correctly
- [ ] No fallback or mock responses

---

## 🚨 Critical Production Deployment Notes

1. **DEVELOPMENT_MODE=false is MANDATORY**
   - The system will fail to start if any critical service is unavailable
   - No fallback responses or development mode messages
   - All components must be fully operational

2. **Database Connectivity is Required**
   - Cosmos DB Gremlin API must be accessible
   - Network connectivity and authentication must work
   - Graph container must contain data

3. **All Services Must Initialize**
   - Gremlin client connection required
   - LLM services must be available
   - Vector store must be properly initialized

4. **No Silent Failures**
   - All errors are logged and returned to clients
   - No development mode fallbacks mask real issues
   - 503 errors indicate service unavailability

---

## 📝 Deployment Checklist Summary

**Before Production Deployment:**
- [ ] All environment variables configured correctly
- [ ] Cosmos DB Gremlin API accessible and contains data
- [ ] LLM services (Gemini) are available and authenticated
- [ ] Vector store initialized with proper data
- [ ] Comprehensive tests pass without development mode messages
- [ ] Error handling works correctly
- [ ] Performance is acceptable under expected load

**REMEMBER:** In production mode, the system is designed to fail fast rather than provide degraded functionality. This ensures reliability and prevents silent failures.
