from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
import logging
# Import custom exceptions from the client module
from src.clients.zerodha_client import ZerodhaTokenError, ZerodhaAPIError
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel

from src.app_state import AppState, MarketDataState
from src.config import AppSettings
from src.core.utils import create_api_success_response, format_datetime_for_api # Import utilities
from src.database import execute_db_query

try:
    from backend.server import get_app_state, get_settings
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance
    def get_settings(): return _global_settings_instance

logger = logging.getLogger(__name__)

zerodha_router = APIRouter(prefix="/system", tags=["Zerodha System Control"])
zerodha_direct_router = APIRouter(prefix="/zerodha", tags=["Zerodha Direct Authentication"])

class ZerodhaAuthRequest(BaseModel):
    request_token: str

@zerodha_router.get("/zerodha-auth-status", summary="Get Zerodha authentication status from app_state")
async def get_zerodha_auth_status_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    try:
        client = app_state.clients.zerodha_client_instance
        client_status_summary = {"message": "Zerodha client not initialized in app_state.clients."}
        login_url_to_provide = None

        if client and hasattr(client, 'get_client_status_summary'):
            client_status_summary = client.get_client_status_summary()
        elif client:
             client_status_summary = {
                "is_kite_instance_initialized": True,
                "app_state_zerodha_data_connected_flag": app_state.market_data.zerodha_data_connected,
             }

        is_effectively_connected = app_state.market_data.zerodha_data_connected
        if isinstance(client_status_summary, dict) and 'is_session_active_sdk_level' in client_status_summary:
            is_effectively_connected = client_status_summary['is_session_active_sdk_level']

        if settings.ZERODHA_API_KEY and not is_effectively_connected:
            if client and hasattr(client, 'get_login_url'):
                login_url_to_provide = client.get_login_url()
                if not login_url_to_provide: # get_login_url might return None if kite is not init'd
                    logger.warning("client.get_login_url() returned None. Cannot provide specific login URL.")
            else:
                 logger.warning("Zerodha client instance or get_login_url method not available. Cannot provide specific login URL.")

        response_data = {
            "zerodha_connection_state_from_app_state": app_state.market_data.zerodha_data_connected,
            "client_instance_status": client_status_summary,
        }
        if login_url_to_provide:
            response_data["oauth_login_url"] = login_url_to_provide
            response_data["instructions"] = "Visit oauth_login_url to get request_token for authentication via /api/zerodha/callback."

        return create_api_success_response(data=response_data)
    except Exception as e:
        logger.error(f"Error in /zerodha-auth-status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Zerodha auth status: {str(e)}")

@zerodha_router.post("/zerodha-authenticate", summary="Authenticate Zerodha with request token")
async def authenticate_zerodha_route(auth_data: ZerodhaAuthRequest, app_state: AppState = Depends(get_app_state)):
    try:
        request_token = auth_data.request_token
        if not request_token: raise HTTPException(status_code=400, detail="Request token is required.")

        client = app_state.clients.zerodha_client_instance
        if not client or not hasattr(client, 'generate_session'):
            raise HTTPException(status_code=503, detail="Zerodha client not available or does not support session generation.")

        # generate_session now returns True on success, or raises specific exceptions on failure.
        await client.generate_session(request_token)

        # If it didn't raise, it's a success.
        logger.info(f"Zerodha re-authentication successful via /system/zerodha-authenticate for user: {client.current_user_id or 'Unknown'}")
        client_status = client.get_client_status_summary() if hasattr(client, 'get_client_status_summary') else "Status method not available"
        return create_api_success_response(message="Zerodha re-authentication successful.", data={"client_status": client_status})

    except ZerodhaTokenError as e_token:
        logger.warning(f"ZerodhaTokenError in /system/zerodha-authenticate: {e_token.message}")
        raise HTTPException(status_code=e_token.status_code, detail=e_token.message)
    except ZerodhaAPIError as e_api:
        logger.error(f"ZerodhaAPIError in /system/zerodha-authenticate: {e_api.message} (Status: {e_api.status_code})", exc_info=True)
        raise HTTPException(status_code=e_api.status_code, detail=e_api.message)
    except HTTPException as http_exc: # Re-raise existing HTTPExceptions
        raise http_exc
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"Unexpected error in /system/zerodha-authenticate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected server error during Zerodha re-authentication: {str(e)}")

