#!/usr/bin/env python3
"""
Azure Cosmos DB Gremlin API Connectivity Troubleshooting Tool

This comprehensive diagnostic tool helps identify and resolve connectivity issues
with Azure Cosmos DB Gremlin API. It performs step-by-step validation of:

1. Environment configuration
2. Network connectivity
3. Authentication
4. Service availability
5. Common misconfigurations

Usage:
    python cosmos_gremlin_diagnostics.py

Requirements:
    pip install gremlin-python azure-cosmos requests python-dotenv tenacity
"""

import asyncio
import json
import socket
import ssl
import time
import requests
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import urllib.parse
from dotenv import load_dotenv
import os

# Gremlin imports
try:
    from gremlin_python.driver import client, serializer
    from gremlin_python.driver.protocol import GremlinServerError
    from gremlin_python.process.anonymous_traversal import traversal
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    import websockets
    GREMLIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Gremlin Python dependencies not available: {e}")
    GREMLIN_AVAILABLE = False

class DiagnosticResult(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"
    INFO = "ℹ️ INFO"

@dataclass
class TestResult:
    test_name: str
    result: DiagnosticResult
    message: str
    details: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None

class CosmosGremlinDiagnostics:
    """Comprehensive Cosmos DB Gremlin API diagnostics."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.config = {}
        
    def add_result(self, test_name: str, result: DiagnosticResult, message: str, 
                   details: Dict[str, Any] = None, recommendation: str = None):
        """Add a test result."""
        test_result = TestResult(test_name, result, message, details, recommendation)
        self.results.append(test_result)
        
        # Print result immediately
        icon = result.value
        print(f"{icon} {test_name}: {message}")
        if recommendation:
            print(f"   💡 Recommendation: {recommendation}")
        if details:
            for key, value in details.items():
                print(f"   📋 {key}: {value}")
        print()

    def load_configuration(self) -> bool:
        """Load and validate environment configuration."""
        print("🔧 LOADING CONFIGURATION")
        print("=" * 60)
        
        load_dotenv()
        
        required_vars = [
            "GREMLIN_URL", "GREMLIN_KEY", "GREMLIN_DATABASE", 
            "GREMLIN_GRAPH", "GREMLIN_USERNAME"
        ]
        
        config = {}
        all_present = True
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.add_result(
                    f"Config: {var}",
                    DiagnosticResult.FAIL,
                    "Environment variable not set or empty",
                    recommendation="Set this variable in your .env file"
                )
                all_present = False
            else:
                config[var] = value
                # Mask sensitive data in display
                display_value = value if var != "GREMLIN_KEY" else f"{value[:10]}...{value[-4:]}"
                self.add_result(
                    f"Config: {var}",
                    DiagnosticResult.PASS,
                    f"Loaded successfully",
                    details={"value": display_value}
                )
        
        if all_present:
            self.config = config
            
            # Validate URL format
            url = config["GREMLIN_URL"]
            if not url.startswith("wss://") or not url.endswith(".azure.com:443/"):
                self.add_result(
                    "Config: URL Format",
                    DiagnosticResult.WARN,
                    "URL format may be incorrect for Cosmos DB",
                    details={"expected_format": "wss://<account>.gremlin.cosmos.azure.com:443/"},
                    recommendation="Verify URL matches Cosmos DB Gremlin endpoint format"
                )
            else:
                self.add_result(
                    "Config: URL Format",
                    DiagnosticResult.PASS,
                    "URL format appears correct for Cosmos DB"
                )
                
            # Extract account name for further tests
            try:
                # Parse URL to extract account name
                # wss://emoscuko.gremlin.cosmos.azure.com:443/ -> emoscuko
                account_name = url.replace("wss://", "").split(".")[0]
                self.config["ACCOUNT_NAME"] = account_name
                self.add_result(
                    "Config: Account Name",
                    DiagnosticResult.INFO,
                    f"Extracted account name: {account_name}"
                )
            except Exception as e:
                self.add_result(
                    "Config: Account Name",
                    DiagnosticResult.WARN,
                    f"Could not extract account name: {e}"
                )
        
        return all_present

    def test_network_connectivity(self) -> bool:
        """Test basic network connectivity to Cosmos DB."""
        print("🌐 TESTING NETWORK CONNECTIVITY")
        print("=" * 60)
        
        if not self.config:
            self.add_result(
                "Network: Skipped",
                DiagnosticResult.FAIL,
                "Configuration not loaded"
            )
            return False
        
        url = self.config["GREMLIN_URL"]
        
        # Extract hostname and port
        try:
            # wss://emoscuko.gremlin.cosmos.azure.com:443/ -> emoscuko.gremlin.cosmos.azure.com, 443
            clean_url = url.replace("wss://", "").replace("/", "")
            if ":" in clean_url:
                hostname, port_str = clean_url.rsplit(":", 1)
                port = int(port_str)
            else:
                hostname = clean_url
                port = 443  # Default for WSS
                
        except Exception as e:
            self.add_result(
                "Network: URL Parsing",
                DiagnosticResult.FAIL,
                f"Could not parse URL: {e}"
            )
            return False
        
        # Test DNS resolution
        try:
            resolved_ip = socket.gethostbyname(hostname)
            self.add_result(
                "Network: DNS Resolution",
                DiagnosticResult.PASS,
                f"Successfully resolved {hostname}",
                details={"resolved_ip": resolved_ip}
            )
        except socket.gaierror as e:
            self.add_result(
                "Network: DNS Resolution",
                DiagnosticResult.FAIL,
                f"DNS resolution failed for {hostname}",
                details={"error": str(e)},
                recommendation="Check if the account name is correct and the Cosmos DB account exists"
            )
            return False
        
        # Test TCP connectivity
        try:
            sock = socket.create_connection((hostname, port), timeout=10)
            sock.close()
            self.add_result(
                "Network: TCP Connection",
                DiagnosticResult.PASS,
                f"Successfully connected to {hostname}:{port}"
            )
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self.add_result(
                "Network: TCP Connection",
                DiagnosticResult.FAIL,
                f"TCP connection failed to {hostname}:{port}",
                details={"error": str(e)},
                recommendation="Check firewall settings, VPN, or network restrictions"
            )
            return False
        
        # Test SSL/TLS handshake
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    self.add_result(
                        "Network: SSL/TLS",
                        DiagnosticResult.PASS,
                        f"SSL/TLS handshake successful",
                        details={
                            "cert_subject": dict(x[0] for x in cert['subject']),
                            "cert_issuer": dict(x[0] for x in cert['issuer'])
                        }
                    )
        except ssl.SSLError as e:
            self.add_result(
                "Network: SSL/TLS",
                DiagnosticResult.FAIL,
                f"SSL/TLS handshake failed",
                details={"error": str(e)},
                recommendation="Check SSL certificate validity and TLS version compatibility"
            )
            return False
        except Exception as e:
            self.add_result(
                "Network: SSL/TLS",
                DiagnosticResult.WARN,
                f"SSL/TLS test inconclusive: {e}"
            )
        
        return True

    def test_azure_service_availability(self) -> bool:
        """Test Azure service availability and status."""
        print("☁️ TESTING AZURE SERVICE AVAILABILITY")
        print("=" * 60)
        
        if "ACCOUNT_NAME" not in self.config:
            self.add_result(
                "Azure: Service Check",
                DiagnosticResult.WARN,
                "Cannot perform service check without account name"
            )
            return False
        
        account_name = self.config["ACCOUNT_NAME"]
        
        # Test Azure Resource Manager API access
        try:
            # Check if we can reach Azure's public endpoints
            response = requests.get(
                "https://management.azure.com/providers/Microsoft.DocumentDB?api-version=2021-10-15",
                timeout=10
            )
            
            if response.status_code == 401:
                # Expected - we don't have auth, but service is reachable
                self.add_result(
                    "Azure: ARM API",
                    DiagnosticResult.PASS,
                    "Azure Resource Manager API is reachable"
                )
            elif response.status_code == 200:
                self.add_result(
                    "Azure: ARM API",
                    DiagnosticResult.PASS,
                    "Azure Resource Manager API is accessible"
                )
            else:
                self.add_result(
                    "Azure: ARM API",
                    DiagnosticResult.WARN,
                    f"Unexpected response from ARM API: {response.status_code}"
                )
                
        except requests.RequestException as e:
            self.add_result(
                "Azure: ARM API",
                DiagnosticResult.FAIL,
                f"Cannot reach Azure Resource Manager API",
                details={"error": str(e)},
                recommendation="Check internet connectivity to Azure services"
            )
            return False
        
        # Check Azure service health (if possible)
        try:
            # Try to check service health via public endpoint
            health_url = "https://status.azure.com/api/v2/status.json"
            response = requests.get(health_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Look for Cosmos DB issues
                cosmos_issues = []
                for service in data.get('services', []):
                    if 'cosmos' in service.get('name', '').lower() or 'documentdb' in service.get('name', '').lower():
                        if service.get('status') != 'available':
                            cosmos_issues.append(service)
                
                if not cosmos_issues:
                    self.add_result(
                        "Azure: Service Health",
                        DiagnosticResult.PASS,
                        "No known Cosmos DB service issues reported"
                    )
                else:
                    self.add_result(
                        "Azure: Service Health",
                        DiagnosticResult.WARN,
                        f"Potential Cosmos DB service issues detected",
                        details={"issues": cosmos_issues},
                        recommendation="Check Azure status page for current outages"
                    )
            else:
                self.add_result(
                    "Azure: Service Health",
                    DiagnosticResult.INFO,
                    "Could not check Azure service health status"
                )
                
        except Exception as e:
            self.add_result(
                "Azure: Service Health",
                DiagnosticResult.INFO,
                f"Service health check inconclusive: {e}"
            )
        
        return True

    def test_authentication_format(self) -> bool:
        """Test authentication credential format and structure."""
        print("🔐 TESTING AUTHENTICATION FORMAT")
        print("=" * 60)
        
        if not self.config:
            return False
        
        username = self.config.get("GREMLIN_USERNAME", "")
        password = self.config.get("GREMLIN_KEY", "")
        database = self.config.get("GREMLIN_DATABASE", "")
        graph = self.config.get("GREMLIN_GRAPH", "")
        
        # Validate username format
        expected_username_format = f"/dbs/{database}/colls/{graph}"
        if username == expected_username_format:
            self.add_result(
                "Auth: Username Format",
                DiagnosticResult.PASS,
                "Username format is correct for Cosmos DB"
            )
        elif username == self.config.get("ACCOUNT_NAME", ""):
            self.add_result(
                "Auth: Username Format",
                DiagnosticResult.INFO,
                "Username appears to be account name (also valid for Cosmos DB)"
            )
        else:
            self.add_result(
                "Auth: Username Format",
                DiagnosticResult.WARN,
                f"Username format may be incorrect",
                details={
                    "current": username,
                    "expected_format": expected_username_format,
                    "alternative": self.config.get("ACCOUNT_NAME", "")
                },
                recommendation=f"Try using either '{expected_username_format}' or account name"
            )
        
        # Validate key format
        if len(password) == 88 and password.endswith("=="):
            self.add_result(
                "Auth: Key Format",
                DiagnosticResult.PASS,
                "Key format appears correct (base64, 88 chars, ends with ==)"
            )
        elif len(password) == 86 and not password.endswith("=="):
            self.add_result(
                "Auth: Key Format",
                DiagnosticResult.PASS,
                "Key format appears correct (base64, 86 chars)"
            )
        else:
            self.add_result(
                "Auth: Key Format",
                DiagnosticResult.WARN,
                f"Key format may be incorrect",
                details={
                    "length": len(password),
                    "ends_with_equals": password.endswith("=="),
                    "expected": "Base64 encoded, typically 86-88 characters"
                },
                recommendation="Verify you're using the PRIMARY KEY from Cosmos DB, not connection string"
            )
        
        return True

    async def test_gremlin_connection(self) -> bool:
        """Test actual Gremlin connection and query execution."""
        print("🔍 TESTING GREMLIN CONNECTION")
        print("=" * 60)
        
        if not GREMLIN_AVAILABLE:
            self.add_result(
                "Gremlin: Dependencies",
                DiagnosticResult.FAIL,
                "Gremlin Python dependencies not available",
                recommendation="Install with: pip install gremlin-python"
            )
            return False
        
        if not self.config:
            return False
        
        # Test with different authentication approaches
        auth_approaches = [
            {
                "name": "Standard Cosmos DB Format",
                "username": f"/dbs/{self.config['GREMLIN_DATABASE']}/colls/{self.config['GREMLIN_GRAPH']}",
                "password": self.config["GREMLIN_KEY"]
            },
            {
                "name": "Account Name Format",
                "username": self.config.get("ACCOUNT_NAME", ""),
                "password": self.config["GREMLIN_KEY"]
            }
        ]
        
        for approach in auth_approaches:
            success = await self._test_single_gremlin_connection(approach)
            if success:
                return True
        
        # If all approaches failed, provide comprehensive recommendations
        self.add_result(
            "Gremlin: Connection Summary",
            DiagnosticResult.FAIL,
            "All authentication approaches failed",
            recommendation="Review the detailed recommendations below"
        )
        
        return False

    async def _test_single_gremlin_connection(self, auth_config: Dict[str, str]) -> bool:
        """Test a single Gremlin connection approach."""
        approach_name = auth_config["name"]
        
        try:
            # Create Gremlin client
            gremlin_client = client.Client(
                url=self.config["GREMLIN_URL"],
                traversal_source="g",
                username=auth_config["username"],
                password=auth_config["password"],
                message_serializer=serializer.GraphSONSerializersV2d0()
            )
            
            # Test simple query
            start_time = time.time()
            result = gremlin_client.submit("g.V().limit(1).count()").all().result()
            execution_time = (time.time() - start_time) * 1000
            
            count = result[0] if result else 0
            
            self.add_result(
                f"Gremlin: {approach_name}",
                DiagnosticResult.PASS,
                f"Connection successful! Graph has {count} vertices",
                details={
                    "execution_time_ms": f"{execution_time:.2f}",
                    "vertex_count": count,
                    "username_used": auth_config["username"][:20] + "..." if len(auth_config["username"]) > 20 else auth_config["username"]
                }
            )
            
            # Test write capability (create and delete a test vertex)
            try:
                # Create test vertex
                create_result = gremlin_client.submit(
                    "g.addV('TestVertex').property('test_id', 'diagnostic_test').property('created_at', datetime())"
                ).all().result()
                
                # Delete test vertex
                gremlin_client.submit(
                    "g.V().has('test_id', 'diagnostic_test').drop()"
                ).all().result()
                
                self.add_result(
                    f"Gremlin: Write Test",
                    DiagnosticResult.PASS,
                    "Write operations successful (create/delete test vertex)"
                )
                
            except Exception as e:
                self.add_result(
                    f"Gremlin: Write Test",
                    DiagnosticResult.WARN,
                    f"Write test failed: {str(e)}",
                    recommendation="Check if your key has write permissions"
                )
            
            gremlin_client.close()
            return True
            
        except GremlinServerError as e:
            self.add_result(
                f"Gremlin: {approach_name}",
                DiagnosticResult.FAIL,
                f"Gremlin server error: {str(e)}",
                details={"error_type": "GremlinServerError"},
                recommendation="Check authentication credentials and database/graph names"
            )
            
        except Exception as e:
            error_str = str(e)
            if "unauthorized" in error_str.lower() or "authentication" in error_str.lower():
                self.add_result(
                    f"Gremlin: {approach_name}",
                    DiagnosticResult.FAIL,
                    f"Authentication failed: {error_str}",
                    recommendation="Verify GREMLIN_KEY is the PRIMARY KEY from Cosmos DB Keys section"
                )
            elif "timeout" in error_str.lower():
                self.add_result(
                    f"Gremlin: {approach_name}",
                    DiagnosticResult.FAIL,
                    f"Connection timeout: {error_str}",
                    recommendation="Check network connectivity and firewall settings"
                )
            else:
                self.add_result(
                    f"Gremlin: {approach_name}",
                    DiagnosticResult.FAIL,
                    f"Connection failed: {error_str}",
                    details={"error_type": type(e).__name__}
                )
        
        return False

    def test_common_issues(self) -> None:
        """Test for common configuration issues."""
        print("🔧 CHECKING COMMON ISSUES")
        print("=" * 60)
        
        if not self.config:
            return
        
        # Check for common URL mistakes
        url = self.config["GREMLIN_URL"]
        
        if "documents.azure.com" in url:
            self.add_result(
                "Common Issues: URL",
                DiagnosticResult.FAIL,
                "Using SQL API URL instead of Gremlin API URL",
                details={
                    "current_url": url,
                    "issue": "SQL API URL found"
                },
                recommendation="Use the Gremlin endpoint: wss://<account>.gremlin.cosmos.azure.com:443/"
            )
        
        if not url.startswith("wss://"):
            self.add_result(
                "Common Issues: Protocol",
                DiagnosticResult.FAIL,
                "URL should use 'wss://' protocol for Gremlin",
                recommendation="Change protocol from 'ws://' or 'https://' to 'wss://'"
            )
        
        if ":8182" in url:
            self.add_result(
                "Common Issues: Port",
                DiagnosticResult.WARN,
                "Using port 8182 (typical for local Gremlin) instead of 443 for Cosmos DB",
                recommendation="Use port 443 for Azure Cosmos DB Gremlin API"
            )
        
        # Check for read-only key usage
        key = self.config["GREMLIN_KEY"]
        if len(key) < 80:
            self.add_result(
                "Common Issues: Key Length",
                DiagnosticResult.WARN,
                "Key appears too short - may be using read-only key",
                recommendation="Ensure you're using the PRIMARY KEY, not SECONDARY or READ-ONLY key"
            )

    def generate_recommendations(self) -> None:
        """Generate final recommendations based on test results."""
        print("💡 FINAL RECOMMENDATIONS")
        print("=" * 60)
        
        failed_tests = [r for r in self.results if r.result == DiagnosticResult.FAIL]
        warn_tests = [r for r in self.results if r.result == DiagnosticResult.WARN]
        
        if not failed_tests:
            print("🎉 All critical tests passed! Your configuration appears correct.")
            print("   If you're still experiencing issues, they may be intermittent network problems.")
            return
        
        print("🚨 Critical Issues Found:")
        for test in failed_tests:
            print(f"   • {test.test_name}: {test.message}")
            if test.recommendation:
                print(f"     💡 {test.recommendation}")
        
        if warn_tests:
            print("\n⚠️ Warnings (may affect connectivity):")
            for test in warn_tests:
                print(f"   • {test.test_name}: {test.message}")
                if test.recommendation:
                    print(f"     💡 {test.recommendation}")
        
        print("\n🔧 Step-by-Step Resolution:")
        print("1. Fix any FAILED tests first (critical issues)")
        print("2. Address WARNING tests (potential issues)")
        print("3. Verify in Azure Portal:")
        print("   - Cosmos DB account exists and is running")
        print("   - Gremlin API is enabled")
        print("   - Graph database and container exist")
        print("   - Firewall settings allow your IP")
        print("4. Test connectivity from your deployment environment")
        print("5. Check Azure service health for any outages")

async def main():
    """Run complete Cosmos DB Gremlin diagnostics."""
    print("🔍 Azure Cosmos DB Gremlin API Connectivity Diagnostics")
    print("=" * 80)
    print("This tool diagnoses connectivity issues with Azure Cosmos DB Gremlin API")
    print("=" * 80)
    
    diagnostics = CosmosGremlinDiagnostics()
    
    # Run all diagnostic tests
    config_ok = diagnostics.load_configuration()
    
    if config_ok:
        network_ok = diagnostics.test_network_connectivity()
        diagnostics.test_azure_service_availability()
        diagnostics.test_authentication_format()
        
        if network_ok:
            await diagnostics.test_gremlin_connection()
    
    diagnostics.test_common_issues()
    diagnostics.generate_recommendations()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    results_by_type = {}
    for result in diagnostics.results:
        result_type = result.result
        if result_type not in results_by_type:
            results_by_type[result_type] = []
        results_by_type[result_type].append(result)
    
    for result_type, tests in results_by_type.items():
        print(f"{result_type.value}: {len(tests)} tests")
    
    failed_count = len([r for r in diagnostics.results if r.result == DiagnosticResult.FAIL])
    
    if failed_count == 0:
        print("\n✅ DIAGNOSIS COMPLETE: No critical issues found!")
        print("   Your Cosmos DB Gremlin configuration appears correct.")
        return 0
    else:
        print(f"\n❌ DIAGNOSIS COMPLETE: {failed_count} critical issues found!")
        print("   Review the recommendations above to resolve connectivity issues.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
