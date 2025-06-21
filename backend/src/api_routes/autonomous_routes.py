from fastapi import APIRouter, Depends
from datetime import datetime
from src.app_state import AppState, app_state
from src.core.utils import create_api_success_response

# Create dependency function inline
def get_app_state():
    return app_state

def format_datetime_for_api(dt):
    """Format datetime for API response"""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)

autonomous_router = APIRouter(prefix="/autonomous", tags=["autonomous"])

@autonomous_router.get("/system-metrics", summary="Get autonomous trading system metrics")
async def get_autonomous_system_metrics(app_state: AppState = Depends(get_app_state)):
    """Get comprehensive autonomous trading system metrics"""
    sys_status = app_state.system_status
    trading_ctrl = app_state.trading_control
    market_data = app_state.market_data
    
    # Calculate uptime
    uptime_seconds = 0
    if sys_status.app_start_time:
        uptime_seconds = (datetime.utcnow() - sys_status.app_start_time).total_seconds()
    
    # Calculate system performance metrics
    metrics_data = {
        "system_health": {
            "overall_status": sys_status.system_health,
            "database_connected": sys_status.database_connected,
            "redis_connected": sys_status.redis_connected,
            "uptime_seconds": uptime_seconds,
            "uptime_hours": round(uptime_seconds / 3600, 2),
            "websocket_connections": sys_status.websocket_connections,
            "last_update": format_datetime_for_api(sys_status.last_system_update_utc)
        },
        "trading_metrics": {
            "autonomous_trading_active": trading_ctrl.autonomous_trading_active,
            "paper_trading_mode": trading_ctrl.paper_trading,
            "trading_active": trading_ctrl.trading_active,
            "emergency_mode": trading_ctrl.emergency_mode,
            "market_open": sys_status.market_open
        },
        "market_data_metrics": {
            "truedata_connected": market_data.truedata_connected,
            "zerodha_connected": market_data.zerodha_data_connected,
            "active_data_source": market_data.active_data_source,
            "live_symbols_count": len(market_data.live_market_data),
            "last_data_update": format_datetime_for_api(market_data.last_data_update_time)
        },
        "strategy_metrics": {
            "total_strategies": 7,  # Fixed number of elite strategies
            "active_strategies": 0,  # Would be calculated from database
            "elite_strategies_count": 7,  # All 7 strategies are elite
            "last_strategy_update": format_datetime_for_api(sys_status.last_system_update_utc)
        },
        "performance_summary": {
            "total_signals_today": 0,  # Would be calculated from database
            "successful_trades_today": 0,  # Would be calculated from database  
            "current_portfolio_value": 0.0,  # Would be calculated from positions
            "daily_pnl": 0.0,  # Would be calculated from trades
            "success_rate_percentage": 0.0  # Would be calculated from historical data
        }
    }
    
    return create_api_success_response(data=metrics_data)