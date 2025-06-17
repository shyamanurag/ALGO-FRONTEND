<file>
      <absolute_file_name>/app/backend/src/core/position_tracker.py</absolute_file_name>
      <# f_and_o_scalping_system/core/position_tracker.py
"""
Position Tracking and Management System
Handles all position lifecycle operations with proper state management
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json

from .models import Position, PositionStatus
from ..events import EventBus, EventType, TradingEvent

logger = logging.getLogger(__name__)

class PositionTracker:
    """
    Centralized position tracking with:
    - Real-time P&L calculation
    - Risk metrics computation
    - Event-driven updates
    - Redis persistence
    """

    def __init__(self, event_bus: EventBus, redis_client=None):
        self.event_bus = event_bus
        self.redis = redis_client
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        
        # Performance metrics
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0
        }
        
        self.capital = 1000000  # Default 10L capital
        self.daily_pnl = 0.0
        self.total_exposure = 0.0
        
        # Subscribe to events
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Set up event handlers for position tracking"""
        try:
            self.event_bus.subscribe(EventType.ORDER_FILLED, self._handle_order_filled)
            self.event_bus.subscribe(EventType.POSITION_UPDATED, self._handle_position_updated)
        except Exception as e:
            logger.warning(f"Event handler setup failed: {e}")

    async def _handle_order_filled(self, event: TradingEvent):
        """Handle order filled events"""
        try:
            order_data = event.data
            await self._update_position_from_order(order_data)
        except Exception as e:
            logger.error(f"Error handling order filled event: {e}")

    async def _handle_position_updated(self, event: TradingEvent):
        """Handle position update events"""
        try:
            position_data = event.data
            await self._update_position_pnl(position_data)
        except Exception as e:
            logger.error(f"Error handling position update event: {e}")

    async def _update_position_from_order(self, order_data: Dict):
        """Update position based on order fill"""
        try:
            symbol = order_data.get('symbol', '')
            quantity = order_data.get('quantity', 0)
            price = order_data.get('price', 0)
            side = order_data.get('side', 'BUY')
            
            position_id = f"{symbol}_{datetime.now().strftime('%Y%m%d')}"
            
            if position_id in self.positions:
                # Update existing position
                position = self.positions[position_id]
                if side == 'BUY':
                    position.quantity += quantity
                else:
                    position.quantity -= quantity
                    
                # Update average price
                total_value = position.average_entry_price * abs(position.quantity) + price * quantity
                position.average_entry_price = total_value / abs(position.quantity) if position.quantity != 0 else 0
            else:
                # Create new position
                position = Position(
                    position_id=position_id,
                    symbol=symbol,
                    quantity=quantity if side == 'BUY' else -quantity,
                    average_entry_price=price,
                    current_price=price,
                    entry_time=datetime.utcnow(),
                    status=PositionStatus.OPEN
                )
                self.positions[position_id] = position
                
            await self._save_position(position)
            
        except Exception as e:
            logger.error(f"Error updating position from order: {e}")

    async def _update_position_pnl(self, market_data: Dict):
        """Update P&L for all positions based on market data"""
        try:
            for position in self.positions.values():
                symbol_base = self._get_symbol_base(position.symbol)
                if symbol_base in market_data:
                    new_price = market_data[symbol_base].get('ltp', position.current_price)
                    position.current_price = new_price
                    
                    # Calculate unrealized P&L
                    price_diff = new_price - position.average_entry_price
                    position.unrealized_pnl = price_diff * position.quantity
                    
                    await self._save_position(position)
                    
        except Exception as e:
            logger.error(f"Error updating position P&L: {e}")

    async def _save_position(self, position: Position):
        """Save position to Redis if available"""
        try:
            if self.redis:
                key = f"position:{position.position_id}"
                position_dict = {
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'average_entry_price': position.average_entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'status': position.status.value,
                    'entry_time': position.entry_time.isoformat()
                }
                await self.redis.hset(key, mapping=position_dict)
        except Exception as e:
            logger.warning(f"Failed to save position to Redis: {e}")

    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
            total_realized = self.metrics['realized_pnl']
            total_pnl = total_unrealized + total_realized
            
            return {
                'unrealized_pnl': total_unrealized,
                'realized_pnl': total_realized,
                'total_pnl': total_pnl,
                'daily_pnl': self.daily_pnl,
                'pnl_percent': (total_pnl / self.capital) * 100 if self.capital > 0 else 0,
                'open_positions': len(self.positions),
                'total_trades': self.metrics['total_trades'],
                'win_rate': self._calculate_win_rate(),
                'winners': self.metrics['winning_trades'],
                'losers': self.metrics['losing_trades']
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'unrealized_pnl': 0,
                'realized_pnl': 0,
                'total_pnl': 0,
                'daily_pnl': 0,
                'pnl_percent': 0,
                'open_positions': 0,
                'total_trades': 0,
                'win_rate': 0,
                'winners': 0,
                'losers': 0
            }

    def get_risk_metrics(self) -> Dict:
        """Calculate current risk metrics"""
        try:
            current_exposure = sum(abs(p.quantity * p.current_price) for p in self.positions.values())
            max_loss = sum(abs(p.unrealized_pnl) for p in self.positions.values() if p.unrealized_pnl < 0)
            
            return {
                'current_exposure': current_exposure,
                'max_potential_loss': max_loss,
                'exposure_percent': (current_exposure / self.capital) * 100 if self.capital > 0 else 0,
                'positions_at_risk': len([p for p in self.positions.values() if p.unrealized_pnl < 0])
            }
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {
                'current_exposure': 0,
                'max_potential_loss': 0,
                'exposure_percent': 0,
                'positions_at_risk': 0
            }

    def _calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        try:
            total_trades = self.metrics['winning_trades'] + self.metrics['losing_trades']
            if total_trades == 0:
                return 0.0
            return (self.metrics['winning_trades'] / total_trades) * 100
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.0

    def _get_symbol_base(self, symbol: str) -> str:
        """Extract base symbol from option symbol"""
        try:
            if 'NIFTY' in symbol and 'BANKNIFTY' not in symbol:
                return 'NIFTY'
            elif 'BANKNIFTY' in symbol:
                return 'BANKNIFTY'
            elif 'FINNIFTY' in symbol:
                return 'FINNIFTY'
            else:
                # Remove numbers and CE/PE
                import re
                return re.sub(r'[0-9]+|CE|PE', '', symbol).strip()
        except Exception as e:
            logger.error(f"Error extracting symbol base: {e}")
            return symbol

    async def close_position(self, position_id: str, exit_price: float) -> bool:
        """Close a position and update metrics"""
        try:
            if position_id not in self.positions:
                return False
                
            position = self.positions[position_id]
            position.status = PositionStatus.CLOSED
            position.current_price = exit_price
            
            # Calculate final P&L
            price_diff = exit_price - position.average_entry_price
            position.realized_pnl = price_diff * position.quantity
            
            # Update metrics
            self.metrics['total_trades'] += 1
            self.metrics['realized_pnl'] += position.realized_pnl
            
            if position.realized_pnl > 0:
                self.metrics['winning_trades'] += 1
            else:
                self.metrics['losing_trades'] += 1
                
            # Move to closed positions
            self.closed_positions.append(position)
            del self.positions[position_id]
            
            # Save to Redis
            await self._save_position(position)
            
            return True
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())

    def get_position_by_symbol(self, symbol: str) -> Optional[Position]:
        """Get position by symbol"""
        for position in self.positions.values():
            if position.symbol == symbol:
                return position
        return None

    async def reset_daily_metrics(self):
        """Reset daily metrics at market open"""
        try:
            self.daily_pnl = 0.0
            self.metrics['total_trades'] = 0
            self.metrics['winning_trades'] = 0
            self.metrics['losing_trades'] = 0
            logger.info("Daily metrics reset successfully")
        except Exception as e:
            logger.error(f"Error resetting daily metrics: {e}")
</content>
    </file>