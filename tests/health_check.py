#!/usr/bin/env python3
"""
Health Check Script for FastAPI Application

This script tests the health and error handling of the FastAPI application
after the startup improvements have been implemented.

Usage:
    python health_check.py [--host HOST] [--port PORT]
"""

import asyncio
import aiohttp
import sys
import argparse
from typing import Dict, Any
from loguru import logger


class HealthChecker:
    """Health check utility for the FastAPI application."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results = []
        
    async def check_endpoint(self, session: aiohttp.ClientSession, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
        """Check a single endpoint and return results."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                content = await response.text()
                
                try:
                    json_content = await response.json()
                except:
                    json_content = None
                
                result = {
                    "endpoint": endpoint,
                    "url": url,
                    "status_code": response.status,
                    "expected_status": expected_status,
                    "success": response.status == expected_status,
                    "content_type": response.headers.get('content-type', ''),
                    "content_length": len(content),
                    "json_content": json_content,
                    "error": None
                }
                
                if result["success"]:
                    logger.info(f"✅ {endpoint} - Status: {response.status}")
                else:
                    logger.warning(f"⚠️ {endpoint} - Expected: {expected_status}, Got: {response.status}")
                    if json_content and 'detail' in json_content:
                        logger.info(f"   Error: {json_content['detail']}")
                
                return result
                
        except asyncio.TimeoutError:
            result = {
                "endpoint": endpoint,
                "url": url,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "error": "Timeout",
                "json_content": None
            }
            logger.error(f"❌ {endpoint} - Timeout")
            return result
            
        except aiohttp.ClientConnectorError:
            result = {
                "endpoint": endpoint,
                "url": url,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "error": "Connection refused",
                "json_content": None
            }
            logger.error(f"❌ {endpoint} - Connection refused")
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "url": url,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "error": str(e),
                "json_content": None
            }
            logger.error(f"❌ {endpoint} - Error: {e}")
            return result
    
    async def run_health_checks(self):
        """Run comprehensive health checks."""
        logger.info(f"🏥 Starting health checks for {self.base_url}")
        
        # Define endpoints to check
        endpoints = [
            # Basic health endpoints
            ("/api/v1/health", 200),
            ("/docs", 200),  # FastAPI docs
            
            # Application endpoints that should work without Gremlin
            ("/api/v1/schema", 200),  # Should return schema info
            
            # Endpoints that should fail gracefully when Gremlin is unavailable
            ("/api/v1/search/hotels", 503),  # Should return 503 Service Unavailable
            ("/average/TestHotel", 503),     # Should return 503 Service Unavailable
            ("/rating/TestHotel", 503),      # Should return 503 Service Unavailable
            ("/reviews/TestHotel", 503),     # Should return 503 Service Unavailable
        ]
        
        async with aiohttp.ClientSession() as session:
            # Test application startup/connectivity first
            logger.info("🔍 Testing basic connectivity...")
            
            try:
                async with session.get(f"{self.base_url}/docs", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info("✅ Application is running and responding")
                    else:
                        logger.error(f"❌ Application responded with status {response.status}")
                        return False
            except:
                logger.error("❌ Cannot connect to application - is it running?")
                logger.info("💡 Try starting the application with: python main.py")
                return False
            
            # Run endpoint checks
            logger.info("🧪 Testing endpoints...")
            
            for endpoint, expected_status in endpoints:
                result = await self.check_endpoint(session, endpoint, expected_status)
                self.results.append(result)
            
            # Print summary
            self.print_summary()
            
            return all(result["success"] for result in self.results)
    
    def print_summary(self):
        """Print health check summary."""
        logger.info("\n" + "="*60)
        logger.info("📊 HEALTH CHECK SUMMARY")
        logger.info("="*60)
        
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results if result["success"])
        failed_checks = total_checks - passed_checks
        
        logger.info(f"Total Checks: {total_checks}")
        logger.info(f"Passed: {passed_checks}")
        logger.info(f"Failed: {failed_checks}")
        logger.info(f"Success Rate: {(passed_checks / total_checks * 100):.1f}%" if total_checks > 0 else "0%")
        
        if failed_checks > 0:
            logger.info("\n❌ FAILED CHECKS:")
            for result in self.results:
                if not result["success"]:
                    status = result["status_code"] or "No Response"
                    expected = result["expected_status"]
                    error = result.get("error", "Status mismatch")
                    logger.info(f"   • {result['endpoint']}: Expected {expected}, Got {status} ({error})")
        else:
            logger.info("\n🎉 All health checks passed!")
            
        logger.info("\n🔧 ERROR HANDLING VERIFICATION:")
        error_endpoints = [r for r in self.results if r["endpoint"].startswith(("/average/", "/rating/", "/reviews/", "/api/v1/search/"))]
        
        if error_endpoints:
            properly_handled = 0
            for result in error_endpoints:
                if result["json_content"] and isinstance(result["json_content"], dict):
                    if "detail" in result["json_content"] and "error_code" in result["json_content"]:
                        properly_handled += 1
                        logger.info(f"   ✅ {result['endpoint']}: Proper error structure")
                    else:
                        logger.info(f"   ⚠️ {result['endpoint']}: Basic error response")
                else:
                    logger.info(f"   ❌ {result['endpoint']}: No structured error response")
            
            logger.info(f"\nStructured Error Responses: {properly_handled}/{len(error_endpoints)}")
        
        logger.info("="*60 + "\n")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Health check for FastAPI application")
    parser.add_argument("--host", default="localhost", help="Host to check (default: localhost)")
    parser.add_argument("--port", default="8000", help="Port to check (default: 8000)")
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    checker = HealthChecker(base_url)
    success = await checker.run_health_checks()
    
    return 0 if success else 1


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Health check interrupted by user")
        sys.exit(1)
