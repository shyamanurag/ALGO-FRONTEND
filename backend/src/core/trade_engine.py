"""
Trade Engine
Handles trading logic and strategy execution
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio
from dataclasses import dataclass
import pandas as pd

from .zerodha import ZerodhaIntegration
from .risk_manager import RiskManager
from .position_manager import PositionManager
from .market_data import MarketDataManager
from .config import settings

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Trading signal from strategy"""
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    strategy_id: str
    metadata: Dict[str, Any]

class TradeEngine:
    """Main trading engine that executes strategies"""
    
    def __init__(self, 
                 broker: ZerodhaIntegration,
                 risk_manager: RiskManager,
                 position_manager: PositionManager,
                 market_data: MarketDataManager):
        self.broker = broker
        self.risk_manager = risk_manager
        self.position_manager = position_manager
        self.market_data = market_data
        self.active_strategies: Dict[str, Any] = {}
        self.trade_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Start the trade engine"""
        try:
            self.is_running = True
            # Start market data processing
            await self.market_data.start()
            # Start trade processing
            asyncio.create_task(self._process_trades())
            # Start strategy monitoring
            asyncio.create_task(self._monitor_strategies())
            logger.info("Trade engine started successfully")
        except Exception as e:
            logger.error(f"Failed to start trade engine: {e}")
            raise
            
    async def stop(self):
        """Stop the trade engine"""
        try:
            self.is_running = False
            # Stop market data
            await self.market_data.stop()
            # Close all positions if configured
            if settings.ZERODHA.CLOSE_POSITIONS_ON_STOP:
                await self._close_all_positions()
            logger.info("Trade engine stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping trade engine: {e}")
            raise
            
    async def add_strategy(self, strategy_id: str, strategy: Any):
        """Add a trading strategy"""
        try:
            if strategy_id in self.active_strategies:
                raise ValueError(f"Strategy {strategy_id} already exists")
            self.active_strategies[strategy_id] = strategy
            # Subscribe to market data
            await self.market_data.subscribe(strategy.symbols)
            logger.info(f"Strategy {strategy_id} added successfully")
        except Exception as e:
            logger.error(f"Failed to add strategy {strategy_id}: {e}")
            raise
            
    async def remove_strategy(self, strategy_id: str):
        """Remove a trading strategy"""
        try:
            if strategy_id not in self.active_strategies:
                raise ValueError(f"Strategy {strategy_id} not found")
            strategy = self.active_strategies.pop(strategy_id)
            # Unsubscribe from market data
            await self.market_data.unsubscribe(strategy.symbols)
            logger.info(f"Strategy {strategy_id} removed successfully")
        except Exception as e:
            logger.error(f"Failed to remove strategy {strategy_id}: {e}")
            raise
            
    async def _process_trades(self):
        """Process trade signals from strategies"""
        while self.is_running:
            try:
                # Get signal from queue
                signal: TradeSignal = await self.trade_queue.get()
                
                # Check risk limits
                if not await self.risk_manager.check_trade_allowed(signal):
                    logger.warning(f"Trade rejected by risk manager: {signal}")
                    continue
                    
                # Execute trade
                order = await self.broker.place_order(
                    symbol=signal.symbol,
                    quantity=signal.quantity,
                    transaction_type=signal.direction,
                    order_type='MARKET',
                    price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    target=signal.target
                )
                
                # Update position
                await self.position_manager.update_position(
                    order_id=order['order_id'],
                    strategy_id=signal.strategy_id,
                    metadata=signal.metadata
                )
                
                logger.info(f"Trade executed: {order}")
                
            except Exception as e:
                logger.error(f"Error processing trade: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
                
    async def _monitor_strategies(self):
        """Monitor and execute strategies"""
        while self.is_running:
            try:
                for strategy_id, strategy in self.active_strategies.items():
                    # Get market data
                    data = await self.market_data.get_latest_data(strategy.symbols)
                    if not data:
                        continue
                        
                    # Generate signals
                    signals = await strategy.generate_signals(data)
                    if not signals:
                        continue
                        
                    # Queue signals for processing
                    for signal in signals:
                        await self.trade_queue.put(signal)
                        
                await asyncio.sleep(1)  # Prevent tight loop
                
            except Exception as e:
                logger.error(f"Error monitoring strategies: {e}")
                await asyncio.sleep(1)
                
    async def _close_all_positions(self):
        """Close all open positions"""
        try:
            positions = await self.position_manager.get_all_positions()
            for position in positions:
                await self.broker.place_order(
                    symbol=position['symbol'],
                    quantity=position['quantity'],
                    transaction_type='SELL' if position['quantity'] > 0 else 'BUY',
                    order_type='MARKET'
                )
            logger.info("All positions closed successfully")
        except Exception as e:
            logger.error(f"Error closing positions: {e}")
            raise 