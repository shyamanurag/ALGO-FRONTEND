from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta # Added timedelta

# Assuming these are the dependency injectors from server.py or a common deps file
try:
    from backend.server import get_app_state, get_settings
except ImportError:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning("Could not import get_app_state, get_settings from backend.server. Using local fallbacks for admin_routes.")
    from src.app_state import app_state as _global_app_state_instance_admin
    from src.config import settings as _global_settings_instance_admin
    async def get_app_state(): return _global_app_state_instance_admin
    async def get_settings(): return _global_settings_instance_admin

from src.app_state import AppState
from src.config import AppSettings
from src.database import execute_db_query, fetch_one_db
from src.core.utils import create_api_success_response
from src.core.security import ( # Import security utilities
    UserInDB, Token, TokenData, # Token is the response model, TokenData for JWT content
    verify_password,
    create_access_token,
    get_password_hash,
    get_admin_user_from_settings
)
from pydantic import BaseModel, Field

# OAuth2 scheme
# If admin_router is mounted at "/api/admin" in server.py, then tokenUrl="token" is correct.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class StrategyConfigAdmin(BaseModel):
    name: str
    enabled: bool
    parameters: Dict = Field(default_factory=dict)
    allocation: float = Field(default=0.1, ge=0, le=1)

logger = logging.getLogger(__name__)
# The router was named api_router in the previous version of this file.
# For consistency with other route modules, let's rename it to admin_router.
# However, server.py imports it as `api_router as admin_router`.
# To avoid breaking server.py's import, I'll keep it as api_router here.
# A better fix would be to standardize to admin_router here AND in server.py's import.
# For now, keeping api_router.
api_router = APIRouter()


