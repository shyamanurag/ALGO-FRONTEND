"""
Backend API Testing for ALGO-FRONTEND Autonomous Trading System
Final Verification Testing after Mock Data Cleanup
"""

import requests
import unittest
import sys
import json
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://50da0ed4-e9ce-42e7-8c8a-d11c27e08d6f.preview.emergentagent.com"

class AlgoFrontendBackendTest(unittest.TestCase):
    """Test suite for ALGO-FRONTEND backend API endpoints - Final Verification"""
    
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
            self.fail(f"Backend connection failed: {str(e)}")
    
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
            
            # Verify TrueData shows DISCONNECTED (expected when not configured)
            self.assertEqual(data['truedata']['status'] if 'status' in data['truedata'] else data['truedata'].get('connected', None), 
                           "DISCONNECTED", "TrueData should show DISCONNECTED")
        except Exception as e:
            self.fail(f"Health check failed: {str(e)}")
    
    def test_03_trading_signals_empty(self):
        """Test trading signals table is completely empty (0 signals)"""
        try:
            response = requests.get(f"{self.api_url}/trading-signals/active")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("signals", data)
            signals = data["signals"]
            
            # Check that there are 0 signals
            self.assertEqual(len(signals), 0, "Expected 0 active trading signals after cleanup")
            
            # Check for "No trading signals" message
            self.assertIn("message", data)
            self.assertIn("No trading signals", data["message"], "Expected 'No trading signals' message")
            
            print(f"✅ Trading signals verification successful:")
            print(f"  Total signals: {len(signals)} (Expected: 0)")
            print(f"  Message: {data['message']}")
        except Exception as e:
            self.fail(f"Trading signals verification failed: {str(e)}")
    
    def test_04_market_data_real_data_only(self):
        """Test market data live shows REAL_DATA_ONLY data integrity"""
        try:
            response = requests.get(f"{self.api_url}/market-data/live")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check for data integrity field
            self.assertIn("provider_details", data)
            provider_details = data["provider_details"]
            self.assertIn("data_integrity", provider_details)
            self.assertEqual(provider_details["data_integrity"], "REAL_DATA_ONLY", 
                           "Expected REAL_DATA_ONLY data integrity")
            
            print(f"✅ Market data integrity verification successful:")
            print(f"  Data integrity: {provider_details['data_integrity']} (Expected: REAL_DATA_ONLY)")
        except Exception as e:
            self.fail(f"Market data integrity verification failed: {str(e)}")
    
    def test_05_system_status_no_data(self):
        """Test system status shows NO_DATA source (correct for no real data feeds)"""
        try:
            response = requests.get(f"{self.api_url}/system/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("status", data)
            
            status = data["status"]
            
            # Check data source is NO_DATA
            self.assertIn("data_source", status)
            self.assertEqual(status["data_source"], "NO_DATA", "Expected NO_DATA source")
            
            print(f"✅ System status verification successful:")
            print(f"  Data source: {status['data_source']} (Expected: NO_DATA)")
            print(f"  System health: {status['system_health']}")
        except Exception as e:
            self.fail(f"System status verification failed: {str(e)}")
    
    def test_06_autonomous_status_healthy_no_signals(self):
        """Test autonomous status shows system is healthy with 7 strategies but 0 mock signals"""
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
            
            # Check that there are 0 active signals
            self.assertEqual(data["active_signals"], 0, "Expected 0 active signals after cleanup")
            
            print(f"✅ Autonomous status verification successful:")
            print(f"  Status: {data['status']}")
            print(f"  Active strategies: {data['strategies_active']} (Expected: 7)")
            print(f"  Active signals: {data['active_signals']} (Expected: 0)")
        except Exception as e:
            self.fail(f"Autonomous status verification failed: {str(e)}")
    
    def test_07_no_suspicious_mock_signals(self):
        """Test no mock signals with suspicious names exist"""
        try:
            response = requests.get(f"{self.api_url}/trading-signals/all")
            
            # If endpoint doesn't exist, try alternative
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/trading-signals/active")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("signals", data)
            signals = data["signals"]
            
            # Check for suspicious signal names
            suspicious_patterns = ["PATTERN_RECOGNITION", "VOLUME_SPIKE", "MOMENTUM_BREAKOUT"]
            suspicious_signals = []
            
            for signal in signals:
                for pattern in suspicious_patterns:
                    if pattern.lower() in str(signal).lower():
                        suspicious_signals.append(signal)
            
            self.assertEqual(len(suspicious_signals), 0, 
                           f"Found {len(suspicious_signals)} suspicious mock signals: {suspicious_signals}")
            
            print(f"✅ No suspicious mock signals verification successful:")
            print(f"  Total signals: {len(signals)} (Expected: 0)")
            print(f"  Suspicious signals found: {len(suspicious_signals)} (Expected: 0)")
        except Exception as e:
            self.fail(f"Suspicious mock signals verification failed: {str(e)}")
    
    def test_08_perfect_score_signals_check(self):
        """Test no signals with perfect 10.0 scores exist (database trigger should prevent)"""
        try:
            response = requests.get(f"{self.api_url}/trading-signals/all")
            
            # If endpoint doesn't exist, try alternative
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/trading-signals/active")
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("signals", data)
            signals = data["signals"]
            
            # Check for perfect 10.0 score signals
            perfect_score_signals = [s for s in signals if s.get("quality_score", 0) == 10.0]
            
            self.assertEqual(len(perfect_score_signals), 0, 
                           f"Found {len(perfect_score_signals)} signals with perfect 10.0 scores")
            
            print(f"✅ No perfect score signals verification successful:")
            print(f"  Perfect score signals found: {len(perfect_score_signals)} (Expected: 0)")
        except Exception as e:
            self.fail(f"Perfect score signals verification failed: {str(e)}")
    
    def test_09_data_source_verification(self):
        """Test data source verification for TrueData and Zerodha"""
        try:
            response = requests.get(f"{self.api_url}/system/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("status", data)
            status = data["status"]
            
            # Check TrueData shows DISCONNECTED
            self.assertIn("truedata", status)
            truedata = status["truedata"]
            self.assertIn("connected", truedata)
            self.assertFalse(truedata["connected"], "TrueData should show disconnected")
            
            # Check Zerodha shows not configured
            self.assertIn("zerodha", status)
            zerodha = status["zerodha"]
            self.assertIn("configured", zerodha)
            self.assertFalse(zerodha["configured"], "Zerodha should show not configured")
            
            print(f"✅ Data source verification successful:")
            print(f"  TrueData connected: {truedata['connected']} (Expected: False)")
            print(f"  Zerodha configured: {zerodha['configured']} (Expected: False)")
        except Exception as e:
            self.fail(f"Data source verification failed: {str(e)}")
    
    def test_10_admin_metrics_verification(self):
        """Test admin metrics show 0 signals and correct system health"""
        try:
            response = requests.get(f"{self.api_url}/admin/overall-metrics")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("metrics", data)
            
            metrics = data["metrics"]
            
            # Check total signals is 0
            self.assertIn("total_signals", metrics)
            self.assertEqual(metrics["total_signals"], 0, "Expected 0 total signals")
            
            # Check active strategies is 7
            self.assertIn("active_strategies", metrics)
            self.assertEqual(metrics["active_strategies"], 7, "Expected 7 active strategies")
            
            print(f"✅ Admin metrics verification successful:")
            print(f"  Total signals: {metrics['total_signals']} (Expected: 0)")
            print(f"  Active strategies: {metrics['active_strategies']} (Expected: 7)")
            print(f"  System health: {metrics['system_health']}")
        except Exception as e:
            self.fail(f"Admin metrics verification failed: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting ALGO-FRONTEND Backend API Final Verification Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
