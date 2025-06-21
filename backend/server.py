"""
Elite Autonomous Algo Trading Platform
Main application file. Initializes FastAPI app, loads configuration, sets up state,
and includes all API routers.
"""

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
import asyncio
import json
from datetime import datetime, time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functools import partial

from src.config import settings, AppSettings
from src.app_state import app_state, AppState, MarketDataState, StrategyState, TradingControlState, SystemOverallState, ClientsState
from src.core.schemas import ErrorDetail, HTTPErrorResponse
from src.core.logging_config import setup_logging
from src.database import execute_db_query, fetch_one_db

# ROOT_DIR in server.py refers to the 'backend/' directory.
# settings.PROJECT_ROOT_DIR refers to the directory containing 'backend/'.
# settings.SRC_DIR refers to 'backend/src/'.
ROOT_DIR = Path(__file__).parent

setup_logging(log_level=settings.LOG_LEVEL)
logger_server = logging.getLogger(__name__)

CORE_COMPONENTS_AVAILABLE = False
try:
    import sys
    # sys.path.append(str(ROOT_DIR)) # Not strictly needed if project structure is standard
    from src.core.models import Order
    from src.recommendations import EliteRecommendationEngine
    CORE_COMPONENTS_AVAILABLE = True
    logger_server.info("Core component source files appear available.")
except ImportError as e:
    logger_server.warning(f"Core component source files might be missing: {e}")

app = FastAPI(title="Elite Autonomous Algo Trading Platform", version="2.0.0") # Version could also be from settings

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_code = getattr(exc, 'error_code', f"HTTP_{exc.status_code}")
    error_context = getattr(exc, 'context', None)
    logger_server.error(
        f"HTTPException: Status={exc.status_code}, Code={error_code}, Detail='{exc.detail}', Path='{request.url.path}'",
        exc_info=False)
    error_detail = ErrorDetail(code=error_code, message=str(exc.detail), context=error_context)
    return JSONResponse(status_code=exc.status_code, content=HTTPErrorResponse(errors=[error_detail]).model_dump(), headers=getattr(exc, "headers", None))

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger_server.exception(f"Unhandled exception: {request.method} {request.url.path}", exc_info=exc)
    exc_type_str = str(type(exc).__name__)
    error_message = "An unexpected internal server error occurred."
    error_detail = ErrorDetail(code="INTERNAL_SERVER_ERROR", message=error_message,
                               context={"exception_type": exc_type_str} if settings.LOG_LEVEL.upper() == "DEBUG" else None)
    return JSONResponse(status_code=500, content=HTTPErrorResponse(errors=[error_detail]).model_dump())

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

from src.api_routes.admin_routes import api_router as admin_router
from src.api_routes.strategy_routes import strategy_router, autonomous_strategy_router
from src.api_routes.trading_routes import trading_router
from src.api_routes.market_data_routes import market_data_router
from src.api_routes.user_routes import user_router
from src.api_routes.system_routes import system_router
from src.api_routes.truedata_routes import truedata_router
from src.api_routes.zerodha_routes import zerodha_router, zerodha_direct_router
from src.api_routes.webhook_routes import webhook_router

