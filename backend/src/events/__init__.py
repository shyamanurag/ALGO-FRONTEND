"""
Event handling system for the ALGO-FRONTEND trading platform.
Provides event bus and event types for decoupled communication between components.
"""

import asyncio
from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for the trading system."""
    
    # Market Data Events
    MARKET_DATA_RECEIVED = "market_data_received"
    MARKET_STATUS_CHANGE = "market_status_change"
    
    # Trading Events  
    ORDER_PLACED = "order_placed"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    
    # Position Events
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    
    # Risk Events
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    MARGIN_CALL = "margin_call"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    
    # Strategy Events
    SIGNAL_GENERATED = "signal_generated"
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"
    
    # Data Events
    DATABASE_CONNECTED = "database_connected"
    DATABASE_DISCONNECTED = "database_disconnected"
    DATA_FEED_CONNECTED = "data_feed_connected"
    DATA_FEED_DISCONNECTED = "data_feed_disconnected"


@dataclass
class TradingEvent:
    """Base event class for all trading system events."""
    
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class EventBus:
    """
    Event bus for handling asynchronous event distribution.
    Allows decoupled communication between trading system components.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._event_history: List[TradingEvent] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()
        
    async def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to specific event type."""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to {event_type.value}")
    
    async def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all events."""
        async with self._lock:
            self._global_subscribers.append(callback)
            logger.debug("Subscribed to all events")
    
    async def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from specific event type."""
        async with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    logger.debug(f"Unsubscribed from {event_type.value}")
                except ValueError:
                    logger.warning(f"Callback not found for {event_type.value}")
    
    async def publish(self, event: TradingEvent) -> None:
        """Publish event to all subscribers."""
        async with self._lock:
            # Add to history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        # Notify specific subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
        
        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in global event callback: {e}")
        
        logger.debug(f"Published event: {event.event_type.value}")
    
    def get_event_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[TradingEvent]:
        """Get event history, optionally filtered by type."""
        if event_type:
            events = [e for e in self._event_history if e.event_type == event_type]
        else:
            events = self._event_history.copy()
        
        return events[-limit:] if limit else events
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.info("Event history cleared")


# Global event bus instance
event_bus = EventBus()


# Convenience functions for common event operations
async def emit_market_data_event(symbol: str, data: Dict[str, Any], source: str = "market_data") -> None:
    """Emit market data received event."""
    event = TradingEvent(
        event_type=EventType.MARKET_DATA_RECEIVED,
        timestamp=datetime.utcnow(),
        data={"symbol": symbol, "market_data": data},
        source=source
    )
    await event_bus.publish(event)


async def emit_order_event(event_type: EventType, order_data: Dict[str, Any], source: str = "order_manager") -> None:
    """Emit order-related event."""
    event = TradingEvent(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        data=order_data,
        source=source
    )
    await event_bus.publish(event)


async def emit_position_event(event_type: EventType, position_data: Dict[str, Any], source: str = "position_tracker") -> None:
    """Emit position-related event."""
    event = TradingEvent(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        data=position_data,
        source=source
    )
    await event_bus.publish(event)


async def emit_risk_event(event_type: EventType, risk_data: Dict[str, Any], source: str = "risk_manager") -> None:
    """Emit risk-related event."""
    event = TradingEvent(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        data=risk_data,
        source=source
    )
    await event_bus.publish(event)


async def emit_system_event(event_type: EventType, system_data: Dict[str, Any], source: str = "system") -> None:
    """Emit system-related event."""
    event = TradingEvent(
        event_type=event_type,
        timestamp=datetime.utcnow(),
        data=system_data,
        source=source
    )
    await event_bus.publish(event)