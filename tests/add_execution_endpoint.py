#!/usr/bin/env python3
"""
Add Secure Gremlin Execution Endpoint

This script adds a secure endpoint for executing raw Gremlin queries during testing.
This endpoint should only be enabled in development mode for security reasons.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

def add_execution_endpoint():
    """Add a secure execution endpoint to the semantic routes."""
    
    semantic_routes_path = Path(__file__).parent / "app" / "api" / "routes" / "semantic.py"
    
    # Read the current file
    with open(semantic_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the endpoint already exists
    if "/execute" in content:
        print("✅ Execution endpoint already exists")
        return True
    
    # Add the execution endpoint code before the helper functions
    execution_endpoint_code = '''

@router.post("/execute", response_model=Dict[str, Any])
async def execute_gremlin_query(
    request: Dict[str, str],
    gremlin_client: SchemaAwareGremlinClient = Depends(get_gremlin_client)
):
    """
    **DEVELOPMENT MODE ONLY** - Execute a raw Gremlin query.
    
    ⚠️  WARNING: This endpoint executes arbitrary Gremlin queries and should
    only be enabled in development mode for testing purposes.
    
    Request body:
    {
        "query": "g.V().hasLabel('Hotel').limit(5).valueMap()"
    }
    
    Returns the raw query results.
    """
    # Security check - only allow in development mode
    settings = get_settings()
    if not settings.development_mode:
        raise HTTPException(
            status_code=403,
            detail="Gremlin query execution endpoint is only available in development mode"
        )
    
    if not gremlin_client or not gremlin_client.is_connected:
        raise HTTPException(
            status_code=503,
            detail="Graph database not available"
        )
    
    gremlin_query = request.get("query", "").strip()
    if not gremlin_query:
        raise HTTPException(
            status_code=400,
            detail="Query parameter is required"
        )
    
    # Basic validation to prevent obviously dangerous queries
    dangerous_patterns = ["drop", "delete", "clear", "truncate"]
    query_lower = gremlin_query.lower()
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Query contains potentially dangerous operation: {pattern}"
            )
    
    try:
        start_time = time.time()
        results = await gremlin_client.execute_query(gremlin_query)
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "query": gremlin_query,
            "results": results,
            "results_count": len(results) if isinstance(results, list) else 1,
            "execution_time_ms": execution_time,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error executing Gremlin query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )'''
    
    # Find the insertion point (before helper functions)
    helper_functions_marker = "# Helper Functions"
    if helper_functions_marker in content:
        insertion_point = content.find(helper_functions_marker)
        new_content = content[:insertion_point] + execution_endpoint_code + "\n\n" + content[insertion_point:]
    else:
        # If no helper functions marker, append before the end
        new_content = content + execution_endpoint_code
    
    # Write the updated content
    with open(semantic_routes_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Added secure Gremlin execution endpoint to semantic.py")
    print("⚠️  Note: This endpoint is only available in development mode")
    return True


if __name__ == "__main__":
    print("🔧 Adding secure Gremlin execution endpoint...")
    
    if add_execution_endpoint():
        print("✅ Execution endpoint added successfully")
        print("💡 You can now test raw Gremlin queries via POST /api/v1/semantic/execute")
        print("📋 Example request: {'query': 'g.V().hasLabel(\"Hotel\").limit(5).valueMap()'}")
    else:
        print("❌ Failed to add execution endpoint")
        sys.exit(1)
