import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Optional, Callable, List, Any
import ssl
import certifi

# Import settings from the application's config module
from src.config import settings # Centralized configuration

# --- Global Variables for Singleton State ---
live_market_data: Dict[str, Dict[str, Any]] = {}
truedata_connection_status: Dict[str, Any] = {
    "connected": False,
    "last_update": None,
    "error_message": None,
    "active_symbols": []
}
# --- End Global Variables ---

# --- Logger Setup ---
logger = logging.getLogger(__name__)
# Basic configuration if no root logger is set (e.g. when run standalone)
# In the main app, logging is configured by server.py calling setup_logging.
if not logger.hasHandlers() and not logging.getLogger().hasHandlers(): # Check root logger too
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# --- End Logger Setup ---


class TrueDataSingletonClient:
    _instance = None

    # --- Client Configuration (Now primarily from imported settings) ---
    TD_USERNAME: Optional[str] = None
    TD_PASSWORD: Optional[str] = None
    TD_APIKEY: Optional[str] = None
    WS_URL: str = "wss://api.truedata.in/websocket" # Default, will be overridden by settings
    SYMBOLS_TO_SUBSCRIBE: List[str] = []

    # SSL Context - Using library defaults is generally fine for standard wss.
    # Custom context can be configured here if needed:
    # ssl_context = ssl.create_default_context(cafile=certifi.where())

    # --- Internal State ---
    websocket_client: Optional[websockets.WebSocketClientProtocol] = None
    is_connecting: bool = False
    reconnect_attempts: int = 0
    # Max attempts and delays will also come from settings

    # Callbacks
    _on_data_callback: Optional[Callable[[Dict], Any]] = None # Can be sync or async
    _on_status_change_callback: Optional[Callable[[bool, Optional[str]], Any]] = None # Can be sync or async

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TrueDataSingletonClient, cls).__new__(cls, *args, **kwargs)
            # Initialize config from settings when instance is first created
            cls._instance._load_config_from_settings()
        return cls._instance

    def _load_config_from_settings(self):
        """Loads configuration from the global settings object."""
        self.TD_USERNAME = settings.TRUEDATA_USERNAME
        self.TD_PASSWORD = settings.TRUEDATA_PASSWORD
        self.TD_APIKEY = settings.TRUEDATA_APIKEY # Optional
        self.WS_URL = settings.TRUEDATA_WEBSOCKET_URL
        # Ensure default symbols is a copy if it's mutable from settings
        self.SYMBOLS_TO_SUBSCRIBE = list(settings.TRUEDATA_DEFAULT_SYMBOLS)
        
        # Reconnection parameters from settings
        self.max_reconnect_attempts = settings.TRUEDATA_RECONNECT_MAX_ATTEMPTS
        self.reconnect_delay_base = settings.TRUEDATA_RECONNECT_INITIAL_DELAY
        self.max_reconnect_delay = settings.TRUEDATA_RECONNECT_MAX_DELAY # New setting for max delay cap

        logger.info(f"[{self.__class__.__name__}] Configuration loaded from settings. User: {self.TD_USERNAME}, URL: {self.WS_URL}")


    async def _update_global_status(self, connected: bool, error_message: Optional[str] = None, symbols: Optional[List[str]] = None):
        global truedata_connection_status
        truedata_connection_status["connected"] = connected
        truedata_connection_status["last_update"] = datetime.now().isoformat()
        
        # Preserve last error unless a new one is explicitly passed or connection is successful
        if error_message is not None or connected:
            truedata_connection_status["error_message"] = error_message

        if symbols is not None:
            truedata_connection_status["active_symbols"] = sorted(list(set(symbols))) # Keep unique and sorted

        if self._on_status_change_callback:
            try:
                res = self._on_status_change_callback(connected, truedata_connection_status["error_message"])
                if asyncio.iscoroutine(res): await res
            except Exception as e_cb_status:
                logger.error(f"Error in _on_status_change_callback: {e_cb_status}", exc_info=True)

    async def connect(self):
        if self.websocket_client and self.websocket_client.open:
            logger.info(f"[{self.__class__.__name__}] Already connected.")
            return
        if self.is_connecting:
            logger.info(f"[{self.__class__.__name__}] Connection attempt already in progress.")
            return

        self.is_connecting = True
        # Ensure latest config is loaded if it can change dynamically (not typical for BaseSettings)
        # self._load_config_from_settings() # Usually done once at init

        if not self.TD_USERNAME or not self.TD_PASSWORD:
            logger.error(f"[{self.__class__.__name__}] TrueData username or password not configured. Cannot connect.")
            await self._update_global_status(False, "Username or password not configured.")
            self.is_connecting = False
            return

        logger.info(f"[{self.__class__.__name__}] Attempting to connect to {self.WS_URL} for user {self.TD_USERNAME}...")

        try:
            self.websocket_client = await websockets.connect(
                self.WS_URL,
                ping_interval=settings.TRUEDATA_PING_INTERVAL,
                ping_timeout=settings.TRUEDATA_PING_TIMEOUT,
                close_timeout=settings.TRUEDATA_CLOSE_TIMEOUT
            )
            logger.info(f"[{self.__class__.__name__}] WebSocket connection established. Authenticating...")
            
            auth_payload = {"username": self.TD_USERNAME, "password": self.TD_PASSWORD}
            if self.TD_APIKEY: auth_payload["apikey"] = self.TD_APIKEY
            
            await self.websocket_client.send(json.dumps(auth_payload))
            # Optional: Wait for a specific auth success message if protocol defines one.
            # For now, assume connection implies auth success for this client structure.
            logger.info(f"[{self.__class__.__name__}] Authentication payload sent.")

            await self._update_global_status(True, error_message=None) # Mark connected
            logger.info(f"[{self.__class__.__name__}] Subscribing to default/current symbols...")
            await self.subscribe_symbols(list(self.SYMBOLS_TO_SUBSCRIBE)) # Ensure it's a list copy

            self.reconnect_attempts = 0
            asyncio.create_task(self.listen_for_messages())

        except websockets.exceptions.InvalidStatusCode as e_status:
            logger.error(f"[{self.__class__.__name__}] WebSocket connection failed: Invalid status {e_status.status_code}.", exc_info=True)
            await self._update_global_status(False, f"Connection Failed: Status {e_status.status_code}")
            self.websocket_client = None
        except ConnectionRefusedError:
            logger.error(f"[{self.__class__.__name__}] WebSocket connection refused from {self.WS_URL}.", exc_info=True)
            await self._update_global_status(False, "Connection Refused")
            self.websocket_client = None
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Failed to connect/authenticate with TrueData: {e}", exc_info=True)
            await self._update_global_status(False, f"Connection Error: {str(e)[:100]}") # Avoid overly long error messages in status
            self.websocket_client = None
        finally:
            self.is_connecting = False

    async def listen_for_messages(self):
        logger.info(f"[{self.__class__.__name__}] Listening for messages from TrueData...")
        try:
            while self.websocket_client and self.websocket_client.open:
                message_str = await self.websocket_client.recv()
                self._process_message(message_str)
        except websockets.exceptions.ConnectionClosedError as e_closed_err:
            logger.error(f"[{self.__class__.__name__}] Connection closed with error: {e_closed_err.code} {e_closed_err.reason}", exc_info=True)
            await self._update_global_status(False, f"Connection Closed Error: {e_closed_err.code}")
            await self.handle_reconnect()
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"[{self.__class__.__name__}] Connection closed gracefully (OK).")
            await self._update_global_status(False, "Connection Closed OK by server")
            await self.handle_reconnect() # Reconnect unless shutdown was intended
        except Exception as e_listen:
            logger.error(f"[{self.__class__.__name__}] Error in message listener: {e_listen}", exc_info=True)
            await self._update_global_status(False, f"Listener Error: {str(e_listen)[:50]}")
            await self.handle_reconnect()
        finally:
            if not (self.websocket_client and self.websocket_client.open):
                 logger.info(f"[{self.__class__.__name__}] Listener loop ended; WebSocket no longer open.")
                 if truedata_connection_status["connected"]:
                      await self._update_global_status(False, "Listener terminated, connection lost.")

    def _process_message(self, message_str: str):
        global live_market_data
        try:
            data_packet = json.loads(message_str)
            
            if 'message' in data_packet and isinstance(data_packet['message'], dict):
                msg_content = data_packet['message'].get('message', '')
                if msg_content == 'HeartBeat' or 'TrueData Real Time Data Service' in msg_content:
                    logger.debug(f"Heartbeat/Info: {msg_content}")
                    truedata_connection_status["last_update"] = datetime.now().isoformat()
                    return

            if 'trade' in data_packet and isinstance(data_packet['trade'], list) and len(data_packet['trade']) >= 3:
                tick = data_packet['trade']
                symbol_id = str(tick[0]) # Assuming symbol_id is the first element
                
                ltp_data = {
                    "symbol_id": symbol_id, # Use the ID as key internally
                    "ltp": float(tick[2]),
                    "timestamp": datetime.fromtimestamp(int(tick[1])/1000).isoformat() if isinstance(tick[1], (int, float)) else str(tick[1]),
                    "volume": int(tick[3]) if len(tick) > 3 and tick[3] is not None else 0,
                    # Add more fields based on actual protocol and needs
                }
                live_market_data[symbol_id] = ltp_data
                
                if self._on_data_callback:
                    try:
                        res = self._on_data_callback(ltp_data.copy()) # Send a copy
                        if asyncio.iscoroutine(res): asyncio.create_task(res) # If callback is async but called from sync
                    except Exception as e_cb_data: logger.error(f"Error in _on_data_callback: {e_cb_data}", exc_info=True)
            # else: logger.debug(f"Other msg: {message_str[:100]}")

        except json.JSONDecodeError: logger.warning(f"JSONDecodeError: {message_str[:200]}")
        except Exception as e_proc: logger.error(f"Msg processing error: {e_proc} - Data: {message_str[:200]}", exc_info=True)

    async def subscribe_symbols(self, symbols: List[str]):
        current_subs = set(self.SYMBOLS_TO_SUBSCRIBE)
        new_subs_to_add = [s for s in symbols if s not in current_subs]
        if not new_subs_to_add and current_subs: # If no new symbols but already subscribed to some, resubscribe all
            pass # Or just return if only new symbols are to be sent. User client sends all.
        
        self.SYMBOLS_TO_SUBSCRIBE = sorted(list(set(self.SYMBOLS_TO_SUBSCRIBE + symbols)))

        if not self.websocket_client or not self.websocket_client.open:
            logger.warning(f"[{self.__class__.__name__}] WS not connected. Symbols will be subscribed on connect: {self.SYMBOLS_TO_SUBSCRIBE}")
            return
        
        logger.info(f"[{self.__class__.__name__}] Attempting to subscribe to: {self.SYMBOLS_TO_SUBSCRIBE}")
        try:
            # Example payload: {"type":"subscribe", "symbols": ["NIFTY", "BANKNIFTY"]}
            # User client example: {"t": "s", "k": ["ID1", "ID2"]}
            # The singleton should use symbol names as per its SYMBOLS_TO_SUBSCRIBE list
            # If mapping to IDs is needed, it should happen here or before. Assuming names for now.
            await self.websocket_client.send(json.dumps({"type": "subscribe", "symbols": self.SYMBOLS_TO_SUBSCRIBE}))
            await self._update_global_status(True, symbols=self.SYMBOLS_TO_SUBSCRIBE)
            logger.info(f"[{self.__class__.__name__}] Subscription request sent for: {self.SYMBOLS_TO_SUBSCRIBE}")
        except Exception as e_sub: logger.error(f"Error subscribing: {e_sub}", exc_info=True)


    async def unsubscribe_symbols(self, symbols: List[str]):
        self.SYMBOLS_TO_SUBSCRIBE = sorted([s for s in self.SYMBOLS_TO_SUBSCRIBE if s not in symbols])
        
        if not self.websocket_client or not self.websocket_client.open:
            logger.warning(f"[{self.__class__.__name__}] WS not connected. Symbol list updated locally.")
            return
        
        logger.info(f"[{self.__class__.__name__}] Unsubscribing from {symbols}. Remaining: {self.SYMBOLS_TO_SUBSCRIBE}")
        try:
            # If TrueData requires resending the full list for unsubscription:
            await self.websocket_client.send(json.dumps({"type": "subscribe", "symbols": self.SYMBOLS_TO_SUBSCRIBE}))
            # Or if it has a specific unsubscribe type:
            # await self.websocket_client.send(json.dumps({"type": "unsubscribe", "symbols": symbols}))
            await self._update_global_status(True, symbols=self.SYMBOLS_TO_SUBSCRIBE)
            logger.info(f"[{self.__class__.__name__}] Unsubscription/update request sent.")
        except Exception as e_unsub: logger.error(f"Error unsubscribing: {e_unsub}", exc_info=True)

    async def handle_reconnect(self):
        if self.is_connecting: return
        # Check if client was intentionally stopped
        if _truedata_client_singleton_instance is None or not _truedata_client_singleton_instance.websocket_client: # implies shutdown_truedata_client was called
            logger.info(f"[{self.__class__.__name__}] Reconnect aborted, client seems to be shut down.")
            return

        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = self.reconnect_delay_base * (2 ** (self.reconnect_attempts -1))
            delay = min(delay, self.max_reconnect_delay if hasattr(self, 'max_reconnect_delay') else 60)
            delay += random.uniform(0, 0.1 * delay)
            logger.info(f"[{self.__class__.__name__}] Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} in {delay:.2f}s.")
            await asyncio.sleep(delay)
            await self.connect()
        else:
            logger.error(f"[{self.__class__.__name__}] Max reconnect attempts ({self.max_reconnect_attempts}) reached.")
            await self._update_global_status(False, "Max reconnect attempts reached.")

    async def close_connection(self):
        logger.info(f"[{self.__class__.__name__}] User requested close_connection.")
        self.reconnect_attempts = self.max_reconnect_attempts + 1 # Prevent auto-reconnect
        if self.websocket_client:
            try:
                await self.websocket_client.close()
                logger.info(f"[{self.__class__.__name__}] WebSocket client close() called.")
            except Exception as e_close:
                logger.error(f"[{self.__class__.__name__}] Error during manual websocket_client.close(): {e_close}", exc_info=True)
            finally:
                 self.websocket_client = None
        await self._update_global_status(False, "Connection closed by user request.")

    def set_on_data_callback(self, callback: Callable[[Dict], Any]): self._on_data_callback = callback
    def set_on_status_change_callback(self, callback: Callable[[bool, Optional[str]], Any]): self._on_status_change_callback = callback

