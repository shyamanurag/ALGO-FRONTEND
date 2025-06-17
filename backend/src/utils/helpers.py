# Helper utilities for trading system
"""
Common helper functions for the trading system
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator to retry function calls with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {e}")
                    await asyncio.sleep(wait_time)
            return None
        return wrapper
    return decorator

def get_atm_strike(spot_price: float, base: int = 50) -> float:
    """Get At-The-Money strike price"""
    return round(spot_price / base) * base

def get_strike_with_offset(spot_price: float, offset: int, base: int = 50) -> float:
    """Get strike price with offset from ATM"""
    atm = get_atm_strike(spot_price, base)
    return atm + (offset * base)

def format_symbol_for_broker(symbol: str, strike: float = None, option_type: str = None, expiry: str = None) -> str:
    """Format symbol for broker API"""
    if strike and option_type and expiry:
        return f"{symbol}{expiry}{int(strike)}{option_type}"
    return symbol

def calculate_option_lot_size(symbol: str) -> int:
    """Get lot size for options"""
    lot_sizes = {
        'NIFTY': 50,
        'BANKNIFTY': 25,
        'FINNIFTY': 40
    }
    return lot_sizes.get(symbol, 50)

def is_market_hours() -> bool:
    """Check if market is currently open"""
    now = datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    return market_open <= now <= market_close

def calculate_technical_indicators(data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate basic technical indicators"""
    return {
        'rsi': 50.0,  # Placeholder
        'macd': 0.0,  # Placeholder
        'bollinger_upper': 0.0,  # Placeholder
        'bollinger_lower': 0.0,  # Placeholder
    }