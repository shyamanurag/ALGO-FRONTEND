from fastapi import APIRouter, HTTPException, Request, Depends
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, time
import json
import uuid
import os
import pytz
from pydantic import BaseModel

from src.app_state import AppState, SystemOverallState, TradingControlState, MarketDataState, StrategyState
from src.config import AppSettings
from src.core.utils import create_api_success_response, format_datetime_for_api # Import utilities
from src.database import execute_db_query, fetch_one_db

try:
    from backend.server import get_app_state, get_settings
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance
    from src.config import settings as _global_settings_instance
    def get_app_state(): return _global_app_state_instance
    def get_settings(): return _global_settings_instance
    from backend.server import get_app_state, get_settings
except ImportError:
    _fallback_logger_sys = logging.getLogger(__name__)
    _fallback_logger_sys.error("CRITICAL: Could not import get_app_state, get_settings from backend.server for system_routes.py.")
    from src.app_state import app_state as _global_app_state_instance_sys
    from src.config import settings as _global_settings_instance_sys
    async def get_app_state(): return _global_app_state_instance_sys
    async def get_settings(): return _global_settings_instance_sys

logger = logging.getLogger(__name__)

class SystemStatusResponse(BaseModel):
    status: str
    trading_active: bool
    paper_trading: bool
    daily_pnl: float
    active_positions: int = 0
    market_data_symbols: int = 0
    components_health: Dict[str, str] = {}
    uptime: Optional[str] = None

system_router = APIRouter(tags=["System & Autonomous Control"])

def check_and_update_market_open_status(app_state: AppState, settings: AppSettings) -> bool:
    _market_open_time = settings.MARKET_OPEN_TIME
    _market_close_time = settings.MARKET_CLOSE_TIME
    ist_tz = pytz.timezone('Asia/Kolkata')
    current_ist_time = datetime.now(ist_tz)
    is_open = False
    if current_ist_time.weekday() < 5:
        is_open = _market_open_time <= current_ist_time.time() <= _market_close_time
    app_state.system_status.market_open = is_open
    return is_open

async def local_restore_auth_tokens(app_state: AppState):
    logger.info("Attempting token restoration via system_routes placeholder...")
    if not app_state.clients.db_pool:
        logger.warning("DB pool not available for token restoration.")
        return False
    return False

@system_router.get("/status", response_model=SystemStatusResponse, summary="Get comprehensive system status")
async def get_system_status_root(app_state: AppState = Depends(get_app_state)):
    # This route returns a Pydantic model directly, which is fine. No change needed here for create_api_success_response.
    sys_status = app_state.system_status
    trading_ctrl = app_state.trading_control
    market_data = app_state.market_data
    clients = app_state.clients
    strats = app_state.strategies

    components_health = {
        'database': 'HEALTHY' if sys_status.database_connected else 'NOT_CONNECTED',
        'redis': 'HEALTHY' if sys_status.redis_connected else 'NOT_CONFIGURED',
        'truedata': 'CONNECTED' if market_data.truedata_connected else 'DISCONNECTED',
        'zerodha': 'CONNECTED' if market_data.zerodha_data_connected else 'DISCONNECTED',
        'elite_engine': 'AVAILABLE' if clients.elite_engine else 'NOT_INITIALIZED',
        'order_manager': 'AVAILABLE' if clients.order_manager else 'NOT_INITIALIZED',
        'strategies_count': len(strats.strategy_instances),
        'active_strategies_count': len([s for s in strats.strategy_instances.values() if s.is_active]),
    }
    uptime_str = "N/A"
    if sys_status.app_start_time:
        uptime_delta = datetime.utcnow() - sys_status.app_start_time
        uptime_str = str(uptime_delta).split('.')[0]

    return SystemStatusResponse(
        status=sys_status.system_health, trading_active=trading_ctrl.trading_active,
        paper_trading=trading_ctrl.paper_trading, daily_pnl=sys_status.daily_pnl,
        active_positions=0, market_data_symbols=len(market_data.live_market_data),
        components_health=components_health, uptime=uptime_str
    )

@system_router.get("/status", summary="Get detailed system status")
async def get_system_status_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    """Get comprehensive system status including all components"""
    sys_status = app_state.system_status
    trading_ctrl = app_state.trading_control
    market_data = app_state.market_data
    market_open = check_and_update_market_open_status(app_state, settings)
    
    uptime_seconds = 0
    if sys_status.app_start_time:
        uptime_seconds = (datetime.utcnow() - sys_status.app_start_time).total_seconds()
    
    status_data = {
        "system_health": sys_status.system_health,
        "autonomous_trading": trading_ctrl.autonomous_trading_active,
        "paper_trading": trading_ctrl.paper_trading,
        "trading_active": trading_ctrl.trading_active,
        "market_open": market_open,
        "database_connected": sys_status.database_connected,
        "redis_connected": sys_status.redis_connected,
        "truedata_connected": market_data.truedata_connected,
        "zerodha_connected": market_data.zerodha_data_connected,
        "websocket_connections": sys_status.websocket_connections,
        "uptime_seconds": uptime_seconds,
        "last_update": format_datetime_for_api(sys_status.last_system_update_utc),
        "data_source": market_data.active_data_source,
        "emergency_mode": trading_ctrl.emergency_mode,
        "live_symbols_count": len(market_data.live_market_data)
    }
    return create_api_success_response(data=status_data)

