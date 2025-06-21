import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, time

# Assuming the FastAPI app instance is in backend.server (or backend.main)
try:
    from backend.main import app, get_app_state, get_settings, get_market_data_state, AppSettings, AppState, MarketDataState
except ImportError:
    from backend.server import app, get_app_state, get_settings, get_market_data_state, AppSettings, AppState, MarketDataState

# For overriding pytz if it's not available in test environment
# import sys
# mock_pytz = MagicMock()
# sys.modules['pytz'] = mock_pytz


class TestMarketDataFlow(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        # Create clean AppState and AppSettings for each test
        self.test_settings = AppSettings(
            MARKET_OPEN_TIME_STR="09:15",
            MARKET_CLOSE_TIME_STR="16:30", # Extended for testing market open easily
            TRUEDATA_USERNAME="test_td_user",
            DATA_PROVIDER_ENABLED=True,
            # Other settings if routes directly use them beyond what app_state provides
        )
        self.test_app_state = AppState()
        self.test_app_state.config = self.test_settings # Link settings to app_state
        self.test_app_state.clients.elite_engine = MagicMock() # Mock elite engine for /analysis route

        # Override dependencies
        app.dependency_overrides[get_app_state] = lambda: self.test_app_state
        app.dependency_overrides[get_settings] = lambda: self.test_settings
        app.dependency_overrides[get_market_data_state] = lambda: self.test_app_state.market_data

        # Mock pytz if it's problematic in the test environment
        # For this test, we'll assume pytz is available or the fallback logic in routes is acceptable.
        # If precise time testing is needed and pytz is an issue, mocking it would be done here.


    def tearDown(self):
        # Clear dependency overrides after each test
        app.dependency_overrides = {}

    def _set_market_time(self, is_open: bool):
        # Helper to mock market time for testing /status and /indices
        # This requires mocking datetime.now() within the route's scope or pytz behavior
        # For simplicity in this test, we'll adjust settings and rely on route logic.
        # A more robust way is to patch datetime.now() used by the route.
        if is_open:
            self.test_settings.MARKET_OPEN_TIME_STR = (datetime.now().time().replace(hour=datetime.now().hour-1 if datetime.now().hour > 0 else 0)).strftime("%H:%M")
            self.test_settings.MARKET_CLOSE_TIME_STR = (datetime.now().time().replace(hour=datetime.now().hour+1 if datetime.now().hour < 23 else 23)).strftime("%H:%M")
        else:
            # Make market hours such that current time is outside
            self.test_settings.MARKET_OPEN_TIME_STR = "01:00"
            self.test_settings.MARKET_CLOSE_TIME_STR = "02:00"
        # Re-initialize app_state's config if it caches parsed times (it does via properties)
        self.test_app_state.config = self.test_settings


    def test_01_market_status_td_connected_market_open(self):
        self.test_app_state.market_data.truedata_connected = True
        self.test_app_state.market_data.zerodha_data_connected = False
        self.test_app_state.market_data.active_data_source = "truedata_singleton" # or "truedata_consolidated"
        self.test_app_state.market_data.market_data_last_update = datetime.utcnow()
        self._set_market_time(is_open=True)

        response = self.client.get("/api/market-data/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        status = data["market_data_overall_status"]
        self.assertTrue(status["truedata_module_connected_flag"])
        self.assertFalse(status["zerodha_module_connected_flag"])
        self.assertTrue(status["market_hours_currently_active"])
        self.assertEqual(status["active_data_source_in_use"], self.test_app_state.market_data.active_data_source)

    def test_02_market_status_zd_connected_market_closed(self):
        self.test_app_state.market_data.truedata_connected = False
        self.test_app_state.market_data.zerodha_data_connected = True
        self.test_app_state.market_data.active_data_source = "zerodha"
        self.test_app_state.market_data.market_data_last_update = datetime.utcnow()
        self._set_market_time(is_open=False)

        response = self.client.get("/api/market-data/status")
        self.assertEqual(response.status_code, 200)
        status = response.json()["market_data_overall_status"]
        self.assertFalse(status["truedata_module_connected_flag"])
        self.assertTrue(status["zerodha_module_connected_flag"])
        self.assertFalse(status["market_hours_currently_active"])

    def test_03_market_status_both_disconnected(self):
        self.test_app_state.market_data.truedata_connected = False
        self.test_app_state.market_data.zerodha_data_connected = False
        self._set_market_time(is_open=True)

        response = self.client.get("/api/market-data/status")
        self.assertEqual(response.status_code, 200)
        status = response.json()["market_data_overall_status"]
        self.assertFalse(status["truedata_module_connected_flag"])
        self.assertFalse(status["zerodha_module_connected_flag"])

    def test_04_get_live_data_empty(self):
        response = self.client.get("/api/market-data/live")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"], {})
        self.assertEqual(data["count"], 0)

    def test_05_get_live_data_with_content(self):
        self.test_app_state.market_data.live_market_data = {
            "NIFTY": {"ltp": 18000},
            "BANKNIFTY": {"ltp": 40000}
        }
        response = self.client.get("/api/market-data/live")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["data"]["NIFTY"]["ltp"], 18000)

    def test_06_get_symbol_data_exists(self):
        self.test_app_state.market_data.live_market_data = {"RELIANCE": {"ltp": 2500}}
        response = self.client.get("/api/market-data/symbol/RELIANCE")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["ltp"], 2500)

    def test_07_get_symbol_data_not_exists(self):
        response = self.client.get("/api/market-data/symbol/INFOSYS")
        self.assertEqual(response.status_code, 404) # As per route logic

    def test_08_get_market_indices(self):
        self.test_app_state.market_data.live_market_data = {
            "NIFTY": {"ltp": 18050, "change_percent": 0.5},
            "BANKNIFTY": {"ltp": 40100, "change_percent": -0.2}
        }
        self.test_app_state.market_data.truedata_connected = True # Simulate connection
        self._set_market_time(True)

        response = self.client.get("/api/market-data/indices")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("NIFTY", data["indices_data"])
        self.assertEqual(data["indices_data"]["NIFTY"]["ltp"], 18050)
        self.assertIn("BANKNIFTY", data["indices_data"])
        self.assertEqual(data["indices_data"]["BANKNIFTY"]["ltp"], 40100)
        self.assertIn("FINNIFTY", data["indices_data"]) # Will be None
        self.assertIsNone(data["indices_data"]["FINNIFTY"])

    def test_09_market_analysis_route(self):
        # Scenario 1: elite_engine not available (already mocked in setUp, so this is default)
        # For more specific test, set it to None explicitly if setUp changes
        self.test_app_state.clients.elite_engine = None
        response = self.client.get("/api/market-data/analysis")
        self.assertEqual(response.status_code, 503) # Elite engine not available

        # Scenario 2: elite_engine available, but no key symbol data
        self.test_app_state.clients.elite_engine = MagicMock() # Make it available
        self.test_app_state.market_data.live_market_data = {"RELIANCE": {"ltp": 2000}} # No NIFTY/BANKNIFTY
        response = self.client.get("/api/market-data/analysis")
        self.assertEqual(response.status_code, 404) # No live data for key symbols

        # Scenario 3: elite_engine available, key symbols have data
        self.test_app_state.market_data.live_market_data["NIFTY"] = {"ltp": 18000}
        response = self.client.get("/api/market-data/analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("NIFTY", data["example_ltp_found"])

    def test_10_test_feed_route(self):
        initial_count = len(self.test_app_state.market_data.live_market_data)
        response = self.client.post("/api/market-data/test-feed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("NIFTY_TEST", self.test_app_state.market_data.live_market_data)
        self.assertTrue(self.test_app_state.market_data.truedata_connected) # Route simulates this
        self.assertGreater(len(self.test_app_state.market_data.live_market_data), initial_count)

if __name__ == '__main__':
    unittest.main()
```
