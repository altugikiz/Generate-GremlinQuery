# 🔍 Azure Cosmos DB Gremlin API Connectivity Troubleshooting Guide

## 🎯 Current Issue
**RetryError[ConnectionError]** when connecting to Cosmos DB Gremlin API during production startup.

---

## � Quick Diagnostics Checklist

### 1. **Environment Configuration** ✅
Current configuration from `.env`:
- [x] GREMLIN_URL: `wss://emoscuko.gremlin.cosmos.azure.com:443/`
- [x] GREMLIN_DATABASE: `reviewdb`
- [x] GREMLIN_GRAPH: `review6`
- [x] GREMLIN_USERNAME: `emoscuko`
- [x] GREMLIN_KEY: Configured (Hidden for security)
- [x] DEVELOPMENT_MODE: `false` (Production mode)

### 2. **Network Connectivity Tests** 🔄

#### Test 1: DNS Resolution
```powershell
nslookup emoscuko.gremlin.cosmos.azure.com
```

#### Test 2: TCP Port Connectivity
```powershell
Test-NetConnection -ComputerName emoscuko.gremlin.cosmos.azure.com -Port 443
```

#### Test 3: TLS/SSL Handshake Test
```python
# Run this Python test
python -c "
import socket
import ssl
context = ssl.create_default_context()
with socket.create_connection(('emoscuko.gremlin.cosmos.azure.com', 443), timeout=10) as sock:
    with context.wrap_socket(sock, server_hostname='emoscuko.gremlin.cosmos.azure.com') as ssock:
        print('✅ TLS connection successful')
        print(f'TLS version: {ssock.version()}')
        print(f'Cipher: {ssock.cipher()}')
"
```

### 3. **Azure Portal Verification** 🔄

