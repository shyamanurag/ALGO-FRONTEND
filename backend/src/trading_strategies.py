import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

from src.app_state import AppState, StrategyInstanceInfo
from src.config import AppSettings
from src.database import execute_db_query
from src.clients.zerodha_client import ZerodhaTokenError, ZerodhaAPIError # Import custom exceptions

try:
    from src.core.momentum_surfer import MomentumSurfer
    from src.core.news_impact_scalper import NewsImpactScalper
    from src.core.volatility_explosion import VolatilityExplosion
    # from src.core.confluence_amplifier import ConfluenceAmplifier # Example for settings.CONFLUENCE_AMPLIFIER_MIN_SIGNALS
    # from src.core.pattern_hunter import PatternHunter # Example for settings.HARMONIC_PATTERNS_ENABLED
    CORE_STRATEGY_CLASSES_AVAILABLE = True
except ImportError:
    logging.getLogger(__name__).warning("Actual strategy classes from src.core.* not found. Using dummy placeholders.")
    CORE_STRATEGY_CLASSES_AVAILABLE = False
    class BaseStrategyPlaceholder:
        def __init__(self, strategy_id: str, symbol: str, app_state: AppState, settings: AppSettings, config: Dict = None):
            self.strategy_id = strategy_id; self.symbol = symbol; self.app_state = app_state
            self.settings = settings; self.config = config or {}
            self._internal_logger = logging.getLogger(f"{__name__}.{self.strategy_id}")
            self._internal_logger.info(f"DummyStrat {self.strategy_id}/{self.symbol} init. Config: {self.config}, Global Harmonic Enabled: {self.settings.HARMONIC_PATTERNS_ENABLED}")
        async def generate_signal(self):
            action = "BUY" if uuid.uuid4().int % 2 == 0 else "SELL"
            price = self.app_state.market_data.live_market_data.get(self.symbol, {}).get('ltp', 100)
            if price == 0: price = 100
            self._internal_logger.info(f"DummyStrat {self.strategy_id} gen signal: {action} {self.symbol} @ {price}")
            return {"symbol": self.symbol, "action": action, "price": price, "quantity": 1, "order_type": "MARKET", "strategy_name": self.strategy_id, "stop_loss": price * 0.98, "take_profit": price * 1.02, "quality_score": 0.75}
        def get_strategy_metrics(self): return {"dummy_metric": 1, "trades_today": 0, "pnl": 0.0}
        is_enabled: bool = True; allocation: float = 0.1
    MomentumSurfer = NewsImpactScalper = VolatilityExplosion = BaseStrategyPlaceholder
    # ConfluenceAmplifier = PatternHunter = BaseStrategyPlaceholder # If using these examples

logger = logging.getLogger(__name__)

