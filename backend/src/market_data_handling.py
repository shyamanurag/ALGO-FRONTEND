import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any, Callable, Coroutine # Added Callable, Coroutine
import copy # For deep copying live market data

# Import the new TrueData client interface functions
from backend.truedata_client import (
    initialize_truedata as initialize_truedata_singleton,
    get_truedata_status as get_truedata_status_singleton,
    is_connected as is_truedata_singleton_connected,
    live_market_data as global_truedata_live_market_data, # For reading
    truedata_connection_status as global_truedata_connection_status # For reading status
)
# Keep Zerodha client import
from .clients.zerodha_client import ConsolidatedZerodhaClient

from .app_state import AppState, MarketDataState, ClientsState
from .config import AppSettings

logger = logging.getLogger(__name__)

async def _sync_truedata_globals_to_app_state(app_state: AppState):
    """
    Periodically syncs data from the TrueData client's global variables
    to the main application state (app_state).
    """
    if not app_state:
        logger.error("Sync TD Globals: AppState not available.")
        return

    # Sync connection status
    current_singleton_status = is_truedata_singleton_connected()
    if app_state.market_data.truedata_connected != current_singleton_status:
        app_state.market_data.truedata_connected = current_singleton_status
        logger.info(f"MarketDataHandling: Synced TrueData connection status to app_state: {'CONNECTED' if current_singleton_status else 'DISCONNECTED'}")
        app_state.market_data.market_data_last_update = datetime.utcnow()
        if current_singleton_status:
            app_state.market_data.active_data_source = "truedata_singleton"
        elif app_state.market_data.active_data_source == "truedata_singleton":
            app_state.market_data.active_data_source = None

    # Sync live market data
    # This is a direct copy. Consider if deepcopy is needed or if specific updates are better.
    # A direct assignment makes app_state.market_data.live_market_data point to the same dict
    # as global_truedata_live_market_data. This might be intended by the singleton pattern for direct access.
    # However, for controlled updates and avoiding unintended shared state issues, a copy is safer.
    # For now, let's assume the singleton's global_truedata_live_market_data is the source of truth
    # and app_state needs to reflect it.

    # Efficiently sync live_market_data
    # Update existing keys, add new ones, remove old ones
    updated_symbols = set()
    changed_during_sync = False

    for symbol_id, data_item in global_truedata_live_market_data.items():
        updated_symbols.add(symbol_id)
        if symbol_id not in app_state.market_data.live_market_data or \
           app_state.market_data.live_market_data[symbol_id] != data_item:
            app_state.market_data.live_market_data[symbol_id] = data_item.copy() # Store copies
            changed_during_sync = True

    # Remove symbols from app_state that are no longer in global_truedata_live_market_data
    symbols_to_remove = [s for s in app_state.market_data.live_market_data if s not in updated_symbols]
    if symbols_to_remove:
        for s in symbols_to_remove:
            del app_state.market_data.live_market_data[s]
        changed_during_sync = True

    if changed_during_sync:
        app_state.market_data.market_data_last_update = datetime.utcnow()
        logger.info(f"MarketDataHandling: Live market data synced from TrueData globals. Cache size: {len(app_state.market_data.live_market_data)}")
    # else:
    #     logger.debug(f"MarketDataHandling: Live market data sync: No changes detected. Cache size: {len(app_state.market_data.live_market_data)}")

    # Sync last_update timestamp from global status if available and more recent
    global_last_update_str = global_truedata_connection_status.get('last_update')
    if global_last_update_str:
        try:
            global_last_update_dt = datetime.fromisoformat(global_last_update_str)
            if app_state.market_data.market_data_last_update is None or global_last_update_dt > app_state.market_data.market_data_last_update:
                app_state.market_data.market_data_last_update = global_last_update_dt
        except ValueError:
            logger.warning(f"Could not parse 'last_update' from global_truedata_connection_status: {global_last_update_str}")


