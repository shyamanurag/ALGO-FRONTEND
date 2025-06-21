from fastapi import APIRouter, HTTPException, Request, Depends
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import json
import asyncio
import socket
import websockets

from src.app_state import AppState # Keep AppState for general purposes if needed by other parts of routes
from src.config import AppSettings
from src.core.utils import create_api_success_response, format_datetime_for_api

# Import new TrueData singleton interface functions
from backend.truedata_client import (
    initialize_truedata as initialize_truedata_singleton,
    get_truedata_status as get_truedata_status_singleton,
    is_connected as is_truedata_singleton_connected,
    shutdown_truedata_client as shutdown_truedata_singleton,
    add_truedata_symbols, # Assuming these might be useful for API control
    remove_truedata_symbols,
    live_market_data as global_truedata_live_market_data # For direct data view if needed
)

try:
    from backend.server import get_app_state, get_settings # These provide AppState and AppSettings
except ImportError:
    _fallback_logger_td = logging.getLogger(__name__)
    _fallback_logger_td.error("CRITICAL: Could not import get_app_state, get_settings from backend.server for truedata_routes.py.")
    # Fallback for standalone testing if needed, though ideally routes are tested via TestClient
    from src.app_state import app_state as _global_app_state_instance_td
    from src.config import settings as _global_settings_instance_td
    async def get_app_state(): return _global_app_state_instance_td
    async def get_settings(): return _global_settings_instance_td

logger = logging.getLogger(__name__)

truedata_router = APIRouter(prefix="/system", tags=["TrueData System Control & Tests"])

@truedata_router.post("/truedata/connect", summary="Initialize/Attempt to connect the TrueData Singleton Client")
async def truedata_connect_route(settings: AppSettings = Depends(get_settings)):
    # The singleton's initialize_truedata handles its own connection logic.
    # We pass necessary config from settings if they are not purely from ENV for the singleton.
    # The singleton provided uses ENV vars primarily, or class defaults.
    # initialize_truedata_singleton can take params to override its internal defaults/env vars.
    try:
        logger.info("API call to initialize/connect TrueData Singleton Client.")
        await initialize_truedata_singleton(
            username=settings.TRUEDATA_USERNAME, # Pass from app settings
            password=settings.TRUEDATA_PASSWORD, # Pass from app settings
            # apikey=settings.TRUEDATA_APIKEY, # If AppSettings has this
            # ws_url=settings.TRUEDATA_WS_URL_OVERRIDE or settings.TRUEDATA_URL, # Construct or pass appropriate URL
            # symbols=list(settings.PARSED_TRUEDATA_SYMBOL_MAPPINGS.values()) # Initial symbols
        )
        # The singleton manages its connection state internally.
        # The success of this call means initialization was triggered.
        # Actual connection status is polled via get_truedata_status_singleton or synced to app_state.
        return create_api_success_response(message="TrueData client initialization/connection process triggered.")
    except Exception as e:
        logger.error(f"Error calling initialize_truedata_singleton: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during TrueData client initialization: {str(e)}")

@truedata_router.post("/truedata/disconnect", summary="Attempt to disconnect the TrueData Singleton Client")
async def truedata_disconnect_route():
    try:
        logger.info("API call to disconnect TrueData Singleton Client.")
        await shutdown_truedata_singleton()
        return create_api_success_response(message="TrueData client shutdown process triggered.")
    except Exception as e:
        logger.error(f"Error calling shutdown_truedata_singleton: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during TrueData client shutdown: {str(e)}")

@truedata_router.get("/truedata/status", summary="Get TrueData client and connection status")
async def get_truedata_status_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    logger.debug("API call for TrueData status.")

    singleton_status = get_truedata_status_singleton() # Get direct status from singleton's global var

    status_data = {
        "singleton_client_status": singleton_status,
        "app_state_synced_truedata_connected_flag": app_state.market_data.truedata_connected, # From periodic sync
        "active_data_source_in_app_state": app_state.market_data.active_data_source,
        "last_app_state_sync_utc": format_datetime_for_api(app_state.market_data.market_data_last_update),
        "configured_username_from_settings": settings.TRUEDATA_USERNAME,
        "sample_live_data_from_singleton_global": dict(list(global_truedata_live_market_data.items())[:3]) # Show a few symbols
    }
    return create_api_success_response(data=status_data, message="TrueData status from singleton and app_state.")

