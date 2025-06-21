from fastapi import APIRouter, HTTPException, Request, Depends
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, time # Keep time for MARKET_OPEN_TIME comparisons if settings doesn't provide datetime.time
import json
import uuid
import random # For test-feed

# Import AppState and AppSettings for dependency injection and type hinting
from src.app_state import AppState, MarketDataState # MarketDataState for specific dependency
from src.config import AppSettings

# Import dependency injectors
try:
    from backend.server import get_app_state, get_settings, get_market_data_state
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance  
    def get_settings(): return _global_settings_instance
    def get_market_data_state(): return _global_app_state_instance.market_data

logger = logging.getLogger(__name__)

market_data_router = APIRouter(prefix="/market-data", tags=["Market Data"])

# Removed get_live_market_data_internal helper, routes will access app_state.market_data directly.

@market_data_router.get("/analysis", summary="Get comprehensive market analysis using perfect analyzers")
async def get_market_analysis_route(app_state: AppState = Depends(get_app_state)):
    # Analyzers are expected to be in app_state.clients.analyzers or similar
    # For now, using app_state.clients.elite_engine as a proxy if analyzers are part of it, or a direct analyzers field.
    # Let's assume app_state.clients.analyzers if it were structured that way.
    # Given current app_state.py, analyzers are not directly on app_state.clients.
    # The original placeholder `analyzers` was a module-level dict.
    # For this refactor, we'll assume analyzers are part of elite_engine or a similar service in app_state.clients.
    # If elite_engine itself contains the analyzers:

    # elite_engine_instance = app_state.clients.elite_engine
    # if not elite_engine_instance or not hasattr(elite_engine_instance, 'get_analyzers_status'): # Hypothetical method
    #     raise HTTPException(status_code=503, detail="Market analyzers via elite_engine not available or not initialized.")
    # current_analyzers = elite_engine_instance.get_analyzers_status() # Hypothetical

    # Using a simpler check based on presence of elite_engine for now as analyzers specific state is not in AppState
    if not app_state.clients.elite_engine:
         raise HTTPException(status_code=503, detail="Elite engine (containing analyzers) not available.")

    symbols_to_check = ["NIFTY", "BANKNIFTY", "FINNIFTY"] # These should ideally be configurable
    market_data_available_for_analysis = False
    example_data_found = {}

    for symbol in symbols_to_check:
        data = app_state.market_data.live_market_data.get(symbol.upper())
        if data and data.get('ltp') is not None: # Check for ltp specifically
            market_data_available_for_analysis = True
            example_data_found[symbol] = data.get('ltp')

    if not market_data_available_for_analysis:
        raise HTTPException(status_code=404, detail=f"No live market data for key symbols ({', '.join(symbols_to_check)}) to perform analysis.")

    return {
        "status": "success",
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "message": "Market analysis placeholder: Live market data for key symbols is present.",
        "example_ltp_found": example_data_found,
        "analyzers_status_note": "Placeholder - real analyzer status would be here, e.g., from elite_engine."
        # "analyzers_status": current_analyzers # If fetched from elite_engine
    }

@market_data_router.get("/status", summary="Get market data provider status")
async def get_market_data_status_route(
    market_data_state: MarketDataState = Depends(get_market_data_state),
    settings: AppSettings = Depends(get_settings)
):
    try:
        now_utc = datetime.utcnow()

        # Use settings for market open/close times
        _market_open_time = settings.MARKET_OPEN_TIME
        _market_close_time = settings.MARKET_CLOSE_TIME

        # Timezone handling for market hours check
        is_market_hours_val = False
        try:
            import pytz
            ist_tz = pytz.timezone('Asia/Kolkata')
            current_time_ist = datetime.now(ist_tz).time()
            current_day_ist = datetime.now(ist_tz).weekday()
            if current_day_ist < 5: # Monday to Friday
                is_market_hours_val = _market_open_time <= current_time_ist <= _market_close_time
        except ImportError:
            logger.warning("pytz not installed, market hours check may be based on server's local time if not IST.")
            # Fallback to naive datetime comparison if pytz is not available
            # This is less reliable if server is not in IST.
            now_local_time = datetime.now().time()
            is_market_hours_val = _market_open_time <= now_local_time <= _market_close_time and datetime.now().weekday() < 5

        data_age_minutes = -1.0
        if market_data_state.market_data_last_update:
            data_age_seconds = (now_utc - market_data_state.market_data_last_update).total_seconds()
            data_age_minutes = round(data_age_seconds / 60, 2)

        status_payload = {
            "truedata_module_connected_flag": market_data_state.truedata_connected,
            "zerodha_module_connected_flag": market_data_state.zerodha_data_connected,
            "active_data_source_in_use": market_data_state.active_data_source,
            "data_provider_globally_enabled": settings.DATA_PROVIDER_ENABLED,
            "market_hours_currently_active": is_market_hours_val,
            "last_data_update_utc": market_data_state.market_data_last_update.isoformat() if market_data_state.market_data_last_update else None,
            "data_age_minutes": data_age_minutes,
            "symbols_in_cache_count": len(market_data_state.live_market_data),
            "cache_sample_keys": list(market_data_state.live_market_data.keys())[:5],
            "truedata_config_details": {
                "username": settings.TRUEDATA_USERNAME,
                "url": settings.TRUEDATA_URL,
                "port": settings.TRUEDATA_PORT,
                "sandbox_mode": settings.TRUEDATA_SANDBOX
            },
            "connection_status_derived": "LIVE_DATA_RECENT" if market_data_state.truedata_connected and data_age_minutes >= 0 and data_age_minutes < 2 else "STALE_OR_DISCONNECTED",
            "current_server_time_utc": now_utc.isoformat(),
        }
        return {"success": True, "market_data_overall_status": status_payload}
    except Exception as e:
        logger.error(f"Error getting market data status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting market data status: {str(e)}")