#### Cosmos DB Account Status
1. **Navigate to**: [Azure Portal](https://portal.azure.com) → Cosmos DB → `emoscuko`
2. **Check**:
   - Account Status: Should be "Online"
   - Gremlin API: Should be enabled  
   - Database `reviewdb`: Should exist
   - Graph `review6`: Should exist

#### Network Access Settings
1. **Go to**: **Networking** → **Firewall and virtual networks**
2. **Verify one of these**:
   - ✅ "Allow access from Azure Portal" is enabled
   - ✅ Your current IP is in allowed list
   - ✅ "Accept connections from within public Azure datacenters" is enabled

#### Keys and Connection Validation
1. **Go to**: **Keys** section in Azure Portal
2. **Verify**:
   - Primary Key matches your `GREMLIN_KEY` in `.env`
   - Account name matches `emoscuko`
   - Gremlin Endpoint shows: `emoscuko.gremlin.cosmos.azure.com:443`

### 4. **Authentication Format Check** ⚠️

**CRITICAL**: Gremlin-Python library requires specific username format:

```python
# ❌ WRONG (current in .env):
GREMLIN_USERNAME=emoscuko

# ✅ CORRECT (what the library expects):
username = f"/dbs/{database}/colls/{graph}"  # "/dbs/reviewdb/colls/review6"
```

**This might be your main issue!** Let's check your Gremlin client code.

Your current configuration:
```bash
GREMLIN_URL=wss://emoscuko.gremlin.cosmos.azure.com:443/
GREMLIN_DATABASE=reviewdb
GREMLIN_GRAPH=review6
GREMLIN_USERNAME=emoscuko
```

**Common Issues to Check:**

#### URL Format Validation
```bash
# ✅ CORRECT (your current config)
GREMLIN_URL=wss://emoscuko.gremlin.cosmos.azure.com:443/

# ❌ WRONG - SQL API URL
GREMLIN_URL=https://emoscuko.documents.azure.com:443/

# ❌ WRONG - HTTP instead of WSS
GREMLIN_URL=ws://emoscuko.gremlin.cosmos.azure.com:443/

# ❌ WRONG - Local Gremlin port
GREMLIN_URL=wss://emoscuko.gremlin.cosmos.azure.com:8182/
```

#### Authentication Format
```bash
# Option 1: Database/Collection format (try this first)
GREMLIN_USERNAME=/dbs/reviewdb/colls/review6

# Option 2: Account name format (try if Option 1 fails)
GREMLIN_USERNAME=emoscuko
```

### 3. **Test Network Connectivity**

#### DNS Resolution Test
```bash
# Test if the hostname resolves
nslookup emoscuko.gremlin.cosmos.azure.com
```

#### TCP Connection Test
```bash
# Windows
telnet emoscuko.gremlin.cosmos.azure.com 443

# Linux/Mac
nc -zv emoscuko.gremlin.cosmos.azure.com 443
```

#### SSL/TLS Test
```bash
# Test SSL certificate
openssl s_client -connect emoscuko.gremlin.cosmos.azure.com:443 -servername emoscuko.gremlin.cosmos.azure.com
```

### 4. **Validate Authentication Credentials**

#### Get Correct Primary Key
1. Azure Portal → Cosmos DB → Settings → Keys
2. Copy the **PRIMARY KEY** (not connection string)
3. Should be ~88 characters, base64 encoded, ending with `==`

```bash
# ✅ CORRECT format
GREMLIN_KEY=ABC123...xyz789==  # 88 characters

# ❌ WRONG - Connection string
GREMLIN_KEY=AccountEndpoint=https://...;AccountKey=...;

# ❌ WRONG - Read-only key (too short)
GREMLIN_KEY=short_key_here  # <80 characters
```

### 5. **Test with Python Gremlin Console**

Create a simple test script:

```python
# test_gremlin_simple.py
from gremlin_python.driver import client, serializer

def test_connection():
    try:
        # Try both authentication formats
        configs = [
            {
                "name": "Database/Collection Format",
                "username": "/dbs/reviewdb/colls/review6"
            },
            {
                "name": "Account Name Format", 
                "username": "emoscuko"
            }
        ]
        
        for config in configs:
            print(f"Testing {config['name']}...")
            
            gremlin_client = client.Client(
                url="wss://emoscuko.gremlin.cosmos.azure.com:443/",
                traversal_source="g",
                username=config["username"],
                password="YOUR_PRIMARY_KEY_HERE",  # Replace with actual key
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Test simple query
            result = gremlin_client.submit("g.V().limit(1).count()").all().result()
            print(f"✅ Success! Vertex count: {result[0] if result else 0}")
            
            gremlin_client.close()
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

---

## 🚨 Common Issues & Solutions

### **Issue 1: Firewall Blocking Connection**

**Symptoms:**
- TCP connection fails
- Connection timeout errors

**Solutions:**
1. **Add your IP to Cosmos DB firewall:**
   ```bash
   # In Azure Portal:
   # Cosmos DB → Networking → Firewall and virtual networks
   # Add your current public IP address
   ```

2. **Enable Azure Portal access:**
   ```bash
   # Check "Allow access from Azure Portal"
   ```

3. **For Azure-hosted applications:**
   ```bash
   # Check "Accept connections from within public Azure datacenters"
   ```

### **Issue 2: Wrong Authentication Format**

**Symptoms:**
- Authentication/authorization errors
- "Unauthorized" messages

**Solutions:**

1. **Try database/collection username format:**
   ```bash
   GREMLIN_USERNAME=/dbs/reviewdb/colls/review6
   ```

2. **Try account name format:**
   ```bash
   GREMLIN_USERNAME=emoscuko
   ```

3. **Verify you're using PRIMARY KEY:**
   ```bash
   # Get from Azure Portal → Cosmos DB → Keys → PRIMARY KEY
   # Should be ~88 characters ending with ==
   ```

### **Issue 3: Wrong API Endpoint**

**Symptoms:**
- Cannot resolve hostname
- Wrong port errors

**Solutions:**

1. **Use Gremlin API endpoint (not SQL):**
   ```bash
   # ✅ CORRECT
   wss://emoscuko.gremlin.cosmos.azure.com:443/
   
   # ❌ WRONG (SQL API)
   https://emoscuko.documents.azure.com:443/
   ```

2. **Use correct port (443, not 8182):**
   ```bash
   # ✅ CORRECT for Cosmos DB
   :443/
   
   # ❌ WRONG (local Gremlin)
   :8182/
   ```

### **Issue 4: Service/Region Issues**

**Symptoms:**
- Intermittent connectivity
- Service unavailable errors

**Solutions:**

1. **Check Azure Service Health:**
   - Visit [Azure Status](https://status.azure.com/)
   - Look for Cosmos DB issues in your region

2. **Verify account region:**
   ```bash
   # Ensure your app is connecting to the correct region
   # Check Azure Portal → Cosmos DB → Overview → Location
   ```

3. **Check account status:**
   ```bash
   # Azure Portal → Cosmos DB → Overview → Status should be "Online"
   ```

### **Issue 5: Network/Corporate Firewall**

**Symptoms:**
- Works from home but not office
- SSL/TLS handshake failures

**Solutions:**

1. **Check corporate firewall:**
   ```bash
   # Ensure these are allowed:
   # - Outbound HTTPS (443) to *.azure.com
   # - WebSocket (WSS) connections
   # - TLS 1.2+ support
   ```

2. **Test from different network:**
   ```bash
   # Try mobile hotspot to isolate network issues
   ```

3. **Check proxy settings:**
   ```bash
   # Ensure proxy allows WebSocket connections to Azure
   ```

---

## 🧪 Testing External Tools

### **1. Azure CLI Test**
```bash
# Install Azure CLI if not already installed
az login

# Test Cosmos DB connectivity
az cosmosdb gremlin graph show \
  --account-name emoscuko \
  --database-name reviewdb \
  --name review6 \
  --resource-group YOUR_RESOURCE_GROUP
```

### **2. PowerShell Test**
```powershell
# Test TCP connectivity
Test-NetConnection -ComputerName "emoscuko.gremlin.cosmos.azure.com" -Port 443

# Test DNS resolution
Resolve-DnsName "emoscuko.gremlin.cosmos.azure.com"
```

### **3. Node.js Gremlin Test**
```javascript
// Install: npm install gremlin
const gremlin = require('gremlin');

const authenticator = new gremlin.driver.auth.PlainTextSaslAuthenticator(
  '/dbs/reviewdb/colls/review6',  // or 'emoscuko'
  'YOUR_PRIMARY_KEY_HERE'
);

const client = new gremlin.driver.Client(
  'wss://emoscuko.gremlin.cosmos.azure.com:443/',
  { 
    authenticator,
    traversalsource: 'g',
    rejectUnauthorized: true,
    mimeType: 'application/vnd.gremlin-v2.0+json'
  }
);

client.submit('g.V().limit(1).count()')
  .then(result => {
    console.log('✅ Success:', result);
    client.close();
  })
  .catch(err => {
    console.error('❌ Error:', err);
    client.close();
  });
```

---

## 🎯 Next Steps for Resolution

### **Immediate Actions:**

1. **Run the diagnostic tool:**
   ```bash
   python cosmos_gremlin_diagnostics.py
   ```

2. **Check Azure Portal:**
   - Verify Cosmos DB account status
   - Check firewall settings
   - Confirm database/graph existence

3. **Test authentication formats:**
   ```bash
   # Try both username formats in the diagnostic tool
   ```

### **If Still Failing:**

1. **Create a minimal test case:**
   ```python
   # Isolate the connection test from your FastAPI app
   python test_gremlin_simple.py
   ```

2. **Check Azure support:**
   - Open Azure support ticket
   - Include diagnostic tool output
   - Mention connectivity from your specific location/network

3. **Alternative authentication:**
   ```bash
   # Try using Azure Active Directory authentication (if applicable)
   # This may bypass some key-related issues
   ```

---

## 📋 Production Deployment Checklist

Before deploying to production:

- [ ] Cosmos DB account is in the correct region
- [ ] Firewall allows connections from deployment environment
- [ ] Using PRIMARY KEY (not read-only or secondary)
- [ ] Database and graph container exist and have data
- [ ] Network security groups allow outbound HTTPS/WSS
- [ ] DNS resolution works from deployment environment
- [ ] SSL/TLS certificates are valid and up-to-date
- [ ] Azure service health shows no known issues
- [ ] Load balancing/proxy allows WebSocket connections

---

## 💡 Quick Win Solutions

Try these in order:

1. **Change username format:**
   ```bash
   GREMLIN_USERNAME=/dbs/reviewdb/colls/review6
   ```

2. **Verify primary key:**
   ```bash
   # Get fresh PRIMARY KEY from Azure Portal
   ```

3. **Add current IP to firewall:**
   ```bash
   # Azure Portal → Cosmos DB → Networking → Add current IP
   ```

4. **Enable Azure Portal access:**
   ```bash
   # Check "Allow access from Azure Portal" box
   ```

5. **Test from different network:**
   ```bash
   # Use mobile hotspot to rule out corporate firewall
   ```

Most connectivity issues are resolved by steps 1-4! 🚀

---

## ✅ **ISSUE RESOLVED** 

### 🎯 **Root Cause Found:**
The **RetryError[ConnectionError]** issue was **NOT** a Cosmos DB connectivity problem. The actual cause was:

1. **Event Loop Conflicts**: The diagnostic tools were creating conflicting asyncio event loops
2. **Testing Methodology**: Need to use **synchronous** Gremlin tests to avoid loop conflicts
3. **Cosmos DB Connectivity**: ✅ **Working perfectly** - all network, authentication, and query tests pass

### 🧪 **Verification Results:**

#### ✅ **Network Connectivity Tests**
```powershell
# DNS Resolution ✅
nslookup emoscuko.gremlin.cosmos.azure.com
# Result: 51.116.146.224 (Germany West Central)

# TCP Connectivity ✅  
Test-NetConnection -ComputerName emoscuko.gremlin.cosmos.azure.com -Port 443
# Result: TcpTestSucceeded: True
```

#### ✅ **Gremlin Connection Tests**
```bash
python simple_gremlin_sync_test.py
# Results: 5/5 tests PASSED (100% success rate)
# - Basic Count: ✅ PASS
# - Schema Info: ✅ PASS  
# - Sample Vertex: ✅ PASS
# - Edge Count: ✅ PASS
# - Edge Labels: ✅ PASS
```

#### ✅ **FastAPI Production Startup**
```
🚀 PRODUCTION MODE: Application startup completed successfully!
✅ Gremlin client connected successfully
✅ Graph Query LLM initialized successfully  
✅ Vector store initialized successfully
✅ Vector retriever initialized successfully
✅ RAG pipeline initialized successfully
🚀 PRODUCTION MODE: Real Gremlin execution enabled - No development fallbacks
```

### 🔧 **Solution Steps:**

1. **Use Synchronous Gremlin Testing**: Avoid async event loop conflicts with `simple_gremlin_sync_test.py`
2. **Production Mode Configuration**: Ensure `DEVELOPMENT_MODE=false` in `.env`
3. **FastAPI Startup**: The `SyncGremlinClient` properly handles event loops in production
4. **Network Verification**: Basic connectivity tests confirm Cosmos DB is reachable

### 💡 **Key Learnings:**

- **Diagnostic Tool Conflicts**: Some async diagnostic tools can create misleading errors
- **Event Loop Management**: Use synchronous wrappers for Gremlin operations in FastAPI
- **Production Mode**: The system now properly fails fast if Cosmos DB is unreachable
- **Cosmos DB Working**: The database, authentication, and network connectivity are all functioning correctly

### 🎉 **Current Status:**
**✅ PRODUCTION MODE: FULLY OPERATIONAL**
- FastAPI server running on `http://localhost:8000`
- Real Cosmos DB Gremlin connectivity established  
- All critical services initialized successfully
- No development mode fallbacks active

---