# --- Interface Functions ---
_truedata_client_singleton_instance: Optional[TrueDataSingletonClient] = None

async def initialize_truedata(
    settings_override: Optional[Any] = None, # Allow passing full settings object
    username: Optional[str] = None,
    password: Optional[str] = None,
    apikey: Optional[str] = None,
    ws_url: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    on_data: Optional[Callable[[Dict], Any]] = None,
    on_status_change: Optional[Callable[[bool, Optional[str]], Any]] = None
):
    global _truedata_client_singleton_instance
    if _truedata_client_singleton_instance is None:
        _truedata_client_singleton_instance = TrueDataSingletonClient()
        # Initial config load from global `settings` happened in __new__/_load_config_from_settings

    # Allow overriding specific settings if passed, otherwise client uses its loaded config
    client = _truedata_client_singleton_instance
    if settings_override: # If a full settings object is passed, re-init config from it
        client.TD_USERNAME = settings_override.TRUEDATA_USERNAME
        client.TD_PASSWORD = settings_override.TRUEDATA_PASSWORD
        client.TD_APIKEY = settings_override.TRUEDATA_APIKEY
        client.WS_URL = settings_override.TRUEDATA_WEBSOCKET_URL
        client.SYMBOLS_TO_SUBSCRIBE = list(settings_override.TRUEDATA_DEFAULT_SYMBOLS)
        client.max_reconnect_attempts = settings_override.TRUEDATA_RECONNECT_MAX_ATTEMPTS
        client.reconnect_delay_base = settings_override.TRUEDATA_RECONNECT_INITIAL_DELAY
        client.max_reconnect_delay = settings_override.TRUEDATA_RECONNECT_MAX_DELAY
        logger.info(f"[{client.__class__.__name__}] Re-configured from passed settings object.")


    if username: client.TD_USERNAME = username
    if password: client.TD_PASSWORD = password
    if apikey: client.TD_APIKEY = apikey
    if ws_url: client.WS_URL = ws_url
    if symbols: client.SYMBOLS_TO_SUBSCRIBE = list(set(symbols)) # Use provided symbols, ensure unique

    if on_data: client.set_on_data_callback(on_data)
    if on_status_change: client.set_on_status_change_callback(on_status_change)

    if not (client.websocket_client and client.websocket_client.open):
        if not client.is_connecting:
             # Ensure connect is not awaited here if initialize_truedata is called from sync context often
             # If initialize_market_data_handling is async, direct await is fine.
             await client.connect()
    else: logger.info(f"[{client.__class__.__name__}] Already initialized and connected/connecting.")

