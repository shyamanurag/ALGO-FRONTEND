"""
Volatility Explosion Strategy - Clean Implementation
Captures sudden volatility breakouts with volume confirmation
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class VolatilityState:
    """Volatility tracking state"""
    baseline_volatility: float = 0.0
    current_volatility: float = 0.0
    volatility_percentile: float = 50.0
    explosion_detected: bool = False
    explosion_start_time: Optional[datetime] = None
    volume_confirmation: bool = False
    direction: str = "NEUTRAL"
    
    def reset(self):
        """Reset volatility state"""
        self.explosion_detected = False
        self.explosion_start_time = None
        self.volume_confirmation = False
        self.direction = "NEUTRAL"

class VolatilityExplosion:
    """
    Volatility Explosion Strategy
    Detects and trades sudden volatility spikes with volume confirmation
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = "VolatilityExplosion"
        self.is_enabled = True
        self.allocation = 0.12
        
        # Strategy parameters
        self.volatility_lookback = self.config.get('volatility_lookback', 30)
        self.explosion_threshold = self.config.get('explosion_threshold', 2.5)  # 2.5x baseline
        self.volume_confirmation_ratio = self.config.get('volume_confirmation_ratio', 2.0)
        self.min_baseline_volatility = self.config.get('min_baseline_volatility', 0.005)  # 0.5%
        self.profit_target_percent = self.config.get('profit_target', 1.2)
        self.stop_loss_percent = self.config.get('stop_loss', 0.8)
        self.explosion_window_minutes = self.config.get('explosion_window_minutes', 15)
        
        # State tracking
        self.volatility_states = {}
        self.last_analysis_time = {}
        
        logger.info(f"VolatilityExplosion initialized with config: {self.config}")
    
    async def analyze(self, symbol: str, price_data: List[float], volume_data: List[float], 
                     current_time: datetime) -> Optional[Dict]:
        """
        Analyze for volatility explosion opportunities
        """
        try:
            if len(price_data) < self.volatility_lookback + 10 or len(volume_data) < self.volatility_lookback + 10:
                return None
            
            # Check trading hours
            if not self._is_trading_hours():
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame({
                'close': price_data,
                'volume': volume_data
            })
            df.index = pd.date_range(end=current_time, periods=len(df), freq='1min')
            
            # Calculate returns
            df['returns'] = df['close'].pct_change()
            
            # Get or create volatility state
            if symbol not in self.volatility_states:
                self.volatility_states[symbol] = VolatilityState()
            
            state = self.volatility_states[symbol]
            
            # Update volatility measurements
            self._update_volatility_state(df, state)
            
            # Check for volatility explosion
            explosion_signal = self._detect_volatility_explosion(df, state, current_time)
            
            if explosion_signal:
                self.last_analysis_time[symbol] = current_time
                logger.info(f"Volatility explosion detected for {symbol}: {explosion_signal}")
            
            return explosion_signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _update_volatility_state(self, df: pd.DataFrame, state: VolatilityState):
        """Update volatility state measurements"""
        try:
            # Calculate baseline volatility (rolling window)
            baseline_window = df['returns'].tail(self.volatility_lookback).dropna()
            if len(baseline_window) > 0:
                state.baseline_volatility = baseline_window.std()
            
            # Calculate current volatility (recent 5 periods)
            current_window = df['returns'].tail(5).dropna()
            if len(current_window) > 0:
                state.current_volatility = current_window.std()
            
            # Calculate volatility percentile
            all_volatilities = df['returns'].rolling(5).std().dropna()
            if len(all_volatilities) > 0:
                current_vol = state.current_volatility
                percentile = (all_volatilities < current_vol).mean() * 100
                state.volatility_percentile = percentile
            
        except Exception as e:
            logger.error(f"Error updating volatility state: {e}")
    
    def _detect_volatility_explosion(self, df: pd.DataFrame, state: VolatilityState, 
                                   current_time: datetime) -> Optional[Dict]:
        """Detect volatility explosion with volume confirmation"""
        try:
            # Check if baseline volatility is meaningful
            if state.baseline_volatility < self.min_baseline_volatility:
                return None
            
            # Check for volatility explosion
            if state.current_volatility > (state.baseline_volatility * self.explosion_threshold):
                
                # Check volume confirmation
                volume_confirmed = self._check_volume_confirmation(df)
                state.volume_confirmation = volume_confirmed
                
                if not volume_confirmed:
                    return None
                
                # Determine direction based on recent price movement
                recent_price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
                
                if recent_price_change > 0.002:  # 0.2% up
                    state.direction = "BULLISH"
                elif recent_price_change < -0.002:  # 0.2% down
                    state.direction = "BEARISH"
                else:
                    return None  # No clear direction
                
                # Mark explosion detected
                if not state.explosion_detected:
                    state.explosion_detected = True
                    state.explosion_start_time = current_time
                
                # Create signal
                signal = self._create_volatility_signal(df, state, current_time)
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting volatility explosion: {e}")
            return None
    
    def _check_volume_confirmation(self, df: pd.DataFrame) -> bool:
        """Check for volume confirmation of volatility explosion"""
        try:
            # Current volume
            current_volume = df['volume'].iloc[-1]
            
            # Average volume baseline
            avg_volume = df['volume'].tail(20).mean()
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                return volume_ratio >= self.volume_confirmation_ratio
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return False
    
    def _create_volatility_signal(self, df: pd.DataFrame, state: VolatilityState, 
                                 current_time: datetime) -> Optional[Dict]:
        """Create volatility explosion signal"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Determine option type based on direction
            if state.direction == "BULLISH":
                option_type = "CALL"
                signal_direction = "BUY"
            elif state.direction == "BEARISH":
                option_type = "PUT"
                signal_direction = "SELL"
            else:
                return None
            
            # Calculate quality score
            quality_score = self._calculate_explosion_quality_score(df, state)
            
            # Calculate position sizing
            quantity = self._calculate_quantity(df['close'].iloc[0], current_price)  # Pass symbol approximation
            
            signal = {
                'signal': signal_direction,
                'symbol': 'UNKNOWN',  # Will be set by caller
                'option_type': option_type,
                'strike': self._get_atm_strike(current_price),
                'quality_score': quality_score,
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss_percent': self.stop_loss_percent,
                'profit_target_percent': self.profit_target_percent,
                'setup_type': "VOLATILITY_EXPLOSION",
                'explosion_ratio': state.current_volatility / state.baseline_volatility if state.baseline_volatility > 0 else 0,
                'volatility_percentile': state.volatility_percentile,
                'volume_confirmation': state.volume_confirmation,
                'direction': state.direction,
                'baseline_volatility': state.baseline_volatility,
                'current_volatility': state.current_volatility,
                'timestamp': current_time,
                'strategy': self.name
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating volatility signal: {e}")
            return None
    
    def _calculate_explosion_quality_score(self, df: pd.DataFrame, state: VolatilityState) -> float:
        """Calculate volatility explosion quality score"""
        try:
            base_score = 6.0
            
            # Volatility explosion strength bonus
            if state.baseline_volatility > 0:
                explosion_ratio = state.current_volatility / state.baseline_volatility
                if explosion_ratio > 4.0:
                    base_score += 2.0
                elif explosion_ratio > 3.0:
                    base_score += 1.5
                elif explosion_ratio > 2.5:
                    base_score += 1.0
            
            # Volatility percentile bonus
            if state.volatility_percentile > 95:
                base_score += 1.5
            elif state.volatility_percentile > 90:
                base_score += 1.0
            elif state.volatility_percentile > 80:
                base_score += 0.5
            
            # Volume confirmation bonus
            if state.volume_confirmation:
                base_score += 1.0
            
            # Direction clarity bonus
            recent_change = abs((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5])
            if recent_change > 0.01:  # 1% move
                base_score += 1.0
            elif recent_change > 0.005:  # 0.5% move
                base_score += 0.5
            
            return min(base_score, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 6.0
    
    def _get_atm_strike(self, price: float) -> float:
        """Get at-the-money strike price"""
        return round(price / 50) * 50  # Round to nearest 50
    
    def _calculate_quantity(self, symbol_proxy: float, price: float) -> int:
        """Calculate position quantity"""
        try:
            # Default lot sizes (approximation based on price)
            if price > 40000:  # Likely BANKNIFTY
                base_lot_size = 25
            elif price > 15000:  # Likely NIFTY
                base_lot_size = 50
            else:  # Likely FINNIFTY or others
                base_lot_size = 40
            
            # Calculate based on allocation
            capital = 500000  # Default capital
            allocation_amount = capital * self.allocation
            estimated_premium = price * 0.015  # Higher premium for volatility trades
            
            lots = max(1, int(allocation_amount / (estimated_premium * base_lot_size)))
            return lots * base_lot_size
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 50
    
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours"""
        current_time = datetime.now().time()
        return time(9, 15) <= current_time <= time(15, 30)
    
    def get_strategy_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        active_explosions = sum(1 for state in self.volatility_states.values() if state.explosion_detected)
        
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'allocation': self.allocation,
            'active_symbols': len(self.volatility_states),
            'active_explosions': active_explosions,
            'parameters': {
                'explosion_threshold': self.explosion_threshold,
                'volume_confirmation_ratio': self.volume_confirmation_ratio,
                'profit_target': self.profit_target_percent,
                'stop_loss': self.stop_loss_percent,
                'volatility_lookback': self.volatility_lookback
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if strategy is healthy"""
        return self.is_enabled and len(self.volatility_states) >= 0
