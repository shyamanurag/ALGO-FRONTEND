import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

try:
    from backend.main import app, get_app_state, get_settings, AppSettings, AppState
except ImportError:
    from backend.server import app, get_app_state, get_settings, AppSettings, AppState

from backend.src.api_routes.trading_routes import TradeRequest # For payload

# Suppress most logging for tests
import logging
logging.basicConfig(level=logging.CRITICAL)
logger_test = logging.getLogger(__name__)
# logger_test.setLevel(logging.DEBUG)


class TestTradingFlow(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.test_settings = AppSettings(PAPER_TRADING=True) # Ensure paper trading for these tests
        self.test_app_state = AppState()
        self.test_app_state.config = self.test_settings

        # Mock crucial dependencies
        self.test_app_state.clients.db_pool = AsyncMock() # Mock database pool

        # Mock OrderManager
        self.mock_order_manager = MagicMock()
        self.mock_order_manager.place_order = AsyncMock() # Make it async
        self.test_app_state.clients.order_manager = self.mock_order_manager

        # Mock database query function used by store_manual_trade_in_database and store_signal_in_database
        self.patcher_execute_db = patch('backend.src.api_routes.trading_routes.execute_db_query', AsyncMock(return_value=None))
        self.mock_execute_db_query_in_routes = self.patcher_execute_db.start()

        # Patch execute_strategy_loop where it's imported by trading_routes for the /generate-signal test
        # This is to prevent actual strategy execution and just check if the route calls it.
        self.patcher_strategy_loop = patch('backend.src.api_routes.trading_routes.execute_strategy_loop', AsyncMock(return_value=None))
        self.mock_execute_strategy_loop_in_routes = self.patcher_strategy_loop.start()

        # Override FastAPI dependencies
        app.dependency_overrides[get_app_state] = lambda: self.test_app_state
        app.dependency_overrides[get_settings] = lambda: self.test_settings

    def tearDown(self):
        self.patcher_execute_db.stop()
        self.patcher_strategy_loop.stop()
        app.dependency_overrides = {}


    def test_01_manual_trade_paper_trading_success(self):
        logger_test.debug("Running test_01_manual_trade_paper_trading_success")
        self.test_app_state.trading_control.paper_trading = True # Explicitly ensure paper trading

        # Expected successful paper trade response from PlaceholderOrderManager
        paper_order_id = f"PAPER_MOCK_{datetime.now().timestamp()}"
        self.mock_order_manager.place_order.return_value = {
            "success": True,
            "order_id": paper_order_id,
            "status": "FILLED", # Paper orders are often instantly filled
            "average_price": 100.50,
            "message": f"Paper order {paper_order_id} FILLED."
        }

        trade_payload = TradeRequest(
            symbol="TESTING इक्विटी", # Test with non-ASCII
            action="BUY",
            quantity=10,
            order_type="MARKET",
            user_id="test_user_001"
        )

        response = self.client.post("/api/trading/manual-trade", json=trade_payload.model_dump())

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["data"]["success"]) # Assuming create_api_success_response wraps it in "data"
        self.assertEqual(data["data"]["order_id"], paper_order_id)
        self.assertEqual(data["data"]["status"], "FILLED")

        # Verify order manager was called correctly
        self.mock_order_manager.place_order.assert_called_once()
        call_args = self.mock_order_manager.place_order.call_args[0][0] # First positional arg (order_details)
        self.assertEqual(call_args['symbol'], "TESTING इक्विटी")
        self.assertEqual(call_args['side'], "BUY")
        self.assertTrue(self.mock_order_manager.place_order.call_args[1]['is_paper']) # Keyword arg is_paper

        # Verify that store_manual_trade_in_database (which calls execute_db_query) was triggered
        # It's called if order_result.get('success') is true.
        # It makes two calls if order is FILLED (one for order, one for position)
        self.assertGreaterEqual(self.mock_execute_db_query_in_routes.call_count, 1)
        # Check the first call (order insertion)
        first_db_call_args = self.mock_execute_db_query_in_routes.call_args_list[0][0]
        self.assertIn("INSERT INTO orders", first_db_call_args[0]) # Query string
        self.assertEqual(first_db_call_args[2], trade_payload.symbol) # Symbol param
        self.assertEqual(first_db_call_args[3], trade_payload.quantity) # Quantity param


    def test_02_manual_trade_order_manager_failure(self):
        logger_test.debug("Running test_02_manual_trade_order_manager_failure")
        self.test_app_state.trading_control.paper_trading = True

        self.mock_order_manager.place_order.return_value = {
            "success": False,
            "message": "Insufficient paper funds.",
            "status": "REJECTED_PAPER_NOMONEY"
        }

        trade_payload = TradeRequest(symbol="FAILTEST", action="SELL", quantity=5)
        response = self.client.post("/api/trading/manual-trade", json=trade_payload.model_dump())

        self.assertEqual(response.status_code, 500) # Route raises HTTPException 500 on failure
        data = response.json()
        # Assuming error response structure from generic_exception_handler or http_exception_handler
        # The route raises: HTTPException(status_code=500, detail=f"Order placement failed: {error_msg}")
        self.assertIn("Order placement failed: Insufficient paper funds.", data["errors"][0]["message"])

        # Ensure DB store was NOT called for failed order
        self.mock_execute_db_query_in_routes.assert_not_called()


    def test_03_generate_signal_route_success(self):
        logger_test.debug("Running test_03_generate_signal_route_success")
        # Ensure dependent states are set as the route checks them
        self.test_app_state.system_status.database_connected = True
        self.test_app_state.trading_control.autonomous_trading_active = True # or settings.PAPER_TRADING = True

        response = self.client.post("/api/trading/generate-signal")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["data"]["success"])
        self.assertEqual(data["data"]["message"], "Strategy execution loop triggered.")

        # Verify that the (mocked) execute_strategy_loop was called
        self.mock_execute_strategy_loop_in_routes.assert_called_once_with(
            self.test_app_state, self.test_settings
        )

    def test_04_generate_signal_route_db_not_connected(self):
        logger_test.debug("Running test_04_generate_signal_route_db_not_connected")
        self.test_app_state.system_status.database_connected = False # Simulate DB not connected

        response = self.client.post("/api/trading/generate-signal")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn("Database not connected", data["errors"][0]["message"])
        self.mock_execute_strategy_loop_in_routes.assert_not_called()


if __name__ == '__main__':
    unittest.main()
```
