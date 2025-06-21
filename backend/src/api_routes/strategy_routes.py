from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path # Added Path
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid

from src.app_state import AppState, StrategyInstanceInfo
from src.config import AppSettings
from src.core.utils import create_api_success_response, format_datetime_for_api # Import the utilities
from src.database import execute_db_query, fetch_one_db

try:
    from backend.server import get_app_state, get_settings
except ImportError:
    # Use fallback functions (this is expected due to circular imports)
    from src.app_state import app_state as _global_app_state_instance_strat
    from src.config import settings as _global_settings_instance_strat
    def get_app_state(): return _global_app_state_instance_strat
    def get_settings(): return _global_settings_instance_strat

logger = logging.getLogger(__name__)

strategy_router = APIRouter(prefix="/strategies", tags=["Strategies"])
autonomous_strategy_router = APIRouter(prefix="/autonomous", tags=["Autonomous Strategies"])

def get_strategy_description(strategy_name: str) -> str:
    descriptions = {
        'momentum_surfer': 'Advanced momentum detection with VWAP confluence',
        'news_impact_scalper': 'High-frequency news-driven scalping',
        'volatility_explosion': 'Volatility breakout capture',
    }
    return descriptions.get(strategy_name.lower().replace(" ", "_"), 'Advanced trading strategy')

@strategy_router.get("/", summary="Get all trading strategies")
async def get_strategies_route(app_state: AppState = Depends(get_app_state)): # No path/query params to change
    try:
        strategies_output = []
        for name, strat_info in app_state.strategies.strategy_instances.items(): # No change
            type_name = "UnknownStrategy" # No change
            if strat_info.instance: type_name = strat_info.instance.__class__.__name__ # No change
            elif strat_info.config and strat_info.config.get('class_name_for_display'):  # No change
                type_name = strat_info.config.get('class_name_for_display') # No change

            strategy_data = { # No change
                'id': name,  # No change
                'name': strat_info.config.get('display_name', name),  # No change
                'enabled': strat_info.is_active, # No change
                'allocation': strat_info.config.get('allocation', 0.1),  # No change
                'type': type_name, # No change
                'health': strat_info.status_message,  # No change
                'description': get_strategy_description(name) # No change
            }
            strategy_data['metrics'] = { # No change
                'trades_today': strat_info.daily_trades, # No change
                'pnl_today': strat_info.daily_pnl, # No change
            }
            strategies_output.append(strategy_data) # No change

        return create_api_success_response(data={ # No change
            "strategies": strategies_output, # No change
            "total_strategies": len(strategies_output), # No change
            "active_strategies": len([s for s in strategies_output if s['enabled']]), # No change
            "timestamp": datetime.utcnow().isoformat() # Can also use utils.format_datetime_for_api # No change
        })
    except Exception as e: # No change
        logger.error(f"Error getting strategies: {e}", exc_info=True) # No change
        # This will be handled by the registered http_exception_handler # No change
        raise HTTPException(status_code=500, detail=f"Error getting strategies: {str(e)}") # No change

@strategy_router.get("/metrics", summary="Get real-time strategy performance metrics")
async def get_strategy_metrics_route(app_state: AppState = Depends(get_app_state)): # No path/query params to change
    if not app_state.clients.db_pool:
        logger.warning("get_strategy_metrics_route: Database not available. Falling back to in-memory metrics.")
        metrics_from_memory = []
        for name, strat_info in app_state.strategies.strategy_instances.items(): # No change
            metrics_from_memory.append({ # No change
                "name": name, "active": strat_info.is_active, # No change
                "signals_today": strat_info.daily_trades,  # No change
                "total_signals": "N/A_DB_DOWN", "win_rate": "N/A_DB_DOWN",  # No change
                "avg_quality": "N/A_DB_DOWN", "last_signal_at": "N/A_DB_DOWN",  # No change
                "pnl_today": strat_info.daily_pnl, "status_source": "in-memory-app-state" # No change
            })
        return create_api_success_response( # No change
            data={"strategies": metrics_from_memory},  # No change
            message="Metrics from in-memory state (DB unavailable for detailed query)." # No change
        )

    try: # No change
        strategies_metrics_db = [] # No change
        for strat_id, strat_info in app_state.strategies.strategy_instances.items(): # No change
            db_metrics = await fetch_one_db( # No change
                """SELECT COUNT(CASE WHEN DATE(generated_at) = DATE('now', 'localtime') THEN 1 ELSE NULL END) as signals_today,
                          COUNT(*) as total_signals,
                          AVG(quality_score) as avg_quality,
                          MAX(generated_at) as last_signal_at
                   FROM trading_signals WHERE strategy_name = ?""",
                strat_id, db_conn_or_path=app_state.clients.db_pool # No change
            )

            metric_entry = { # No change
                "name": strat_id, "active": strat_info.is_active, # No change
                "pnl_today_mem": strat_info.daily_pnl,  # No change
                "status_source": "db_and_memory" # No change
            }
            if db_metrics: # No change
                metric_entry.update({ # No change
                    "signals_today_db": db_metrics["signals_today"], # No change
                    "total_signals_db": db_metrics["total_signals"], # No change
                    "win_rate_db": "N/A_CALC_NEEDED",  # No change
                    "avg_quality_db": round(db_metrics["avg_quality"] or 0, 2), # No change
                    "last_signal_at_db": db_metrics["last_signal_at"].isoformat() if db_metrics["last_signal_at"] else None, # No change
                })
            else: # No change
                 metric_entry.update({"error": "DB_QUERY_FAILED_FOR_STRAT_METRICS"}) # No change
            strategies_metrics_db.append(metric_entry) # No change

        return create_api_success_response(data={"strategies": strategies_metrics_db}) # No change
    except Exception as e: # No change
        logger.error(f"Error getting strategy metrics from DB: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error getting strategy metrics from DB: {str(e)}") # No change

