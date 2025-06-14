"""
Response models for the trading system API
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseResponse):
    """Standard error response"""
    error_code: str
    error_details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseResponse):
    """Paginated response with metadata"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class TradeResponse(BaseResponse):
    """Trade execution response"""
    trade_id: str
    symbol: str
    quantity: float
    price: float
    side: str
    status: str
    execution_time: datetime
    fees: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class PositionResponse(BaseResponse):
    """Position response"""
    data: Optional[List[Dict[str, Any]]] = None

class MarketDataResponse(BaseResponse):
    """Market data response"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_trade: Optional[Dict[str, Any]] = None
    indicators: Optional[Dict[str, Any]] = None

class WebhookResponse(BaseResponse):
    """Webhook processing response"""
    webhook_id: str
    source: str
    event_type: str
    processed_at: datetime
    status: str
    metadata: Optional[Dict[str, Any]] = None

class UserResponse(BaseResponse):
    """User operation response"""
    user_id: str
    username: str
    email: str
    role: str
    status: str
    last_login: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

class HealthResponse(BaseResponse):
    """System health response"""
    version: str
    components: Dict[str, str]
    uptime: float
    memory_usage: float
    cpu_usage: float
    active_connections: int
    last_backup: Optional[datetime] = None

class RiskResponse(BaseResponse):
    """Risk management response"""
    risk_level: str
    exposure: float
    limits: Dict[str, float]
    warnings: List[str]
    actions_taken: List[str]
    metadata: Optional[Dict[str, Any]] = None

class TradingStatusResponse(BaseResponse):
    """Trading status response"""
    pass

class PerformanceMetricsResponse(BaseResponse):
    """Performance metrics response"""
    pass

class StrategyResponse(BaseResponse):
    """Strategy response"""
    pass

class RiskMetricsResponse(BaseResponse):
    """Risk metrics response"""
    pass 