# Routes for adding/removing symbols dynamically (if supported by singleton client)
@truedata_router.post("/truedata/subscribe", summary="Subscribe to additional TrueData symbols")
async def truedata_subscribe_symbols_route(symbols: List[str]):
    if not symbols:
        raise HTTPException(status_code=400, detail="Symbols list cannot be empty.")
    try:
        logger.info(f"API call to subscribe to TrueData symbols: {symbols}")
        await add_truedata_symbols(symbols)
        return create_api_success_response(message=f"Subscription request for {symbols} sent to TrueData client.")
    except Exception as e:
        logger.error(f"Error calling add_truedata_symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error subscribing to symbols: {str(e)}")

@truedata_router.post("/truedata/unsubscribe", summary="Unsubscribe from TrueData symbols")
async def truedata_unsubscribe_symbols_route(symbols: List[str]):
    if not symbols:
        raise HTTPException(status_code=400, detail="Symbols list cannot be empty.")
    try:
        logger.info(f"API call to unsubscribe from TrueData symbols: {symbols}")
        await remove_truedata_symbols(symbols)
        return create_api_success_response(message=f"Unsubscription request for {symbols} sent to TrueData client.")
    except Exception as e:
        logger.error(f"Error calling remove_truedata_symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error unsubscribing from symbols: {str(e)}")


# The following test routes primarily use settings and basic socket operations,
# so they might not need significant changes beyond ensuring they align with how the
# singleton might be configured (e.g., if URL/port are now fixed in the singleton).
# For now, they use settings directly, which is fine.

@truedata_router.get("/truedata-config", summary="Get current TrueData configuration from settings")
async def get_truedata_config_route(settings: AppSettings = Depends(get_settings)):
    # This route shows settings, not live client config, so it's mostly fine.
    # Singleton specific effective URL/port could be added if different from settings.
    singleton_client_effective_url = "N/A (Client Not Initialized)"
    # This would require getting the instance, which is not directly exposed by interface.
    # For simplicity, we'll rely on get_truedata_status_singleton for live client info.

    config_data = {
        "settings_username": settings.TRUEDATA_USERNAME,
        "settings_url": settings.TRUEDATA_URL,
        "settings_port": settings.TRUEDATA_PORT,
        "settings_sandbox_mode": settings.TRUEDATA_SANDBOX,
        "settings_data_provider_enabled_flag": settings.DATA_PROVIDER_ENABLED,
        "settings_symbol_mappings_configured_count": len(settings.PARSED_TRUEDATA_SYMBOL_MAPPINGS),
        # "singleton_effective_ws_url": os.environ.get("TRUEDATA_WS_URL_GLOBAL", "wss://api.truedata.in/websocket") # Example of showing singleton's default
    }
    return create_api_success_response(data={"config_from_settings": config_data, "timestamp": format_datetime_for_api(datetime.utcnow())})

@truedata_router.post("/test-truedata-protocol", summary="Test TrueData LOGIN command via direct socket connection (uses settings)")
async def test_truedata_protocol_route(settings: AppSettings = Depends(get_settings)):
    td_url, td_port, td_user, td_pass = settings.TRUEDATA_URL, settings.TRUEDATA_PORT, settings.TRUEDATA_USERNAME, settings.TRUEDATA_PASSWORD
    if not all([td_url, td_port, td_user, td_pass]):
        raise HTTPException(status_code=400, detail="TrueData credentials/URL/port not fully configured in settings for protocol test.")
    logger.info(f"🧪 Testing TrueData LOGIN (socket) for {td_user}@{td_url}:{td_port}")
    results = {}
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(3)
        sock.connect((td_url, td_port)); login_cmd = f"LOGIN {td_user} {td_pass}\r\n"
        sock.send(login_cmd.encode()); response = sock.recv(1024).decode(); sock.close()
        results["direct_socket_login_test"] = {"command_sent": login_cmd.strip(), "response_received": response.strip(), "is_success_keyword_present": any(k in response.upper() for k in ["OK", "SUCCESS", "LOGIN SUCCESSFUL"])}
    except Exception as e: results["direct_socket_login_test"] = {"error_details": str(e), "target_host": td_url, "target_port": td_port}

    response_data = {"connection_parameters_used": {"host":td_url, "port":td_port, "user":td_user}, "socket_test_results": results}
    return create_api_success_response(data=response_data)