@strategy_router.put("/{strategy_id}/toggle", summary="Toggle strategy active status")
async def toggle_strategy_route(strategy_id: str = Path(..., min_length=1, description="The ID or display name of the strategy to toggle"), app_state: AppState = Depends(get_app_state)):
    logger.info(f"Request to toggle strategy: {strategy_id}")

    strat_info = app_state.strategies.strategy_instances.get(strategy_id) # No change
    internal_strategy_id = strategy_id # Keep track of the key used to find the strategy

    if not strat_info:
        found_by_display_name = False
        for key, si in app_state.strategies.strategy_instances.items():
            if si.config.get('display_name', key) == strategy_id:
                internal_strategy_id = key
                strat_info = si
                found_by_display_name = True
                break
        if not found_by_display_name:
             raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found.")

    strat_info.is_active = not strat_info.is_active
    strat_info.status_message = "ACTIVE" if strat_info.is_active else "INACTIVE_USER_TOGGLED"

    app_state.system_status.strategies_active = len([
        si for si in app_state.strategies.strategy_instances.values() if si.is_active
    ])
    app_state.system_status.last_system_update_utc = datetime.utcnow()

    logger.info(f"Strategy '{internal_strategy_id}' (display: '{strategy_id}') toggled to {'ACTIVE' if strat_info.is_active else 'INACTIVE'}. Total active: {app_state.system_status.strategies_active}")

    return create_api_success_response(
        data={
            "strategy_id": internal_strategy_id,
            "display_name_requested": strategy_id,
            "new_status": "ACTIVE" if strat_info.is_active else "INACTIVE",
            "is_active_flag": strat_info.is_active
        },
        message=f"Strategy '{internal_strategy_id}' toggled to {'activated' if strat_info.is_active else 'deactivated'}.",
    )

@autonomous_strategy_router.put("/strategy/{strategy_id}/toggle", summary="Toggle autonomous strategy status")
async def toggle_autonomous_strategy_alias_route(strategy_id: str, app_state: AppState = Depends(get_app_state)):
    # This route directly calls the other toggle route, so response format will be handled there.
    return await toggle_strategy_route(strategy_id, app_state)

@strategy_router.post("/{strategy_name}/reset", summary="Reset strategy dynamic metrics")
async def reset_strategy_route(strategy_name: str, app_state: AppState = Depends(get_app_state)):
    logger.info(f"Request to reset metrics for strategy: {strategy_name}")

    strat_info = app_state.strategies.strategy_instances.get(strategy_name)
    if not strat_info: # No change
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found.") # No change

    try: # No change
        strat_info.daily_pnl = 0.0 # No change
        strat_info.daily_trades = 0 # No change
        strat_info.status_message = "METRICS_RESET_IN_MEMORY" # No change

        if app_state.clients.db_pool: # No change
            # This is a conceptual action. Actual DB reset might be more complex or not done here. # No change
            # For example, marking signals as "archived_due_to_reset" instead of deleting. # No change
            # await execute_db_query("DELETE FROM trading_signals WHERE strategy_name = ?", strategy_name, db_conn_or_path=app_state.clients.db_pool) # No change
            logger.info(f"DB records for strategy '{strategy_name}' would conceptually be handled here (e.g., archived/deleted).") # No change

        app_state.system_status.last_system_update_utc = datetime.utcnow() # No change
        logger.info(f"In-memory metrics for strategy '{strategy_name}' have been reset.") # No change
        return create_api_success_response( # No change
            message=f"In-memory metrics for strategy '{strategy_name}' reset successfully.", # No change
            data={"strategy_name": strategy_name, "reset_status": "in_memory_done", "db_action_note": "Conceptual DB reset logged."} # No change
        )
    except Exception as e: # No change
        logger.error(f"Error resetting strategy {strategy_name}: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error resetting strategy {strategy_name}: {str(e)}") # No change

@strategy_router.get("/system/status", summary="Get detailed system status")
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
        "last_update": format_datetime_for_api(sys_status.last_system_update_utc),
        "data_source": market_data.active_data_source,
        "emergency_mode": trading_ctrl.emergency_mode,
        "live_symbols_count": len(market_data.live_market_data)
    }
    return create_api_success_response(data=status_data)

