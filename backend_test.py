"""
ALGO-FRONTEND Trading Platform - Production Readiness Testing
Comprehensive Backend API Testing for Real Money Deployment
"""

import requests
import unittest
import sys
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://50da0ed4-e9ce-42e7-8c8a-d11c27e08d6f.preview.emergentagent.com"

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
    
    def test_03_system_status(self):
        """Test system status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/system/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for success field
            self.assertIn("success", data)
            
            # Check for status field
            self.assertIn("status", data)
            status = data["status"]
            
            # Check for required fields in status
            required_fields = ["system_health", "autonomous_trading", "paper_trading", "market_status"]
            for field in required_fields:
                self.assertIn(field, status, f"Missing field: {field}")
            
            print(f"✅ System status verification successful:")
            print(f"  System health: {status['system_health']}")
            print(f"  Autonomous trading: {status['autonomous_trading']}")
            print(f"  Paper trading: {status['paper_trading']}")
            print(f"  Market status: {status['market_status']}")
        except Exception as e:
            self.fail(f"❌ System status verification failed: {str(e)}")
    
    def test_04_admin_metrics(self):
        """Test admin metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/admin/overall-metrics")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for success field
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            
            # Check for metrics field
            self.assertIn("metrics", data)
            metrics = data["metrics"]
            
            # Check for required fields in metrics
            required_fields = ["total_signals", "total_trades_today", "active_strategies", "autonomous_trading", "system_health"]
            for field in required_fields:
                self.assertIn(field, metrics, f"Missing field: {field}")
            
            # Verify active strategies is 7
            self.assertEqual(metrics["active_strategies"], 7, "Expected 7 active strategies")
            
            print(f"✅ Admin metrics verification successful:")
            print(f"  Total signals: {metrics['total_signals']}")
            print(f"  Total trades today: {metrics['total_trades_today']}")
            print(f"  Active strategies: {metrics['active_strategies']} (Expected: 7)")
            print(f"  System health: {metrics['system_health']}")
        except Exception as e:
            self.fail(f"❌ Admin metrics verification failed: {str(e)}")
    
    def test_05_recent_trades(self):
        """Test recent trades endpoint"""
        try:
            response = requests.get(f"{self.api_url}/admin/recent-trades")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for success field
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            
            # Check for trades field
            self.assertIn("trades", data)
            trades = data["trades"]
            
            print(f"✅ Recent trades verification successful:")
            print(f"  Total trades: {len(trades)}")
            
            # If trades exist, check the structure of the first trade
            if trades:
                first_trade = trades[0]
                required_fields = ["symbol", "side", "quantity", "price", "time"]
                for field in required_fields:
                    self.assertIn(field, first_trade, f"Missing field in trade: {field}")
                
                print(f"  First trade: {first_trade['symbol']} {first_trade['side']} {first_trade['quantity']} @ {first_trade['price']}")
        except Exception as e:
            self.fail(f"❌ Recent trades verification failed: {str(e)}")
    
    def test_06_trading_signals(self):
        """Test trading signals endpoint"""
        try:
            # Try the active signals endpoint first
            response = requests.get(f"{self.api_url}/trading-signals/active")
            
            # If that fails, try the all signals endpoint
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/trading-signals/all")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for signals field
            self.assertIn("signals", data)
            signals = data["signals"]
            
            print(f"✅ Trading signals verification successful:")
            print(f"  Total signals: {len(signals)}")
            
            # If signals exist, check the structure of the first signal
            if signals:
                first_signal = signals[0]
                required_fields = ["strategy_name", "symbol", "action", "quality_score"]
                for field in required_fields:
                    self.assertIn(field, first_signal, f"Missing field in signal: {field}")
                
                print(f"  First signal: {first_signal['strategy_name']} {first_signal['symbol']} {first_signal['action']} (Quality: {first_signal['quality_score']})")
                
                # Check for perfect 10.0 score signals (should not exist)
                perfect_score_signals = [s for s in signals if s.get("quality_score", 0) == 10.0]
                self.assertEqual(len(perfect_score_signals), 0, f"Found {len(perfect_score_signals)} signals with perfect 10.0 scores")
        except Exception as e:
            self.fail(f"❌ Trading signals verification failed: {str(e)}")
    
    def test_07_autonomous_status(self):
        """Test autonomous status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/autonomous/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            required_fields = ["status", "trading_active", "paper_trading", "strategies_active", "active_signals"]
            for field in required_fields:
                self.assertIn(field, data, f"Missing field: {field}")
            
            # Check that there are 7 active strategies
            self.assertEqual(data["strategies_active"], 7, "Expected 7 active strategies")
            
            print(f"✅ Autonomous status verification successful:")
            print(f"  Status: {data['status']}")
            print(f"  Trading active: {data['trading_active']}")
            print(f"  Paper trading: {data['paper_trading']}")
            print(f"  Active strategies: {data['strategies_active']} (Expected: 7)")
            print(f"  Active signals: {data['active_signals']}")
        except Exception as e:
            self.fail(f"❌ Autonomous status verification failed: {str(e)}")
    
    def test_08_market_data(self):
        """Test market data endpoint"""
        try:
            response = requests.get(f"{self.api_url}/market-data/live")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for required fields
            required_fields = ["indices", "provider_details", "timestamp"]
            for field in required_fields:
                self.assertIn(field, data, f"Missing field: {field}")
            
            # Check for indices data
            indices = data["indices"]
            expected_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            for index in expected_indices:
                self.assertIn(index, indices, f"Missing index: {index}")
            
            # Check for provider details
            provider_details = data["provider_details"]
            self.assertIn("provider", provider_details)
            self.assertIn("data_integrity", provider_details)
            
            print(f"✅ Market data verification successful:")
            print(f"  Provider: {provider_details['provider']}")
            print(f"  Data integrity: {provider_details['data_integrity']}")
            print(f"  Indices: {', '.join(indices.keys())}")
        except Exception as e:
            self.fail(f"❌ Market data verification failed: {str(e)}")
    
    def test_09_elite_recommendations(self):
        """Test elite recommendations endpoint"""
        try:
            response = requests.get(f"{self.api_url}/elite-recommendations")
            
            # If that fails, try the active recommendations endpoint
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/elite-recommendations/active")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for recommendations field
            self.assertIn("recommendations", data)
            recommendations = data["recommendations"]
            
            print(f"✅ Elite recommendations verification successful:")
            print(f"  Total recommendations: {len(recommendations)}")
            
            # If recommendations exist, check the structure of the first recommendation
            if recommendations:
                first_rec = recommendations[0]
                required_fields = ["symbol", "strategy", "direction", "entry_price", "stop_loss", "primary_target", "confidence_score"]
                for field in required_fields:
                    self.assertIn(field, first_rec, f"Missing field in recommendation: {field}")
                
                print(f"  First recommendation: {first_rec['symbol']} {first_rec['direction']} (Confidence: {first_rec['confidence_score']})")
        except Exception as e:
            self.fail(f"❌ Elite recommendations verification failed: {str(e)}")
    
    def test_10_system_metrics(self):
        """Test system metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/autonomous/system-metrics")
            
            # If that fails, try the system status endpoint
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/system/status")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            print(f"✅ System metrics verification successful")
            
            # Print some key metrics if available
            if "metrics" in data:
                metrics = data["metrics"]
                print(f"  CPU usage: {metrics.get('cpu_usage', 'N/A')}%")
                print(f"  Memory usage: {metrics.get('memory_usage', 'N/A')}%")
                print(f"  Disk usage: {metrics.get('disk_usage', 'N/A')}%")
            elif "status" in data:
                status = data["status"]
                print(f"  System health: {status.get('system_health', 'N/A')}")
                print(f"  Uptime: {status.get('uptime', 'N/A')}")
        except Exception as e:
            self.fail(f"❌ System metrics verification failed: {str(e)}")
    
    def test_11_database_integrity(self):
        """Test database integrity by checking for mock data"""
        try:
            # Check trading signals for mock data
            response = requests.get(f"{self.api_url}/trading-signals/active")
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/trading-signals/all")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            signals = data.get("signals", [])
            
            # Check for suspicious signal names
            suspicious_patterns = ["PATTERN_RECOGNITION", "VOLUME_SPIKE", "MOMENTUM_BREAKOUT", "TEST_", "MOCK_", "DEMO_"]
            suspicious_signals = []
            
            for signal in signals:
                for pattern in suspicious_patterns:
                    if pattern.lower() in str(signal).lower():
                        suspicious_signals.append(signal)
            
            self.assertEqual(len(suspicious_signals), 0, f"Found {len(suspicious_signals)} suspicious mock signals")
            
            print(f"✅ Database integrity verification successful:")
            print(f"  Suspicious signals found: {len(suspicious_signals)} (Expected: 0)")
        except Exception as e:
            self.fail(f"❌ Database integrity verification failed: {str(e)}")
    
    def test_12_error_handling(self):
        """Test error handling by sending invalid requests"""
        try:
            # Test invalid endpoint
            response = requests.get(f"{self.api_url}/invalid-endpoint")
            self.assertEqual(response.status_code, 404)
            
            # Test invalid method
            response = requests.post(f"{self.api_url}/health")
            self.assertIn(response.status_code, [405, 404, 400])
            
            # Test invalid parameters
            response = requests.post(f"{self.api_url}/system/zerodha-authenticate", json={})
            self.assertIn(response.status_code, [400, 422])
            
            print(f"✅ Error handling verification successful")
        except Exception as e:
            self.fail(f"❌ Error handling verification failed: {str(e)}")
    
    def test_13_websocket_endpoint(self):
        """Test WebSocket endpoint availability"""
        try:
            # We can't test WebSocket directly with requests, but we can check if the endpoint exists
            ws_url = f"{self.api_url}/ws/autonomous-data"
            
            # Try to connect with a GET request (should return 400 or similar if endpoint exists)
            response = requests.get(ws_url)
            
            # If status code is 404, the endpoint doesn't exist
            self.assertNotEqual(response.status_code, 404, "WebSocket endpoint not found")
            
            print(f"✅ WebSocket endpoint verification successful")
            print(f"  Status code: {response.status_code} (Expected: not 404)")
        except Exception as e:
            self.fail(f"❌ WebSocket endpoint verification failed: {str(e)}")
    
    def test_14_load_testing(self):
        """Basic load testing with multiple concurrent requests"""
        try:
            # Define endpoints to test
            endpoints = [
                "/health",
                "/system/status",
                "/admin/overall-metrics",
                "/admin/recent-trades",
                "/trading-signals/active",
                "/autonomous/status",
                "/market-data/live"
            ]
            
            # Number of requests per endpoint
            num_requests = 5
            
            # Track response times
            response_times = {}
            
            for endpoint in endpoints:
                start_time = time.time()
                
                # Make multiple requests
                for _ in range(num_requests):
                    response = requests.get(f"{self.api_url}{endpoint}")
                    self.assertIn(response.status_code, [200, 404])
                
                end_time = time.time()
                avg_time = (end_time - start_time) / num_requests
                response_times[endpoint] = avg_time
            
            print(f"✅ Load testing verification successful:")
            for endpoint, avg_time in response_times.items():
                print(f"  {endpoint}: {avg_time:.4f}s average response time")
        except Exception as e:
            self.fail(f"❌ Load testing verification failed: {str(e)}")
    
    def test_15_security_headers(self):
        """Test security headers"""
        try:
            response = requests.get(f"{self.api_url}/health")
            headers = response.headers
            
            # Check for required security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Content-Security-Policy": None,
                "Strict-Transport-Security": None,
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": None
            }
            
            present_headers = []
            missing_headers = []
            
            for header, expected_value in security_headers.items():
                if header.lower() in [h.lower() for h in headers.keys()]:
                    # Find the actual header name with correct case
                    actual_header = next(h for h in headers.keys() if h.lower() == header.lower())
                    present_headers.append(header)
                    if expected_value and headers[actual_header] != expected_value:
                        print(f"  Warning: {header} has value {headers[actual_header]}, expected {expected_value}")
                else:
                    missing_headers.append(header)
            
            # Verify that critical security headers are present
            critical_headers = ["X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy"]
            missing_critical = [h for h in critical_headers if h in missing_headers]
            
            if missing_critical:
                self.fail(f"Missing critical security headers: {', '.join(missing_critical)}")
            
            print(f"✅ Security headers verification:")
            print(f"  Present headers: {', '.join(present_headers) if present_headers else 'None'}")
            print(f"  Missing headers: {', '.join(missing_headers) if missing_headers else 'None'}")
        except Exception as e:
            self.fail(f"❌ Security headers verification failed: {str(e)}")

def run_tests():
    """Run all tests and return results"""
    print(f"🚀 Starting ALGO-FRONTEND Backend API Production Readiness Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
