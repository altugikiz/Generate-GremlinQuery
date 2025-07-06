#!/usr/bin/env python3
"""
Detailed Gremlin Connection Diagnostics

This script performs comprehensive diagnostics for Cosmos DB Gremlin connection issues,
including network connectivity, DNS resolution, SSL certificate validation, and more.
"""

import asyncio
import os
import sys
import socket
import ssl
import time
import websockets
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from urllib.parse import urlparse
import traceback

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


def setup_logging():
    """Configure detailed logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG"
    )


def load_environment():
    """Load environment variables."""
    env_path = current_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"✅ Loaded .env file from: {env_path}")
        return True
    else:
        logger.error(f"❌ .env file not found at: {env_path}")
        return False


def test_dns_resolution(hostname):
    """Test DNS resolution for the hostname."""
    try:
        logger.info(f"🔍 Testing DNS resolution for: {hostname}")
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        logger.info(f"✅ DNS resolution successful:")
        for ip in ip_addresses:
            logger.info(f"   - {ip}")
        return True, ip_addresses
    except Exception as e:
        logger.error(f"❌ DNS resolution failed: {e}")
        return False, []


def test_tcp_connection(hostname, port, timeout=10):
    """Test TCP connection to hostname:port."""
    try:
        logger.info(f"🔌 Testing TCP connection to: {hostname}:{port}")
        sock = socket.create_connection((hostname, port), timeout)
        sock.close()
        logger.info(f"✅ TCP connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ TCP connection failed: {e}")
        return False


def test_ssl_connection(hostname, port, timeout=10):
    """Test SSL/TLS connection."""
    try:
        logger.info(f"🔒 Testing SSL/TLS connection to: {hostname}:{port}")
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Test connection
        sock = socket.create_connection((hostname, port), timeout)
        ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
        
        # Get certificate info
        cert = ssl_sock.getpeercert()
        logger.info(f"✅ SSL/TLS connection successful")
        logger.info(f"   Certificate subject: {cert.get('subject', 'Unknown')}")
        logger.info(f"   Certificate issuer: {cert.get('issuer', 'Unknown')}")
        logger.info(f"   Certificate version: {cert.get('version', 'Unknown')}")
        
        ssl_sock.close()
        return True, cert
    except Exception as e:
        logger.error(f"❌ SSL/TLS connection failed: {e}")
        return False, None


async def test_websocket_connection(url, timeout=10):
    """Test WebSocket connection."""
    try:
        logger.info(f"🌐 Testing WebSocket connection to: {url}")
        
        # Try to connect with basic WebSocket
        async with websockets.connect(url, timeout=timeout) as websocket:
            logger.info(f"✅ WebSocket connection successful")
            
            # Test ping/pong
            pong_waiter = await websocket.ping()
            latency = await asyncio.wait_for(pong_waiter, timeout=5)
            logger.info(f"   Ping latency: {latency:.3f}s")
            
        return True
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Full error: {traceback.format_exc()}")
        return False


async def test_gremlin_protocol(url, username, password, timeout=10):
    """Test Gremlin protocol over WebSocket."""
    try:
        logger.info(f"🏗️ Testing Gremlin protocol connection...")
        
        # Import gremlin_python for testing
        try:
            from gremlin_python.driver import client
            from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        except ImportError as e:
            logger.error(f"❌ gremlin_python not available: {e}")
            return False
        
        # Parse URL to extract components
        parsed_url = urlparse(url)
        
        # Create connection string for gremlin-python
        # Format: wss://hostname:port/gremlin
        gremlin_url = f"{parsed_url.scheme}://{parsed_url.netloc}/gremlin"
        
        logger.info(f"   Connecting to: {gremlin_url}")
        logger.info(f"   Username: {username}")
        logger.info(f"   Password: {'*' * len(password)}")
        
        # Try to create a client
        gremlin_client = client.Client(
            gremlin_url,
            'g',
            username=username,
            password=password,
            message_serializer=None,
            timeout=timeout
        )
        
        # Test a simple query
        result = gremlin_client.submit("g.V().limit(1).count()").all().result()
        logger.info(f"✅ Gremlin protocol test successful")
        logger.info(f"   Query result: {result}")
        
        gremlin_client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Gremlin protocol test failed: {e}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Full traceback:")
        logger.error(traceback.format_exc())
        return False


def check_firewall_and_network():
    """Check common network issues."""
    logger.info("🔥 Checking network and firewall settings...")
    
    # Check if running on corporate network
    try:
        # Try to resolve a known external domain
        socket.gethostbyname("google.com")
        logger.info("✅ External DNS resolution working")
    except:
        logger.warning("⚠️ External DNS resolution failed - possible corporate firewall")
    
    # Check common proxy settings
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    proxy_found = False
    for var in proxy_vars:
        if os.getenv(var):
            logger.warning(f"⚠️ Proxy detected: {var}={os.getenv(var)}")
            proxy_found = True
    
    if not proxy_found:
        logger.info("✅ No proxy settings detected")
    else:
        logger.warning("⚠️ Proxy settings may interfere with WebSocket connections")


async def run_diagnostics():
    """Run complete diagnostics."""
    logger.info("🧪 GREMLIN CONNECTION DIAGNOSTICS")
    logger.info("=" * 60)
    
    # Load environment
    if not load_environment():
        return False
    
    # Get connection details
    gremlin_url = os.getenv('GREMLIN_URL')
    username = os.getenv('GREMLIN_USERNAME')
    password = os.getenv('GREMLIN_KEY')
    
    if not all([gremlin_url, username, password]):
        logger.error("❌ Missing required environment variables")
        return False
    
    # Parse URL
    try:
        parsed_url = urlparse(gremlin_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'wss' else 80)
        
        logger.info(f"📋 Connection Details:")
        logger.info(f"   URL: {gremlin_url}")
        logger.info(f"   Hostname: {hostname}")
        logger.info(f"   Port: {port}")
        logger.info(f"   Protocol: {parsed_url.scheme}")
        logger.info(f"   Username: {username}")
        
    except Exception as e:
        logger.error(f"❌ Invalid URL format: {e}")
        return False
    
    # Run diagnostic tests
    tests = []
    
    # Test 1: Network and firewall
    check_firewall_and_network()
    
    # Test 2: DNS resolution
    dns_success, ips = test_dns_resolution(hostname)
    tests.append(("DNS Resolution", dns_success))
    
    # Test 3: TCP connection
    tcp_success = test_tcp_connection(hostname, port)
    tests.append(("TCP Connection", tcp_success))
    
    # Test 4: SSL connection
    ssl_success, cert = test_ssl_connection(hostname, port)
    tests.append(("SSL/TLS Connection", ssl_success))
    
    # Test 5: WebSocket connection
    ws_success = await test_websocket_connection(gremlin_url)
    tests.append(("WebSocket Connection", ws_success))
    
    # Test 6: Gremlin protocol
    gremlin_success = await test_gremlin_protocol(gremlin_url, username, password)
    tests.append(("Gremlin Protocol", gremlin_success))
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 DIAGNOSTIC RESULTS")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, success in tests:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{test_name:25}: {status}")
        if success:
            passed += 1
    
    logger.info("=" * 60)
    success_rate = (passed / len(tests)) * 100
    logger.info(f"Success Rate: {passed}/{len(tests)} ({success_rate:.1f}%)")
    
    # Recommendations
    logger.info("=" * 60)
    logger.info("💡 RECOMMENDATIONS")
    logger.info("=" * 60)
    
    if passed == len(tests):
        logger.info("🎉 All tests passed! Your connection should work.")
        logger.info("   If FastAPI still fails, check application startup sequence.")
    elif passed == 0:
        logger.error("🔥 All tests failed! Check:")
        logger.error("   1. Network connectivity")
        logger.error("   2. Firewall settings")
        logger.error("   3. Azure Cosmos DB service status")
        logger.error("   4. Credentials validity")
    else:
        logger.warning("⚠️ Partial success. Issues found:")
        
        for test_name, success in tests:
            if not success:
                if "DNS" in test_name:
                    logger.warning("   - DNS: Check internet connection and DNS settings")
                elif "TCP" in test_name:
                    logger.warning("   - TCP: Check firewall and port accessibility")
                elif "SSL" in test_name:
                    logger.warning("   - SSL: Check certificate validity and TLS version")
                elif "WebSocket" in test_name:
                    logger.warning("   - WebSocket: Check proxy settings and WebSocket support")
                elif "Gremlin" in test_name:
                    logger.warning("   - Gremlin: Check credentials and service configuration")
    
    return passed == len(tests)


def main():
    """Main entry point."""
    setup_logging()
    
    try:
        success = asyncio.run(run_diagnostics())
        
        if success:
            logger.info("🏁 Diagnostics completed successfully!")
            sys.exit(0)
        else:
            logger.error("🏁 Diagnostics found issues!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Diagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
