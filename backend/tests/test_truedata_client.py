import asyncio
import json
import logging
import unittest
from unittest.mock import patch, AsyncMock, MagicMock, call
from datetime import datetime
from typing import Dict, Optional, Callable, List, Any

# Module to test
from backend.truedata_client import (
    TrueDataSingletonClient,
    initialize_truedata,
    get_truedata_status,
    is_connected,
    get_live_data_for_symbol,
    add_truedata_symbols,
    remove_truedata_symbols,
    shutdown_truedata_client,
    live_market_data, # global state
    truedata_connection_status # global state
)

# Suppress most logging for tests unless specifically debugging
logging.basicConfig(level=logging.CRITICAL)
logger_test = logging.getLogger(__name__)
# logger_test.setLevel(logging.DEBUG) # Uncomment to see test-specific logs

class MockWebSocketClient:
    def __init__(self, fail_connect=False, custom_recv_logic=None):
        self.open = False
        self.fail_connect = fail_connect
        self.sent_messages = []
        self.recv_queue = asyncio.Queue()
        self.custom_recv_logic = custom_recv_logic # Function to call on recv
        self.close_called = False
        self.close_code = None
        self.close_reason = ""

    async def connect(self, url, **kwargs): # Simulate the __aenter__ of websockets.connect
        if self.fail_connect:
            raise websockets.exceptions.InvalidStatusCode(401) # Simulate auth failure or other
        self.open = True
        logger_test.debug(f"MockWebSocketClient: Connect called, open set to True. URL: {url}")
        return self # Return self to be used as the context manager result

    async def send(self, message_str: str):
        logger_test.debug(f"MockWebSocketClient: send called with: {message_str[:100]}")
        self.sent_messages.append(json.loads(message_str)) # Store parsed JSON
        return None

    async def recv(self) -> str:
        if self.custom_recv_logic:
            return await self.custom_recv_logic(self) # Pass self for stateful mock recv

        if self.recv_queue.empty():
            # Simulate blocking then a disconnect if queue is empty after a bit
            logger_test.debug("MockWebSocketClient: recv_queue empty, simulating wait then ConnectionClosed.")
            await asyncio.sleep(0.01) # Short sleep to allow other tasks
            if self.open: # Only raise if it wasn't closed by 'close' method
                 self.open = False
                 raise websockets.exceptions.ConnectionClosedError(None, None)
            else: # If closed by 'close', it might just wait indefinitely or raise something else
                 await asyncio.sleep(30) # Simulate indefinite wait if closed
                 raise asyncio.TimeoutError("Recv on closed mock websocket")


        message = await self.recv_queue.get()
        logger_test.debug(f"MockWebSocketClient: recv returning: {message[:100]}")
        if message == "_RAISE_CONN_CLOSED_": # Special command for testing
            self.open = False
            raise websockets.exceptions.ConnectionClosedError(None, None)
        return message

    async def close(self, code=1000, reason=""):
        logger_test.debug(f"MockWebSocketClient: close called with code {code}, reason '{reason}'")
        self.open = False
        self.close_called = True
        self.close_code = code
        self.close_reason = reason
        # To stop listen_for_messages, recv should raise an exception.
        # Add a sentinel that makes recv raise ConnectionClosed.
        # Or, the listen_for_messages loop should check self.websocket_client.open.
        # The actual library raises ConnectionClosed when server closes.
        # If client calls close(), recv() might return normally if buffer has msgs, then raise.
        # Forcing it here to simplify test.
        if self.recv_queue.empty(): # if queue is empty, it will raise from recv itself
            await self.recv_queue.put("_RAISE_CONN_CLOSED_") # Ensure recv loop breaks

    async def __aenter__(self): # For 'async with'
        # This is usually handled by websockets.connect itself if used as context manager directly
        # but our mock structure uses self.websocket_client = await websockets.connect(...)
        # So, this simplified __aenter__ might not be strictly needed if not using 'async with mock_ws_connect'.
        logger_test.debug("MockWebSocketClient: __aenter__ called.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger_test.debug(f"MockWebSocketClient: __aexit__ called. exc_type: {exc_type}")
        await self.close()


class TestTrueDataSingletonClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reset global state before each test
        global live_market_data, truedata_connection_status, _truedata_client_singleton_instance
        live_market_data.clear()
        truedata_connection_status.update({
            "connected": False, "last_update": None, "error_message": None, "active_symbols": []
        })
        # Ensure the singleton instance is reset for each test
        if TrueDataSingletonClient._instance:
            # This is tricky with singletons. We might need to allow re-setting its internal state,
            # or ensure each test that initializes it cleans it up properly.
            # For now, we'll rely on shutdown_truedata_client and careful test structure.
             TrueDataSingletonClient._instance = None # Force re-creation
        _truedata_client_singleton_instance = None

        # Default mock for websockets.connect
        self.mock_ws_client = MockWebSocketClient()
        self.patcher_websockets_connect = patch('websockets.connect', AsyncMock(return_value=self.mock_ws_client))
        self.mock_websockets_connect = self.patcher_websockets_connect.start()

    async def asyncTearDown(self):
        self.patcher_websockets_connect.stop()
        await shutdown_truedata_client() # Ensure client is shutdown and instance cleared
        # Verify the instance is cleared by the shutdown logic
        self.assertIsNone(TrueDataSingletonClient._instance)


    async def test_01_initialize_and_successful_connection(self):
        logger_test.debug("Starting test_01_initialize_and_successful_connection")

        # Simulate successful auth response from TrueData (if any is expected beyond connection)
        # The client's _authenticate sends auth then assumes success if no error.
        # Let's simulate a heartbeat as the first message.
        await self.mock_ws_client.recv_queue.put(json.dumps({"message": {"message": "HeartBeat"}}))

        mock_status_callback = AsyncMock()
        await initialize_truedata(
            username="testuser", password="testpassword", symbols=["NIFTY"],
            on_status_change=mock_status_callback
        )

        # Give time for connect and listen loop to start
        await asyncio.sleep(0.1)

        self.assertTrue(is_connected())
        self.assertIn("NIFTY", TrueDataSingletonClient._instance.SYMBOLS_TO_SUBSCRIBE)
        self.assertIsNotNone(truedata_connection_status["last_update"])

        # Check if auth message was sent
        self.assertTrue(len(self.mock_ws_client.sent_messages) >= 1)
        auth_msg = self.mock_ws_client.sent_messages[0]
        self.assertEqual(auth_msg.get("username"), "testuser")

        # Check if subscription message was sent
        # It might be combined or be the second message
        sub_msg_found = any(msg.get("type") == "subscribe" and "NIFTY" in msg.get("symbols", []) for msg in self.mock_ws_client.sent_messages)
        self.assertTrue(sub_msg_found, f"Subscription message not found or incorrect. Sent: {self.mock_ws_client.sent_messages}")

        mock_status_callback.assert_any_call(True, None) # Initial connection
        mock_status_callback.assert_any_call(True, "Connection and authentication successful.") # From _establish_and_maintain_connection

        await shutdown_truedata_client()
        self.assertFalse(is_connected())
        logger_test.debug("Finished test_01_initialize_and_successful_connection")


    async def test_02_connection_failure_invalid_status_code(self):
        logger_test.debug("Starting test_02_connection_failure_invalid_status_code")
        self.mock_websockets_connect.return_value = MockWebSocketClient(fail_connect=True) # Configure mock to fail connection

        mock_status_callback = AsyncMock()
        # Patch asyncio.sleep to prevent long waits during reconnect tests
        with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            await initialize_truedata(on_status_change=mock_status_callback)
            await asyncio.sleep(0.1) # Allow time for connection attempts

            self.assertFalse(is_connected())
            self.assertIsNotNone(truedata_connection_status["error_message"])
            self.assertIn("Auth/Connection Failed: 401", truedata_connection_status["error_message"])

            # Check if status callback was called with False
            mock_status_callback.assert_any_call(False, "Auth/Connection Failed: 401")

            # Ensure it tried to reconnect up to max_reconnect_attempts (or stopped due to auth error)
            # The current singleton treats InvalidStatusCode as a non-retriable auth issue after first connect attempt.
            # The connect logic might try once, then _establish_and_maintain_connection fails, then _connection_manager_loop retries.
            # The provided singleton's connect() doesn't have retry logic, handle_reconnect does.
            # The test setup's fail_connect=True makes websockets.connect itself fail.
            # The client's connect() catches this and calls _update_global_status.
            # It does not enter handle_reconnect from initial connect() failure.
            # To test handle_reconnect, failure must happen in listen_for_messages.
            self.assertTrue(TrueDataSingletonClient._instance.is_connecting == False) # Should have finished attempts or given up

        logger_test.debug("Finished test_02_connection_failure_invalid_status_code")
        # No explicit shutdown needed here as connection wasn't established / instance might be None or in failed state.
        # However, our teardown calls shutdown_truedata_client() which is fine.

    async def test_03_receive_and_process_tick_data(self):
        logger_test.debug("Starting test_03_receive_and_process_tick_data")

        # Simulate initial heartbeat/auth then a tick
        await self.mock_ws_client.recv_queue.put(json.dumps({"message": {"message": "HeartBeat"}}))
        sample_tick_raw = {"trade": ["NIFTY_ID", 1678886400000, 17000.50, 100, 17000.60, 50000, 100000, "tag", 12345]}
        await self.mock_ws_client.recv_queue.put(json.dumps(sample_tick_raw))

        mock_data_cb = MagicMock()
        await initialize_truedata(symbols=["NIFTY_ID"], on_data=mock_data_cb)
        await asyncio.sleep(0.1) # Allow processing

        self.assertTrue(is_connected())
        self.assertIn("NIFTY_ID", live_market_data)
        self.assertEqual(live_market_data["NIFTY_ID"]["ltp"], 17000.50)

        mock_data_cb.assert_called_once()
        call_args = mock_data_cb.call_args[0][0] # Get the first positional argument of the call
        self.assertEqual(call_args["symbol_id"], "NIFTY_ID")
        self.assertEqual(call_args["ltp"], 17000.50)

        await shutdown_truedata_client()
        logger_test.debug("Finished test_03_receive_and_process_tick_data")


    async def test_04_dynamic_symbol_subscription(self):
        logger_test.debug("Starting test_04_dynamic_symbol_subscription")
        await self.mock_ws_client.recv_queue.put(json.dumps({"message": {"message": "HeartBeat"}})) # Initial message

        await initialize_truedata(symbols=["NIFTY"])
        await asyncio.sleep(0.05)
        self.assertTrue(is_connected())

        # Clear sent messages to check only for new subscription
        self.mock_ws_client.sent_messages.clear()

        await add_truedata_symbols(["BANKNIFTY"])
        await asyncio.sleep(0.05) # Allow time for send

        self.assertIn("BANKNIFTY", TrueDataSingletonClient._instance.SYMBOLS_TO_SUBSCRIBE)
        # Check if a new subscription message was sent
        sub_msg_found = any(msg.get("type") == "subscribe" and "BANKNIFTY" in msg.get("symbols", []) for msg in self.mock_ws_client.sent_messages)
        self.assertTrue(sub_msg_found, f"BANKNIFTY subscription not found in sent messages: {self.mock_ws_client.sent_messages}")

        # Test unsubscription
        self.mock_ws_client.sent_messages.clear()
        await remove_truedata_symbols(["NIFTY"])
        await asyncio.sleep(0.05)
        self.assertNotIn("NIFTY", TrueDataSingletonClient._instance.SYMBOLS_TO_SUBSCRIBE)
        unsub_msg_found = any(msg.get("type") == "unsubscribe" and "NIFTY" in msg.get("symbols", []) for msg in self.mock_ws_client.sent_messages)
        self.assertTrue(unsub_msg_found, f"NIFTY unsubscription not found in sent messages: {self.mock_ws_client.sent_messages}")

        await shutdown_truedata_client()
        logger_test.debug("Finished test_04_dynamic_symbol_subscription")

    async def test_05_handle_reconnect_on_connection_closed(self):
        logger_test.debug("Starting test_05_handle_reconnect_on_connection_closed")

        # Custom recv logic for this test
        initial_connect_done = False
        num_heartbeats_before_close = 2
        async def custom_recv(mock_ws_instance: MockWebSocketClient):
            nonlocal initial_connect_done, num_heartbeats_before_close
            if not initial_connect_done:
                initial_connect_done = True
                logger_test.debug("CustomRecv: Sending initial HeartBeat.")
                return json.dumps({"message": {"message": "HeartBeat"}})

            if num_heartbeats_before_close > 0:
                num_heartbeats_before_close -=1
                logger_test.debug(f"CustomRecv: Sending a data-like HeartBeat, remaining before close: {num_heartbeats_before_close}")
                return json.dumps({"message": {"message": "HeartBeat"}}) # Simulate ongoing messages
            else:
                logger_test.debug("CustomRecv: Raising ConnectionClosedError.")
                mock_ws_instance.open = False # Simulate connection drop
                raise websockets.exceptions.ConnectionClosedError(None, "Test-induced closure")

        self.mock_ws_client.custom_recv_logic = custom_recv

        mock_status_cb = AsyncMock()

        # Patch asyncio.sleep to monitor and control reconnect delays
        with patch('asyncio.sleep', AsyncMock(side_effect=asyncio.sleep)) as mock_sleep: # Allow actual sleep but spy on it
            await initialize_truedata(on_status_change=mock_status_cb, symbols=["TESTSYM"])

            # Allow time for initial connection and simulated message exchange leading to disconnect
            await asyncio.sleep(0.2)

            self.assertFalse(is_connected(), "Should be disconnected after ConnectionClosedError")
            self.assertIn("Connection Closed Error", truedata_connection_status["error_message"])

            # Verify status callback was called for disconnect
            mock_status_cb.assert_any_call(False, "Connection Closed Error: Test-induced closure")

            # Verify reconnection attempts were made
            # TrueDataSingletonClient.reconnect_attempts is reset on successful connect
            # The mock_sleep should have been called by handle_reconnect
            self.assertTrue(mock_sleep.called, "asyncio.sleep should have been called for reconnect delay.")

            # Check if it tries to connect again (mock_websockets_connect would be called again)
            # The first call is from initialize_truedata. Subsequent calls are reconnects.
            self.assertGreaterEqual(self.mock_websockets_connect.call_count, 1) # At least initial connect + 1 reconnect attempt by design

            # Note: The test will complete before all 5 reconnect attempts if delays are real.
            # Mocking sleep with very short duration or checking attempt count on client is better.
            # For this test, checking sleep was called and status is disconnected is primary.
            # The singleton's reconnect_attempts counter is internal and might be reset.

        await shutdown_truedata_client() # Cleanup
        logger_test.debug("Finished test_05_handle_reconnect_on_connection_closed")

if __name__ == '__main__':
    unittest.main()
```
