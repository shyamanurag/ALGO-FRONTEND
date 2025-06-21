import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from kiteconnect import KiteConnect
from kiteconnect.exceptions import (
    TokenException, InputException, GeneralException, NetworkException, DataException,
    OrderException, PermissionException
)

# Module to test
from backend.src.clients.zerodha_client import (
    ConsolidatedZerodhaClient,
    ZerodhaTokenError,
    ZerodhaAPIError
)
# Mock AppState and AppSettings
from backend.src.app_state import AppState, MarketDataState, SystemOverallState, ClientsState
from backend.src.config import AppSettings as RealAppSettings # Use real one for structure, but mock instance

# Suppress most logging for tests
import logging
logging.basicConfig(level=logging.CRITICAL)
logger_test = logging.getLogger(__name__)
# logger_test.setLevel(logging.DEBUG)


class MockKiteConnect:
    def __init__(self, api_key=None, access_token=None, timeout=None):
        self.api_key = api_key
        self.access_token = access_token
        self.public_token = None
        self.user_id = None
        self.timeout = timeout
        self.session_hook = None # Not typically used in V3 like this

        # Mock methods that will be called by the client
        self.generate_session = MagicMock()
        self.profile = MagicMock()
        self.margins = MagicMock()
        self.positions = MagicMock()
        self.orders = MagicMock()
        self.place_order = MagicMock()
        self.cancel_order = MagicMock()
        self.invalidate_access_token = MagicMock() # Or logout()
        self.login_url = MagicMock(return_value="https://test.kite.trade/connect/login?api_key=test_api_key&v=3")
        self.set_access_token = MagicMock(side_effect=self._set_access_token_effect)

    def _set_access_token_effect(self, access_token):
        self.access_token = access_token
        logger_test.debug(f"MockKiteConnect: access_token set to {access_token}")


class TestConsolidatedZerodhaClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_settings = RealAppSettings(
            ZERODHA_API_KEY="test_api_key",
            ZERODHA_API_SECRET="test_api_secret",
            DEFAULT_HTTP_TIMEOUT_SECONDS=10,
            DEFAULT_ORDER_TAG="UnitTestApp"
        )
        self.mock_app_state = AppState()
        self.mock_app_state.config = self.mock_settings # Important: client uses app_state.config for some things indirectly

        # Mock the database part of app_state.clients if needed for token persistence
        self.mock_app_state.clients.db_pool = AsyncMock() # Mock the pool itself

        # Patch KiteConnect instantiation within the client module
        self.patcher_kite_connect = patch('backend.src.clients.zerodha_client.KiteConnect', MockKiteConnect)
        self.MockKiteConnectClass = self.patcher_kite_connect.start()

        # Patch database calls made by the client
        self.patcher_execute_db = patch('backend.src.clients.zerodha_client.execute_db_query', AsyncMock(return_value=None))
        self.mock_execute_db_query = self.patcher_execute_db.start()

        self.patcher_fetch_one_db = patch('backend.src.clients.zerodha_client.fetch_one_db', AsyncMock(return_value=None))
        self.mock_fetch_one_db = self.patcher_fetch_one_db.start()

        # Create client instance for each test
        self.client = ConsolidatedZerodhaClient(self.mock_settings, self.mock_app_state)
        # The KiteConnect instance is now self.client.kite, which is an instance of MockKiteConnect
        self.mock_kite_sdk_instance = self.client.kite


    async def asyncTearDown(self):
        self.patcher_kite_connect.stop()
        self.patcher_execute_db.stop()
        self.patcher_fetch_one_db.stop()

    def test_01_initialization(self):
        logger_test.debug("Running test_01_initialization")
        self.assertIsNotNone(self.client.kite)
        self.MockKiteConnectClass.assert_called_once_with(
            api_key="test_api_key",
            timeout=10
        )
        self.assertEqual(self.client.api_key, "test_api_key")
        self.assertIsNone(self.client.access_token)

    async def test_02_generate_session_success(self):
        logger_test.debug("Running test_02_generate_session_success")
        mock_session_data = {
            "access_token": "new_access_token",
            "public_token": "new_public_token",
            "user_id": "TESTUSER123",
            # other fields...
        }
        self.mock_kite_sdk_instance.generate_session.return_value = mock_session_data

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_session_data # Simulate sync call in thread

            success = await self.client.generate_session("test_request_token")

            self.assertTrue(success)
            self.assertEqual(self.client.access_token, "new_access_token")
            self.assertEqual(self.client.public_token, "new_public_token")
            self.assertEqual(self.client.current_user_id, "TESTUSER123")
            self.assertTrue(self.mock_app_state.market_data.zerodha_data_connected)
            self.assertEqual(self.mock_app_state.market_data.active_data_source, "zerodha")

            self.mock_kite_sdk_instance.generate_session.assert_called_once_with("test_request_token", "test_api_secret")
            self.mock_kite_sdk_instance.set_access_token.assert_called_once_with("new_access_token")

            # Verify DB persistence
            self.mock_execute_db_query.assert_called_once()
            db_call_args = self.mock_execute_db_query.call_args[0]
            self.assertIn("INSERT OR REPLACE INTO auth_tokens", db_call_args[0]) # Check query string
            self.assertEqual(db_call_args[1], 'zerodha') # provider
            self.assertEqual(db_call_args[2], 'TESTUSER123') # user_id
            self.assertEqual(db_call_args[3], 'new_access_token') # access_token


    async def test_03_generate_session_token_exception(self):
        logger_test.debug("Running test_03_generate_session_token_exception")
        self.mock_kite_sdk_instance.generate_session.side_effect = TokenException("Invalid token")

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = TokenException("Invalid token")

            with self.assertRaises(ZerodhaTokenError) as context:
                await self.client.generate_session("invalid_request_token")

            self.assertIn("Failed to generate session due to token issue: Invalid token", str(context.exception))
            self.assertFalse(self.mock_app_state.market_data.zerodha_data_connected)
            self.assertIsNone(self.client.access_token)

    async def test_04_set_access_token_success_and_verify(self):
        logger_test.debug("Running test_04_set_access_token_success_and_verify")
        # Mock the profile call which is used for verification
        self.mock_kite_sdk_instance.profile.return_value = {"user_id": "USERFROMDB"}

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {"user_id": "USERFROMDB"} # For the get_profile call

            result = await self.client.set_access_token("db_access_token", user_id="USERFROMDB", public_token="db_public_token")

            self.assertTrue(result)
            self.assertEqual(self.client.access_token, "db_access_token")
            self.assertEqual(self.client.current_user_id, "USERFROMDB")
            self.assertTrue(self.mock_app_state.market_data.zerodha_data_connected)
            self.mock_kite_sdk_instance.set_access_token.assert_called_with("db_access_token")
            self.mock_kite_sdk_instance.profile.assert_called_once()


    async def test_05_set_access_token_verification_fails_token_exception(self):
        logger_test.debug("Running test_05_set_access_token_verification_fails_token_exception")
        self.mock_kite_sdk_instance.profile.side_effect = TokenException("Token invalid during profile fetch")

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = TokenException("Token invalid during profile fetch")

            result = await self.client.set_access_token("bad_token", user_id="USER123")

            self.assertFalse(result)
            self.assertIsNone(self.client.access_token) # Token should be cleared
            self.assertFalse(self.mock_app_state.market_data.zerodha_data_connected)
            # _handle_token_exception should have been called, check DB update for inactive
            self.mock_execute_db_query.assert_called_once_with(
                "UPDATE auth_tokens SET is_active = FALSE, updated_at = ? WHERE provider = 'zerodha' AND user_id = ?",
                unittest.mock.ANY, # for datetime.utcnow()
                "USER123",
                db_conn_or_path=self.mock_app_state.clients.db_pool
            )

    async def test_06_api_call_wrapper_token_exception(self):
        logger_test.debug("Running test_06_api_call_wrapper_token_exception")
        # First, set a token to make it seem connected
        self.client.access_token = "some_initial_token"
        self.client.current_user_id = "USERTEST"
        self.mock_app_state.market_data.zerodha_data_connected = True

        self.mock_kite_sdk_instance.margins.side_effect = TokenException("Token expired for margins")

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = TokenException("Token expired for margins")

            with self.assertRaises(ZerodhaTokenError) as context:
                await self.client.get_funds() # Uses _api_call_wrapper

            self.assertIn("Token error during margins: Token expired for margins", str(context.exception))
            self.assertIsNone(self.client.access_token) # Should be cleared by _handle_token_exception
            self.assertFalse(self.mock_app_state.market_data.zerodha_data_connected)
            # Check DB update for inactive token
            self.mock_execute_db_query.assert_called_once_with(
                "UPDATE auth_tokens SET is_active = FALSE, updated_at = ? WHERE provider = 'zerodha' AND user_id = ?",
                unittest.mock.ANY,
                "USERTEST",
                db_conn_or_path=self.mock_app_state.clients.db_pool
            )

    async def test_07_api_call_wrapper_other_kite_exception(self):
        logger_test.debug("Running test_07_api_call_wrapper_other_kite_exception")
        self.client.access_token = "valid_token" # Assume connected
        self.mock_app_state.market_data.zerodha_data_connected = True

        self.mock_kite_sdk_instance.positions.side_effect = InputException("Invalid input for positions", code=400)

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = InputException("Invalid input for positions", code=400)

            with self.assertRaises(ZerodhaAPIError) as context:
                await self.client.get_positions()

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("Invalid input for positions: Invalid input for positions", str(context.exception.message))
            self.assertTrue(self.mock_app_state.market_data.zerodha_data_connected) # Should not disconnect for non-token errors

    async def test_08_place_order_success(self):
        logger_test.debug("Running test_08_place_order_success")
        self.client.access_token = "valid_token"
        self.mock_app_state.market_data.zerodha_data_connected = True
        self.mock_kite_sdk_instance.place_order.return_value = "test_order_id_123"

        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "test_order_id_123"

            order_id = await self.client.place_order(
                variety='regular', exchange='NSE', tradingsymbol='INFY',
                transaction_type='BUY', quantity=1, product='CNC', order_type='MARKET'
            )
            self.assertEqual(order_id, "test_order_id_123")
            self.mock_kite_sdk_instance.place_order.assert_called_once_with(
                variety='regular', exchange='NSE', tradingsymbol='INFY',
                transaction_type='BUY', quantity=1, product='CNC', order_type='MARKET',
                price=None, trigger_price=None, disclosed_quantity=None,
                squareoff=None, stoploss=None, trailing_stoploss=None,
                tag=self.mock_settings.DEFAULT_ORDER_TAG
            )

    async def test_09_disconnect_success(self):
        logger_test.debug("Running test_09_disconnect_success")
        self.client.access_token = "token_to_invalidate"
        self.client.public_token = "public_token_to_clear"
        self.client.current_user_id = "USERXYZ"
        self.mock_app_state.market_data.zerodha_data_connected = True

        # Mock invalidate_access_token if it's expected to be called by KiteSDK instance
        # self.mock_kite_sdk_instance.invalidate_access_token = AsyncMock() # If it were async
        self.mock_kite_sdk_instance.invalidate_access_token = MagicMock()


        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
             # mock_to_thread for self.kite.invalidate_access_token
            mock_to_thread.return_value = None # Simulate successful sync call

            await self.client.disconnect()

            self.mock_kite_sdk_instance.invalidate_access_token.assert_called_once()
            self.assertIsNone(self.client.access_token)
            self.assertIsNone(self.client.public_token)
            self.assertFalse(self.mock_app_state.market_data.zerodha_data_connected)

            # Verify DB update for inactive token
            self.mock_execute_db_query.assert_called_once_with(
                "UPDATE auth_tokens SET is_active = FALSE, updated_at = ? WHERE provider = 'zerodha' AND user_id = ?",
                unittest.mock.ANY, # for datetime.utcnow()
                "USERXYZ",
                db_conn_or_path=self.mock_app_state.clients.db_pool
            )

if __name__ == '__main__':
    unittest.main()
```
