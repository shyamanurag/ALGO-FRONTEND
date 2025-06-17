# Event System Package
from .event_bus import EventBus
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime

class EventType(Enum):
    # Order Events
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    
    # Position Events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    
    # Risk Events
    RISK_ALERT = "risk_alert"
    RISK_VIOLATION = "risk_violation"
    
    # Market Events
    MARKET_DATA_UPDATE = "market_data_update"
    MARKET_OPENED = "market_opened"
    MARKET_CLOSED = "market_closed"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"

@dataclass
class TradingEvent:
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "system"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

__all__ = ['EventBus', 'EventType', 'TradingEvent']