@zerodha_direct_router.get("/auth-url", summary="Generate Zerodha OAuth login URL")
async def get_zerodha_auth_url_direct_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    try:
        client = app_state.clients.zerodha_client_instance
        login_url = None
        if client and hasattr(client, 'get_login_url'):
            login_url = client.get_login_url()
            if not login_url: # get_login_url might return None if kite is not init'd
                logger.error("client.get_login_url() returned None. Zerodha client might not be properly initialized with API key.")
                raise HTTPException(status_code=503, detail="Zerodha client not ready to generate login URL.")
        elif settings.ZERODHA_API_KEY: # Fallback only if client or its method is missing, but key IS present
            logger.warning("Zerodha client instance or get_login_url method not available. Providing a generic login URL. THIS IS NOT IDEAL as redirect URI might not match.")
            # THIS IS A GENERAL LINK, THE ACTUAL SDK LOGIN URL IS PREFERRED
            login_url = "https://kite.trade/" # General link, not API specific to avoid key exposure
        else:
            raise HTTPException(status_code=503, detail="Zerodha API key not configured. Cannot generate login URL.")

        logger.info(f"Login URL to be provided: {login_url}")
        return create_api_success_response(data={"login_url": login_url}, message="Client should have redirect_uri pre-configured or handle it.")
    except HTTPException as e_http: raise e_http
    except Exception as e:
        logger.error(f"Error generating Zerodha auth URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating Zerodha auth URL: {str(e)}")

class ZerodhaCallbackQueryParams(BaseModel):
    request_token: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None

@zerodha_direct_router.get("/callback", summary="Handle Zerodha OAuth callback")
async def zerodha_oauth_callback_direct_route(params: ZerodhaCallbackQueryParams = Depends(), app_state: AppState = Depends(get_app_state)):
    # This route returns HTMLResponse, so create_api_success_response is not applicable here.
    if params.status != "success" or not params.request_token:
        error_message = f"Zerodha OAuth callback error. Status: {params.status}, Action: {params.action}, Token: {'Present' if params.request_token else 'Missing'}"
        logger.error(error_message)
        return HTMLResponse(f"<body>❌ Auth Failed: {error_message}. Please try logging in again.</body>", status_code=400)

    request_token = params.request_token
    logger.info(f"Received request_token at /zerodha/callback: {request_token[:7]}...")
    client = app_state.clients.zerodha_client_instance
    if not client or not hasattr(client, 'generate_session'):
        logger.error("Zerodha client not available/configured for callback session generation.")
        return HTMLResponse("<body>❌ Server Configuration Error: Zerodha client not ready. Check server logs.</body>", status_code=503)

    try:
        await client.generate_session(request_token)
        # If generate_session succeeds, client.current_user_id should be populated.
        user_id_display = client.current_user_id or getattr(client, 'client_display_name', 'UNKNOWN_USER')
        logger.info(f"Zerodha auth successful via callback for user '{user_id_display}'. Token persisted.")
        return HTMLResponse(f"<body>✅ Zerodha Authentication Successful for user {user_id_display}. You can close this window.</body>")
    except ZerodhaTokenError as e_token:
        logger.warning(f"ZerodhaTokenError during OAuth callback: {e_token.message}")
        return HTMLResponse(f"<body>❌ Authentication Failed: {e_token.message}. Please try again or contact support.</body>", status_code=e_token.status_code)
    except ZerodhaAPIError as e_api:
        logger.error(f"ZerodhaAPIError during OAuth callback: {e_api.message} (Status: {e_api.status_code})", exc_info=True)
        return HTMLResponse(f"<body>❌ Authentication Error: {e_api.message}. Please check the details or contact support.</body>", status_code=e_api.status_code)
    except Exception as e:
        logger.error(f"Unexpected error during Zerodha OAuth callback: {e}", exc_info=True)
        return HTMLResponse("<body>❌ An unexpected server error occurred during authentication. Please try again later.</body>", status_code=500)

@zerodha_direct_router.get("/status", summary="Get current Zerodha connection status from client")
async def get_zerodha_status_direct_route(app_state: AppState = Depends(get_app_state)):
    client = app_state.clients.zerodha_client_instance
    client_status_summary = {"message": "Zerodha client not initialized in app_state.clients."}
    if client and hasattr(client, 'get_client_status_summary'):
        client_status_summary = client.get_client_status_summary()

    response_data = {
        "client_status": client_status_summary,
        "app_state_market_data_zerodha_connected": app_state.market_data.zerodha_data_connected
    }
    return create_api_success_response(data=response_data)

@zerodha_direct_router.post("/disconnect", summary="Disconnect Zerodha session (clears local token)")
async def disconnect_zerodha_direct_route(app_state: AppState = Depends(get_app_state)):
    client = app_state.clients.zerodha_client_instance
    message = ""
    if client and hasattr(client, 'disconnect'):
        await client.disconnect()
        logger.info("Zerodha client disconnect method called. Session token cleared locally.")
        message = "Zerodha session disconnected (local token cleared)."
    else:
        app_state.market_data.zerodha_data_connected = False # Fallback if client or method missing
        logger.info("Zerodha client not available or no disconnect method; updated app_state directly.")
        message = "Zerodha connection status in app_state set to disconnected (client might be missing)."

    return create_api_success_response(message=message, data={"status": "disconnected"})