async def initialize_market_data_handling(
    app: Any, # FastAPI app instance, not directly used here now for TD
    settings: AppSettings,
    market_data_state: MarketDataState, # app_state.market_data
    clients_state: ClientsState,     # app_state.clients
    app_state_instance: AppState     # Full app_state
):
    logger.info("Initializing Market Data Handling...")
    market_data_state.live_market_data.clear()

    # Initialize TrueData Singleton Client
    if settings.DATA_PROVIDER_ENABLED and settings.TRUEDATA_USERNAME and settings.TRUEDATA_PASSWORD:
        logger.info(f"MarketDataHandling: Initializing TrueData Singleton Client for user: {settings.TRUEDATA_USERNAME}")

        # Define callbacks for the singleton client
        def _truedata_data_feed_handler(tick_data: Dict):
            # This callback is executed by the singleton client when it processes a message.
            # The primary update to app_state.live_market_data happens via the
            # _sync_truedata_globals_to_app_state job.
            # This callback can be used for immediate logging or pre-processing if needed.
            logger.debug(f"MarketDataHandling (on_data_cb): Tick received by singleton: {tick_data.get('symbol_id')} LTP: {tick_data.get('ltp')}")
            # Optionally, could do some very light, non-blocking processing here.

        async def _truedata_status_change_handler(is_conn: bool, err_msg: Optional[str]):
            # This callback is executed by the singleton client on connection status changes.
            # The primary update to app_state.truedata_connected happens via the sync job.
            # This callback is mainly for logging the event as it happens from the client's perspective.
            logger.info(f"MarketDataHandling (on_status_cb): Singleton client connection status: {'Connected' if is_conn else 'Disconnected'}. Message: {err_msg or 'N/A'}")
            # Trigger an immediate sync if status changes, to reflect faster in app_state
            # This is good for responsiveness of app_state.market_data.truedata_connected
            if app_state_instance.market_data.truedata_connected != is_conn: # Check against current app_state
                 await _sync_truedata_globals_to_app_state(app_state_instance)


        # The singleton's initialize_truedata is async
        await initialize_truedata_singleton(
            settings_override=settings, # Pass the main settings object
            symbols=settings.TRUEDATA_DEFAULT_SYMBOLS, # Explicitly pass default symbols
            on_data=_truedata_data_feed_handler,
            on_status_change=_truedata_status_change_handler
        )

        # Initial sync after attempting to initialize
        await _sync_truedata_globals_to_app_state(app_state_instance)
        logger.info("MarketDataHandling: TrueData Singleton Client initialization process started.")
    else:
        logger.warning("MarketDataHandling: TrueData provider not enabled or credentials missing. TrueData Singleton Client not started.")
        market_data_state.truedata_connected = False
        # No client instance to store in clients_state for the singleton

    # Initialize Zerodha Client (remains unchanged)
    if settings.ZERODHA_API_KEY and settings.ZERODHA_API_SECRET:
        try:
            zerodha_client = ConsolidatedZerodhaClient(settings=settings, app_state=app_state_instance)
            clients_state.zerodha_client_instance = zerodha_client
            logger.info("ConsolidatedZerodhaClient instance created and stored in app_state.clients.")
            # Initial connection status for Zerodha is typically false until login
            logger.info(f"Zerodha client initialized. Connection status (initial from app_state): {market_data_state.zerodha_data_connected}")
        except Exception as e_zc:
            logger.error(f"Error initializing ConsolidatedZerodhaClient: {e_zc}", exc_info=True)
            clients_state.zerodha_client_instance = None
    else:
        logger.info("Zerodha API key/secret not configured. Zerodha client not initialized.")
        clients_state.zerodha_client_instance = None

    market_data_state.market_data_last_update = datetime.utcnow()
    logger.info("Market Data Handling initialization sequence finished.")


def get_live_market_data(symbol: str, market_data_state: MarketDataState) -> Optional[Dict[str, Any]]:
    # This now reads from app_state, which is synced from the singleton's globals
    return market_data_state.live_market_data.get(symbol.upper())

def get_all_live_market_data(market_data_state: MarketDataState) -> Dict[str, Any]:
    # This now reads from app_state
    return market_data_state.live_market_data

def get_market_data_status(market_data_state: MarketDataState, settings: AppSettings) -> Dict[str, Any]:
    data_age_seconds = -1.0
    if market_data_state.market_data_last_update:
        data_age_seconds = (datetime.utcnow() - market_data_state.market_data_last_update).total_seconds()

    # Get TrueData status from the singleton's interface function or synced app_state
    # Using synced app_state here for consistency with other data reads
    td_connected = market_data_state.truedata_connected
    # For more detailed status from singleton if needed:
    # td_status_details = get_truedata_status_singleton()
    # td_connected = td_status_details.get("connected", False)

    return {
        "truedata_connected": td_connected,
        "zerodha_data_connected": market_data_state.zerodha_data_connected,
        "active_data_source": market_data_state.active_data_source,
        "last_update_utc": market_data_state.market_data_last_update.isoformat() if market_data_state.market_data_last_update else None,
        "data_age_seconds": round(data_age_seconds, 2) if data_age_seconds != -1.0 else "N/A",
        "symbols_in_cache": len(market_data_state.live_market_data), # From synced data
        "sample_symbols": list(market_data_state.live_market_data.keys())[:5],
        "truedata_config_user_from_settings": settings.TRUEDATA_USERNAME, # This is from settings, not live status
    }

# This function is no longer needed as the singleton client manages its own connection status internally.
# The _sync_truedata_globals_to_app_state handles updating app_state.
# def set_truedata_connected_status(status: bool, market_data_state: MarketDataState):
#     if market_data_state.truedata_connected != status:
#         market_data_state.truedata_connected = status
#         market_data_state.market_data_last_update = datetime.utcnow()
#         logger.info(f"External call: TrueData connection status set to {status} in app_state.market_data.")


async def get_historical_data_for_strategy(
    symbol: str, days_back: int, interval: str, app_state: AppState, settings: AppSettings
) -> Optional[List[Dict[str, Any]]]:
    logger.info(f"Attempting to fetch historical data for {symbol}...")
    # For TrueData historical, if the singleton client exposes such a method, it would be called here.
    # Assuming the singleton does not yet have a get_historical_data method exposed via its interface.
    # For now, TrueData historical part remains non-functional with the singleton.

    zd_client = app_state.clients.zerodha_client_instance
    client_to_use: Optional[Any] = None
    client_name = "None"

    # Prioritize Zerodha if available and connected, as TrueData singleton's historical API isn't defined here yet
    if zd_client and app_state.market_data.zerodha_data_connected and hasattr(zd_client, 'get_historical_data'): # Assuming method name
        client_to_use = zd_client
        client_name = "Zerodha"
    # else if is_truedata_singleton_connected():
    #    logger.info("TrueData singleton is connected, but its historical data fetch method is not integrated here yet.")

    if not client_to_use:
        logger.warning(f"No suitable client for historical data for {symbol} (Zerodha not connected/available, TrueData historical not integrated).")
        return []
    try:
        logger.info(f"Using {client_name} client for historical for {symbol}.")
        # Example for Zerodha (actual method name might vary, e.g., 'historical_data')
        # data = await client_to_use.historical_data(symbol_token, from_date, to_date, interval)
        logger.warning(f"Placeholder: Historical data fetch for {symbol} via {client_name} not fully implemented. Returning [].")
        return []
    except Exception as e:
        logger.error(f"Error fetching historical for {symbol} via {client_name}: {e}", exc_info=True)
        return []

```
