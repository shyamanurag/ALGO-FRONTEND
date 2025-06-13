"""
Momentum Breakout Strategy
Trades breakouts with momentum confirmation
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass

from ..core.trade_engine import TradeSignal
from ..core.market_data import MarketDataManager

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """Strategy configuration"""
    lookback_period: int = 20  # Lookback period for breakout
    momentum_period: int = 10  # Period for momentum calculation
    volume_threshold: float = 1.5  # Volume threshold multiplier
    atr_period: int = 14  # ATR period for stop loss
    risk_reward: float = 2.0  # Risk:Reward ratio
    max_positions: int = 5  # Maximum concurrent positions

class MomentumBreakoutStrategy:
    """Momentum breakout trading strategy"""
    
    def __init__(self, 
                 market_data: MarketDataManager,
                 config: Optional[StrategyConfig] = None):
        self.market_data = market_data
        self.config = config or StrategyConfig()
        self.symbols = []  # Will be set when strategy is added
        self.positions = {}  # Track active positions
        
    async def generate_signals(self, data: Dict[str, pd.DataFrame]) -> List[TradeSignal]:
        """Generate trading signals"""
        signals = []
        
        for symbol, df in data.items():
            try:
                # Skip if already in position
                if symbol in self.positions:
                    continue
                    
                # Calculate indicators
                df['sma'] = df['close'].rolling(self.config.lookback_period).mean()
                df['momentum'] = df['close'].pct_change(self.config.momentum_period)
                df['volume_ma'] = df['volume'].rolling(self.config.lookback_period).mean()
                df['atr'] = self._calculate_atr(df)
                
                # Get latest values
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Check for breakout
                if (latest['close'] > latest['sma'] and  # Price above SMA
                    prev['close'] <= prev['sma'] and  # Previous close below SMA
                    latest['volume'] > latest['volume_ma'] * self.config.volume_threshold and  # Volume confirmation
                    latest['momentum'] > 0):  # Positive momentum
                    
                    # Calculate position size
                    quantity = self._calculate_position_size(
                        price=latest['close'],
                        atr=latest['atr']
                    )
                    
                    # Calculate stop loss and target
                    stop_loss = latest['close'] - (latest['atr'] * 2)
                    target = latest['close'] + (latest['atr'] * 2 * self.config.risk_reward)
                    
                    # Create signal
                    signal = TradeSignal(
                        symbol=symbol,
                        direction='BUY',
                        quantity=quantity,
                        entry_price=latest['close'],
                        stop_loss=stop_loss,
                        target=target,
                        strategy_id='momentum_breakout',
                        metadata={
                            'breakout_price': latest['close'],
                            'momentum': latest['momentum'],
                            'volume_ratio': latest['volume'] / latest['volume_ma'],
                            'atr': latest['atr']
                        }
                    )
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
                
        return signals
        
    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(self.config.atr_period).mean()
        
        return atr
        
    def _calculate_position_size(self, price: float, atr: float) -> int:
        """Calculate position size based on risk"""
        # This is a simplified calculation
        # In production, you'd want to consider:
        # - Account size
        # - Risk per trade
        # - Maximum position size
        # - Available margin
        risk_per_trade = 1000  # $1000 risk per trade
        position_size = risk_per_trade / (atr * 2)  # 2 ATR stop loss
        return int(position_size)
        
    async def on_position_update(self, position: Dict[str, Any]):
        """Handle position updates"""
        symbol = position['symbol']
        if position['quantity'] == 0:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = position 