# --- Authentication Endpoint ---
@api_router.post("/token", response_model=Token, tags=["Admin Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: AppSettings = Depends(get_settings)
):
    # This is a conceptual step for the subtask. In real life, hash generation is a separate one-off step.
    # We are modifying the settings object in memory for this run if hash is not present.
    effective_admin_password_hash = settings.ADMIN_PASSWORD_HASH
    if settings.ADMIN_PASSWORD_PLAIN and not settings.ADMIN_PASSWORD_HASH:
        logger.warning(
            f"ADMIN_PASSWORD_HASH not set. Generating from ADMIN_PASSWORD_PLAIN for user '{settings.ADMIN_USERNAME}'. "
            "This should ideally be a one-time setup. The generated hash should be stored securely in .env as ADMIN_PASSWORD_HASH."
        )
        effective_admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD_PLAIN)
        # For this subtask, we don't persist this back to settings object or .env,
        # but use the generated hash for this authentication attempt.
        # A real application might update the settings object if it's designed to be mutable and reflect this.

    # Use effective_admin_password_hash which might be from settings or just generated
    # get_admin_user_from_settings needs to be aware of this potential in-memory hash or take it as arg.
    # For simplicity, get_admin_user_from_settings will re-generate if hash is missing and plain is present.
    admin_user = get_admin_user_from_settings(settings, form_data.username) # Pass full settings

    if not admin_user or not verify_password(form_data.password, admin_user.hashed_password):
        raise HTTPException(
            status_code=401, # Changed from 400 to 401 for unauthorized
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if admin_user.disabled: # Check if user is disabled
        raise HTTPException(status_code=400, detail="Inactive user") # 400 or 403 might be appropriate

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token_jwt = create_access_token( # Use renamed function from security.py
        data={"sub": admin_user.username, "role": admin_user.role}, # "role" added to token data
        expires_delta=access_token_expires
    )
    return {"access_token": access_token_jwt, "token_type": "bearer"}

# --- Dependency for Protected Routes ---
async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    settings: AppSettings = Depends(get_settings)
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        if username is None or role != "admin": # Check for role
            logger.warning(f"Token validation failed: username missing or role is not admin. Payload: {payload}")
            raise credentials_exception
        # TokenData can be used here for validation if more claims are present
        # token_data = TokenData(username=username, role=role)
    except JWTError as e:
        logger.error(f"JWT Error during token decoding: {e}", exc_info=True)
        raise credentials_exception

    user = get_admin_user_from_settings(settings, username) # Pass full settings
    if user is None or user.disabled: # Check if user is disabled
        logger.warning(f"User '{username}' not found or disabled after token validation.")
        raise credentials_exception
    return user

# --- Protected Admin Routes ---
@api_router.get("/overall-metrics", summary="Get overall system and trading metrics for admin")
async def get_admin_overall_metrics(
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.info(f"Admin request for overall metrics by user: {current_admin.username}")
    # ... (rest of the logic as before) ...
    active_strategies = [name for name, si_info in app_state.strategies.strategy_instances.items() if si_info.is_active]
    total_pnl_today = sum(si_info.daily_pnl for si_info in app_state.strategies.strategy_instances.values())
    total_trades_today = sum(si_info.daily_trades for si_info in app_state.strategies.strategy_instances.values())
    metrics_data = {
        "timestamp": datetime.utcnow().isoformat(), "system_health": app_state.system_status.system_health,
        "market_open": app_state.system_status.market_open, "autonomous_trading_active": app_state.trading_control.autonomous_trading_active,
        "paper_trading_mode": app_state.trading_control.paper_trading, "active_strategies_count": len(active_strategies),
        "active_strategies_names": active_strategies, "total_pnl_today": total_pnl_today, "total_trades_today": total_trades_today,
        "database_connected": app_state.system_status.database_connected, "truedata_connected": app_state.market_data.truedata_connected,
        "zerodha_connected": app_state.market_data.zerodha_data_connected,
    }
    return create_api_success_response(data=metrics_data)


@api_router.post("/strategies/{strategy_name}/configure", summary="Configure a trading strategy")
async def configure_strategy(
    strategy_name: str,
    config: StrategyConfigAdmin,
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.info(f"Admin user '{current_admin.username}' configuring strategy: {strategy_name} with config: {config.model_dump()}")
    # ... (rest of the logic as before) ...
    strat_info = app_state.strategies.strategy_instances.get(strategy_name)
    if not strat_info or not strat_info.instance:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found or instance not initialized.")
    strat_info.is_active = config.enabled; strat_info.config['parameters'] = config.parameters
    strat_info.config['enabled'] = config.enabled; strat_info.config['allocation'] = config.allocation
    logger.info(f"Strategy '{strategy_name}' configured by '{current_admin.username}'.")
    return create_api_success_response(data={"configured_strategy": strategy_name, "new_settings": config.model_dump()}, message=f"Strategy '{strategy_name}' configured successfully.")

@api_router.put("/trading/pause", summary="Pause autonomous trading system")
async def pause_autonomous_trading(
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.warning(f"Admin user '{current_admin.username}' PAUSING autonomous trading.")
    app_state.trading_control.autonomous_trading_active = False
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(message="Autonomous trading paused successfully.", data={"autonomous_trading_active": False})

@api_router.put("/trading/resume", summary="Resume autonomous trading system")
async def resume_autonomous_trading(
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.info(f"Admin user '{current_admin.username}' RESUMING autonomous trading.")
    app_state.trading_control.autonomous_trading_active = True
    app_state.system_status.last_system_update_utc = datetime.utcnow()
    return create_api_success_response(message="Autonomous trading resumed successfully.", data={"autonomous_trading_active": True})

@api_router.get("/users/summary", summary="Get summary of all users")
async def get_users_summary_admin(
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.info(f"Admin user '{current_admin.username}' requesting users summary.")
    # ... (rest of the logic as before) ...
    if not app_state.clients.db_pool: raise HTTPException(status_code=503, detail="Database service not available.")
    users_data_raw = await execute_db_query("SELECT user_id, username, email, status, created_at FROM users ORDER BY created_at DESC LIMIT 100", db_conn_or_path=app_state.clients.db_pool)
    users_summary = [dict(row) for row in users_data_raw] if users_data_raw else []
    return create_api_success_response(data={"users_summary": users_summary, "total_displaying": len(users_summary)})

@api_router.get("/zerodha/admin-status", summary="Get Zerodha client admin-level status")
async def get_zerodha_admin_status(
    app_state: AppState = Depends(get_app_state),
    current_admin: UserInDB = Depends(get_current_admin_user) # Protected
):
    logger.info(f"Admin user '{current_admin.username}' requesting Zerodha client status.")
    zerodha_client = app_state.clients.zerodha_client_instance
    if not zerodha_client:
        raise HTTPException(status_code=503, detail="Zerodha client not initialized in app_state.clients.")
    try:
        status = zerodha_client.get_client_status_summary() if hasattr(zerodha_client, 'get_client_status_summary') else "Client status method not available."
        return create_api_success_response(data={"zerodha_admin_status": status})
    except Exception as e:
        logger.error(f"Error getting Zerodha admin status by '{current_admin.username}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching Zerodha status from client: {str(e)}")

```
