#!/usr/bin/env python3
"""
Backend API Testing for ALGO-FRONTEND Trading Platform
Focused on testing the three critical issues that were fixed:
1. Missing backend endpoints (/api/system/status)
2. WebSocket 403 errors (/api/ws/autonomous-data)
3. TrueData/Zerodha integration
"""

import requests
import sys
import json
import websocket
import threading
import time
from datetime import datetime

class CriticalIssuesTester:
    def __init__(self, base_url=None):
        # Use the environment variable from frontend/.env
        self.base_url = base_url
        if not self.base_url:
            print("❌ Error: No base URL provided")
            sys.exit(1)
            
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🔍 Testing API at: {self.base_url}")

    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        self.tests_run += 1
        url = f"{self.base_url}{endpoint}"
        
        if not headers:
            headers = {'Content-Type': 'application/json'}
            
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                self.test_results.append({
                    "name": name,
                    "success": False,
                    "error": f"Unsupported method: {method}"
                })
                return False, None
                
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
                    "response": response_data
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
                    "response": response_data
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

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
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
        
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "success_rate": success_rate,
            "failed_tests": failed_tests
        }

    def test_system_status_endpoint(self):
        """Test the system status endpoint (ISSUE 1)"""
        print("\n🔍 ISSUE 1: Testing System Status Endpoint...")
        
        # Test the fixed system status endpoint
        success, data = self.run_test("System Status Endpoint", "GET", "/api/system/status")
        
        if success:
            # Verify the response contains all required fields
            required_fields = [
                "system_health", "autonomous_trading", "paper_trading", 
                "trading_active", "market_open", "database_connected", 
                "truedata_connected", "zerodha_connected", "websocket_connections"
            ]
            
            if "data" in data:
                data_obj = data["data"]
                missing_fields = [field for field in required_fields if field not in data_obj]
                
                if missing_fields:
                    print(f"⚠️ System Status response is missing required fields: {missing_fields}")
                    self.test_results.append({
                        "name": "System Status Fields Validation",
                        "success": False,
                        "error": f"Missing fields: {missing_fields}"
                    })
                    self.tests_run += 1
                else:
                    print("✅ System Status response contains all required fields")
                    self.test_results.append({
                        "name": "System Status Fields Validation",
                        "success": True
                    })
                    self.tests_run += 1
                    self.tests_passed += 1
            else:
                print("⚠️ System Status response does not contain 'data' field")
        
        # Also test the health endpoint for comparison
        self.run_test("Health Check", "GET", "/api/health")

    def test_truedata_integration(self):
        """Test TrueData integration (ISSUE 3)"""
        print("\n🔍 ISSUE 3: Testing TrueData Integration...")
        
        # Test TrueData connect endpoint
        connect_success, _ = self.run_test("TrueData Connect", "POST", "/api/truedata/connect", data={
            "username": "tdwsp697",
            "password": "shyam@697"
        })
        
        # Check system status after connect attempt
        if connect_success:
            time.sleep(1)  # Give the system a moment to process the connection
            self.run_test("System Status After Connect", "GET", "/api/system/status")
        
        # Test TrueData disconnect endpoint
        disconnect_success, _ = self.run_test("TrueData Disconnect", "POST", "/api/truedata/disconnect", data={})
        
        # Check system status after disconnect
        if disconnect_success:
            time.sleep(1)  # Give the system a moment to process the disconnection
            self.run_test("System Status After Disconnect", "GET", "/api/system/status")

    def test_websocket_connectivity(self):
        """Test WebSocket connectivity (ISSUE 2)"""
        print("\n🔍 ISSUE 2: Testing WebSocket Connectivity...")
        
        # We can't directly test WebSocket connections in this test framework
        # But we can check if the endpoint is registered by making a GET request
        self.run_test("WebSocket Endpoint Check", "GET", "/api/ws/autonomous-data", expected_status=400)
        
        # Now test actual WebSocket connection
        ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws/autonomous-data'
        print(f"\n🔍 Testing WebSocket connection to: {ws_url}")
        
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
            ws = websocket.WebSocketApp(
                ws_url,
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

    def run_critical_tests(self):
        """Run tests for the three critical issues"""
        print("\n🚀 Starting Critical Issues Testing...")
        
        # Test core health endpoint first
        self.run_test("Core API Health Check", "GET", "/api/health")
        
        # Test ISSUE 1: System Status Endpoint
        self.test_system_status_endpoint()
        
        # Test ISSUE 2: WebSocket Connectivity
        self.test_websocket_connectivity()
        
        # Test ISSUE 3: TrueData Integration
        self.test_truedata_integration()
        
        # Print summary
        return self.print_summary()

def main():
    # Get backend URL from frontend/.env
    import os
    import re
    
    # Read the REACT_APP_BACKEND_URL from frontend/.env
    backend_url = None
    try:
        with open('/app/frontend/.env', 'r') as f:
            env_content = f.read()
            match = re.search(r'REACT_APP_BACKEND_URL=(.+)', env_content)
            if match:
                backend_url = match.group(1).strip()
    except Exception as e:
        print(f"❌ Error reading frontend/.env: {e}")
    
    if not backend_url:
        print("❌ Could not find REACT_APP_BACKEND_URL in frontend/.env")
        sys.exit(1)
    
    # Create tester and run tests
    tester = CriticalIssuesTester(backend_url)
    results = tester.run_critical_tests()
    
    # Exit with appropriate code
    if results["tests_passed"] == results["tests_run"]:
        print("\n✅ All critical issues have been resolved!")
        return 0
    else:
        print(f"\n⚠️ {results['tests_run'] - results['tests_passed']} tests failed. Some critical issues may still exist.")
        return 1

if __name__ == "__main__":
    sys.exit(main())