#!/usr/bin/env python3
"""
CORS Verification Test for Elite Autonomous Algo Trading Platform

This script tests the CORS configuration and API connectivity between the frontend and backend.
It verifies that the frontend can successfully connect to the backend without CORS errors.

Tests:
1. Backend API Health Check
2. CORS Headers Verification
3. WebSocket Connectivity
4. Key Endpoints Accessibility
"""

import requests
import sys
import json
import websocket
import threading
import time
from datetime import datetime
import re

class CORSVerificationTester:
    def __init__(self):
        # Read the frontend and backend URLs from the .env files
        self.frontend_url = self._get_frontend_url()
        self.backend_url = self._get_backend_url()
        
        if not self.frontend_url or not self.backend_url:
            print("❌ Error: Could not determine frontend or backend URLs")
            sys.exit(1)
            
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🔍 Testing CORS configuration between:")
        print(f"   Frontend: {self.frontend_url}")
        print(f"   Backend: {self.backend_url}")
    
    def _get_frontend_url(self):
        """Get the frontend URL from the .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                env_content = f.read()
                # The frontend URL is the domain itself
                return "https://fresh-start-14.preview.emergentagent.com"
        except Exception as e:
            print(f"❌ Error reading frontend URL: {e}")
            return None
    
    def _get_backend_url(self):
        """Get the backend URL from the .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                env_content = f.read()
                match = re.search(r'REACT_APP_BACKEND_URL=(.+)', env_content)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"❌ Error reading backend URL: {e}")
            return None
    
    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None, origin=None):
        """Run a single API test with CORS headers"""
        self.tests_run += 1
        url = f"{self.backend_url}{endpoint}"
        
        if not headers:
            headers = {'Content-Type': 'application/json'}
        
        # Add Origin header for CORS testing if provided
        if origin:
            headers['Origin'] = origin
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'OPTIONS':
                response = requests.options(url, headers=headers, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                self.test_results.append({
                    "name": name,
                    "success": False,
                    "error": f"Unsupported method: {method}"
                })
                return False, None
            
            # Check if CORS headers are present in the response
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"📄 Response: {json.dumps(response_data, indent=2)[:500]}...")
                except:
                    response_data = response.text
                    print(f"📄 Response: {response_data[:500]}...")
                
                self.test_results.append({
                    "name": name,
                    "success": True,
                    "status_code": response.status_code,
                    "response": response_data,
                    "cors_headers": cors_headers
                })
                
                return True, response_data
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"📄 Error Response: {json.dumps(response_data, indent=2)}")
                except:
                    response_data = response.text
                    print(f"📄 Error Response: {response_data}")
                
                self.test_results.append({
                    "name": name,
                    "success": False,
                    "status_code": response.status_code,
                    "response": response_data,
                    "cors_headers": cors_headers
                })
                
                return False, response_data
        
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
            return False, None
    
    def test_cors_preflight(self, endpoint):
        """Test CORS preflight request for an endpoint"""
        print(f"\n🔍 Testing CORS Preflight for {endpoint}...")
        
        headers = {
            'Origin': self.frontend_url,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        return self.run_test(
            f"CORS Preflight for {endpoint}",
            "OPTIONS",
            endpoint,
            200,  # or 204, both are acceptable for OPTIONS
            headers=headers,
            origin=self.frontend_url
        )
    
    def test_cors_actual_request(self, endpoint):
        """Test actual request with CORS headers"""
        print(f"\n🔍 Testing CORS Actual Request for {endpoint}...")
        
        headers = {
            'Origin': self.frontend_url,
            'Content-Type': 'application/json'
        }
        
        return self.run_test(
            f"CORS Actual Request for {endpoint}",
            "GET",
            endpoint,
            200,
            headers=headers,
            origin=self.frontend_url
        )
    
    def test_websocket_connectivity(self):
        """Test WebSocket connectivity with CORS headers"""
        print("\n🔍 Testing WebSocket Connectivity...")
        
        # Convert HTTP URL to WebSocket URL
        ws_url = self.backend_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws/autonomous-data'
        print(f"   WebSocket URL: {ws_url}")
        
        ws_success = False
        ws_error = None
        ws_received_message = None
        
        def on_message(ws, message):
            nonlocal ws_received_message
            print(f"📥 WebSocket message received: {message}")
            ws_received_message = message
        
        def on_error(ws, error):
            nonlocal ws_error
            print(f"❌ WebSocket error: {error}")
            ws_error = error
        
        def on_close(ws, close_status_code, close_msg):
            print(f"🔌 WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            nonlocal ws_success
            print("✅ WebSocket connection opened successfully")
            ws_success = True
            print("📤 Sending ping message...")
            ws.send(json.dumps({"type": "ping"}))
        
        def ws_thread():
            # Add Origin header for CORS testing
            headers = {
                'Origin': self.frontend_url
            }
            
            ws = websocket.WebSocketApp(
                ws_url,
                header=headers,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=5, ping_timeout=3)
        
        # Start WebSocket connection in a separate thread
        self.tests_run += 1
        thread = threading.Thread(target=ws_thread)
        thread.daemon = True
        thread.start()
        
        # Wait for the connection to establish or fail
        timeout = 10
        start_time = time.time()
        while time.time() - start_time < timeout:
            if ws_success or ws_error:
                break
            time.sleep(0.5)
        
        # Wait a bit more for potential messages
        if ws_success:
            time.sleep(2)
        
        # Record the result
        if ws_success:
            self.tests_passed += 1
            print("✅ WebSocket connection test passed")
            if ws_received_message:
                print(f"✅ WebSocket received response: {ws_received_message}")
            
            self.test_results.append({
                "name": "WebSocket Connection Test",
                "success": True,
                "response": ws_received_message
            })
        else:
            print(f"❌ WebSocket connection test failed: {ws_error}")
            self.test_results.append({
                "name": "WebSocket Connection Test",
                "success": False,
                "error": str(ws_error) if ws_error else "Connection timed out"
            })
        
        print("Note: WebSocket testing complete.")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 CORS Verification Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test["success"]]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test.get('error') or test.get('status_code')}")
        
        # Print success rate
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        # Print CORS status
        cors_tests = [test for test in self.test_results if test.get('cors_headers')]
        cors_success = all(
            test.get('cors_headers', {}).get('Access-Control-Allow-Origin') for test in cors_tests
        )
        
        if cors_success:
            print("\n✅ CORS configuration appears to be working correctly")
        else:
            print("\n❌ CORS configuration may have issues")
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": success_rate,
            "failed_tests": failed_tests,
            "cors_success": cors_success
        }
    
    def run_verification_tests(self):
        """Run all verification tests"""
        print("\n🚀 Starting CORS Verification Tests...")
        
        # Test 1: Backend API Health Check
        self.run_test("Backend API Health Check", "GET", "/api/health", origin=self.frontend_url)
        self.run_test("Backend API System Status", "GET", "/api/system/status", origin=self.frontend_url)
        
        # Test 2: CORS Headers Verification
        self.test_cors_preflight("/api/health")
        self.test_cors_preflight("/api/system/status")
        self.test_cors_preflight("/api/market-data/live")
        
        # Test 3: WebSocket Connectivity
        self.test_websocket_connectivity()
        
        # Test 4: Key Endpoints Accessibility
        self.test_cors_actual_request("/api/health")
        self.test_cors_actual_request("/api/system/status")
        self.test_cors_actual_request("/api/market-data/live")
        
        # Test TrueData endpoints
        self.run_test("TrueData Connect Endpoint", "POST", "/api/truedata/connect", data={}, origin=self.frontend_url)
        self.run_test("TrueData Disconnect Endpoint", "POST", "/api/truedata/disconnect", data={}, origin=self.frontend_url)
        
        # Print summary
        return self.print_summary()

def main():
    tester = CORSVerificationTester()
    results = tester.run_verification_tests()
    
    # Exit with appropriate code
    if results["cors_success"] and results["tests_passed"] >= results["tests_run"] * 0.8:
        print("\n✅ CORS configuration has been successfully verified!")
        return 0
    else:
        print("\n⚠️ CORS configuration may still have issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())