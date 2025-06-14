"""
Enhanced Momentum Surfer Strategy - Clean Implementation
Sophisticated momentum detection with VWAP, ADX, and RSI confluence
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
class MomentumState:
    """Enhanced momentum state tracking"""
    trend_direction: str = "NEUTRAL"
    trend_strength: float = 0.0
    consecutive_signals: int = 0
    last_signal_time: Optional[datetime] = None
    vwap_position: str = "NEUTRAL"
    adx_reading: float = 0.0
    rsi_reading: float = 50.0
    volume_confirmation: bool = False
    
    def reset(self):
        """Reset momentum state"""
        self.trend_direction = "NEUTRAL"
        self.trend_strength = 0.0
        self.consecutive_signals = 0
        self.last_signal_time = None
        self.vwap_position = "NEUTRAL"
        self.volume_confirmation = False

class MomentumSurfer:
    """
    Enhanced momentum strategy with sophisticated signal generation
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = "MomentumSurfer"
        self.is_enabled = True
        self.allocation = 0.15
        
        # Strategy parameters
        self.vwap_bands_width = self.config.get('vwap_bands_width', 0.002)
        self.adx_threshold = self.config.get('adx_threshold', 25.0)
        self.adx_period = self.config.get('adx_period', 14)
        self.rsi_period = self.config.get('rsi_period', 14)
        self.volume_threshold = self.config.get('volume_threshold', 1.5)
        self.min_expected_move_points = self.config.get('min_expected_move', 30)
        self.profit_target_percent = self.config.get('profit_target', 0.8)
        self.stop_loss_percent = self.config.get('stop_loss', 0.6)
        
        # State tracking
        self.momentum_states = {}
        self.last_analysis_time = {}
        
        logger.info(f"MomentumSurfer initialized with config: {self.config}")
    
    async def analyze(self, symbol: str, price_data: List[float], volume_data: List[float], 
                     current_time: datetime) -> Optional[Dict]:
        """
        Analyze symbol for momentum opportunities
        """
        try:
            if len(price_data) < 50 or len(volume_data) < 50:
                return None
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame({
                'close': price_data,
                'volume': volume_data
            })
            df.index = pd.date_range(end=current_time, periods=len(df), freq='1min')
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(df)
            
            # Get or create momentum state
            if symbol not in self.momentum_states:
                self.momentum_states[symbol] = MomentumState()
            
            state = self.momentum_states[symbol]
            
            # Check trading hours
            if not self._is_trading_hours():
                return None
            
            # Check cooldown
            if not self._check_cooldown(symbol, current_time):
                return None
            
            # Analyze momentum setup
            signal = self._analyze_momentum_setup(symbol, df, indicators, state, current_time)
            
            if signal:
                self.last_analysis_time[symbol] = current_time
                logger.info(f"Momentum signal generated for {symbol}: {signal}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all required technical indicators"""
        try:
            indicators = {}
            
            # VWAP calculation
            typical_price = df['close']  # Simplified VWAP using close prices
            vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
            indicators['vwap'] = vwap.iloc[-1]
            
            # VWAP bands
            vwap_std = typical_price.rolling(20).std().iloc[-1]
            indicators['vwap_upper'] = indicators['vwap'] + (vwap_std * 2)
            indicators['vwap_lower'] = indicators['vwap'] - (vwap_std * 2)
            
            # ADX (simplified calculation)
            high_low = abs(df['close'].diff())
            tr = high_low.rolling(14).mean()
            plus_dm = df['close'].diff().clip(lower=0).rolling(14).mean()
            minus_dm = (-df['close'].diff()).clip(lower=0).rolling(14).mean()
            
            plus_di = 100 * (plus_dm / tr)
            minus_di = 100 * (minus_dm / tr)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(14).mean()
            indicators['adx'] = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 20
            
            # RSI calculation
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
            
            # Volume analysis
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            indicators['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price position relative to VWAP
            current_price = df['close'].iloc[-1]
            indicators['price_vs_vwap'] = (current_price - indicators['vwap']) / indicators['vwap']
            
            # Momentum strength
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
            indicators['momentum_strength'] = abs(price_change) * 100
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _analyze_momentum_setup(self, symbol: str, df: pd.DataFrame, indicators: Dict, 
                               state: MomentumState, current_time: datetime) -> Optional[Dict]:
        """Analyze for momentum trading setup"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Update state with current readings
            state.adx_reading = indicators.get('adx', 20)
            state.rsi_reading = indicators.get('rsi', 50)
            
            # Check ADX strength requirement
            if state.adx_reading < self.adx_threshold:
                return None
            
            # Check volume confirmation
            volume_ratio = indicators.get('volume_ratio', 1)
            state.volume_confirmation = volume_ratio >= self.volume_threshold
            
            if not state.volume_confirmation:
                return None
            
            # Determine VWAP position
            price_vs_vwap = indicators.get('price_vs_vwap', 0)
            if price_vs_vwap > 0.001:  # 0.1% above VWAP
                state.vwap_position = "ABOVE"
            elif price_vs_vwap < -0.001:  # 0.1% below VWAP
                state.vwap_position = "BELOW"
            else:
                state.vwap_position = "NEUTRAL"
            
            # Generate signals based on confluence
            signal = None
            
            # Bullish momentum setup
            if (state.vwap_position == "ABOVE" and 
                state.rsi_reading > 55 and state.rsi_reading < 75 and
                indicators.get('momentum_strength', 0) > 0.2):
                
                signal = self._create_momentum_signal(
                    symbol, "CALL", current_price, indicators, "BULLISH_MOMENTUM", current_time
                )
            
            # Bearish momentum setup
            elif (state.vwap_position == "BELOW" and 
                  state.rsi_reading < 45 and state.rsi_reading > 25 and
                  indicators.get('momentum_strength', 0) > 0.2):
                
                signal = self._create_momentum_signal(
                    symbol, "PUT", current_price, indicators, "BEARISH_MOMENTUM", current_time
                )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing momentum setup: {e}")
            return None
    
    def _create_momentum_signal(self, symbol: str, option_type: str, current_price: float,
                               indicators: Dict, setup_type: str, current_time: datetime) -> Dict:
        """Create momentum trading signal"""
        try:
            # Calculate strike price
            if option_type == "CALL":
                strike = self._get_atm_strike(current_price)
            else:  # PUT
                strike = self._get_atm_strike(current_price)
            
            # Calculate quality score based on confluence
            quality_score = self._calculate_quality_score(indicators, setup_type)
            
            # Calculate position sizing
            quantity = self._calculate_quantity(symbol, current_price)
            
            signal = {
                'signal': 'BUY' if option_type == 'CALL' else 'SELL',
                'symbol': symbol,
                'option_type': option_type,
                'strike': strike,
                'quality_score': quality_score,
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss_percent': self.stop_loss_percent,
                'profit_target_percent': self.profit_target_percent,
                'setup_type': setup_type,
                'indicators': {
                    'adx': indicators.get('adx', 0),
                    'rsi': indicators.get('rsi', 50),
                    'volume_ratio': indicators.get('volume_ratio', 1),
                    'vwap': indicators.get('vwap', current_price),
                    'momentum_strength': indicators.get('momentum_strength', 0)
                },
                'timestamp': current_time,
                'strategy': self.name
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating momentum signal: {e}")
            return None
    
    def _calculate_quality_score(self, indicators: Dict, setup_type: str) -> float:
        """Calculate signal quality score (1-10)"""
        try:
            base_score = 5.0
            
            # ADX strength bonus
            adx = indicators.get('adx', 20)
            if adx > 30:
                base_score += 1.0
            if adx > 40:
                base_score += 0.5
            
            # Volume confirmation bonus
            volume_ratio = indicators.get('volume_ratio', 1)
            if volume_ratio > 2.0:
                base_score += 1.0
            elif volume_ratio > 1.5:
                base_score += 0.5
            
            # Momentum strength bonus
            momentum = indicators.get('momentum_strength', 0)
            if momentum > 0.5:
                base_score += 1.0
            elif momentum > 0.3:
                base_score += 0.5
            
            # RSI positioning bonus
            rsi = indicators.get('rsi', 50)
            if 45 <= rsi <= 75:  # Good range for momentum
                base_score += 0.5
            
            return min(base_score, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 5.0
    
    def _get_atm_strike(self, price: float) -> float:
        """Get at-the-money strike price"""
        return round(price / 50) * 50  # Round to nearest 50
    
    def _calculate_quantity(self, symbol: str, price: float) -> int:
        """Calculate position quantity"""
        try:
            # Default lot sizes
            lot_sizes = {
                'NIFTY': 50,
                'BANKNIFTY': 25,
                'FINNIFTY': 40
            }
            
            base_lot_size = 50
            for key, size in lot_sizes.items():
                if key in symbol.upper():
                    base_lot_size = size
                    break
            
            # Calculate based on allocation
            capital = 500000  # Default capital
            allocation_amount = capital * self.allocation
            estimated_premium = price * 0.01  # Rough estimate
            
            lots = max(1, int(allocation_amount / (estimated_premium * base_lot_size)))
            return lots * base_lot_size
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 50
    
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours"""
        current_time = datetime.now().time()
        return time(9, 15) <= current_time <= time(15, 30)
    
    def _check_cooldown(self, symbol: str, current_time: datetime) -> bool:
        """Check if cooldown period has passed"""
        if symbol not in self.last_analysis_time:
            return True
        
        last_time = self.last_analysis_time[symbol]
        cooldown_minutes = 5  # 5 minute cooldown
        
        return (current_time - last_time).total_seconds() >= (cooldown_minutes * 60)
    
    def get_strategy_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'allocation': self.allocation,
            'active_symbols': len(self.momentum_states),
            'parameters': {
                'adx_threshold': self.adx_threshold,
                'volume_threshold': self.volume_threshold,
                'profit_target': self.profit_target_percent,
                'stop_loss': self.stop_loss_percent
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if strategy is healthy"""
        return self.is_enabled and len(self.momentum_states) >= 0
