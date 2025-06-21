from fastapi import APIRouter, HTTPException, Depends, Request, Path, Query # Added Path, Query
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid
from pydantic import BaseModel, Field

from src.app_state import AppState
from src.config import AppSettings
from src.core.utils import create_api_success_response # Import the utility
from src.database import execute_db_query, fetch_one_db

try:
    from backend.server import get_app_state, get_settings
except ImportError:
    _fallback_logger_trading = logging.getLogger(__name__)
    _fallback_logger_trading.error("CRITICAL: Could not import get_app_state, get_settings from backend.server for trading_routes.py.")
    from src.app_state import app_state as _global_app_state_instance_trading
    from src.config import settings as _global_settings_instance_trading
    async def get_app_state(): return _global_app_state_instance_trading
    async def get_settings(): return _global_settings_instance_trading

logger = logging.getLogger(__name__)

class TradeRequest(BaseModel):
    symbol: str = Field(..., min_length=1, description="Trading symbol, e.g., 'RELIANCE-EQ'")
    action: str = Field(..., min_length=2, max_length=10, description="Trade action: BUY, SELL, SHORT, COVER") # Assuming actions like BUY, SELL
    quantity: int = Field(..., gt=0, description="Order quantity, must be greater than 0")
    order_type: Optional[str] = Field(default="MARKET", min_length=3, description="Order type: MARKET, LIMIT, SL, SL-M")
    price: Optional[float] = Field(default=None, ge=0.0, description="Price for LIMIT or SL orders, must be >= 0 if provided")
    user_id: Optional[str] = Field(default="default_manual_user", min_length=1)

class EliteRecommendationResponse(BaseModel):
    recommendation_id: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    strategy: str = Field(..., min_length=1)
    direction: str = Field(..., min_length=1)
    entry_price: float = Field(..., ge=0)
    stop_loss: float = Field(..., ge=0)
    primary_target: float = Field(..., ge=0)
    confidence_score: float = Field(..., ge=0, le=1)
    timeframe: str = Field(..., min_length=1)
    summary: str

trading_router = APIRouter(tags=["Trading"])

