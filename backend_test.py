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
6. Strategy Management:
   - GET /api/strategies/metrics - Strategy performance metrics
   - GET /api/strategies/performance - Detailed strategy performance data
   - GET /api/strategies/{name}/details - Individual strategy analysis
7. Trading Operations:
   - POST /api/trading/place-order - Real order placement functionality
   - GET /api/trading/orders - Order history and management
   - POST /api/trading/cancel-order/{order_id} - Cancel order
   - POST /api/trading/square-off/{symbol} - Position square-off functionality
   - POST /api/trading/square-off-all - Emergency position closure
   - GET /api/positions - Live position tracking
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
    
    def test_03_admin_overall_metrics(self):
        """Test admin overall metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/admin/overall-metrics")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("metrics", data)
            
            metrics = data["metrics"]
            required_metrics = ["total_signals", "total_trades_today", "active_strategies", 
                               "autonomous_trading", "system_health"]
            
            for field in required_metrics:
                self.assertIn(field, metrics, f"Missing metric: {field}")
            
            print(f"✅ Admin overall metrics endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Total signals: {metrics.get('total_signals')}")
            print(f"  Total trades today: {metrics.get('total_trades_today')}")
            print(f"  Active strategies: {metrics.get('active_strategies')}")
            print(f"  System health: {metrics.get('system_health')}")
            
        except Exception as e:
            self.fail(f"❌ Admin overall metrics endpoint failed: {str(e)}")
    
    def test_04_admin_recent_trades(self):
        """Test admin recent trades endpoint"""
        try:
            response = requests.get(f"{self.api_url}/admin/recent-trades")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("trades", data)
            
            trades = data["trades"]
            self.assertIsInstance(trades, list)
            
            if trades:
                trade = trades[0]
                required_fields = ["id", "symbol", "side", "quantity", "price", "time"]
                for field in required_fields:
                    self.assertIn(field, trade, f"Missing field in trade: {field}")
            
            print(f"✅ Admin recent trades endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Number of trades: {len(trades)}")
            
        except Exception as e:
            self.fail(f"❌ Admin recent trades endpoint failed: {str(e)}")
    
    def test_05_system_start_truedata(self):
        """Test system start TrueData endpoint"""
        try:
            response = requests.post(f"{self.api_url}/system/start-truedata")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            
            print(f"✅ System start TrueData endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            
        except Exception as e:
            self.fail(f"❌ System start TrueData endpoint failed: {str(e)}")
    
    def test_06_system_start_truedata_tcp(self):
        """Test system start TrueData TCP endpoint"""
        try:
            response = requests.post(f"{self.api_url}/system/start-truedata-tcp")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            
            print(f"✅ System start TrueData TCP endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            
        except Exception as e:
            self.fail(f"❌ System start TrueData TCP endpoint failed: {str(e)}")
    
    def test_07_system_truedata_status(self):
        """Test system TrueData status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/system/truedata-status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ System TrueData status endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "connection_status" in data:
                print(f"  Connection status: {data['connection_status']}")
            if "live_data_count" in data:
                print(f"  Live data count: {data['live_data_count']}")
            
        except Exception as e:
            self.fail(f"❌ System TrueData status endpoint failed: {str(e)}")
    
    def test_08_system_fix_status(self):
        """Test system fix status endpoint"""
        try:
            response = requests.post(f"{self.api_url}/system/fix-status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            self.assertIn("system_health", data)
            self.assertIn("autonomous_trading", data)
            
            print(f"✅ System fix status endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  System health: {data['system_health']}")
            print(f"  Autonomous trading: {data['autonomous_trading']}")
            
        except Exception as e:
            self.fail(f"❌ System fix status endpoint failed: {str(e)}")
    
    def test_09_system_force_live_mode(self):
        """Test system force live mode endpoint"""
        try:
            response = requests.post(f"{self.api_url}/system/force-live-mode")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("message", data)
            self.assertIn("truedata_connected", data)
            self.assertIn("autonomous_trading", data)
            
            print(f"✅ System force live mode endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data['message']}")
            print(f"  TrueData connected: {data['truedata_connected']}")
            print(f"  Autonomous trading: {data['autonomous_trading']}")
            
        except Exception as e:
            self.fail(f"❌ System force live mode endpoint failed: {str(e)}")
    
    def test_10_system_zerodha_auth_status(self):
        """Test system Zerodha auth status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/system/zerodha-auth-status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ System Zerodha auth status endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "zerodha_status" in data:
                print(f"  Zerodha status: {data['zerodha_status']}")
            
        except Exception as e:
            self.fail(f"❌ System Zerodha auth status endpoint failed: {str(e)}")
    
    def test_11_system_zerodha_authenticate(self):
        """Test system Zerodha authenticate endpoint with mock request token"""
        try:
            # Create a mock request token
            mock_request_token = "mock_request_token_for_testing"
            
            # Test the authenticate endpoint with the mock token
            response = requests.post(
                f"{self.api_url}/system/zerodha-authenticate",
                json={"request_token": mock_request_token}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ System Zerodha authenticate endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Message: {data.get('message', 'N/A')}")
            
        except Exception as e:
            self.fail(f"❌ System Zerodha authenticate endpoint failed: {str(e)}")
    
    def test_12_websocket_endpoint(self):
        """Test WebSocket endpoint"""
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
    
    def test_13_websocket_connection(self):
        """Test WebSocket connection"""
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
    
    def test_14_hybrid_data_status(self):
        """Test hybrid data status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/system/hybrid-data-status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Hybrid data status endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "hybrid_status" in data:
                print(f"  Hybrid status: {data['hybrid_status']}")
            if "primary_provider" in data:
                print(f"  Primary provider: {data['primary_provider']}")
            
        except Exception as e:
            self.fail(f"❌ Hybrid data status endpoint failed: {str(e)}")
            
    def test_15_strategies_metrics(self):
        """Test strategies metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/strategies/metrics")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Strategies metrics endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "metrics" in data:
                print(f"  Number of strategies: {len(data['metrics'])}")
                
            # Verify no mock data is present
            if "metrics" in data and data["metrics"]:
                for strategy in data["metrics"]:
                    self.assertNotIn("demo", str(strategy).lower())
                    self.assertNotIn("mock", str(strategy).lower())
            
        except Exception as e:
            self.fail(f"❌ Strategies metrics endpoint failed: {str(e)}")
            
    def test_16_strategies_performance(self):
        """Test strategies performance endpoint"""
        try:
            response = requests.get(f"{self.api_url}/strategies/performance")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Strategies performance endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "performance" in data:
                print(f"  Performance data available: {bool(data['performance'])}")
                
            # Verify no mock data is present
            if "performance" in data and data["performance"]:
                for perf in data["performance"]:
                    self.assertNotIn("demo", str(perf).lower())
                    self.assertNotIn("mock", str(perf).lower())
            
        except Exception as e:
            self.fail(f"❌ Strategies performance endpoint failed: {str(e)}")
            
    def test_17_strategy_details(self):
        """Test strategy details endpoint"""
        try:
            # Test with a known strategy name
            strategy_name = "momentum_surfer"
            response = requests.get(f"{self.api_url}/strategies/{strategy_name}/details")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Strategy details endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "details" in data:
                print(f"  Details available: {bool(data['details'])}")
                
            # Verify no mock data is present
            if "details" in data and data["details"]:
                self.assertNotIn("demo", str(data["details"]).lower())
                self.assertNotIn("mock", str(data["details"]).lower())
            
        except Exception as e:
            self.fail(f"❌ Strategy details endpoint failed: {str(e)}")
            
    def test_18_trading_place_order(self):
        """Test trading place order endpoint"""
        try:
            # Create a test order
            test_order = {
                "symbol": "NIFTY",
                "action": "BUY",
                "quantity": 50,
                "order_type": "MARKET"
            }
            
            response = requests.post(
                f"{self.api_url}/trading/place-order",
                json=test_order
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Trading place order endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "order_id" in data:
                print(f"  Order ID: {data['order_id']}")
            
        except Exception as e:
            self.fail(f"❌ Trading place order endpoint failed: {str(e)}")
            
    def test_19_trading_orders(self):
        """Test trading orders endpoint"""
        try:
            response = requests.get(f"{self.api_url}/trading/orders")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("orders", data)
            
            print(f"✅ Trading orders endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Number of orders: {len(data['orders'])}")
            
            # Verify no mock data is present
            if data["orders"]:
                for order in data["orders"]:
                    self.assertNotIn("demo", str(order).lower())
                    self.assertNotIn("mock", str(order).lower())
            
        except Exception as e:
            self.fail(f"❌ Trading orders endpoint failed: {str(e)}")
            
    def test_20_positions(self):
        """Test positions endpoint"""
        try:
            response = requests.get(f"{self.api_url}/positions")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            self.assertIn("positions", data)
            
            print(f"✅ Positions endpoint working correctly")
            print(f"  Success: {data['success']}")
            print(f"  Number of positions: {len(data['positions'])}")
            
            # Verify no mock data is present
            if data["positions"]:
                for position in data["positions"]:
                    self.assertNotIn("demo", str(position).lower())
                    self.assertNotIn("mock", str(position).lower())
            
        except Exception as e:
            self.fail(f"❌ Positions endpoint failed: {str(e)}")
            
    def test_21_square_off_all(self):
        """Test square off all endpoint"""
        try:
            response = requests.post(f"{self.api_url}/trading/square-off-all")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            self.assertIn("success", data)
            
            print(f"✅ Square off all endpoint working correctly")
            print(f"  Success: {data['success']}")
            if "message" in data:
                print(f"  Message: {data['message']}")
            
        except Exception as e:
            self.fail(f"❌ Square off all endpoint failed: {str(e)}")

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
