# Core Exceptions for Trading System
"""
Custom exceptions for the trading system
"""

class TradingSystemException(Exception):
    """Base exception for trading system"""
    pass

class OrderException(TradingSystemException):
    """Exception for order-related errors"""
    pass

class OrderError(OrderException):
    """Alias for OrderException"""
    pass

class PositionException(TradingSystemException):
    """Exception for position-related errors"""
    pass

class RiskException(TradingSystemException):
    """Exception for risk management errors"""
    pass

class DataException(TradingSystemException):
    """Exception for data-related errors"""
    pass

class StrategyException(TradingSystemException):
    """Exception for strategy-related errors"""
    pass

class BrokerException(TradingSystemException):
    """Exception for broker-related errors"""
    pass