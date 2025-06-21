import logging
import os
from typing import Dict, Optional, List, Any, Coroutine, Callable
from datetime import datetime
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.exceptions import (
    KiteException, TokenException, UserException, GeneralException, DataException,
    NetworkException, OrderException, InputException, PermissionException
)

from src.config import AppSettings
from src.app_state import AppState
from src.database import execute_db_query, fetch_one_db
# Assuming APIException is a base class for custom API errors,
# If not, we'd need to define it or use FastAPI's HTTPException directly in routes.
# For now, let's define a simple one here for client-raised issues.

class ClientException(Exception):
    """Base exception for client-specific errors."""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

class ZerodhaTokenError(ClientException):
    """Custom exception for Zerodha token issues (e.g., expired, invalid)."""
    def __init__(self, message="Zerodha token is invalid or expired. Please re-authenticate."):
        super().__init__(message, status_code=401) # Unauthorized

class ZerodhaAPIError(ClientException):
    """General Zerodha API error."""
    pass


logger = logging.getLogger(__name__)

class ConsolidatedZerodhaClient:
    def __init__(self, settings: AppSettings, app_state: AppState):
        self.settings = settings
        self.app_state = app_state

        self.api_key: Optional[str] = settings.ZERODHA_API_KEY
        self.api_secret: Optional[str] = settings.ZERODHA_API_SECRET
        self.client_display_name: str = settings.ZERODHA_ACCOUNT_NAME or settings.ZERODHA_CLIENT_ID or "ZerodhaClient"

        self.kite: Optional[KiteConnect] = None
        self.access_token: Optional[str] = None
        self.public_token: Optional[str] = None
        self.current_user_id: Optional[str] = None # This will be the actual user_id from Kite session

        self.kws: Optional[KiteTicker] = None # KiteTicker WebSocket client
        self.market_data_callbacks: List[Callable[[List[Dict]], Coroutine[Any, Any, None]]] = []
        self.order_update_callbacks: List[Callable[[Dict], Coroutine[Any, Any, None]]] = []

        if self.api_key:
            try:
                self.kite = KiteConnect(
                    api_key=self.api_key,
                    timeout=settings.DEFAULT_HTTP_TIMEOUT_SECONDS
                )
                logger.info(f"[{self.client_display_name}] KiteConnect instance created. API Key: {self.api_key[:5]}..., Timeout: {settings.DEFAULT_HTTP_TIMEOUT_SECONDS}s")
            except Exception as e:
                logger.error(f"[{self.client_display_name}] Failed to initialize KiteConnect: {e}", exc_info=True)
                self.kite = None
        else:
            logger.warning(f"[{self.client_display_name}] Zerodha API Key not configured. Client not fully initialized.")

    async def _clear_local_session(self):
        """Clears local session variables."""
        logger.debug(f"[{self.client_display_name}] Clearing local session data.")
        self.access_token = None
        self.public_token = None
        # self.current_user_id should ideally persist if known, unless logout implies forgetting user
        if self.kite:
            self.kite.set_access_token(None) # Clear token in KiteConnect instance

    async def _handle_token_exception(self, operation_name: str):
        """Handles TokenException by clearing session and updating app state."""
        logger.warning(f"[{self.client_display_name}] TokenException during {operation_name}. Invalidating local session.")
        await self._clear_local_session()
        if self.app_state.market_data.zerodha_data_connected:
            self.app_state.market_data.zerodha_data_connected = False
            self.app_state.market_data.active_data_source = None \
                if self.app_state.market_data.active_data_source == "zerodha" \
                else self.app_state.market_data.active_data_source
            logger.info(f"[{self.client_display_name}] Updated app_state: zerodha_data_connected=False.")
        # Optionally, mark token as inactive in DB if current_user_id is known
        if self.current_user_id and self.app_state.clients.db_pool:
            try:
                await execute_db_query(
                    "UPDATE auth_tokens SET is_active = FALSE, updated_at = ? WHERE provider = 'zerodha' AND user_id = ?",
                    datetime.utcnow(), self.current_user_id, db_conn_or_path=self.app_state.clients.db_pool
                )
                logger.info(f"[{self.client_display_name}] Marked token as inactive in DB for user {self.current_user_id}.")
            except Exception as db_err:
                logger.error(f"[{self.client_display_name}] Failed to mark token as inactive in DB for {self.current_user_id}: {db_err}", exc_info=True)


    def get_login_url(self) -> Optional[str]:
        if not self.kite:
            logger.error(f"[{self.client_display_name}] Kite client not initialized, cannot get login URL.")
            return None
        try:
            return self.kite.login_url()
        except Exception as e: # KiteConnect can sometimes raise generic Exception
            logger.error(f"[{self.client_display_name}] Error generating Zerodha login URL: {e}", exc_info=True)
            return None

    async def generate_session(self, request_token: str) -> bool:
        if not self.kite or not self.api_secret:
            logger.error(f"[{self.client_display_name}] Kite client or API secret not available for session generation.")
            self.app_state.market_data.zerodha_data_connected = False
            return False
        try:
            logger.info(f"[{self.client_display_name}] Generating session with request token: {request_token[:7]}...")
            # generate_session is synchronous; run in executor if it becomes blocking for too long
            data = await asyncio.to_thread(self.kite.generate_session, request_token, self.api_secret)

            self.access_token = data.get("access_token")
            self.public_token = data.get("public_token")
            self.current_user_id = data.get("user_id") # Capture the actual user_id

            if not self.access_token or not self.current_user_id:
                logger.error(f"[{self.client_display_name}] Access token or User ID not found in Zerodha session data: {data}")
                self.app_state.market_data.zerodha_data_connected = False
                return False

            self.kite.set_access_token(self.access_token)
            self.app_state.market_data.zerodha_data_connected = True
            self.app_state.market_data.active_data_source = "zerodha"
            self.app_state.system_status.last_system_update_utc = datetime.utcnow()
            logger.info(f"[{self.current_user_id}] Zerodha session generated successfully.")

            if self.app_state.clients.db_pool:
                try:
                    await execute_db_query(
                        """
                        INSERT OR REPLACE INTO auth_tokens
                        (provider, user_id, access_token, public_token, api_key, updated_at, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        'zerodha', self.current_user_id, self.access_token, self.public_token,
                        self.api_key, datetime.utcnow(), True,
                        db_conn_or_path=self.app_state.clients.db_pool
                    )
                    logger.info(f"[{self.current_user_id}] Zerodha tokens persisted to database.")
                except Exception as db_err:
                    logger.error(f"[{self.current_user_id}] Failed to persist Zerodha tokens: {db_err}", exc_info=True)
            else:
                logger.warning(f"[{self.current_user_id}] DB pool not available. Zerodha tokens not persisted.")
            return True
        except TokenException as e:
            logger.error(f"[{self.client_display_name}] TokenException during session generation: {e}", exc_info=True)
            await self._handle_token_exception("generate_session") # Clear local state
            # Re-raise for the route to handle
            raise ZerodhaTokenError(f"Failed to generate session due to token issue: {e.message}")
        except KiteException as e:
            logger.error(f"[{self.client_display_name}] KiteException during session generation: {e}", exc_info=True)
            self.app_state.market_data.zerodha_data_connected = False
            raise ZerodhaAPIError(f"Kite API error during session generation: {e.message}", status_code=e.code if hasattr(e, 'code') else 500)
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"[{self.client_display_name}] Unexpected error generating Zerodha session: {e}", exc_info=True)
            self.app_state.market_data.zerodha_data_connected = False
            raise ZerodhaAPIError(f"Unexpected error during session generation: {str(e)}", status_code=500)


    async def set_access_token(self, access_token: str, user_id: Optional[str] = None, public_token: Optional[str] = None) -> bool:
        log_prefix = f"[{user_id or self.client_display_name}]"
        if not self.kite:
            logger.error(f"{log_prefix} Kite client not initialized, cannot set access token.")
            return False

        self.access_token = access_token
        self.current_user_id = user_id # Trust the user_id passed from DB
        self.public_token = public_token
        self.kite.set_access_token(self.access_token)
        logger.info(f"{log_prefix} Access token set in KiteConnect instance.")

        try:
            profile_data = await self.get_profile() # This now uses the new error handling
            if profile_data and profile_data.get('user_id'):
                self.app_state.market_data.zerodha_data_connected = True
                # Ensure current_user_id is updated if profile fetch reveals a different one (shouldn't happen if DB is source)
                if self.current_user_id != profile_data.get('user_id'):
                    logger.warning(f"{log_prefix} User ID from profile ({profile_data.get('user_id')}) differs from provided/stored ({self.current_user_id}). Using profile's.")
                    self.current_user_id = profile_data.get('user_id')

                logger.info(f"{log_prefix} Zerodha access token verified for user {self.current_user_id}. Connection active.")
                return True
            else: # Profile fetch failed but didn't raise TokenException (e.g. empty response)
                logger.warning(f"{log_prefix} Zerodha access token set, but profile fetch failed or returned no user_id. Token might be invalid.")
                await self._handle_token_exception("set_access_token_profile_check") # Clears token and sets disconnected
                return False
        except ZerodhaTokenError: # Raised by get_profile if token is invalid
            logger.warning(f"{log_prefix} Token validation failed during set_access_token via get_profile.")
            # _handle_token_exception was already called by get_profile's wrapper
            return False
        except ZerodhaAPIError as e: # Other API errors during profile check
            logger.error(f"{log_prefix} API error during token validation profile check: {e.message}", exc_info=True)
            # Don't necessarily invalidate token here, could be temporary server issue
            # but connection is not "fully" verified. Depending on policy, may set zerodha_data_connected = False
            self.app_state.market_data.zerodha_data_connected = False # For safety
            return False


    async def _api_call_wrapper(self, kite_method_name: str, *args, **kwargs):
        if not self.kite or not self.access_token:
            logger.error(f"[{self.client_display_name}] Cannot call '{kite_method_name}': Kite client not initialized or not authenticated.")
            raise ZerodhaTokenError("Client not authenticated. Please login.")
        if not self.app_state.market_data.zerodha_data_connected:
             logger.warning(f"[{self.client_display_name}] Attempting '{kite_method_name}' while zerodha_data_connected is False. Token might be stale.")
             # Proceed, but rely on TokenException handling

        try:
            method_to_call = getattr(self.kite, kite_method_name)
            # KiteConnect methods are synchronous, run them in a thread pool to avoid blocking asyncio loop
            response = await asyncio.to_thread(method_to_call, *args, **kwargs)
            return response
        except TokenException as e:
            logger.error(f"[{self.client_display_name}] TokenException on '{kite_method_name}': {e.message}", exc_info=True)
            await self._handle_token_exception(kite_method_name)
            raise ZerodhaTokenError(f"Token error during {kite_method_name}: {e.message}") from e
        except InputException as e: # Typically 400
            logger.error(f"[{self.client_display_name}] InputException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"Invalid input for {kite_method_name}: {e.message}", status_code=400) from e
        except PermissionException as e: # Typically 403
            logger.error(f"[{self.client_display_name}] PermissionException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"Permission denied for {kite_method_name}: {e.message}", status_code=403) from e
        except OrderException as e: # Typically 400 or other specific codes
            logger.error(f"[{self.client_display_name}] OrderException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"Order execution error for {kite_method_name}: {e.message}", status_code=e.code if hasattr(e, 'code') and e.code else 400) from e
        except NetworkException as e: # Typically 503/504
            logger.error(f"[{self.client_display_name}] NetworkException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"Network error during {kite_method_name}: {e.message}", status_code=503) from e
        except DataException as e: # Typically 500 or 400 if data is malformed by user
            logger.error(f"[{self.client_display_name}] DataException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"Data error during {kite_method_name}: {e.message}", status_code=e.code if hasattr(e, 'code') else 500) from e
        except GeneralException as e: # Typically 500
            logger.error(f"[{self.client_display_name}] GeneralException on '{kite_method_name}': {e.message}", exc_info=True)
            raise ZerodhaAPIError(f"General Kite API error during {kite_method_name}: {e.message}", status_code=e.code if hasattr(e, 'code') else 500) from e
        except KiteException as e: # Catch any other KiteException
            logger.error(f"[{self.client_display_name}] Unhandled KiteException on '{kite_method_name}': {e.message}", exc_info=True)
            await self._handle_token_exception(kite_method_name) # Assume it might be token related if not specifically caught
            raise ZerodhaAPIError(f"Unhandled Kite API error during {kite_method_name}: {e.message}", status_code=e.code if hasattr(e, 'code') else 500) from e
        except Exception as e: # Catch any other unexpected non-Kite errors
            logger.error(f"[{self.client_display_name}] Unexpected non-Kite error on '{kite_method_name}': {e}", exc_info=True)
            raise ZerodhaAPIError(f"Unexpected server error during {kite_method_name}: {str(e)}", status_code=500) from e

    async def get_profile(self) -> Optional[Dict[str, Any]]:
        return await self._api_call_wrapper("profile")

    async def get_funds(self) -> Optional[Dict[str, Any]]:
        return await self._api_call_wrapper("margins")

    async def get_positions(self) -> Optional[Dict[str, Any]]:
        return await self._api_call_wrapper("positions")

    async def get_orders(self) -> Optional[List[Dict[str, Any]]]:
        return await self._api_call_wrapper("orders")

    async def place_order(self, variety, exchange, tradingsymbol, transaction_type, quantity, product, order_type, price=None, trigger_price=None, disclosed_quantity=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None) -> Optional[str]:
        logger.info(f"[{self.current_user_id or self.client_display_name}] Placing order: {transaction_type} {quantity} of {exchange}:{tradingsymbol} ({order_type} {product}), Tag: {tag or self.settings.DEFAULT_ORDER_TAG}")
        return await self._api_call_wrapper("place_order", variety=variety, exchange=exchange, tradingsymbol=tradingsymbol,
                                     transaction_type=transaction_type, quantity=int(quantity), product=product,
                                     order_type=order_type, price=price, trigger_price=trigger_price,
                                     disclosed_quantity=disclosed_quantity, squareoff=squareoff,
                                     stoploss=stoploss, trailing_stoploss=trailing_stoploss,
                                     tag=tag or self.settings.DEFAULT_ORDER_TAG)

    async def cancel_order(self, variety, order_id, parent_order_id=None) -> Optional[str]:
        logger.info(f"[{self.current_user_id or self.client_display_name}] Cancelling order: {order_id} (Variety: {variety})")
        return await self._api_call_wrapper("cancel_order", variety=variety, order_id=order_id, parent_order_id=parent_order_id)

    async def disconnect(self, from_token_exception: bool = False):
        log_prefix = f"[{self.current_user_id or self.client_display_name}]"
        logger.info(f"{log_prefix} Disconnecting Zerodha session.")

        if self.kite and self.access_token and not from_token_exception: # Avoid calling invalidate if token is already known bad
            try:
                logger.info(f"{log_prefix} Attempting to invalidate access token via API.")
                # Invalidate takes access_token as parameter if you want to invalidate a specific one,
                # otherwise it invalidates the one set in the client.
                # For V3, it seems it does not take any params and invalidates current session.
                await asyncio.to_thread(self.kite.invalidate_access_token)
                logger.info(f"{log_prefix} Access token invalidated via API call.")
            except TokenException:
                 logger.warning(f"{log_prefix} Token already invalid or session expired while trying to invalidate.")
            except KiteException as e:
                logger.error(f"{log_prefix} KiteException during token invalidation: {e.message}", exc_info=True)
            except Exception as e:
                logger.error(f"{log_prefix} Unexpected error during token invalidation: {e}", exc_info=True)

        # Clear local session data
        await self._clear_local_session()

        # Update app state
        if self.app_state.market_data.zerodha_data_connected:
            self.app_state.market_data.zerodha_data_connected = False
            self.app_state.market_data.active_data_source = None \
                if self.app_state.market_data.active_data_source == "zerodha" \
                else self.app_state.market_data.active_data_source
            self.app_state.system_status.last_system_update_utc = datetime.utcnow()
            logger.info(f"{log_prefix} Updated app_state: zerodha_data_connected=False.")

        # Mark token as inactive in DB
        if self.current_user_id and self.app_state.clients.db_pool:
            try:
                await execute_db_query(
                    "UPDATE auth_tokens SET is_active = FALSE, updated_at = ? WHERE provider = 'zerodha' AND user_id = ?",
                    datetime.utcnow(), self.current_user_id, db_conn_or_path=self.app_state.clients.db_pool
                )
                logger.info(f"{log_prefix} Marked token as inactive in DB for user {self.current_user_id}.")
            except Exception as db_err:
                logger.error(f"{log_prefix} Failed to mark token as inactive in DB: {db_err}", exc_info=True)

        # TODO: If KiteTicker (self.kws) is implemented, ensure it's also disconnected here.
        # if self.kws and self.kws.is_connected(): self.kws.close(1000, "User requested disconnect")
        logger.info(f"{log_prefix} Zerodha client session cleared and marked as disconnected.")
        return True

    def get_client_status_summary(self) -> Dict:
        return {
            "client_display_name": self.client_display_name,
            "user_id": self.current_user_id,
            "api_key_configured": bool(self.api_key),
            "is_kite_instance_initialized": bool(self.kite),
            "is_session_active_in_app_state": self.app_state.market_data.zerodha_data_connected,
            "access_token_present_locally": bool(self.access_token),
            "public_token_present_locally": bool(self.public_token),
        }

    # --- KiteTicker WebSocket Methods (Stubs or Basic Implementation) ---
    # These are placeholders if full WebSocket integration is a future task.
    # If needed now, they would require significant implementation for connection,
    # callbacks (on_ticks, on_connect, on_close, on_error), and reconnection.

    def register_market_data_callback(self, callback: Callable[[List[Dict]], Coroutine[Any, Any, None]]):
        if callback not in self.market_data_callbacks:
            self.market_data_callbacks.append(callback)
        logger.info(f"[{self.client_display_name}] Market data callback {getattr(callback, '__name__', 'Callback')} registered.")

    def register_order_update_callback(self, callback: Callable[[Dict], Coroutine[Any, Any, None]]):
        if callback not in self.order_update_callbacks:
            self.order_update_callbacks.append(callback)
        logger.info(f"[{self.client_display_name}] Order update callback {getattr(callback, '__name__', 'Callback')} registered.")

    # Add more methods as needed for WebSocket tick handling if in scope.
    # For now, assuming primary ticks via TrueData.
```
