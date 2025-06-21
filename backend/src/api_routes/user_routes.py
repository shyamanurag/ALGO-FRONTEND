from fastapi import APIRouter, HTTPException, Depends, Request, Path, Query # Added Path, Query
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import uuid
from pydantic import BaseModel, Field, EmailStr # Added EmailStr

from src.app_state import AppState
from src.config import AppSettings
from src.core.utils import create_api_success_response, format_datetime_for_api # Import utilities
from src.database import execute_db_query, fetch_one_db

try:
    from backend.server import get_app_state, get_settings
except ImportError:
    _fallback_logger_user = logging.getLogger(__name__)
    _fallback_logger_user.error("CRITICAL: Could not import get_app_state, get_settings from backend.server for user_routes.py.")
    from src.app_state import app_state as _global_app_state_instance_user
    from src.config import settings as _global_settings_instance_user
    async def get_app_state(): return _global_app_state_instance_user
    async def get_settings(): return _global_settings_instance_user

logger = logging.getLogger(__name__)

class UserAccount(BaseModel):
    user_id: Optional[str] = Field(default=None, min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$", description="Optional: Define a custom user ID. If None, one will be generated.")
    zerodha_user_id: Optional[str] = Field(default=None, min_length=1, description="Zerodha client ID, if applicable.")
    status: Optional[str] = Field(default="pending_verification", min_length=3, description="Account status, e.g., active, pending_verification.")
    capital_allocation: Optional[float] = Field(default=100000.0, ge=0.0, description="Capital allocated to this user for trading.")
    risk_percentage: Optional[float] = Field(default=2.0, ge=0.0, le=100.0, description="Risk percentage per trade or daily.")
    notes: Optional[str] = Field(default=None)
    zerodha_password: Optional[str] = Field(default=None, description="[Sensitive] Zerodha password - use with caution, prefer external vault or secure input.")
    totp_secret: Optional[str] = Field(default=None, description="[Sensitive] TOTP secret for Zerodha - use with caution.")
    shared_api: Optional[bool] = Field(default=True)
    individual_login: Optional[bool] = Field(default=True)
    full_name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = Field(default=None) # Using EmailStr for basic email validation
    paper_trading: Optional[bool] = Field(default=True)
    autonomous_trading: Optional[bool] = Field(default=False)

user_router = APIRouter(tags=["Users & Accounts"])

@user_router.get("/users/list", summary="Get list of all users")
async def get_users_list_route(app_state: AppState = Depends(get_app_state)): # No path/query params here
    if not app_state.clients.db_pool:
        logger.warning("/users/list: Database pool not available. Returning empty list.") # No change
        return create_api_success_response(data={"users": []}, message="Database not available, returning empty list.") # No change
    try: # No change
        users_result = await execute_db_query( # No change
            "SELECT DISTINCT user_id, full_name FROM users WHERE status != 'TERMINATED' ORDER BY user_id", # No change
            db_conn_or_path=app_state.clients.db_pool # No change
        )
        users = [{"user_id": row[0], "name": row[1] or f"User {row[0]}"} for row in users_result] if users_result else [] # No change
        return create_api_success_response(data={"users": users}) # No change
    except Exception as e: # No change
        logger.error(f"Error getting users list: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching users: {str(e)}") # No change

@user_router.get("/users/{user_id}/metrics", summary="Get individual user trading metrics")
async def get_user_metrics_route(user_id: str = Path(..., min_length=1, description="User ID to fetch metrics for"), app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool:
        logger.warning(f"/users/{user_id}/metrics: Database pool not available.")
        if user_id == "SHYAM_QSW899":
             metrics_data = {"user_id": "SHYAM_QSW899", "data_source": "NO_DB_FALLBACK_METRICS_FOR_SHYAM", "daily_pnl": 0, "total_trades_today": 0, "capital_allocated": 500000}
             return create_api_success_response(data=metrics_data, message="Metrics from fallback due to DB issue.")
        raise HTTPException(status_code=503, detail="Database service not available.")
    try: # No change
        user_record = await fetch_one_db("SELECT user_id, max_daily_loss FROM users WHERE user_id = ?", user_id, db_conn_or_path=app_state.clients.db_pool) # No change
        if not user_record: raise HTTPException(status_code=404, detail=f"User {user_id} not found.") # No change

        capital_allocated = user_record["max_daily_loss"] if user_record["max_daily_loss"] is not None else (500000 if user_id == "SHYAM_QSW899" else 100000) # No change
        pnl_res = await fetch_one_db("SELECT SUM(realized_pnl) as pnl FROM positions WHERE user_id = ? AND DATE(exit_time) = DATE('now', 'localtime')", user_id, db_conn_or_path=app_state.clients.db_pool) # No change
        daily_pnl = pnl_res["pnl"] if pnl_res and pnl_res["pnl"] is not None else 0.0 # No change
        trades_res = await fetch_one_db("SELECT COUNT(*) as count FROM orders WHERE user_id = ? AND DATE(created_at) = DATE('now', 'localtime')", user_id, db_conn_or_path=app_state.clients.db_pool) # No change
        total_trades_today = trades_res["count"] if trades_res else 0 # No change

        metrics_data = { # No change
            "user_id": user_id, "data_source": "DATABASE_QUERIES", "daily_pnl": daily_pnl, # No change
            "total_trades_today": total_trades_today, "win_rate_today": 0.0, # No change
            "capital_allocated": capital_allocated, "last_updated_utc": format_datetime_for_api(datetime.utcnow()) # No change
        }
        return create_api_success_response(data=metrics_data) # No change
    except Exception as e: # No change
        logger.error(f"Error getting user metrics for {user_id}: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error getting user metrics: {str(e)}") # No change

@user_router.get("/users/{user_id}/trades", summary="Get user's recent trades")
async def get_user_trades_route(user_id: str = Path(..., min_length=1, description="User ID to fetch trades for"), app_state: AppState = Depends(get_app_state), limit: int = Query(default=20, gt=0, le=100, description="Number of recent trades to fetch")):
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.")
    try:
        trades_res = await execute_db_query( # No change to query construction itself
            f"SELECT order_id, symbol, side, filled_quantity, average_price, created_at, strategy_name FROM orders WHERE user_id = ? AND status = 'FILLED' ORDER BY created_at DESC LIMIT {limit}",
            user_id, db_conn_or_path=app_state.clients.db_pool
        )
        trades = [dict(row) for row in trades_res] if trades_res else [] # No change
        for trade in trades:  # No change
            trade['created_at'] = format_datetime_for_api(trade.get('created_at')) # No change
        return create_api_success_response(data={"trades": trades, "user_id": user_id, "count": len(trades)}) # No change
    except Exception as e: # No change
        logger.error(f"Error getting user trades for {user_id}: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error getting user trades: {str(e)}") # No change

@user_router.get("/users/{user_id}/positions", summary="Get user's current open positions")
async def get_user_positions_route(user_id: str = Path(..., min_length=1, description="User ID to fetch positions for"), app_state: AppState = Depends(get_app_state)):
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.")
    try:
        positions_res = await execute_db_query( # No change
            "SELECT position_id, symbol, quantity, average_entry_price, current_price, unrealized_pnl, strategy_name, entry_time FROM positions WHERE user_id = ? AND (status = 'OPEN' OR status = 'open') ORDER BY entry_time DESC",
            user_id, db_conn_or_path=app_state.clients.db_pool
        )
        positions = [dict(row) for row in positions_res] if positions_res else [] # No change
        for pos in positions: # No change
            pos['entry_time'] = format_datetime_for_api(pos.get('entry_time')) # No change
        return create_api_success_response(data={"positions": positions, "user_id": user_id, "count": len(positions)}) # No change
    except Exception as e: # No change
        logger.error(f"Error getting user positions for {user_id}: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error getting user positions: {str(e)}") # No change

@user_router.get("/users/{user_id}/reports", summary="Get user's financial reports (placeholder)")
async def get_user_reports_route(user_id: str = Path(..., min_length=1, description="User ID for the report"), report_type: str = Query(default="daily_summary", min_length=3, description="Type of report, e.g., daily_summary, monthly_pnl")):
    logger.info(f"User report for {user_id}, type: {report_type} (placeholder).")
    report_data = { # No change
        "report_type": report_type, "user_id": user_id, # No change
        "data_source": "PLACEHOLDER_NO_DATA", "generated_at": format_datetime_for_api(datetime.utcnow()), # No change
        "data": {"summary": {"total_pnl_mtd": 0, "total_trades_mtd": 0}, "details": []} # No change
    }
    return create_api_success_response(data=report_data, message="This is a placeholder for user financial reports.") # No change

@user_router.get("/accounts/connected", summary="Get all active accounts")
async def get_connected_accounts_route(app_state: AppState = Depends(get_app_state)): # No path/query params
    if not app_state.clients.db_pool: # No change
        logger.warning("/accounts/connected: Database pool not available.") # No change
        return create_api_success_response(data={"accounts": [], "total_accounts": 0, "active_accounts": 0}, message="DB unavailable.") # No change
    try: # No change
        accounts_res = await execute_db_query( # No change
            "SELECT u.user_id, u.full_name, u.status, u.paper_trading, uc.zerodha_user_id, u.max_daily_loss as capital_allocation, u.created_at FROM users u LEFT JOIN user_credentials uc ON u.user_id = uc.user_id WHERE u.status NOT IN ('TERMINATED', 'ARCHIVED', 'DISABLED', 'pending_verification') ORDER BY u.created_at DESC",
            db_conn_or_path=app_state.clients.db_pool # No change
        )
        accounts_list = [] # No change
        if accounts_res: # No change
            for row_dict in (dict(row) for row in accounts_res): # No change
                accounts_list.append({ # No change
                    "user_id": row_dict['user_id'], "zerodha_user_id": row_dict.get('zerodha_user_id', "N/A"),  # No change
                    "full_name": row_dict.get('full_name', f"User {row_dict['user_id']}"), "status": row_dict['status'], # No change
                    "capital_allocation": row_dict.get('capital_allocation', 0),  # No change
                    "created_at": format_datetime_for_api(row_dict.get('created_at')), # No change
                    "is_paper_trading": bool(row_dict.get('paper_trading')), # No change
                    "api_key_configured": bool(row_dict.get('zerodha_user_id')),  # No change
                })
        return create_api_success_response(data={"accounts": accounts_list, "total_accounts": len(accounts_list), "active_accounts": len(accounts_list)}) # No change
    except Exception as e: # No change
        logger.error(f"Error getting connected accounts: {e}", exc_info=True) # No change
        raise HTTPException(status_code=500, detail=f"Error getting connected accounts: {str(e)}") # No change

@user_router.post("/accounts/onboard-zerodha", summary="Onboard new Zerodha-linked user account")
async def onboard_zerodha_account_route(account_data: UserAccount, app_state: AppState = Depends(get_app_state)): # Body validated by Pydantic
    user_id = account_data.user_id or f"user_{uuid.uuid4().hex[:8]}" # Logic based on validated data
    zerodha_user_id = account_data.zerodha_user_id # Logic based on validated data
    full_name = account_data.full_name or f"User {user_id}" # Logic based on validated data
    email_str = str(account_data.email) if account_data.email else f"{user_id}@placeholder.domain.com" # Handle Pydantic EmailStr
    logger.info(f"Attempting to onboard account: UserID '{user_id}', ZerodhaID '{zerodha_user_id}'")

    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.") # No change
    try:
        # ... (DB logic as before, using app_state.clients.db_pool) ...
        existing_check_query = "SELECT user_id FROM users WHERE user_id = ? OR username = ? OR email = ?"
        params = [user_id, zerodha_user_id or user_id, email]
        if await fetch_one_db(existing_check_query, *params, db_conn_or_path=app_state.clients.db_pool):
            raise HTTPException(status_code=409, detail=f"User ID, Username (Zerodha ID), or Email may already exist.")
        max_daily_loss = (account_data.capital_allocation or 0) * ((account_data.risk_percentage or 0) / 100.0)
        await execute_db_query("INSERT INTO users (user_id, username, email, full_name, password_hash, paper_trading, autonomous_trading, max_daily_loss, created_at, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", user_id, zerodha_user_id or user_id, email, full_name, "default_password_hash_placeholder", account_data.paper_trading, account_data.autonomous_trading, max_daily_loss, datetime.utcnow(), account_data.status, account_data.notes, db_conn_or_path=app_state.clients.db_pool)
        if zerodha_user_id and account_data.zerodha_password and account_data.totp_secret:
            logger.warning(f"Sensitive Zerodha credentials provided for {zerodha_user_id} during onboarding.")
            await execute_db_query("INSERT INTO user_credentials (user_id, zerodha_user_id, zerodha_password_encrypted, totp_secret_encrypted, created_at) VALUES (?, ?, ?, ?, ?)", user_id, zerodha_user_id, f"FAKE_ENCRYPTED({account_data.zerodha_password})", f"FAKE_ENCRYPTED({account_data.totp_secret})", datetime.utcnow(), db_conn_or_path=app_state.clients.db_pool)

        return create_api_success_response(
            data={"user_id_created": user_id, "zerodha_user_id_linked": zerodha_user_id},
            message="Account onboarded successfully."
        )
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        logger.error(f"Error onboarding account for user_id {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error during account onboarding: {str(e)}")

@user_router.delete("/accounts/{user_id}/terminate", summary="Terminate a user account")
async def terminate_account_route(user_id: str, app_state: AppState = Depends(get_app_state)):
    logger.info(f"Attempting to terminate account: {user_id}")
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.")
    try:
        user_rec = await fetch_one_db("SELECT status FROM users WHERE user_id = ?", user_id, db_conn_or_path=app_state.clients.db_pool)
        if not user_rec: raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
        if user_rec["status"] == 'TERMINATED':
            return create_api_success_response(message=f"Account {user_id} already terminated.")

        await execute_db_query("UPDATE users SET status = 'TERMINATED', autonomous_trading = FALSE WHERE user_id = ?", user_id, db_conn_or_path=app_state.clients.db_pool)
        await execute_db_query("UPDATE user_credentials SET login_status = 'TERMINATED_BY_ADMIN' WHERE user_id = ?", user_id, db_conn_or_path=app_state.clients.db_pool)

        logger.info(f"Account {user_id} terminated successfully.")
        return create_api_success_response(message=f"Account {user_id} terminated.")
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        logger.error(f"Error terminating account {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error terminating account: {str(e)}")

@user_router.put("/accounts/{user_id}/toggle-autonomous", summary="Toggle autonomous trading for a user account")
async def toggle_account_autonomous_route(user_id: str, app_state: AppState = Depends(get_app_state)):
    logger.info(f"Attempting to toggle autonomous trading for account: {user_id}")
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.")
    try:
        user_rec = await fetch_one_db("SELECT autonomous_trading, status FROM users WHERE user_id = ?", user_id, db_conn_or_path=app_state.clients.db_pool)
        if not user_rec: raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
        if user_rec["status"] == 'TERMINATED': raise HTTPException(status_code=400, detail=f"Account {user_id} is terminated.")
        if user_rec["status"] == 'pending_verification': raise HTTPException(status_code=400, detail=f"Account {user_id} pending verification.")

        new_autonomous_status = not bool(user_rec["autonomous_trading"])
        await execute_db_query("UPDATE users SET autonomous_trading = ? WHERE user_id = ?", new_autonomous_status, user_id, db_conn_or_path=app_state.clients.db_pool)

        logger.info(f"Account {user_id} autonomous trading set to: {new_autonomous_status}")
        return create_api_success_response(
            data={"user_id": user_id, "autonomous_trading_enabled": new_autonomous_status},
            message=f"Account {user_id} autonomous trading status updated to {new_autonomous_status}"
        )
    except HTTPException as http_exc: raise http_exc
    except Exception as e:
        logger.error(f"Error toggling autonomous trading for {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error toggling autonomous status: {str(e)}")