app.add_middleware(CORSMiddleware,
    allow_origins=[str(settings.FRONTEND_URL)] if settings.FRONTEND_URL and str(settings.FRONTEND_URL) != "*" else ["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])

# active_websocket_connections: set = set() # Removed global WebSocket connection set

class StrategyConfig(BaseModel): # This should ideally move to a relevant module like admin_routes or core.schemas
    name: str; enabled: bool; parameters: Dict = Field(default_factory=dict); allocation: float = 0.2

async def get_app_state() -> AppState: return app_state
async def get_settings() -> AppSettings: return app_state.config
# ... other state getters as before ...
async def get_market_data_state() -> MarketDataState: return app_state.market_data
async def get_trading_control_state() -> TradingControlState: return app_state.trading_control
async def get_system_overall_state() -> SystemOverallState: return app_state.system_status
async def get_clients_state() -> ClientsState: return app_state.clients
async def get_strategy_state() -> StrategyState: return app_state.strategies


def is_market_open(current_app_state: AppState) -> bool:
    if not current_app_state.config:
        logger_server.critical("is_market_open: AppSettings not available in app_state.config!")
        return False
    _market_open_time = current_app_state.config.MARKET_OPEN_TIME
    _market_close_time = current_app_state.config.MARKET_CLOSE_TIME
    from datetime import datetime as dt_local
    import pytz
    ist = pytz.timezone('Asia/Kolkata'); now_ist = dt_local.now(ist)
    if now_ist.weekday() >= 5: is_open = False
    else: is_open = _market_open_time <= now_ist.time() <= _market_close_time
    current_app_state.system_status.market_open = is_open
    return is_open

# Removed old broadcast_websocket_message function. It's now in src.core.utils.py
# Removed old system_health_check_job function. It's now in src.scheduler_jobs.py
# Removed old setup_scheduler_jobs function. It's now in src.scheduler_jobs.py (as initialize_scheduler)

# The WebSocket endpoint below needs to be found by its path, e.g. /ws/trading-data or /ws/{user_id}
# Assuming it's the one found by grep: @app.websocket("/ws/{user_id}")
# If there are multiple, ensure this modification targets the correct one.

@app.websocket("/ws/{user_id}")
async def websocket_trading_data_endpoint(websocket: Any, user_id: str, app_state_local: AppState = Depends(get_app_state)):
    # Param name changed from app_state to app_state_local to avoid conflict if app_state global is accessed
    await websocket.accept()
    logger_server.info(f"WebSocket connection accepted for user {user_id} from {websocket.client.host}")
    app_state_local.system_status.websocket_connections_set.add(websocket)
    app_state_local.system_status.websocket_connections = len(app_state_local.system_status.websocket_connections_set)
    logger_server.info(f"Active WebSocket connections: {app_state_local.system_status.websocket_connections}")
    try:
        while True:
            data = await websocket.receive_text()
            logger_server.debug(f"Received message from WebSocket client {user_id}: {data}")
            # Process incoming messages if needed, or just keep connection alive
            await websocket.send_text(f"Message received: {data}")
    except Exception as e: # Handles disconnects
        logger_server.info(f"WebSocket connection for user {user_id} closed/error: {e}")
    finally:
        app_state_local.system_status.websocket_connections_set.discard(websocket)
        app_state_local.system_status.websocket_connections = len(app_state_local.system_status.websocket_connections_set)
        logger_server.info(f"WebSocket connection for {user_id} removed. Active connections: {app_state_local.system_status.websocket_connections}")


@app.websocket("/api/ws/autonomous-data")
async def websocket_autonomous_data_endpoint(websocket: Any):
    """WebSocket endpoint for autonomous trading data that the frontend expects"""
    await websocket.accept()
    logger_server.info(f"Autonomous WebSocket connection accepted from {websocket.client.host}")
    
    # Get app_state directly without dependency injection for WebSocket
    global app_state
    app_state.system_status.websocket_connections_set.add(websocket)
    app_state.system_status.websocket_connections = len(app_state.system_status.websocket_connections_set)
    
    try:
        # Send initial system status
        initial_data = {
            "type": "initial_data",
            "system_health": app_state.system_status.system_health,
            "trading_active": app_state.trading_control.trading_active,
            "autonomous_trading": app_state.trading_control.autonomous_trading_active,
            "paper_trading": app_state.trading_control.paper_trading,
            "market_open": app_state.system_status.market_open,
            "truedata_connected": app_state.market_data.truedata_connected,
            "zerodha_connected": app_state.market_data.zerodha_data_connected
        }
        await websocket.send_text(json.dumps(initial_data))
        
        while True:
            data = await websocket.receive_text()
            logger_server.debug(f"Received message from autonomous WebSocket: {data}")
            
            # Handle ping/pong for keep-alive
            if data == '{"type":"ping"}':
                await websocket.send_text('{"type":"pong"}')
            else:
                # Echo other messages for now
                await websocket.send_text(f'{{"type":"echo","message":"Received: {data}"}}')
                
    except Exception as e:
        logger_server.info(f"Autonomous WebSocket connection closed/error: {e}")
    finally:
        app_state.system_status.websocket_connections_set.discard(websocket)
        app_state.system_status.websocket_connections = len(app_state.system_status.websocket_connections_set)
        logger_server.info(f"Autonomous WebSocket connection removed. Active connections: {app_state.system_status.websocket_connections}")


@app.on_event("startup")
async def startup_event_main():
    global app_state # app_state is global, settings is now app_state.config
    
    # Set the configuration in app_state
    app_state.config = settings
    
    logger_server.info(f"🚀 Starting Platform (Log Level: {app_state.config.LOG_LEVEL})...") # Use app_state.config
    app_state.system_status.app_start_time = datetime.utcnow()
    app_state.trading_control.paper_trading = app_state.config.PAPER_TRADING
    app_state.trading_control.autonomous_trading_active = app_state.config.AUTONOMOUS_TRADING_ENABLED
    app_state.trading_control.trading_active = True

    try:
        from src.database import setup_database_on_startup
        await setup_database_on_startup(app_state.config, app_state)
        logger_server.info(f"DB Setup: DB={app_state.system_status.database_connected}, Redis={app_state.system_status.redis_connected}")
    except Exception as e_db:
        logger_server.error(f"❌ DB/Redis init error: {e_db}", exc_info=True)
        # ... (error state setting as before)
        app_state.system_status.database_connected = False; app_state.system_status.redis_connected = False
        app_state.system_status.system_health = "ERROR_DB_INIT"


    logger_server.info("🔗 Initializing Market Data Handling...")
    try:
        from src.market_data_handling import initialize_market_data_handling
        await initialize_market_data_handling(app=app, settings=app_state.config, market_data_state=app_state.market_data, clients_state=app_state.clients)
        logger_server.info(f"Market Data Init: TrueData={app_state.market_data.truedata_connected}, Zerodha={app_state.market_data.zerodha_data_connected}")
    except Exception as e_mdh:
        logger_server.error(f"❌ Market Data Handling init error: {e_mdh}", exc_info=True)
        # ... (error state setting as before)
        app_state.market_data.truedata_connected = False; app_state.market_data.zerodha_data_connected = False
        if app_state.system_status.system_health != "ERROR_DB_INIT": app_state.system_status.system_health = "ERROR_MD_INIT"


    if CORE_COMPONENTS_AVAILABLE:
        try:
            from src.recommendations import initialize_elite_trading_system
            await initialize_elite_trading_system(app_state.config, app_state)
            logger_server.info(f"Elite System Initialized. Engine: {bool(app_state.clients.elite_engine)}")
        except Exception as e_elite: logger_server.error(f"❌ Elite System init error: {e_elite}", exc_info=True)
        try:
            from src.trading_strategies import initialize_trading_strategies
            await initialize_trading_strategies(app_state, app_state.config)
            logger_server.info(f"Trading Strategies Initialized. Count: {len(app_state.strategies.strategy_instances)}")
        except Exception as e_strat: logger_server.error(f"❌ Trading Strategies init error: {e_strat}", exc_info=True)
    else:
        logger_server.warning("Core trading components not available. Skipping init of advanced systems.")
        app_state.trading_control.autonomous_trading_active = False

    try:
        from src.scheduler_jobs import initialize_scheduler
        scheduler_instance = initialize_scheduler(app_state, app_state.config)
        app_state.clients.scheduler = scheduler_instance
    except Exception as e_sched: logger_server.error(f"❌ Scheduler setup error: {e_sched}", exc_info=True)
        
    if app_state.system_status.system_health not in ["ERROR_DB_INIT", "ERROR_MD_INIT"]:
        app_state.system_status.system_health = "HEALTHY" if app_state.system_status.database_connected else "DEGRADED_DB"
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    app_state.system_status.initialized_successfully = True
    logger_server.info(f"🎯 Platform OPERATIONAL. Health: {app_state.system_status.system_health}")


async def restore_auth_tokens_from_database_startup_task(current_app_state: AppState):
    if not current_app_state.clients.db_pool:
        logger_server.warning("DB not available for token restore task.") # Corrected log message
        return False
    logger_server.info("Attempting Zerodha token restore from DB...")
    try:
        token_data = await fetch_one_db("SELECT access_token, user_id FROM auth_tokens WHERE provider = 'zerodha' AND is_active = 1 ORDER BY updated_at DESC LIMIT 1", db_conn_or_path=current_app_state.clients.db_pool)
        if token_data and token_data["access_token"]:
            token, user_id = token_data["access_token"], token_data.get("user_id", "UnknownUser")
            logger_server.info(f"Found Zerodha token for user '{user_id}': {token[:10]}...")
            client = current_app_state.clients.zerodha_client_instance
            if client and hasattr(client, 'set_access_token'):
                if client.set_access_token(token, user_id_for_log=user_id):
                    current_app_state.market_data.zerodha_data_connected = True
                    logger_server.info(f"Zerodha token for {user_id} restored to client. Connection active.")
                    return True
                else: logger_server.warning(f"Failed to set token for {user_id} in client.")
            else: logger_server.warning("Zerodha client not available or no set_access_token method.")
        else: logger_server.info("No active Zerodha token in DB.")
    except Exception as e: logger_server.error(f"Error restoring token: {e}", exc_info=True)
    current_app_state.market_data.zerodha_data_connected = False
    return False

@app.on_event("startup")
async def startup_token_restoration():
    global app_state
    logger_server.info("🔄 Token restoration task starting...")
    if await restore_auth_tokens_from_database_startup_task(app_state):
        logger_server.info("✅ Token restoration successful.")
    else: logger_server.info("ℹ️ Token restoration: No tokens restored or failed.")

@app.on_event("shutdown")
async def shutdown_event_main(): # ... (shutdown logic as before, uses app_state) ...
    global app_state
    logger_server.info("🛑 Shutting down Elite Platform...")
    if app_state.clients.scheduler and app_state.clients.scheduler.running:
        app_state.clients.scheduler.shutdown(wait=False); logger_server.info("Scheduler shutdown.")

    app_state.trading_control.trading_active = False
    app_state.trading_control.autonomous_trading_active = False

    # Shutdown TrueData Singleton Client
    try:
        from backend.truedata_client import shutdown_truedata_client as shutdown_truedata_singleton_final
        await shutdown_truedata_singleton_final()
        logger_server.info("TrueData Singleton Client shutdown requested.")
    except ImportError:
        logger_server.error("Could not import shutdown_truedata_singleton_final for shutdown.")
    except Exception as e:
        logger_server.error(f"TrueData Singleton Client shutdown error: {e}", exc_info=True)

    # Shutdown Zerodha Client
    if hasattr(app_state.clients.zerodha_client_instance, 'disconnect'):
        try: await app_state.clients.zerodha_client_instance.disconnect()
        except Exception as e: logger_server.error(f"Zerodha client disconnect error: {e}", exc_info=True)
    if app_state.clients.redis_client: await app_state.clients.redis_client.close(); logger_server.info("Redis client closed.")
    if app_state.clients.db_pool and hasattr(app_state.clients.db_pool, 'close'):
        await app_state.clients.db_pool.close(); logger_server.info("DB pool closed.")
    logger_server.info("Shutdown sequence complete.")


main_api_router = APIRouter()
@main_api_router.get("/")
async def root(): return {"message": "Elite Autonomous Algo Trading Platform - Ready!", "version": settings.APP_VERSION if hasattr(settings, "APP_VERSION") else "2.1.0"} # Example using settings

@main_api_router.get("/system/status", summary="Get detailed system status")
async def get_system_status_route(app_state: AppState = Depends(get_app_state)):
    """Get comprehensive system status including all components"""
    sys_status = app_state.system_status
    trading_ctrl = app_state.trading_control
    market_data = app_state.market_data
    
    uptime_seconds = 0
    if sys_status.app_start_time:
        uptime_seconds = (datetime.utcnow() - sys_status.app_start_time).total_seconds()
    
    status_data = {
        "system_health": sys_status.system_health,
        "autonomous_trading": trading_ctrl.autonomous_trading_active,
        "paper_trading": trading_ctrl.paper_trading,
        "trading_active": trading_ctrl.trading_active,
        "market_open": sys_status.market_open,
        "database_connected": sys_status.database_connected,
        "redis_connected": sys_status.redis_connected,
        "truedata_connected": market_data.truedata_connected,
        "zerodha_connected": market_data.zerodha_data_connected,
        "websocket_connections": sys_status.websocket_connections,
        "uptime_seconds": uptime_seconds,
        "last_update": sys_status.last_system_update_utc.isoformat() if sys_status.last_system_update_utc else None,
        "data_source": market_data.active_data_source,
        "emergency_mode": trading_ctrl.emergency_mode,
        "live_symbols_count": len(market_data.live_market_data)
    }
    return {"success": True, "data": status_data}

app.include_router(main_api_router)

app.include_router(admin_router, prefix="/api/admin", dependencies=[Depends(get_app_state)])
app.include_router(strategy_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(autonomous_strategy_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(trading_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(market_data_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(user_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(system_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(truedata_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(zerodha_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(zerodha_direct_router, prefix="/api", dependencies=[Depends(get_app_state)])
app.include_router(webhook_router, prefix="/api", dependencies=[Depends(get_app_state)])

if __name__ == "__main__":
    import uvicorn
    # Use settings for host and port  
    uvicorn.run("server:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True, workers=1)
