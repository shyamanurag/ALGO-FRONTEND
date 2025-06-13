"""
Trading Utility Functions
Essential helper functions for trading operations
"""

import math
from decimal import Decimal
from typing import Optional


def get_atm_strike(price: float, strike_interval: int = 50) -> float:
    """
    Get at-the-money strike price
    
    Args:
        price: Current market price
        strike_interval: Strike price interval (default 50 for NIFTY)
    
    Returns:
        Rounded ATM strike price
    """
    return round(price / strike_interval) * strike_interval


def get_strike_with_offset(price: float, offset: int, strike_interval: int = 50) -> float:
    """
    Get strike price with offset from ATM
    
    Args:
        price: Current market price  
        offset: Number of strikes away from ATM (positive for higher, negative for lower)
        strike_interval: Strike price interval
        
    Returns:
        Strike price with offset
    """
    atm_strike = get_atm_strike(price, strike_interval)
    return atm_strike + (offset * strike_interval)


def round_price_to_tick(price: float, tick_size: float = 0.05) -> float:
    """
    Round price to nearest tick size
    
    Args:
        price: Price to round
        tick_size: Minimum price movement
        
    Returns:
        Price rounded to tick size
    """
    return round(price / tick_size) * tick_size


def to_decimal(value, precision: int = 2) -> Decimal:
    """
    Convert value to Decimal with specified precision
    
    Args:
        value: Value to convert
        precision: Number of decimal places
        
    Returns:
        Decimal value
    """
    if isinstance(value, str):
        return Decimal(value).quantize(Decimal('0.01'))
    return Decimal(str(round(float(value), precision)))


def calculate_position_size(
    capital: float, 
    risk_percent: float, 
    entry_price: float, 
    stop_loss: float
) -> int:
    """
    Calculate position size based on risk management
    
    Args:
        capital: Available capital
        risk_percent: Risk percentage (e.g., 1 for 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        
    Returns:
        Position size in lots/quantity
    """
    risk_amount = capital * (risk_percent / 100)
    price_risk = abs(entry_price - stop_loss)
    
    if price_risk == 0:
        return 0
        
    position_size = risk_amount / price_risk
    return max(1, int(position_size))


def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss: float, 
    target_price: float
) -> float:
    """
    Calculate risk-reward ratio
    
    Args:
        entry_price: Entry price
        stop_loss: Stop loss price
        target_price: Target price
        
    Returns:
        Risk-reward ratio
    """
    risk = abs(entry_price - stop_loss)
    reward = abs(target_price - entry_price)
    
    if risk == 0:
        return 0
        
    return reward / risk


def get_option_symbol(
    underlying: str,
    expiry_date: str,
    strike: float,
    option_type: str
) -> str:
    """
    Generate option symbol
    
    Args:
        underlying: Underlying symbol (e.g., NIFTY)
        expiry_date: Expiry date in YYMMDD format
        strike: Strike price
        option_type: CE or PE
        
    Returns:
        Option symbol
    """
    return f"{underlying}{expiry_date}{int(strike)}{option_type}"


def is_market_hours() -> bool:
    """
    Check if market is open (simplified version)
    
    Returns:
        True if market hours, False otherwise
    """
    from datetime import datetime, time
    
    now = datetime.now().time()
    market_open = time(9, 15)  # 9:15 AM
    market_close = time(15, 30)  # 3:30 PM
    
    return market_open <= now <= market_close


def calculate_implied_volatility_simple(
    option_price: float,
    underlying_price: float,
    strike: float,
    time_to_expiry: float
) -> float:
    """
    Simplified implied volatility calculation
    
    Args:
        option_price: Current option price
        underlying_price: Current underlying price
        strike: Strike price
        time_to_expiry: Time to expiry in years
        
    Returns:
        Estimated implied volatility
    """
    # Simplified calculation - in production use Black-Scholes
    intrinsic_value = max(0, underlying_price - strike)
    time_value = option_price - intrinsic_value
    
    if time_value <= 0 or time_to_expiry <= 0:
        return 0.15  # Default 15% volatility
        
    # Rough approximation
    iv = (time_value / underlying_price) / math.sqrt(time_to_expiry)
    return max(0.05, min(2.0, iv))  # Clamp between 5% and 200%


# Export all utility functions
__all__ = [
    'get_atm_strike',
    'get_strike_with_offset', 
    'round_price_to_tick',
    'to_decimal',
    'calculate_position_size',
    'calculate_risk_reward_ratio',
    'get_option_symbol',
    'is_market_hours',
    'calculate_implied_volatility_simple'
]