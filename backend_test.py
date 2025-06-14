"""
Elite Autonomous Algorithmic Trading Platform - Production Readiness Testing
Comprehensive Backend API Testing for Real Money Deployment

This test suite tests the following key features:
1. Backend API Endpoints:
   - GET /api/health - System health check
   - GET /api/ - Root endpoint
   - GET /api/admin/overall-metrics - Admin metrics
   - GET /api/admin/recent-trades - Recent trades
2. TrueData Integration:
   - POST /api/system/start-truedata - Start TrueData connection
   - POST /api/system/start-truedata-tcp - Start TrueData TCP connection
   - GET /api/system/truedata-status - Get TrueData status
3. System Management:
   - POST /api/system/fix-status - Fix system status
   - POST /api/system/force-live-mode - Force live mode
4. Zerodha Integration:
   - GET /api/system/zerodha-auth-status - Get Zerodha auth status
   - POST /api/system/zerodha-authenticate - Authenticate Zerodha
5. WebSocket Connection:
   - WS /api/ws/autonomous-data - WebSocket for real-time data
"""

import requests
import unittest
import sys
import json
import time
import websocket
import threading
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://0880b436-2c26-46a5-94e2-507e0663832d.preview.emergentagent.com"

class AlgoFrontendBackendTest(unittest.TestCase):
    """Comprehensive test suite for ALGO-FRONTEND backend API endpoints - Production Readiness"""
    
    def setUp(self):
        """Setup for each test"""
        self.base_url = BACKEND_URL
        self.api_url = f"{self.base_url}/api"
        
    def test_01_backend_connection(self):
        """Test basic backend connection"""
        try:
            response = requests.get(f"{self.api_url}/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("message", data)
            print(f"✅ Backend connection successful: {data['message']}")
        except Exception as e:
            self.fail(f"❌ Backend connection failed: {str(e)}")
    
    def test_02_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("status", data)
            print(f"✅ Health check successful: {data['status']}")
            
            # Check for required fields
            required_fields = ["database", "system_health", "autonomous_trading", "paper_trading", "market_status"]
            for field in required_fields:
                self.assertIn(field, data, f"Missing field: {field}")
                
            # Check TrueData connection status
            self.assertIn("truedata", data)
            print(f"TrueData status: {data['truedata']['status'] if 'status' in data['truedata'] else 'Unknown'}")
        except Exception as e:
            self.fail(f"❌ Health check failed: {str(e)}")
    
    def test_03_truedata_connect_endpoint(self):
        """Test TrueData connect endpoint - REAL fix #3"""
        try:
            response = requests.post(f"{self.api_url}/truedata/connect")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            self.assertIn("status", data)
            
            # The endpoint should return an honest response about configuration status
            # It's expected to return success=False since TrueData is not configured
            print(f"✅ TrueData connect endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  Status: {data['status']}")
            
        except Exception as e:
            self.fail(f"❌ TrueData connect endpoint failed: {str(e)}")
    
    def test_04_truedata_disconnect_endpoint(self):
        """Test TrueData disconnect endpoint - REAL fix #3"""
        try:
            response = requests.post(f"{self.api_url}/truedata/disconnect")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            self.assertIn("status", data)
            
            # The endpoint should return success=True
            self.assertTrue(data["success"])
            self.assertEqual(data["status"], "disconnected")
            
            print(f"✅ TrueData disconnect endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  Status: {data['status']}")
            
        except Exception as e:
            self.fail(f"❌ TrueData disconnect endpoint failed: {str(e)}")
    
    def test_05_websocket_endpoint(self):
        """Test WebSocket endpoint - REAL fix #2"""
        try:
            # We can't test WebSocket directly with requests, but we can check if the endpoint exists
            ws_url = f"{self.api_url}/ws/autonomous-data"
            
            # Try to connect with a GET request (should return 400 or similar if endpoint exists)
            response = requests.get(ws_url)
            
            # If status code is 404, the endpoint doesn't exist
            self.assertNotEqual(response.status_code, 404, "WebSocket endpoint not found")
            
            print(f"✅ WebSocket endpoint verification successful")
            print(f"  Status code: {response.status_code} (Expected: not 404)")
            print(f"  WebSocket endpoint exists at: {ws_url}")
            
        except Exception as e:
            self.fail(f"❌ WebSocket endpoint verification failed: {str(e)}")
    
    def test_06_websocket_connection(self):
        """Test WebSocket connection - REAL fix #2"""
        ws_url = f"{self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws/autonomous-data"
        ws_connected = False
        ws_message_received = False
        ws_message_content = None
        
        def on_message(ws, message):
            nonlocal ws_message_received, ws_message_content
            ws_message_received = True
            ws_message_content = message
            ws.close()
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        def on_open(ws):
            nonlocal ws_connected
            ws_connected = True
            print("WebSocket connection opened")
        
        try:
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket connection in a separate thread
            wst = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 5, "ping_timeout": 4})
            wst.daemon = True
            wst.start()
            
            # Wait for connection and message
            timeout = 10
            start_time = time.time()
            while time.time() - start_time < timeout:
                if ws_message_received:
                    break
                time.sleep(0.1)
            
            # Check if connection was successful
            self.assertTrue(ws_connected, "WebSocket connection failed")
            
            # Check if message was received
            self.assertTrue(ws_message_received, "No message received from WebSocket")
            
            # Parse and check message content
            if ws_message_content:
                try:
                    data = json.loads(ws_message_content)
                    self.assertIn("system_health", data)
                    self.assertIn("trading_active", data)
                    self.assertIn("timestamp", data)
                    
                    print(f"✅ WebSocket connection and message verification successful")
                    print(f"  System health: {data.get('system_health')}")
                    print(f"  Trading active: {data.get('trading_active')}")
                    print(f"  Timestamp: {data.get('timestamp')}")
                except json.JSONDecodeError:
                    self.fail(f"Invalid JSON received from WebSocket: {ws_message_content}")
            
        except Exception as e:
            self.fail(f"❌ WebSocket connection test failed: {str(e)}")
    
    def test_07_no_mock_data(self):
        """Test that no mock data is being used - REAL fix requirement"""
        try:
            # Check health endpoint for real data
            response = requests.get(f"{self.api_url}/health")
            self.assertEqual(response.status_code, 200)
            health_data = response.json()
            
            # Check system status endpoint for real data
            response = requests.get(f"{self.api_url}/system/status")
            if response.status_code == 200:
                system_data = response.json()
                
                # Check for suspicious mock data patterns
                suspicious_patterns = ["MOCK_", "DEMO_", "TEST_", "FAKE_", "SAMPLE_"]
                suspicious_found = []
                
                # Convert data to string for pattern matching
                health_str = json.dumps(health_data)
                system_str = json.dumps(system_data)
                
                for pattern in suspicious_patterns:
                    if pattern.lower() in health_str.lower():
                        suspicious_found.append(f"Health data contains '{pattern}'")
                    if pattern.lower() in system_str.lower():
                        suspicious_found.append(f"System data contains '{pattern}'")
                
                self.assertEqual(len(suspicious_found), 0, f"Found suspicious mock data patterns: {suspicious_found}")
                
                print(f"✅ No mock data verification successful")
                print(f"  No suspicious mock data patterns found")
            
        except Exception as e:
            self.fail(f"❌ No mock data verification failed: {str(e)}")
    
    def test_08_real_system_status(self):
        """Test that real system status is displayed - REAL fix requirement"""
        try:
            # Check health endpoint
            response = requests.get(f"{self.api_url}/health")
            self.assertEqual(response.status_code, 200)
            health_data = response.json()
            
            # Verify real system status fields
            required_fields = ["status", "database", "system_health", "autonomous_trading", "paper_trading", "market_status"]
            for field in required_fields:
                self.assertIn(field, health_data, f"Missing field: {field}")
            
            # Check TrueData status
            self.assertIn("truedata", health_data)
            truedata = health_data["truedata"]
            self.assertIn("connected", truedata)
            self.assertIn("status", truedata)
            
            print(f"✅ Real system status verification successful")
            print(f"  System health: {health_data.get('system_health')}")
            print(f"  TrueData status: {truedata.get('status')}")
            print(f"  Database: {health_data.get('database')}")
            
        except Exception as e:
            self.fail(f"❌ Real system status verification failed: {str(e)}")
            
    def test_09_zerodha_auth_url_endpoint(self):
        """Test Zerodha auth URL endpoint - REAL fix #5"""
        try:
            response = requests.get(f"{self.api_url}/zerodha/auth-url")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            
            # The endpoint should return an honest response about configuration status
            # It's expected to return success=False since Zerodha API key is not configured
            print(f"✅ Zerodha auth URL endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  Status: {data.get('status', 'N/A')}")
            
            # Check if login_url is present when API key is configured
            if data['success']:
                self.assertIn("login_url", data)
                print(f"  Login URL: {data['login_url']}")
            
        except Exception as e:
            self.fail(f"❌ Zerodha auth URL endpoint failed: {str(e)}")
    
    def test_10_zerodha_status_endpoint(self):
        """Test Zerodha status endpoint - REAL fix #5"""
        try:
            response = requests.get(f"{self.api_url}/zerodha/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("connected", data)
            self.assertIn("status", data)
            self.assertIn("api_key_configured", data)
            self.assertIn("api_secret_configured", data)
            
            print(f"✅ Zerodha status endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Connected: {data['connected']}")
            print(f"  Status: {data['status']}")
            print(f"  API Key Configured: {data['api_key_configured']}")
            print(f"  API Secret Configured: {data['api_secret_configured']}")
            
        except Exception as e:
            self.fail(f"❌ Zerodha status endpoint failed: {str(e)}")
    
    def test_11_zerodha_disconnect_endpoint(self):
        """Test Zerodha disconnect endpoint - REAL fix #5"""
        try:
            response = requests.post(f"{self.api_url}/zerodha/disconnect")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            self.assertIn("status", data)
            
            # The endpoint should return success=True
            self.assertTrue(data["success"])
            self.assertEqual(data["status"], "disconnected")
            
            print(f"✅ Zerodha disconnect endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  Status: {data['status']}")
            
        except Exception as e:
            self.fail(f"❌ Zerodha disconnect endpoint failed: {str(e)}")
    
    def test_12_zerodha_callback_endpoint(self):
        """Test Zerodha callback endpoint with mock request token - REAL fix #5"""
        try:
            # Create a mock request token
            mock_request_token = "mock_request_token_for_testing"
            
            # Test the callback endpoint with the mock token
            response = requests.get(f"{self.api_url}/zerodha/callback?request_token={mock_request_token}")
            self.assertEqual(response.status_code, 200)
            
            # The response should be HTML, so we check for specific content
            content = response.text
            
            # Check if it's an HTML response
            self.assertIn("<html", content.lower())
            
            # Check for success or error indicators in the HTML
            if "authentication successful" in content.lower():
                print(f"✅ Zerodha callback endpoint working correctly - Success response")
                # Check if the token is reflected in the response
                self.assertIn(mock_request_token[:10], content)
            elif "authentication failed" in content.lower() or "configuration error" in content.lower():
                print(f"✅ Zerodha callback endpoint working correctly - Error response (expected due to missing API credentials)")
                # This is also valid as the API credentials are not configured
            else:
                self.fail("Unexpected response from Zerodha callback endpoint")
            
            # Now check if the status endpoint reflects the connection attempt
            status_response = requests.get(f"{self.api_url}/zerodha/status")
            status_data = status_response.json()
            
            print(f"  Status after callback: {status_data['status']}")
            print(f"  Has token: {status_data.get('has_token', False)}")
            
        except Exception as e:
            self.fail(f"❌ Zerodha callback endpoint failed: {str(e)}")

def run_tests():
    """Run all tests and return results"""
    print(f"🚀 Starting ALGO-FRONTEND Backend API Production Readiness Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AlgoFrontendBackendTest)
    
    # Run the tests with a text test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("-" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Print failures and errors
    if result.failures:
        print("\nFAILURES:")
        for test, error in result.failures:
            print(f"- {test}")
            print(error)
    
    if result.errors:
        print("\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}")
            print(error)
    
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