@market_data_router.post("/test-feed", summary="Test market data feed by updating app_state.market_data")
async def test_market_data_feed_route(market_data_state: MarketDataState = Depends(get_market_data_state)):
    try:
        test_symbols = ['NIFTY_TEST', 'BANKNIFTY_TEST', 'FINNIFTY_TEST']
        for symbol in test_symbols:
            market_data_state.live_market_data[symbol] = {
                'ltp': round(random.uniform(18000, 22000), 2),
                'volume': random.randint(1000000, 5000000),
                'oi': random.randint(1000000, 10000000),
                'change_percent': round(random.uniform(-3, 3), 2),
                'timestamp': datetime.utcnow().isoformat(),
                'data_source': 'TEST_FEED_SIMULATED_IN_APP_STATE'
            }
        market_data_state.market_data_last_update = datetime.utcnow()
        market_data_state.truedata_connected = True # Simulate connection for test

        logger.info(f"Test feed updated app_state.market_data for symbols: {test_symbols}")
        return {
            "status": "success",
            "message": "Market data feed test successful. app_state.market_data updated with simulated data.",
            "symbols_updated_in_app_state": test_symbols,
            "current_cache_size_in_app_state": len(market_data_state.live_market_data),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error testing market data feed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error testing market data feed: {str(e)}")

@market_data_router.get("/indices", summary="Get live market indices from app_state.market_data")
async def get_market_indices_route(
    market_data_state: MarketDataState = Depends(get_market_data_state),
    settings: AppSettings = Depends(get_settings) # For market times
):
    try:
        _market_open_time = settings.MARKET_OPEN_TIME
        _market_close_time = settings.MARKET_CLOSE_TIME
        current_time_ist_str, is_market_hours_val = "UNKNOWN (pytz error)", False
        try:
            import pytz
            ist_tz = pytz.timezone('Asia/Kolkata')
            current_time_ist = datetime.now(ist_tz)
            current_time_ist_str = current_time_ist.isoformat()
            if current_time_ist.weekday() < 5: # Monday to Friday
                is_market_hours_val = _market_open_time <= current_time_ist.time() <= _market_close_time
        except ImportError: logger.warning("pytz not available for /indices route market hours check.")

        indices_to_fetch = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] # Could be part of settings
        indices_output_data = {}
        data_found_for_any_index = False

        for symbol_key in indices_to_fetch:
            data_from_cache = market_data_state.live_market_data.get(symbol_key.upper())
            if data_from_cache:
                data_found_for_any_index = True
                indices_output_data[symbol_key.upper()] = data_from_cache # Return the whole cached dict
            else:
                 indices_output_data[symbol_key.upper()] = None

        derived_connection_status = "CONNECTED_VIA_CACHE" if data_found_for_any_index and market_data_state.truedata_connected else "DISCONNECTED_OR_NO_DATA_IN_CACHE"

        return {
            "status": "success" if data_found_for_any_index else "no_data_for_indices",
            "timestamp_ist_approx": current_time_ist_str,
            "market_status_derived": "OPEN" if is_market_hours_val else "CLOSED",
            "data_source_report": "APP_STATE_LIVE_CACHE",
            "connection_status_derived": derived_connection_status,
            "last_cache_update_utc": market_data_state.market_data_last_update.isoformat() if market_data_state.market_data_last_update else "N/A",
            "indices_data": indices_output_data
        }
    except Exception as e:
        logger.error(f"Error getting market indices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting market indices: {str(e)}")

@market_data_router.get("/live", summary="Get all live market data from app_state.market_data")
async def get_live_market_data_route(market_data_state: MarketDataState = Depends(get_market_data_state)):
    logger.info("Request for all live market data from app_state.market_data.")
    try:
        if not market_data_state.live_market_data:
            logger.warning("app_state.market_data.live_market_data cache is empty.")
            return {"success": True, "data": {}, "count":0, "message": "Live market data cache in app_state is currently empty."}

        return {"success": True, "data": market_data_state.live_market_data, "count":len(market_data_state.live_market_data)}
    except Exception as e:
        logger.error(f"Error getting all live market data from app_state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error accessing live market data: {str(e)}")

@market_data_router.get("/symbol/{symbol_name}", summary="Get live market data for a specific symbol from app_state.market_data")
# Renamed path parameter to avoid clash with 'symbol' variable name if any
async def get_symbol_data_route(symbol_name: str, market_data_state: MarketDataState = Depends(get_market_data_state)):
    try:
        data = market_data_state.live_market_data.get(symbol_name.upper())
        if data:
            return {"status": "success", "symbol": symbol_name.upper(), "data": data, "source": "APP_STATE_LIVE_CACHE"}
        else:
            raise HTTPException(status_code=404, detail=f"Market data not found in app_state cache for symbol {symbol_name.upper()}")
    except HTTPException as http_exc:
        raise http_exc # Re-raise if already an HTTPException
    except Exception as e:
        logger.error(f"Error getting symbol data for {symbol_name} from app_state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting symbol data: {str(e)}")