class PlaceholderOrderManager:
    def __init__(self, app_state: AppState, settings: AppSettings):
        self.app_state = app_state
        self.settings = settings
        logger.info("PlaceholderOrderManager initialized.")

    async def place_order(self, order_details: Dict[str, Any], is_paper: bool) -> Dict[str, Any]: # Already async, good.
        symbol = order_details.get('symbol', 'S_ERR'); action = order_details.get('side', 'A_ERR')
        quantity = order_details.get('quantity', 0); order_type = order_details.get('order_type', 'MARKET')
        price = order_details.get('price'); product = order_details.get('product', 'MIS'); variety = order_details.get('variety', 'regular')
        tag_from_details = order_details.get('strategy_name', order_details.get('tag'))
        final_tag = (tag_from_details or self.settings.DEFAULT_ORDER_TAG)[:20] # Use settings default tag

        log_prefix = f"OrderMgr ({'PAPER' if is_paper else 'REAL'}) for {order_details.get('user_id', 'sys')}:"
        log_details = f"{action} {quantity} {symbol} @ {order_type} (P:{price}) Tag:{final_tag}"

        if is_paper:
            logger.info(f"{log_prefix} Simulating paper order: {log_details}")
            order_id = f"PAPER_{uuid.uuid4().hex[:6].upper()}"; status = "FILLED"
            exec_price = price
            if order_type.upper() == "MARKET" or not exec_price:
                exec_price = self.app_state.market_data.live_market_data.get(symbol, {}).get('ltp', 100 if not price else price)
                if not exec_price or exec_price == 0: exec_price = 100
            return {"success": True, "order_id": order_id, "status": status, "symbol": symbol, "side": action, "quantity": quantity, "order_type": order_type, "average_price": exec_price, "timestamp": datetime.utcnow().isoformat(), "message": f"Paper order {order_id} FILLED."}
        else:
            logger.info(f"{log_prefix} Attempting REAL order: {log_details}")
            zd_client = self.app_state.clients.zerodha_client_instance
            if not zd_client or not self.app_state.market_data.zerodha_data_connected: # Check app_state for connection status
                logger.error(f"{log_prefix} Zerodha client not available/connected. Cannot place REAL order.")
                return {"success": False, "message": "Zerodha client not available or not connected.", "status": "REJECTED_NO_BROKER"}
            try:
                from kiteconnect import KiteConnect # For enums, consider moving to top if frequently used
                trans_type = KiteConnect.TRANSACTION_TYPE_BUY if action.upper() == "BUY" else KiteConnect.TRANSACTION_TYPE_SELL
                # TODO: Derive exchange from symbol master or settings more reliably
                exchange = "NFO" if any(kw in symbol.upper() for kw in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]) and \
                                    any(char.isdigit() for char in symbol) else "NSE"

                broker_order_id = await zd_client.place_order( # Await the async call
                    variety=variety, exchange=exchange, tradingsymbol=symbol, transaction_type=trans_type,
                    quantity=int(quantity), product=product.upper(), order_type=order_type.upper(), price=price,
                    trigger_price=order_details.get('trigger_price'), tag=final_tag
                )
                if broker_order_id: # Successful placement returns order_id (string)
                    logger.info(f"{log_prefix} REAL order initiated with Zerodha. Broker ID: {broker_order_id}")
                    return {"success": True, "order_id": broker_order_id, "status": "OPEN_PENDING_BROKER", "message": f"Real order placed with broker. ID: {broker_order_id}. Status likely pending."}
                else: # Should not happen if place_order raises exceptions on failure
                    logger.error(f"{log_prefix} Zerodha client returned no order_id without raising an exception. This is unexpected.")
                    return {"success": False, "message": "Broker returned no order_id and no error.", "status": "REJECTED_BROKER_UNKNOWN"}
            except ZerodhaTokenError as e_token:
                logger.error(f"{log_prefix} ZerodhaTokenError placing REAL order for {symbol}: {e_token.message}", exc_info=True)
                return {"success": False, "message": f"Authentication Error: {e_token.message}. Re-login required.", "status": "REJECTED_AUTH_ERROR"}
            except ZerodhaAPIError as e_api:
                logger.error(f"{log_prefix} ZerodhaAPIError placing REAL order for {symbol}: {e_api.message} (Status: {e_api.status_code})", exc_info=True)
                return {"success": False, "message": f"Broker API Error: {e_api.message}", "status": "REJECTED_BROKER_API_ERROR", "broker_error_code": e_api.status_code}
            except Exception as e: # Catch any other unexpected errors
                logger.error(f"{log_prefix} Unexpected exception placing REAL order for {symbol}: {e}", exc_info=True)
                return {"success": False, "message": f"Unexpected Server Exception: {str(e)}", "status": "REJECTED_SERVER_EXCEPTION"}

