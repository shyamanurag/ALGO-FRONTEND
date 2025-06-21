from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, HttpUrl
from typing import Optional, Union, Dict, Any, List
from pathlib import Path
from datetime import datetime, time
import logging
import json

class AppSettings(BaseSettings):
    # Application Info
    APP_NAME: str = Field(default="EliteAlgoPlatform", env="APP_NAME")
    APP_VERSION: str = Field(default="2.1.0", env="APP_VERSION")

    # Application Host/Port for Uvicorn
    APP_HOST: str = Field(default="0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(default=8001, env="PORT")

    # Database settings
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./trading_system.db")
    REDIS_URL: Optional[str] = Field(default=None)

    # Zerodha settings
    ZERODHA_API_KEY: Optional[str] = Field(default=None)
    ZERODHA_API_SECRET: Optional[str] = Field(default=None)
    ZERODHA_CLIENT_ID: Optional[str] = Field(default=None)
    ZERODHA_ACCOUNT_NAME: Optional[str] = Field(default=None)
    ZERODHA_REDIRECT_URL: Optional[HttpUrl] = Field(default="http://localhost:8001/api/zerodha/callback") # type: ignore

    # TrueData settings
    TRUEDATA_USERNAME: Optional[str] = Field(default=None, description="TrueData Username")
    TRUEDATA_PASSWORD: Optional[str] = Field(default=None, description="TrueData Password")
    TRUEDATA_APIKEY: Optional[str] = Field(default=None, description="TrueData API Key (optional, depends on service tier)")
    TRUEDATA_WEBSOCKET_URL: str = Field(default="wss://api.truedata.in/websocket", description="Primary WebSocket URL for TrueData connection.")
    TRUEDATA_DEFAULT_SYMBOLS: List[str] = Field(default_factory=lambda: ["NIFTY", "BANKNIFTY"], description="Default symbols to subscribe to on TrueData connect.")

    # Old/Legacy TrueData URL parts - can be deprecated if TRUEDATA_WEBSOCKET_URL is sufficient
    TRUEDATA_URL_LEGACY: str = Field(default="push.truedata.in", description="Legacy base URL/IP for TrueData (if needed, prefer TRUEDATA_WEBSOCKET_URL)")
    TRUEDATA_PORT_LEGACY: int = Field(default=8084, description="Legacy port for TrueData (if needed, prefer TRUEDATA_WEBSOCKET_URL)")

    TRUEDATA_API_URL: str = Field(default="history.truedata.in", description="URL for TrueData Historical API (if used separately)")
    TRUEDATA_API_PORT: int = Field(default=8080, description="Port for TrueData Historical API (if used separately)")
    TRUEDATA_SANDBOX: bool = Field(default=False, description="TrueData Sandbox mode flag")
    TRUEDATA_SYMBOL_MAPPINGS_JSON: Optional[str] = Field(default='{}', description="JSON string for symbol mappings for TrueData")
    # TRUEDATA_WEBSOCKET_URL_OVERRIDE: Optional[HttpUrl] = Field(default=None) # type: ignore # Replaced by TRUEDATA_WEBSOCKET_URL

    # Websocket client behavior settings (can be used by new client if it implements them)
    TRUEDATA_PING_INTERVAL: int = Field(default=20, description="Ping interval for TrueData WebSocket.")
    TRUEDATA_PING_TIMEOUT: int = Field(default=10, description="Ping timeout for TrueData WebSocket.")
    TRUEDATA_CLOSE_TIMEOUT: int = Field(default=10, description="Close timeout for TrueData WebSocket.")
    TRUEDATA_RECONNECT_MAX_ATTEMPTS: int = Field(default=5, description="Max reconnect attempts for TrueData client.") # Increased default
    TRUEDATA_RECONNECT_INITIAL_DELAY: int = Field(default=5, description="Initial delay for TrueData reconnect.")
    TRUEDATA_RECONNECT_MAX_DELAY: int = Field(default=60, description="Max delay for TrueData reconnect.")

    # Trading parameters
    PAPER_TRADING: bool = Field(default=True)
    AUTONOMOUS_TRADING_ENABLED: bool = Field(default=False)
    DATA_PROVIDER_ENABLED: bool = Field(default=True)
    DEFAULT_ORDER_TAG: str = Field(default="EliteAlgo")

    MARKET_OPEN_TIME_STR: str = Field(default="09:15")
    MARKET_CLOSE_TIME_STR: str = Field(default="15:30")
    INTRADAY_CUTOFF_TIME_STR: str = Field(default="15:00")
    DAILY_STOP_LOSS_PERCENT: float = Field(default=2.0)

    # Scheduler intervals
    HEALTH_CHECK_INTERVAL_SECONDS: int = Field(default=60, description="Interval for system health checks in seconds.")
    STRATEGY_LOOP_INTERVAL_SECONDS: int = Field(default=30, description="Interval for main strategy execution loop in seconds.")
    ELITE_SCAN_INTERVAL_SECONDS: int = Field(default=300, description="Interval for scanning elite recommendations in seconds.")
    TRUEDATA_STATE_SYNC_INTERVAL_SECONDS: int = Field(default=10, description="Interval for syncing TrueData global state to app_state in seconds.")
    TIMEZONE: str = Field(default="Asia/Kolkata", description="Timezone for scheduler and potentially other datetime operations.")

    LOG_LEVEL: str = Field(default="INFO")

    PROJECT_ROOT_DIR_STR: str = Field(default=str(Path(__file__).resolve().parent.parent.parent))
    SRC_DIR_PATH_STR: str = Field(default=str(Path(__file__).resolve().parent))
    TRADING_HOLIDAYS_FILE_PATH_STR: Optional[str] = Field(default="trading_holidays.json")

    FRONTEND_URL: Optional[HttpUrl] = Field(default="http://localhost:3000") # type: ignore
    N8N_WEBHOOK_URL: Optional[HttpUrl] = Field(default=None) # type: ignore

    CONFLUENCE_AMPLIFIER_MIN_SIGNALS: int = Field(default=2)
    HARMONIC_PATTERNS_ENABLED: bool = Field(default=True)
    DEFAULT_SMA_PERIOD: int = Field(default=20)
    DEFAULT_NEWS_SENSITIVITY: float = Field(default=0.8)
    DEFAULT_ATR_MULTIPLIER: float = Field(default=2.0)

    DEFAULT_RECONNECT_ATTEMPTS: int = Field(default=3)
    DEFAULT_WEBSOCKET_TIMEOUT_SECONDS: int = Field(default=10) # General WS timeout
    DEFAULT_HTTP_TIMEOUT_SECONDS: int = Field(default=15)

    # WebSocket Manager Settings
    WEBSOCKET_HEARTBEAT_INTERVAL_SECONDS: int = Field(default=30)
    WEBSOCKET_STALE_CONNECTION_SECONDS: int = Field(default=60)
    WEBSOCKET_REDIS_RECONNECT_DELAY_SECONDS: int = Field(default=5)


    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

    @property
    def MARKET_OPEN_TIME(self) -> time:
        try: return datetime.strptime(self.MARKET_OPEN_TIME_STR, "%H:%M").time()
        except ValueError: logging.getLogger(__name__).error(f"Invalid MARKET_OPEN_TIME_STR: {self.MARKET_OPEN_TIME_STR}. Using 09:15."); return time(9, 15)

    @property
    def MARKET_CLOSE_TIME(self) -> time:
        try: return datetime.strptime(self.MARKET_CLOSE_TIME_STR, "%H:%M").time()
        except ValueError: logging.getLogger(__name__).error(f"Invalid MARKET_CLOSE_TIME_STR: {self.MARKET_CLOSE_TIME_STR}. Using 15:30."); return time(15, 30)

    @property
    def INTRADAY_CUTOFF_TIME(self) -> time:
        try: return datetime.strptime(self.INTRADAY_CUTOFF_TIME_STR, "%H:%M").time()
        except ValueError: logging.getLogger(__name__).error(f"Invalid INTRADAY_CUTOFF_TIME_STR: {self.INTRADAY_CUTOFF_TIME_STR}. Using 15:00."); return time(15, 0)

    @property
    def PROJECT_ROOT_DIR(self) -> Path:
        return Path(self.PROJECT_ROOT_DIR_STR)

    @property
    def SRC_DIR(self) -> Path:
        return Path(self.SRC_DIR_PATH_STR)

    @property
    def TRADING_HOLIDAYS_FILE(self) -> Path:
        if not self.TRADING_HOLIDAYS_FILE_PATH_STR:
            default_path = self.PROJECT_ROOT_DIR / "trading_holidays_default.json"
            logging.getLogger(__name__).warning(f"TRADING_HOLIDAYS_FILE_PATH_STR not set. Using default: {default_path}")
            return default_path
        path_obj = Path(self.TRADING_HOLIDAYS_FILE_PATH_STR)
        if path_obj.is_absolute(): return path_obj
        return self.PROJECT_ROOT_DIR / path_obj

    @property
    def PARSED_TRUEDATA_SYMBOL_MAPPINGS(self) -> Dict[str, str]:
        if self.TRUEDATA_SYMBOL_MAPPINGS_JSON and self.TRUEDATA_SYMBOL_MAPPINGS_JSON != '{}':
            try: return json.loads(self.TRUEDATA_SYMBOL_MAPPINGS_JSON)
            except json.JSONDecodeError as e:
                logging.getLogger(__name__).error(f"Failed to parse TRUEDATA_SYMBOL_MAPPINGS_JSON: {e}. Using empty map.")
                return {}
        logger = logging.getLogger(__name__)
        logger.warning("TRUEDATA_SYMBOL_MAPPINGS_JSON not set or empty. Using default placeholder mappings.")
        return {
            '256265': 'NIFTY', '260105': 'BANKNIFTY', '257801': 'FINNIFTY',
            '2885': 'RELIANCE', '11536': 'TCS', '1333': 'HDFCBANK', '1594': 'INFY',
        }

settings = AppSettings()

if __name__ == "__main__":
    try:
        from src.core.logging_config import setup_logging
        setup_logging(log_level=settings.LOG_LEVEL)
    except ImportError:
        logging.basicConfig(level=settings.LOG_LEVEL.upper() if settings.LOG_LEVEL else "INFO",
                            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        logging.warning("Could not import setup_logging from src.core.logging_config for config.py direct execution.")

    logger = logging.getLogger(__name__)
    logger.info("--- Loaded Application Settings (Verification) ---")

    settings_dict = settings.model_dump()
    settings_dict.pop("TRUEDATA_SYMBOL_MAPPINGS_JSON", None)
    settings_dict["PARSED_TRUEDATA_SYMBOL_MAPPINGS"] = settings.PARSED_TRUEDATA_SYMBOL_MAPPINGS
    settings_dict["PROJECT_ROOT_DIR"] = str(settings.PROJECT_ROOT_DIR)
    settings_dict["SRC_DIR"] = str(settings.SRC_DIR)
    settings_dict["TRADING_HOLIDAYS_FILE"] = str(settings.TRADING_HOLIDAYS_FILE)

    for key, value in settings_dict.items():
        if "SECRET" in key.upper() or "PASSWORD" in key.upper() or "API_KEY" in key.upper() or "TOKEN" in key.upper():
            logger.info(f"  {key}: {'********' if value else None}")
        else:
            logger.info(f"  {key}: {value}")

    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"App Version: {settings.APP_VERSION}")
    logger.info(f"Market Open Time (parsed): {settings.MARKET_OPEN_TIME}")
