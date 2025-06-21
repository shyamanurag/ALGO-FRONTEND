import unittest
import json
from fastapi.testclient import TestClient
from datetime import datetime

try:
    from backend.main import app, get_app_state, get_market_data_state, AppState, MarketDataState
except ImportError:
    from backend.server import app, get_app_state, get_market_data_state, AppState, MarketDataState

# Suppress most logging for tests
import logging
logging.basicConfig(level=logging.CRITICAL)
logger_test = logging.getLogger(__name__)
# logger_test.setLevel(logging.DEBUG)


class TestWebhookFlow(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        # Create clean AppState for each test, specifically MarketDataState
        self.test_app_state = AppState() # Using a real AppState
        # We will specifically override get_market_data_state to return
        # self.test_app_state.market_data

        # Override FastAPI dependencies
        # The webhook route depends on MarketDataState directly
        app.dependency_overrides[get_market_data_state] = lambda: self.test_app_state.market_data
        # If any part of error handling or utils within webhook route path uses full app_state:
        app.dependency_overrides[get_app_state] = lambda: self.test_app_state


    def tearDown(self):
        # Clear dependency overrides after each test
        app.dependency_overrides = {}

    def test_01_truedata_webhook_single_valid_tick(self):
        logger_test.debug("Running test_01_truedata_webhook_single_valid_tick")
        payload = {
            "symbol": "NIFTY_FUT",
            "ltp": 18500.75,
            "volume": 1000,
            "open": 18400,
            "high": 18550,
            "low": 18350,
            "change": 100.75,
            "change_percent": 0.55,
            "timestamp": "2023-10-27T10:00:00Z"
        }

        response = self.client.post("/api/webhook/truedata", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"] # Assuming create_api_success_response structure
        self.assertEqual(data["symbols_received_count"], 1)
        self.assertIn("NIFTY_FUT", data["symbols"])

        # Verify app_state update
        md_state = self.test_app_state.market_data
        self.assertIn("NIFTY_FUT", md_state.live_market_data)
        self.assertEqual(md_state.live_market_data["NIFTY_FUT"]["ltp"], 18500.75)
        self.assertTrue(md_state.truedata_connected)
        self.assertIsNotNone(md_state.market_data_last_update)
        self.assertEqual(md_state.active_data_source, "truedata")


    def test_02_truedata_webhook_list_of_valid_ticks(self):
        logger_test.debug("Running test_02_truedata_webhook_list_of_valid_ticks")
        payload = [
            {"symbol": "RELIANCE", "LTP": 2300.00, "Volume": 5000},
            {"symbol": "TCS", "ltp": 3300.50, "volume": 3000, "change_percent": 1.2}
        ]

        response = self.client.post("/api/webhook/truedata", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["symbols_received_count"], 2)
        self.assertIn("RELIANCE", data["symbols"])
        self.assertIn("TCS", data["symbols"])

        md_state = self.test_app_state.market_data
        self.assertIn("RELIANCE", md_state.live_market_data)
        self.assertEqual(md_state.live_market_data["RELIANCE"]["ltp"], 2300.00)
        self.assertIn("TCS", md_state.live_market_data)
        self.assertEqual(md_state.live_market_data["TCS"]["ltp"], 3300.50)
        self.assertTrue(md_state.truedata_connected)

    def test_03_truedata_webhook_invalid_json_payload(self):
        logger_test.debug("Running test_03_truedata_webhook_invalid_json_payload")
        # Sending a non-JSON string
        response = self.client.post("/api/webhook/truedata", content="this is not json")
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("Invalid JSON payload", error_data["errors"][0]["message"])

    def test_04_truedata_webhook_missing_required_fields(self):
        logger_test.debug("Running test_04_truedata_webhook_missing_required_fields")
        # Missing 'ltp'
        payload = [{"symbol": "NIFTY_NO_LTP", "volume": 100}]
        response = self.client.post("/api/webhook/truedata", json=payload)
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("No valid ticks with symbol and ltp found in payload", error_data["errors"][0]["message"])

        # Missing 'symbol'
        payload2 = [{"ltp": 18000, "volume": 100}]
        response2 = self.client.post("/api/webhook/truedata", json=payload2)
        self.assertEqual(response2.status_code, 400)
        error_data2 = response2.json()
        self.assertIn("No valid ticks with symbol and ltp found in payload", error_data2["errors"][0]["message"])


    def test_05_truedata_webhook_invalid_payload_type(self):
        logger_test.debug("Running test_05_truedata_webhook_invalid_payload_type")
        # Sending JSON string instead of object or array
        response = self.client.post("/api/webhook/truedata", json='"a string"')
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("Invalid payload type, expected JSON object or array", error_data["errors"][0]["message"])


    def test_06_truedata_webhook_empty_list_payload(self):
        logger_test.debug("Running test_06_truedata_webhook_empty_list_payload")
        payload = []
        response = self.client.post("/api/webhook/truedata", json=payload)
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertIn("No valid ticks with symbol and ltp found in payload", error_data["errors"][0]["message"])

    def test_07_truedata_webhook_list_with_some_invalid_ticks(self):
        logger_test.debug("Running test_07_truedata_webhook_list_with_some_invalid_ticks")
        payload = [
            {"symbol": "VALIDTICK1", "ltp": 100.0},
            {"ltp": 200.0}, # Invalid, missing symbol
            {"symbol": "VALIDTICK2", "ltp": 300.0, "volume": "not_an_int"} # Valid symbol/ltp, other fields may cause issues if not parsed carefully
        ]
        # The route's current logic skips ticks with type mismatches for symbol/ltp but might process VALIDTICK2 if only symbol/ltp are checked first.
        # Let's assume it processes what it can.
        response = self.client.post("/api/webhook/truedata", json=payload)
        self.assertEqual(response.status_code, 200) # Because it processes valid ones
        data = response.json()["data"]
        self.assertEqual(data["symbols_received_count"], 2) # VALIDTICK1 and VALIDTICK2
        self.assertIn("VALIDTICK1", data["symbols"])
        self.assertIn("VALIDTICK2", data["symbols"])

        md_state = self.test_app_state.market_data
        self.assertIn("VALIDTICK1", md_state.live_market_data)
        self.assertEqual(md_state.live_market_data["VALIDTICK1"]["ltp"], 100.0)
        self.assertIn("VALIDTICK2", md_state.live_market_data)
        self.assertEqual(md_state.live_market_data["VALIDTICK2"]["ltp"], 300.0)
        # Check if volume for VALIDTICK2 was set to 0 due to "not_an_int"
        self.assertEqual(md_state.live_market_data["VALIDTICK2"]["volume"], 0)


if __name__ == '__main__':
    unittest.main()
```