async def initialize_trading_strategies(app_state: AppState, settings: AppSettings):
    logger.info("Initializing Trading Strategies & OrderManager...")
    strat_state = app_state.strategies; clients = app_state.clients
    clients.order_manager = PlaceholderOrderManager(app_state, settings)
    logger.info("PlaceholderOrderManager initialized in app_state.clients.")

    # Example of using global settings for strategy defaults/params
    strategy_configs = {
        "momentum_surfer_nifty": {"class": MomentumSurfer, "symbol": "NIFTY", "enabled": True,
                                  "params": {"sma_period": settings.DEFAULT_SMA_PERIOD}, # Using setting
                                  "display_name": "Momentum Surfer NIFTY"},
        "news_scalper_infy": {"class": NewsImpactScalper, "symbol": "INFY", "enabled": True,
                              "params": {"news_sensitivity": settings.DEFAULT_NEWS_SENSITIVITY}, # Using setting
                              "display_name": "News Scalper INFY"},
        "volatility_bn": {"class": VolatilityExplosion, "symbol": "BANKNIFTY", "enabled": settings.HARMONIC_PATTERNS_ENABLED, # Example feature flag
                            "params": {"atr_multiplier": settings.DEFAULT_ATR_MULTIPLIER}, # Using setting
                            "display_name": "Volatility Explosion BN"},
    }
    strat_state.strategy_instances.clear()
    for strat_id, cfg_data in strategy_configs.items():
        StratCls = cfg_data["class"]
        instance = StratCls(strategy_id=strat_id, symbol=cfg_data["symbol"], app_state=app_state, settings=settings, config=cfg_data["params"])
        strat_state.strategy_instances[strat_id] = StrategyInstanceInfo(
            instance=instance, config=cfg_data, is_active=cfg_data["enabled"],
            status_message="Initialized" if cfg_data["enabled"] else "Initialized_Disabled_By_Config",
        )
        logger.info(f"Strategy '{strat_id}' ({cfg_data['display_name']}) for '{cfg_data['symbol']}' init. Active: {cfg_data['enabled']}")

    active_c = len([si for si in strat_state.strategy_instances.values() if si.is_active])
    app_state.system_status.strategies_active = active_c
    logger.info(f"Trading Strategies init complete. Active strategies: {active_c}")

async def execute_strategy_loop(app_state: AppState, settings: AppSettings):
    if not app_state.trading_control.autonomous_trading_active: return
    if not app_state.system_status.market_open and not app_state.trading_control.paper_trading: return

    active_exec_count = 0
    for strat_id, strat_info in app_state.strategies.strategy_instances.items():
        if strat_info.is_active and strat_info.instance:
            active_exec_count +=1
            try:
                signal = await strat_info.instance.generate_signal()
                if signal:
                    logger.info(f"Signal from {strat_id}: {signal.get('action')} {signal.get('symbol')} @ {signal.get('price')}")
                    await process_trading_signal(signal, strat_info, app_state, settings)
            except Exception as e: logger.error(f"Error exec strategy {strat_id}: {e}", exc_info=True); strat_info.status_message = f"ERROR_EXEC: {str(e)[:40]}"

    if active_exec_count > 0 and hasattr(app_state.system_status, 'last_strategy_execution_time'):
         app_state.system_status.last_strategy_execution_time = datetime.utcnow()

async def process_trading_signal(signal: Dict[str, Any], strat_info: StrategyInstanceInfo, app_state: AppState, settings: AppSettings):
    logger.debug(f"Processing signal from {signal.get('strategy_name')} for {signal.get('symbol')}")
    signal_id = await store_signal_in_database(signal, app_state)
    if not signal_id: logger.error("Failed to store signal, aborting trade."); return

    if app_state.clients.order_manager:
        order_result = await app_state.clients.order_manager.place_order(order_details=signal, is_paper=app_state.trading_control.paper_trading)
        if order_result and order_result.get("success"):
            logger.info(f"Order for signal {signal_id} placed: {order_result.get('order_id')}, Status: {order_result.get('status')}")
            strat_info.daily_trades += 1
        else: logger.error(f"Order placement failed for signal {signal_id}. Result: {order_result}")
    else: logger.error("OrderManager not found. Cannot process signal.")

async def store_signal_in_database(signal: Dict[str, Any], app_state: AppState) -> Optional[str]:
    signal_id = str(uuid.uuid4())
    if not app_state.clients.db_pool: logger.error("DB pool not available for storing signal."); return None
    try:
        await execute_db_query(
            "INSERT INTO trading_signals (signal_id, strategy_name, symbol, action, price, quantity, order_type, stop_loss, take_profit, quality_score, status, generated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            signal_id, signal.get("strategy_name"), signal["symbol"], signal["action"], signal.get("price"), signal["quantity"], signal.get("order_type"),
            signal.get("stop_loss"), signal.get("take_profit"), signal.get("quality_score"), "GENERATED", datetime.utcnow(),
            json.dumps({"notes": "Signal from autonomous system", "signal_params": signal.get("params")}), # Added signal params to metadata
            db_conn_or_path=app_state.clients.db_pool
        )
        logger.info(f"Trading signal {signal_id} stored.")
        return signal_id
    except Exception as e: logger.error(f"Error storing signal {signal_id}: {e}", exc_info=True); return None

# execute_paper_order helper is removed as its logic is now part of PlaceholderOrderManager.place_order when is_paper=True