@truedata_router.post("/test-truedata-websocket-formats", summary="Test various WebSocket URL formats for TrueData (uses settings)")
async def test_truedata_websocket_formats_route(settings: AppSettings = Depends(get_settings)):
    td_url, td_port, td_user, td_pass = settings.TRUEDATA_URL, settings.TRUEDATA_PORT, settings.TRUEDATA_USERNAME, settings.TRUEDATA_PASSWORD
    if not all([td_url, td_port, td_user, td_pass]):
        raise HTTPException(status_code=400, detail="TrueData credentials/URL/port not fully configured for WebSocket test.")
    logger.info(f"🧪 Testing TrueData WebSocket formats for {td_user}@{td_url}:{td_port}")
    test_paths = ["", "/websocket", "/socket.io/?transport=websocket", "/data", "/feed"] # Common paths
    results = {}
    # This auth_msg_json is an example, TrueDataSingletonClient uses its own internal auth.
    # auth_msg_json = json.dumps({"action": "login", "username": td_user, "password": td_pass})
    for path in test_paths:
        # Prefer wss for TrueData official, but allow ws for local/other test URLs from settings.
        protocol = "wss" if "truedata.in" in td_url else "ws"
        ws_url_val = f"{protocol}://{td_url}:{td_port}{path}"
        if "truedata.in" in td_url and not path.endswith("/websocket"): # Official usually needs /websocket
            if path == "": ws_url_val = f"{protocol}://{td_url}:{td_port}/websocket"
            else: ws_url_val = f"{protocol}://{td_url}:{td_port}{path}/websocket" # if path is like /custom

        try:
            async with websockets.connect(ws_url_val, timeout=2, close_timeout=1, ping_interval=None) as ws_conn:
                # Optional: Send a generic auth if testing requires it, but this test is more about URL format.
                # await ws_conn.send(auth_msg_json)
                # response = await asyncio.wait_for(ws_conn.recv(), timeout=1.5)
                results[ws_url_val] = {"status": "connected_successfully"} #, "initial_response_sample": response[:100]}
        except Exception as e: results[ws_url_val] = {"status": "failed", "error_type": type(e).__name__, "error_details": str(e)[:100]}

    response_data = {"target_host": td_url, "target_port": td_port, "test_results": results}
    return create_api_success_response(data=response_data)

@truedata_router.post("/scan-truedata-ports", summary="Scan common ports for open TCP connection on TrueData host")
async def scan_truedata_ports_route(settings: AppSettings = Depends(get_settings)):
    td_url = settings.TRUEDATA_URL
    common_ports_list = [80, 443, 3000, 3001, 8080, 8081, 8082, 8084, 8086, 8088, settings.TRUEDATA_PORT]
    results = {}
    logger.info(f"🔍 Scanning common TCP ports on {td_url}")
    for port_val in set(common_ports_list):
        try:
            conn = socket.create_connection((td_url, port_val), timeout=0.2)
            conn.close(); results[port_val] = "OPEN"
        except (socket.timeout, ConnectionRefusedError): results[port_val] = "CLOSED"
        except Exception as e: results[port_val] = f"ERROR: {str(e)[:50]}"

    response_data = {"host": td_url, "scanned_tcp_ports": results, "likely_open_ports": [p for p,s in results.items() if s=="OPEN"]}
    return create_api_success_response(data=response_data)

```
