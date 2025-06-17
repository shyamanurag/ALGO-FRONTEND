# Trading system constants
"""
System-wide constants for the trading platform
"""

# Market timing
MARKET_OPEN_TIME = "09:15:00"
MARKET_CLOSE_TIME = "15:30:00"
PRE_MARKET_START = "09:00:00"
POST_MARKET_END = "15:45:00"

# Option types
CALL = "CE"
PUT = "PE"

# Order types
MARKET = "MARKET"
LIMIT = "LIMIT"
SL = "SL"
SL_M = "SL-M"

class OrderTypes:
    """Order type constants"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"
    STOP_LOSS = "SL"
    STOP_LOSS_MARKET = "SL-M"

# Transaction types
BUY = "BUY"
SELL = "SELL"

# Order status
PENDING = "PENDING"
OPEN = "OPEN"
COMPLETE = "COMPLETE"
CANCELLED = "CANCELLED"
REJECTED = "REJECTED"

class OrderStatus:
    """Order status constants"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    FILLED = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

# Exchanges
NSE = "NSE"
BSE = "BSE"
NFO = "NFO"
BFO = "BFO"

# Symbol mappings
LOT_SIZES = {
    'NIFTY': 50,
    'BANKNIFTY': 25,
    'FINNIFTY': 40,
    'MIDCPNIFTY': 75,
    'SENSEX': 10,
    'BANKEX': 15
}

# Strike increments
STRIKE_INCREMENTS = {
    'NIFTY': 50,
    'BANKNIFTY': 100,
    'FINNIFTY': 50,
    'MIDCPNIFTY': 25,
    'SENSEX': 100,
    'BANKEX': 100
}

# Time intervals
TIMEFRAMES = {
    '1m': 60,
    '3m': 180,
    '5m': 300,
    '15m': 900,
    '1h': 3600,
    '1d': 86400
}

# API endpoints (placeholders)
ZERODHA_BASE_URL = "https://api.kite.trade"
TRUEDATA_BASE_URL = "wss://push.truedata.in:8084"

# Risk management
MAX_POSITION_SIZE = 0.1  # 10% of capital per position
MAX_DAILY_LOSS = 0.02    # 2% daily loss limit
MAX_DRAWDOWN = 0.05      # 5% maximum drawdown

# Strategy parameters
DEFAULT_SIGNAL_COOLDOWN = 300  # 5 minutes
DEFAULT_POSITION_TIMEOUT = 7200  # 2 hours

# Database constants
MAX_RETRIES = 3
CONNECTION_TIMEOUT = 30
QUERY_TIMEOUT = 60

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}