def get_truedata_status() -> Dict[str, Any]: return truedata_connection_status.copy()
def is_connected() -> bool: return truedata_connection_status.get("connected", False)
def get_live_data_for_symbol(symbol_id: str) -> Optional[Dict[str, Any]]: return live_market_data.get(symbol_id)

async def add_truedata_symbols(symbols: List[str]):
    if _truedata_client_singleton_instance: await _truedata_client_singleton_instance.subscribe_symbols(symbols)
    else: logger.warning("TD client not init. Cannot add symbols.")

async def remove_truedata_symbols(symbols: List[str]):
    if _truedata_client_singleton_instance: await _truedata_client_singleton_instance.unsubscribe_symbols(symbols)
    else: logger.warning("TD client not init. Cannot remove symbols.")

async def shutdown_truedata_client():
    global _truedata_client_singleton_instance
    if _truedata_client_singleton_instance:
        logger.info(f"[{_truedata_client_singleton_instance.__class__.__name__}] Shutdown initiated.")
        await _truedata_client_singleton_instance.close_connection()
        _truedata_client_singleton_instance = None
    else: logger.info("TrueData client already None or not initialized. Shutdown had no instance to close.")

if __name__ == '__main__':
    async def main_test():
        # Ensure global `settings` is usable if this is run standalone
        # For testing, you might need to mock or provide a basic AppSettings instance
        # For this __main__ block, assume settings are available via `from src.config import settings`
        # or that the client's internal defaults are sufficient for a basic test.

        logging.basicConfig(level=logging.DEBUG)

        def my_data_handler(tick_data): logger.info(f"Tick via CB: {tick_data}")
        async def my_status_handler(is_conn, err_msg):
            logger.info(f"Status via CB: {'Conn' if is_conn else 'Disconn'}. Err: {err_msg or 'OK'}")

        # To test with settings, ensure src.config.settings is valid or provide a mock
        # For example, if running this file directly and src.config cannot be found:
        class MockTestSettings: # Basic mock for standalone testing
            TRUEDATA_USERNAME = "YOUR_USER" # Get from env or hardcode for test
            TRUEDATA_PASSWORD = "YOUR_PASSWORD"
            TRUEDATA_APIKEY = None
            TRUEDATA_WEBSOCKET_URL = "wss://api.truedata.in/websocket" # Or your test URL
            TRUEDATA_DEFAULT_SYMBOLS = ["NIFTY", "BANKNIFTY"]
            TRUEDATA_PING_INTERVAL = 20
            TRUEDATA_PING_TIMEOUT = 10
            TRUEDATA_CLOSE_TIMEOUT = 5
            TRUEDATA_RECONNECT_MAX_ATTEMPTS = 2 # Low for quick test
            TRUEDATA_RECONNECT_INITIAL_DELAY = 2
            TRUEDATA_RECONNECT_MAX_DELAY = 5

        mock_settings_for_test = MockTestSettings()
        # Update with actual env vars if available for testing
        mock_settings_for_test.TRUEDATA_USERNAME = os.environ.get("TRUEDATA_USERNAME_GLOBAL", mock_settings_for_test.TRUEDATA_USERNAME)
        mock_settings_for_test.TRUEDATA_PASSWORD = os.environ.get("TRUEDATA_PASSWORD_GLOBAL", mock_settings_for_test.TRUEDATA_PASSWORD)

        logger.info(f"Test Main: User={mock_settings_for_test.TRUEDATA_USERNAME}, Pass valid? {'Yes' if mock_settings_for_test.TRUEDATA_PASSWORD else 'No'}")

        await initialize_truedata(
            settings_override=mock_settings_for_test, # Pass the mock settings
            symbols=["RELIANCE"],
            on_data=my_data_handler,
            on_status_change=my_status_handler
        )

        try:
            for i in range(30): # Test for 30 seconds
                await asyncio.sleep(1)
                status_now = get_truedata_status()
                logger.debug(f"Test Main Loop: Status - Conn: {status_now['connected']}, Err: {status_now['error_message']}")
                if i == 5: await add_truedata_symbols(["INFY"])
                if i == 10: await remove_truedata_symbols(["RELIANCE"])
        except KeyboardInterrupt: logger.info("Test interrupted.")
        finally: await shutdown_truedata_client()
    asyncio.run(main_test())

```
