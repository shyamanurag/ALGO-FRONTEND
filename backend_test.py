"""
Backend API Testing for ALGO-FRONTEND Autonomous Trading System
Tests the enhanced features including live market data and autonomous trading engine
"""

import requests
import unittest
import sys
import json
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://50da0ed4-e9ce-42e7-8c8a-d11c27e08d6f.preview.emergentagent.com"

class AlgoFrontendBackendTest(unittest.TestCase):
    """Test suite for ALGO-FRONTEND backend API endpoints"""
    
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
        except Exception as e:
            self.fail(f"Health check failed: {str(e)}")
    
    def test_03_live_market_data(self):
        """Test enhanced live market data endpoint"""
        try:
            response = requests.get(f"{self.api_url}/market-data/live")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("indices", data)
            
            # Check for required indices
            required_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            for index in required_indices:
                self.assertIn(index, data["indices"], f"Missing index: {index}")
                
                # Check index data structure
                index_data = data["indices"][index]
                required_fields = ["ltp", "change", "change_percent", "volume", "high", "low", "open"]
                for field in required_fields:
                    self.assertIn(field, index_data, f"Missing field {field} in {index} data")
            
            # Verify realistic price ranges
            nifty_price = data["indices"]["NIFTY"]["ltp"]
            banknifty_price = data["indices"]["BANKNIFTY"]["ltp"]
            finnifty_price = data["indices"]["FINNIFTY"]["ltp"]
            
            self.assertGreater(nifty_price, 15000, "NIFTY price too low")
            self.assertLess(nifty_price, 25000, "NIFTY price too high")
            self.assertGreater(banknifty_price, 35000, "BANKNIFTY price too low")
            self.assertLess(banknifty_price, 55000, "BANKNIFTY price too high")
            self.assertGreater(finnifty_price, 15000, "FINNIFTY price too low")
            self.assertLess(finnifty_price, 25000, "FINNIFTY price too high")
            
            print(f"✅ Live market data successful:")
            print(f"  NIFTY: ₹{nifty_price}")
            print(f"  BANKNIFTY: ₹{banknifty_price}")
            print(f"  FINNIFTY: ₹{finnifty_price}")
            
            # Check connection status
            self.assertIn("connection_status", data["indices"]["NIFTY"])
            connection_status = data["indices"]["NIFTY"]["connection_status"]
            self.assertEqual(connection_status, "Live data streaming...", "Incorrect connection status")
            print(f"  Connection status: {connection_status}")
        except Exception as e:
            self.fail(f"Live market data test failed: {str(e)}")
    
    def test_04_autonomous_strategy_performance(self):
        """Test autonomous strategy performance endpoint"""
        try:
            response = requests.get(f"{self.api_url}/autonomous/strategy-performance")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("strategies", data)
            strategies = data["strategies"]
            
            # Check for all 7 strategies
            expected_strategies = [
                "MomentumSurfer", "NewsImpactScalper", "VolatilityExplosion", 
                "ConfluenceAmplifier", "PatternHunter", "LiquidityMagnet", "VolumeProfileScalper"
            ]
            
            strategy_names = [s["name"] for s in strategies]
            for strategy in expected_strategies:
                self.assertIn(strategy, strategy_names, f"Missing strategy: {strategy}")
            
            # Check that all strategies are active
            for strategy in strategies:
                self.assertEqual(strategy["status"], "ACTIVE", f"Strategy {strategy['name']} is not active")
            
            # Check allocations
            allocations = {s["name"]: s["allocation"] for s in strategies}
            self.assertEqual(allocations["MomentumSurfer"], 15, "Incorrect allocation for MomentumSurfer")
            self.assertEqual(allocations["NewsImpactScalper"], 12, "Incorrect allocation for NewsImpactScalper")
            self.assertEqual(allocations["VolatilityExplosion"], 18, "Incorrect allocation for VolatilityExplosion")
            self.assertEqual(allocations["ConfluenceAmplifier"], 20, "Incorrect allocation for ConfluenceAmplifier")
            self.assertEqual(allocations["PatternHunter"], 16, "Incorrect allocation for PatternHunter")
            self.assertEqual(allocations["LiquidityMagnet"], 14, "Incorrect allocation for LiquidityMagnet")
            self.assertEqual(allocations["VolumeProfileScalper"], 5, "Incorrect allocation for VolumeProfileScalper")
            
            print(f"✅ Autonomous strategy performance successful:")
            print(f"  Total strategies: {len(strategies)}")
            print(f"  All strategies active: {all(s['status'] == 'ACTIVE' for s in strategies)}")
            print(f"  Data source: {data.get('data_source', 'Unknown')}")
        except Exception as e:
            self.fail(f"Autonomous strategy performance test failed: {str(e)}")
    
    def test_05_autonomous_active_orders(self):
        """Test autonomous active orders endpoint"""
        try:
            response = requests.get(f"{self.api_url}/autonomous/active-orders")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("orders", data)
            self.assertIn("message", data)
            self.assertIn("data_source", data)
            
            # Data source should be AUTONOMOUS_ENGINE
            self.assertEqual(data["data_source"], "AUTONOMOUS_ENGINE", "Incorrect data source")
            
            print(f"✅ Autonomous active orders successful:")
            print(f"  Active orders: {len(data['orders'])}")
            print(f"  Message: {data['message']}")
            print(f"  Data source: {data['data_source']}")
        except Exception as e:
            self.fail(f"Autonomous active orders test failed: {str(e)}")
    
    def test_06_autonomous_system_metrics(self):
        """Test autonomous system metrics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/autonomous/system-metrics")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("metrics", data)
            
            metrics = data["metrics"]
            required_fields = [
                "daily_pnl", "total_capital", "used_capital", "available_capital", 
                "capital_utilization", "trades_today", "active_positions", "strategies_active"
            ]
            
            for field in required_fields:
                self.assertIn(field, metrics, f"Missing field: {field}")
            
            # Check total capital is 50 lakh (5000000)
            self.assertEqual(metrics["total_capital"], 5000000, "Incorrect total capital")
            
            # Check strategies active is 7
            self.assertEqual(metrics["strategies_active"], 7, "Incorrect number of active strategies")
            
            print(f"✅ Autonomous system metrics successful:")
            print(f"  Total capital: ₹{metrics['total_capital']}")
            print(f"  Used capital: ₹{metrics['used_capital']}")
            print(f"  Available capital: ₹{metrics['available_capital']}")
            print(f"  Capital utilization: {metrics['capital_utilization']}%")
            print(f"  Active strategies: {metrics['strategies_active']}")
        except Exception as e:
            self.fail(f"Autonomous system metrics test failed: {str(e)}")
    
    def test_07_system_status(self):
        """Test system status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/system/status")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertIn("success", data)
            self.assertTrue(data["success"])
            self.assertIn("status", data)
            
            status = data["status"]
            required_fields = [
                "system_health", "autonomous_trading", "paper_trading", 
                "market_status", "data_source", "truedata"
            ]
            
            for field in required_fields:
                self.assertIn(field, status, f"Missing field: {field}")
            
            # Check TrueData connection
            self.assertIn("connected", status["truedata"])
            
            print(f"✅ System status successful:")
            print(f"  System health: {status['system_health']}")
            print(f"  Autonomous trading: {status['autonomous_trading']}")
            print(f"  Paper trading: {status['paper_trading']}")
            print(f"  Market status: {status['market_status']}")
            print(f"  Data source: {status['data_source']}")
            print(f"  TrueData connected: {status['truedata']['connected']}")
        except Exception as e:
            self.fail(f"System status test failed: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting ALGO-FRONTEND Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Run tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
