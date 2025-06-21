from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, time
import logging # Added for logging

# Forward reference for AppSettings if needed
# from .config import AppSettings

class MarketDataState(BaseModel):
    live_market_data: Dict[str, Any] = Field(default_factory=dict)
    market_data_last_update: Optional[datetime] = None
    truedata_connected: bool = False
    zerodha_data_connected: bool = False
    active_data_source: Optional[str] = None
    data_source_fallback_active: bool = False
    last_data_source_switch: Optional[datetime] = None
    truedata_connection_details: Optional[Dict[str, Any]] = None
    zerodha_connection_details: Optional[Dict[str, Any]] = None

class StrategyInstanceInfo(BaseModel):
    instance: Optional[Any] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = False
    status_message: str = "PENDING_INITIALIZATION"
    daily_trades: int = 0
    daily_pnl: float = 0.0

    class Config:
        arbitrary_types_allowed = True

class StrategyState(BaseModel):
    strategy_instances: Dict[str, StrategyInstanceInfo] = Field(default_factory=dict)
    overall_strategies_pnl: float = 0.0

class TradingControlState(BaseModel):
    paper_trading: bool = True
    autonomous_trading_active: bool = False
    trading_active: bool = True
    emergency_mode: bool = False

class SystemOverallState(BaseModel):
    system_health: str = "INITIALIZING"
    database_connected: bool = False
    redis_connected: bool = False
    websocket_connections: int = 0 # Counter for active connections
    websocket_connections_set: set = Field(default_factory=set) # Holds actual WebSocket objects
    app_start_time: datetime = Field(default_factory=datetime.utcnow)
    last_system_update_utc: datetime = Field(default_factory=datetime.utcnow)
    market_open: bool = False
    initialized_successfully: bool = False # Added based on server.py logic

    class Config: # Ensure arbitrary_types_allowed for the set if it wasn't implicitly handled
        arbitrary_types_allowed = True

class ClientsState(BaseModel):
    db_pool: Optional[Any] = None
    redis_client: Optional[Any] = None
    # truedata_client_instance: Optional[Any] = None # Removed, TrueData client is now a global singleton
    zerodha_client_instance: Optional[Any] = None
    elite_engine: Optional[Any] = None
    order_manager: Optional[Any] = None
    risk_manager: Optional[Any] = None
    position_tracker: Optional[Any] = None
    scheduler: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

class AppState(BaseModel):
    config: Optional[Any] = None # Will hold AppSettings instance
    market_data: MarketDataState = Field(default_factory=MarketDataState)
    strategies: StrategyState = Field(default_factory=StrategyState)
    trading_control: TradingControlState = Field(default_factory=TradingControlState)
    system_status: SystemOverallState = Field(default_factory=SystemOverallState)
    clients: ClientsState = Field(default_factory=ClientsState)

    class Config:
        arbitrary_types_allowed = True

app_state = AppState()

if __name__ == "__main__":
    # For standalone execution/testing of this module, setup basic logging.
    # In the main app, logging is configured by server.py calling setup_logging.
    try:
        from src.core.logging_config import setup_logging
        # Use a default level for standalone testing, or import settings if truly needed (can create circularity)
        setup_logging(log_level="DEBUG")
    except ImportError:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        logging.warning("Could not import setup_logging for app_state.py direct execution. Using basicConfig.")

    logger = logging.getLogger(__name__) # Get logger after potential setup

    logger.info("Initial App State (example usage):")
    # Use model_dump_json for Pydantic v2 if it was intended, or model_dump if dict is enough
    logger.info(app_state.model_dump_json(indent=2))

    # Simulate updating some state components
    app_state.system_status.database_connected = True
    app_state.market_data.truedata_connected = True
    app_state.market_data.live_market_data["NIFTY"] = {"ltp": 18000, "timestamp": datetime.utcnow().isoformat()}
    app_state.trading_control.autonomous_trading_active = True

    class DummyStrategyInstance:
        def __init__(self): self.name = "Dummy"

    dummy_instance = DummyStrategyInstance()
    app_state.strategies.strategy_instances["momentum_v1"] = StrategyInstanceInfo(
        instance=dummy_instance,
        is_active=True,
        status_message="Running example"
    )

    logger.info("\nUpdated App State (example usage):")
    logger.info(app_state.model_dump_json(indent=2))

    # Example of accessing config if it were populated (it's not in standalone run)
    if app_state.config:
        logger.info(f"Configured LOG_LEVEL (if settings were loaded): {app_state.config.LOG_LEVEL}")
    else:
        logger.info("app_state.config is None in standalone app_state.py execution (as expected).")