async def store_manual_trade_in_database(order_params: Dict, order_result: Dict, app_state: AppState):
    if not app_state.clients.db_pool:
        logger.warning("store_manual_trade_in_database: Database pool not available. Skipping DB store.")
        return
    try:
        # ... (database insertion logic as before) ...
        # This helper does not return an API response, so no change for create_api_success_response here.
        # Ensure all execute_db_query calls pass db_conn_or_path=app_state.clients.db_pool
        db_path = app_state.clients.db_pool # For brevity

        await execute_db_query(
            """
            INSERT INTO orders (order_id, user_id, symbol, quantity, order_type, side, price, average_price, status, strategy_name, created_at, filled_at, trade_reason, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            order_result.get('order_id', str(uuid.uuid4())), order_params.get('user_id', 'default_manual_user'),
            order_params['symbol'], order_params['quantity'], order_params['order_type'], order_params['side'],
            order_params.get('price'), order_result.get('average_price', order_result.get('execution_price')),
            order_result.get('status', 'UNKNOWN'), order_params['strategy_name'],
            datetime.utcnow(), datetime.utcnow() if order_result.get('status') == "FILLED" else None,
            order_params.get('trade_reason', 'Manual Trade'), json.dumps(order_result, default=str),
            db_conn_or_path=db_path
        )
        if order_result.get('status') == "FILLED":
            position_id = str(uuid.uuid4())
            avg_price = order_result.get('average_price', order_result.get('execution_price', 0))
            qty = order_params['quantity']
            investment = qty * avg_price if avg_price else 0
            await execute_db_query(
                """
                INSERT INTO positions (position_id, user_id, symbol, quantity, average_entry_price, total_investment, current_price, current_value, status, strategy_name, entry_reason, entry_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, symbol, strategy_name) DO UPDATE SET quantity = quantity + excluded.quantity, total_investment = total_investment + excluded.total_investment, average_entry_price = (total_investment + excluded.total_investment) / (quantity + excluded.quantity)
                """,
                position_id, order_params.get('user_id', 'default_manual_user'), order_params['symbol'],
                qty if order_params['side'] == "BUY" else -qty, avg_price, investment, avg_price, investment,
                'OPEN', order_params['strategy_name'], order_params.get('trade_reason', 'Manual Trade'), datetime.utcnow(),
                db_conn_or_path=db_path
            )
        logger.info(f"Manual trade {order_result.get('order_id')} DB interaction complete.")
    except Exception as e:
        logger.error(f"Error storing manual trade {order_result.get('order_id')} in DB: {e}", exc_info=True)

async def execute_manual_trade_action(trade_request: TradeRequest, app_state: AppState, settings: AppSettings):
    logger.info(f"Executing manual trade action for user {trade_request.user_id}: {trade_request.model_dump_json(indent=2)}") # Use model_dump_json

    order_params = { # ... (order_params setup as before) ...
        'user_id': trade_request.user_id, 'symbol': trade_request.symbol,
        'order_type': trade_request.order_type if trade_request.order_type else "MARKET",
        'quantity': trade_request.quantity, 'side': trade_request.action.upper(),
        'strategy_name': 'MANUAL_TRADE', 'signal_id': str(uuid.uuid4()),
        'trade_reason': f'Manual Order Entry via API by {trade_request.user_id}'
    }
    if trade_request.price and trade_request.order_type.upper() == "LIMIT":
        order_params['price'] = trade_request.price

    order_result: Optional[Dict[str, Any]] = None
    is_paper_trade_mode = app_state.trading_control.paper_trading

    if not app_state.clients.order_manager:
        logger.error("OrderManager not available in app_state. Cannot place manual trade.")
        raise HTTPException(status_code=503, detail="OrderManager not available.")

    try:
        order_result = await app_state.clients.order_manager.place_order(order_params, is_paper=is_paper_trade_mode)
    except Exception as e_oe: # Order Execution exception
        logger.error(f"Exception during manual order placement via OrderManager: {e_oe}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Order placement failed due to an internal error: {str(e_oe)}")

    if order_result and order_result.get('success'):
        logger.info(f"✅ MANUAL ORDER PLACED (via OrderManager): {order_result.get('order_id')}")
        await store_manual_trade_in_database(order_params, order_result, app_state)
        # Using create_api_success_response for the return
        return create_api_success_response(
            data={
                "order_id": order_result.get('order_id', 'N/A'),
                "execution_price": order_result.get('average_price'),
                "status": order_result.get('status'),
                "timestamp": datetime.utcnow().isoformat()
            },
            message=f"Manual trade for {trade_request.symbol} by {trade_request.user_id} processed."
        )
    else:
        error_msg = order_result.get('message', order_result.get('error', 'Unknown error')) if order_result else "Order Manager returned None or unsucessful result."
        logger.error(f"Manual order placement failed: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Order placement failed: {error_msg}")


@trading_router.post("/manual-trade", summary="Place a manual trade")
async def place_manual_trade_route(trade_request: TradeRequest, app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    return await execute_manual_trade_action(trade_request, app_state, settings)

@trading_router.post("/manual-order", summary="Place a manual order (alias for /manual-trade)")
async def place_manual_order_route(trade_request: TradeRequest, app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    return await execute_manual_trade_action(trade_request, app_state, settings)

@trading_router.get("/trading-signals/active", summary="Get active trading signals from database")
async def get_active_trading_signals_route(app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected for trading signals.")
    try:
        signals_res = await execute_db_query(
            "SELECT signal_id, strategy_name, symbol, action, quality_score, status, generated_at, metadata FROM trading_signals WHERE DATE(generated_at) >= DATE('now', '-1 day') AND status IN ('GENERATED', 'VALIDATED') ORDER BY generated_at DESC LIMIT 50",
            db_conn_or_path=app_state.clients.db_pool
        )
        signals_list = [dict(row) for row in signals_res] if signals_res else []
        for signal in signals_list:
            if signal.get('generated_at') and isinstance(signal['generated_at'], datetime):
                signal['generated_at'] = signal['generated_at'].isoformat()
        return create_api_success_response(data={"count": len(signals_list), "signals": signals_list})
    except Exception as e:
        logger.error(f"Error getting trading signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting trading signals: {str(e)}")

@trading_router.post("/trading/generate-signal", summary="Force trigger strategy execution loop")
async def force_generate_signal_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    if not app_state.system_status.database_connected:
        raise HTTPException(status_code=503, detail="Database not connected.")
    if not app_state.trading_control.autonomous_trading_active and not settings.PAPER_TRADING:
        logger.warning("Force signal generation: Autonomous trading off & not paper trading.")
    try:
        from src.trading_strategies import execute_strategy_loop
        await execute_strategy_loop(app_state, settings)
        return create_api_success_response(message="Strategy execution loop triggered.", data={"timestamp": datetime.utcnow().isoformat()})
    except ImportError:
        logger.error("Failed to import execute_strategy_loop for signal generation.")
        raise HTTPException(status_code=500, detail="Signal generation mechanism failed to load.")
    except Exception as e:
        logger.error(f"Error forcing signal generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error forcing signal generation: {str(e)}")

@trading_router.post("/square-off-all", summary="Square off all open positions")
async def square_off_all_positions_route(app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    logger.info(f"Square off all positions request. Paper Mode: {app_state.trading_control.paper_trading}") # Use app_state for paper mode
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database not available.")
    if not app_state.clients.order_manager: raise HTTPException(status_code=503, detail="OrderManager not available.")

    closed_positions_details, total_pnl_simulated = [], 0.0
    try:
        open_positions = await execute_db_query("SELECT position_id, user_id, symbol, quantity, average_entry_price FROM positions WHERE status = 'OPEN'", db_conn_or_path=app_state.clients.db_pool)
        if not open_positions:
            return create_api_success_response(message="No open positions to square off.", data={"positions_closed_count": 0})

        for pos_dict in (dict(p) for p in open_positions):
            exit_order_params = { # ... (params as before) ...
                'user_id': pos_dict['user_id'], 'symbol': pos_dict['symbol'], 'order_type': 'MARKET',
                'quantity': abs(pos_dict['quantity']), 'side': 'SELL' if pos_dict['quantity'] > 0 else 'BUY',
                'strategy_name': 'SQUARE_OFF_ALL_API', 'signal_id': str(uuid.uuid4()),
                'trade_reason': 'Square Off All Positions via API Request'
            }
            order_res = await app_state.clients.order_manager.place_order(exit_order_params, is_paper=app_state.trading_control.paper_trading)
            if order_res and order_res.get('success'):
                # ... (logic for PNL and DB update as before) ...
                exit_price = order_res.get('average_price', pos_dict['average_entry_price'])
                pnl = (exit_price - pos_dict['average_entry_price']) * pos_dict['quantity']
                total_pnl_simulated += pnl
                await execute_db_query("UPDATE positions SET status = 'CLOSED', exit_time = ?, realized_pnl = ?, exit_reason = ? WHERE position_id = ?", datetime.utcnow(), pnl, "API_SQUARE_OFF_ALL", pos_dict['position_id'], db_conn_or_path=app_state.clients.db_pool)
                closed_positions_details.append({'symbol': pos_dict['symbol'], 'pnl': pnl})
                logger.info(f"Squared-off {pos_dict['symbol']}, PnL: {pnl}")
            else: logger.error(f"Failed to square off {pos_dict['symbol']}: {order_res.get('message', 'Unknown') if order_res else 'None'}")

        msg = f"Square off all complete: {len(closed_positions_details)} positions attempted. Total PnL: {total_pnl_simulated}"
        logger.info(msg)
        return create_api_success_response(message=msg, data={"closed_count": len(closed_positions_details), "total_pnl": total_pnl_simulated, "details": closed_positions_details})
    except Exception as e:
        logger.error(f"Error in square_off_all_positions_route: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during square off: {str(e)}")

@trading_router.get("/orders", summary="Get recent trading orders")
async def get_recent_orders_route(app_state: AppState = Depends(get_app_state), limit: int = Query(default=50, ge=1, le=200)): # Added default to Query
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database not connected.")
    try:
        orders_res = await execute_db_query(f"SELECT * FROM orders WHERE created_at >= datetime('now', '-1 day') ORDER BY created_at DESC LIMIT {limit}", db_conn_or_path=app_state.clients.db_pool)
        orders_list = [dict(row) for row in orders_res] if orders_res else []
        for order in orders_list: # Ensure datetime is ISO formatted
            if order.get('created_at') and isinstance(order['created_at'], datetime): order['created_at'] = order['created_at'].isoformat()
            if order.get('filled_at') and isinstance(order['filled_at'], datetime): order['filled_at'] = order['filled_at'].isoformat()
        return create_api_success_response(data={"count": len(orders_list), "orders": orders_list})
    except Exception as e:
        logger.error(f"Error getting orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting orders: {str(e)}")

@trading_router.get("/elite-recommendations", response_model=List[EliteRecommendationResponse], summary="Get current elite trade recommendations")
async def get_elite_recommendations_route(app_state: AppState = Depends(get_app_state)):
    # This route returns a List directly, so create_api_success_response is not used. This is correct.
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database not connected.")
    try: # ... (logic as before, using app_state.clients.db_pool) ...
        recs_data = await execute_db_query("SELECT recommendation_id, symbol, strategy, direction, entry_price, stop_loss, primary_target, confidence_score, timeframe, metadata FROM elite_recommendations WHERE status = 'ACTIVE' AND valid_until > datetime('now', 'localtime') ORDER BY scan_timestamp DESC LIMIT 20", db_conn_or_path=app_state.clients.db_pool)
        recommendations = []
        if recs_data:
            for row_dict in (dict(row) for row in recs_data):
                metadata = json.loads(row_dict.get('metadata', '{}')) if row_dict.get('metadata') else {}
                summary = metadata.get('summary', f"Elite {row_dict['direction']} for {row_dict['symbol']} by {row_dict['strategy']}")
                recommendations.append(EliteRecommendationResponse(**row_dict, summary=summary)) # Pass all fields to model
        return recommendations
    except json.JSONDecodeError as json_err: # ... (error handling as before) ...
        logger.error(f"JSON decode error for elite recommendations metadata: {json_err}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing recommendation data.")
    except Exception as e:
        logger.error(f"Error getting elite recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting elite recommendations: {str(e)}")


@trading_router.get("/elite-recommendations/stats", summary="Get elite recommendations statistics")
async def get_elite_stats_route(app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database not available.")
    stats = {"total_recommendations_ever": 0, "active_recommendations_now": 0, "last_24h_generated": 0}
    try: # ... (logic as before, using app_state.clients.db_pool) ...
        total_res = await fetch_one_db("SELECT COUNT(*) as count FROM elite_recommendations", db_conn_or_path=app_state.clients.db_pool)
        stats["total_recommendations_ever"] = total_res["count"] if total_res else 0
        active_res = await fetch_one_db("SELECT COUNT(*) as count FROM elite_recommendations WHERE status = 'ACTIVE' AND valid_until > datetime('now', 'localtime')", db_conn_or_path=app_state.clients.db_pool)
        stats["active_recommendations_now"] = active_res["count"] if active_res else 0
        recent_res = await fetch_one_db("SELECT COUNT(*) as count FROM elite_recommendations WHERE scan_timestamp >= datetime('now', '-1 day')", db_conn_or_path=app_state.clients.db_pool)
        stats["last_24h_generated"] = recent_res["count"] if recent_res else 0
        return create_api_success_response(data=stats)
    except Exception as e:
        logger.error(f"Error getting elite stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting elite stats: {str(e)}")

@trading_router.post("/elite-recommendations/scan", summary="Trigger manual elite scan")
async def trigger_elite_scan_route(app_state: AppState = Depends(get_app_state)):
    logger.info("Manual elite scan triggered via API.")
    elite_eng = app_state.clients.elite_engine
    if not elite_eng: raise HTTPException(status_code=503, detail="Elite recommendation engine not available.")
    recs_found_list = []
    try: # ... (logic as before, using elite_eng and app_state.config) ...
        if hasattr(elite_eng, 'scan_for_elite_trades') and callable(getattr(elite_eng, 'scan_for_elite_trades')):
            recs_found_list = await elite_eng.scan_for_elite_trades(app_state=app_state, settings=app_state.config)
        else: logger.warning("elite_engine.scan_for_elite_trades is not callable or does not exist.")
        return create_api_success_response(message="Elite scan completed.", data={"recommendations_found_count": len(recs_found_list), "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        logger.error(f"Error in elite scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in elite scan: {str(e)}")

class StubOrderData(BaseModel):
    symbol: str = Field(..., min_length=1)
    action: str = Field(..., min_length=2)
    quantity: int = Field(..., gt=0)
    order_type: Optional[str] = Field(default="MARKET", min_length=3)
    price: Optional[float] = Field(default=None, ge=0.0)

@trading_router.post("/trading/place-order", summary="Place a new trading order (stub)")
async def place_trading_order_stub_route(order_data: StubOrderData, app_state: AppState = Depends(get_app_state), settings: AppSettings = Depends(get_settings)):
    logger.warning("'/trading/place-order' stub called.") # No change to function body for Path/Query
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="DB unavailable for stub order.") # No change to function body
    order_id = f"STUB_ORD_{uuid.uuid4().hex[:6]}"
    await execute_db_query( # No change to function body
        "INSERT INTO orders (order_id, user_id, symbol, quantity, order_type, side, price, status, strategy_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", # No change
        order_id, "stub_user", order_data.symbol, order_data.quantity, order_data.order_type,  # No change
        order_data.action, order_data.price, "FILLED_STUB" if settings.PAPER_TRADING else "PENDING_STUB",  # No change
        "Manual_Stub", datetime.utcnow(), db_conn_or_path=app_state.clients.db_pool # No change
    )
    return create_api_success_response(data={"order_id": order_id, "status": "FILLED_STUB" if settings.PAPER_TRADING else "PENDING_STUB"}, message="Stub order placed.")

@trading_router.post("/trading/cancel-order/{order_id}", summary="Cancel a pending order (stub)")
async def cancel_order_stub_route(order_id: str = Path(..., min_length=1, description="ID of the order to cancel"), app_state: AppState = Depends(get_app_state)):
    logger.warning(f"'/trading/cancel-order/{order_id}' stub called.")
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="DB unavailable for stub cancel.")
    await execute_db_query("UPDATE orders SET status = ? WHERE order_id = ? AND status LIKE ?", "CANCELLED_STUB", order_id, "PENDING%", db_conn_or_path=app_state.clients.db_pool)
    return create_api_success_response(message=f"Order {order_id} cancellation attempted (stub).")

@trading_router.post("/trading/square-off/{symbol}", summary="Square off a specific position (stub)")
async def square_off_position_stub_route(symbol: str = Path(..., min_length=1, description="Symbol of the position to square off"), app_state: AppState = Depends(get_app_state)):
    logger.warning(f"'/trading/square-off/{symbol}' stub called.")
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="DB unavailable for stub square-off.")
    await execute_db_query("UPDATE positions SET status = ?, exit_time = ? WHERE symbol = ? AND (status = 'OPEN' OR status = 'open')", "CLOSED_STUB", datetime.utcnow(), symbol, db_conn_or_path=app_state.clients.db_pool)
    return create_api_success_response(message=f"Position for {symbol} square-off attempted (stub).")

```