@system_router.get("/health", summary="Simplified health check")
async def health_check_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    sys_status = app_state.system_status; trading_ctrl = app_state.trading_control; market_data = app_state.market_data
    market_open = check_and_update_market_open_status(app_state, settings)
    health_data = {
        "overall_status": "HEALTHY" if sys_status.system_health == "HEALTHY" and sys_status.database_connected else "DEGRADED_OR_ERROR",
        "timestamp_utc": format_datetime_for_api(datetime.utcnow()), # Formatted
        "database_connected": sys_status.database_connected, "redis_connected": sys_status.redis_connected,
        "system_health_flag": sys_status.system_health,
        "autonomous_trading_active": trading_ctrl.autonomous_trading_active,
        "paper_trading_mode": trading_ctrl.paper_trading, "market_open_status": market_open,
        "truedata_connected_status": market_data.truedata_connected,
        "zerodha_connected_status": market_data.zerodha_data_connected,
        "active_data_source": market_data.active_data_source,
        "live_symbols_count": len(market_data.live_market_data),
    }
    return create_api_success_response(data=health_data)

@system_router.delete("/system/purge-demo-data", summary="Purge demo/test data from the database")
async def purge_all_demo_data_route(app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database not available for purification.")
    try:
        queries_to_run = [ # ... (queries as before) ...
            ("DELETE FROM orders WHERE trade_reason LIKE '%DEMO%' OR trade_reason LIKE '%TEST%' OR user_id LIKE '%_test_user%'",),
            ("DELETE FROM positions WHERE entry_reason LIKE '%DEMO%' OR strategy_name LIKE '%_test_strat%' OR user_id LIKE '%_test_user%'",),
            ("DELETE FROM trading_signals WHERE metadata LIKE '%\"is_demo\": true%' OR strategy_name LIKE '%_test_strat%'",),
            ("DELETE FROM users WHERE user_id LIKE '%_test_user%' OR email LIKE '%@example.com'",)
        ]
        for query_tuple in queries_to_run:
            await execute_db_query(query_tuple[0], db_conn_or_path=app_state.clients.db_pool)
        logger.info("🔥 Demo data purge queries executed.")
        return create_api_success_response(message="Demo data purge executed. Verify database.", data={"purged_tables_conceptual": ["orders", "positions", "signals", "users"]})
    except Exception as e:
        logger.error(f"Error during demo data purge: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Purification failed: {str(e)}")

@system_router.post("/system/fix-status", summary="Force system state to OPERATIONAL and enable autonomous trading")
async def fix_system_status_route(app_state: AppState = Depends(get_app_state)):
    logger.info("Admin request to force system status to OPERATIONAL and enable autonomous trading.")
    app_state.system_status.system_health = 'OPERATIONAL_FORCED_ADMIN'
    app_state.trading_control.trading_active = True
    app_state.trading_control.autonomous_trading_active = True
    app_state.market_data.truedata_connected = True
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(
        message="System status forced to operational, autonomous trading enabled.",
        data={"system_health": app_state.system_status.system_health,
              "autonomous_trading_active": app_state.trading_control.autonomous_trading_active,
              "truedata_connected_simulated": app_state.market_data.truedata_connected}
    )

@system_router.post("/autonomous/start", summary="Start autonomous trading system")
async def start_autonomous_trading_route(app_state: AppState = Depends(get_app_state)):
    logger.info("Request to START autonomous trading system.")
    app_state.trading_control.autonomous_trading_active = True
    app_state.trading_control.trading_active = True
    app_state.system_status.system_health = 'AUTONOMOUS_ACTIVE'
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(message="Autonomous trading system started.", data={"autonomous_status": True})

@system_router.post("/autonomous/emergency-stop", summary="Emergency stop all autonomous trading")
async def emergency_stop_autonomous_route(app_state: AppState = Depends(get_app_state)):
    logger.critical("🚨 AUTONOMOUS EMERGENCY STOP ACTIVATED via API!")
    app_state.trading_control.autonomous_trading_active = False
    app_state.trading_control.trading_active = False
    app_state.trading_control.emergency_mode = True
    app_state.system_status.system_health = 'EMERGENCY_STOPPED'
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(message="Emergency stop activated. All autonomous operations halted.", data={"emergency_mode": True})

@system_router.post("/emergency-stop", summary="General Emergency stop")
async def emergency_stop_general_route(app_state: AppState = Depends(get_app_state)):
    return await emergency_stop_autonomous_route(app_state=app_state)

@system_router.post("/resume-trading", summary="Resume trading activities after an emergency stop")
async def resume_trading_route(app_state: AppState = Depends(get_app_state)):
    logger.info("Request to RESUME trading activities.")
    app_state.trading_control.trading_active = True
    app_state.trading_control.emergency_mode = False
    app_state.system_status.system_health = 'OPERATIONAL_RESUMED'
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(message="General trading activities resumed. Autonomous mode status unchanged.")

@system_router.get("/autonomous/status", summary="Get autonomous trading system status")
async def get_autonomous_status_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    sys_status = app_state.system_status; trading_ctrl = app_state.trading_control; strats = app_state.strategies
    active_strats = len([s_info for s_info in strats.strategy_instances.values() if s_info.is_active])
    uptime_str = "N/A"
    if sys_status.app_start_time: uptime_str = str(datetime.utcnow() - sys_status.app_start_time).split('.')[0]

    status_data = {
        "overall_system_health": sys_status.system_health,
        "autonomous_trading_active": trading_ctrl.autonomous_trading_active,
        "paper_trading_mode": trading_ctrl.paper_trading,
        "active_strategies_count": active_strats,
        "total_configured_strategies": len(strats.strategy_instances),
        "system_uptime": uptime_str,
        "last_system_update_utc": format_datetime_for_api(sys_status.last_system_update_utc),
        "db_connected": sys_status.database_connected,
        "market_data_connected": app_state.market_data.truedata_connected or app_state.market_data.zerodha_data_connected,
    }
    return create_api_success_response(data=status_data)

# Ensure other routes like /contamination-report, /reset-session, etc., also use create_api_success_response
# Example for /system/contamination-report:
@system_router.get("/system/contamination-report", summary="Generate report of demo/fake data contamination")
async def generate_contamination_report_route(app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool:
        raise HTTPException(status_code=503, detail="Database not available for contamination report")
    try:
        contamination = {}
        tables_to_check = ["orders", "positions", "trading_signals", "users"] # Example tables
        for table in tables_to_check:
            # Simplified query for example; actual keywords might be more complex
            count_res = await fetch_one_db(f"SELECT COUNT(*) as count FROM {table} WHERE user_id LIKE '%_test%' OR strategy_name LIKE '%_test_strat%'", db_conn_or_path=app_state.clients.db_pool)
            contamination[table] = count_res["count"] if count_res else 0

        total_contamination = sum(v for v in contamination.values() if isinstance(v, int))
        report_data = {
            "contamination_report": contamination,
            "total_contaminated_records": total_contamination,
            "system_status_based_on_report": "🦠 HEAVILY CONTAMINATED" if total_contamination > 10 else ("⚠️ SOME CONTAMINATION" if total_contamination > 0 else "✨ LIKELY PURE"),
            "recommendation": "🔥 IMMEDIATE PURIFICATION REQUIRED" if total_contamination > 0 else "Sacred system appears clean based on keywords.",
            "timestamp_utc": format_datetime_for_api(datetime.utcnow())
        }
        return create_api_success_response(data=report_data)
    except Exception as e:
        logger.error(f"Error generating contamination report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Contamination report generation failed: {str(e)}")

@system_router.get("/system/stored-tokens", summary="Get information about stored authentication tokens")
async def get_stored_tokens_route(app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool:
        raise HTTPException(status_code=503, detail="Database not available for stored tokens")
    try:
        tokens_res = await execute_db_query("SELECT provider, user_id, updated_at, is_active FROM auth_tokens WHERE is_active = 1 ORDER BY updated_at DESC", db_conn_or_path=app_state.clients.db_pool)
        tokens = []
        if tokens_res:
            for row_dict in (dict(row) for row in tokens_res):
                tokens.append({
                    "provider": row_dict["provider"], "user_id": row_dict.get("user_id"),
                    "updated_at": format_datetime_for_api(row_dict.get("updated_at")),
                    "is_active": bool(row_dict["is_active"])
                })
        return create_api_success_response(data={"stored_tokens": tokens, "count": len(tokens)}, message="These tokens are available for restoration.")
    except Exception as e:
        logger.error(f"Error getting stored tokens: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting stored tokens: {str(e)}")

async def local_restore_auth_tokens(current_app_state: AppState) -> bool:
    """Local function to restore authentication tokens from database"""
    if not current_app_state.clients.db_pool:
        logger.warning("DB not available for token restore.")
        return False
    
    try:
        token_data = await fetch_one_db(
            "SELECT access_token, provider FROM auth_tokens WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1", 
            db_conn_or_path=current_app_state.clients.db_pool
        )
        if token_data and token_data["access_token"]:
            logger.info(f"Found token for provider '{token_data.get('provider', 'unknown')}'")
            return True
        else:
            logger.info("No active tokens found in DB.")
            return False
    except Exception as e:
        logger.error(f"Error restoring tokens: {e}", exc_info=True)
        return False

@system_router.post("/system/restore-tokens", summary="Manually restore tokens from database (placeholder)")
async def manual_restore_tokens_route(app_state: AppState = Depends(get_app_state)):
    try:
        success = await local_restore_auth_tokens(app_state) # Uses placeholder local_restore_auth_tokens
        return create_api_success_response(
            data={"restoration_attempted": True, "outcome_simulated": success},
            message="Token restoration process called (placeholder)." if success else "Token restoration process called (placeholder), no actual change."
        )
    except Exception as e:
        logger.error(f"Error manually restoring tokens (placeholder call): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to call token restoration: {str(e)}")

