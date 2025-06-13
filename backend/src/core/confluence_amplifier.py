"""
Confluence Amplifier Strategy - Clean Implementation
Multi-signal confluence detection with amplified position sizing
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
class ConfluenceSignal:
    """Individual confluence signal"""
    name: str
    strength: float  # 0-1
    direction: str  # BULLISH, BEARISH, NEUTRAL
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)

@dataclass
class ConfluenceState:
    """Confluence tracking state"""
    active_signals: List[ConfluenceSignal] = field(default_factory=list)
    confluence_score: float = 0.0
    dominant_direction: str = "NEUTRAL"
    signal_count: int = 0
    last_confluence_time: Optional[datetime] = None
    
    def reset(self):
        """Reset confluence state"""
        self.active_signals.clear()
        self.confluence_score = 0.0
        self.dominant_direction = "NEUTRAL"
        self.signal_count = 0

class ConfluenceAmplifier:
    """
    Confluence Amplifier Strategy
    Detects multiple confirming signals and amplifies position size
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = "ConfluenceAmplifier"
        self.is_enabled = True
        self.allocation = 0.18
        
        # Strategy parameters
        self.min_confluence_signals = self.config.get('min_confluence_signals', 3)
        self.min_confluence_score = self.config.get('min_confluence_score', 0.7)
        self.signal_weight_threshold = self.config.get('signal_weight_threshold', 0.3)
        self.amplification_factor = self.config.get('amplification_factor', 1.5)
        self.profit_target_percent = self.config.get('profit_target', 1.0)
        self.stop_loss_percent = self.config.get('stop_loss', 0.7)
        self.confluence_window_minutes = self.config.get('confluence_window_minutes', 10)
        
        # Technical indicator parameters
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.bb_period = 20
        self.bb_std = 2
        
        # State tracking
        self.confluence_states = {}
        self.last_analysis_time = {}
        
        logger.info(f"ConfluenceAmplifier initialized with config: {self.config}")
    
    async def analyze(self, symbol: str, price_data: List[float], volume_data: List[float], 
                     current_time: datetime) -> Optional[Dict]:
        """
        Analyze for confluence trading opportunities
        """
        try:
            if len(price_data) < 50 or len(volume_data) < 50:
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
            
            # Get or create confluence state
            if symbol not in self.confluence_states:
                self.confluence_states[symbol] = ConfluenceState()
            
            state = self.confluence_states[symbol]
            
            # Generate individual signals
            signals = self._generate_confluence_signals(df, current_time)
            
            # Update confluence state
            self._update_confluence_state(state, signals, current_time)
            
            # Check for confluence opportunity
            confluence_signal = self._check_confluence_opportunity(df, state, current_time)
            
            if confluence_signal:
                self.last_analysis_time[symbol] = current_time
                logger.info(f"Confluence signal generated for {symbol}: {confluence_signal}")
            
            return confluence_signal
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _generate_confluence_signals(self, df: pd.DataFrame, current_time: datetime) -> List[ConfluenceSignal]:
        """Generate individual confluence signals"""
        signals = []
        
        try:
            # RSI Signal
            rsi_signal = self._generate_rsi_signal(df, current_time)
            if rsi_signal:
                signals.append(rsi_signal)
            
            # MACD Signal
            macd_signal = self._generate_macd_signal(df, current_time)
            if macd_signal:
                signals.append(macd_signal)
            
            # Bollinger Bands Signal
            bb_signal = self._generate_bollinger_signal(df, current_time)
            if bb_signal:
                signals.append(bb_signal)
            
            # Volume Signal
            volume_signal = self._generate_volume_signal(df, current_time)
            if volume_signal:
                signals.append(volume_signal)
            
            # Price Action Signal
            price_signal = self._generate_price_action_signal(df, current_time)
            if price_signal:
                signals.append(price_signal)
            
            # Moving Average Signal
            ma_signal = self._generate_moving_average_signal(df, current_time)
            if ma_signal:
                signals.append(ma_signal)
            
        except Exception as e:
            logger.error(f"Error generating confluence signals: {e}")
        
        return signals
    
    def _generate_rsi_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate RSI-based signal"""
        try:
            # Calculate RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            if pd.isna(current_rsi):
                return None
            
            # Generate signal based on RSI levels
            if current_rsi < 30:  # Oversold
                return ConfluenceSignal(
                    name="RSI_OVERSOLD",
                    strength=min((30 - current_rsi) / 10, 1.0),
                    direction="BULLISH",
                    timestamp=current_time,
                    metadata={"rsi_value": current_rsi}
                )
            elif current_rsi > 70:  # Overbought
                return ConfluenceSignal(
                    name="RSI_OVERBOUGHT",
                    strength=min((current_rsi - 70) / 10, 1.0),
                    direction="BEARISH",
                    timestamp=current_time,
                    metadata={"rsi_value": current_rsi}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating RSI signal: {e}")
            return None
    
    def _generate_macd_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate MACD-based signal"""
        try:
            # Calculate MACD
            ema_fast = df['close'].ewm(span=self.macd_fast).mean()
            ema_slow = df['close'].ewm(span=self.macd_slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            current_histogram = histogram.iloc[-1]
            prev_histogram = histogram.iloc[-2]
            
            if pd.isna(current_histogram) or pd.isna(prev_histogram):
                return None
            
            # MACD crossover signals
            if prev_histogram <= 0 and current_histogram > 0:  # Bullish crossover
                return ConfluenceSignal(
                    name="MACD_BULLISH_CROSS",
                    strength=min(abs(current_histogram) * 1000, 1.0),
                    direction="BULLISH",
                    timestamp=current_time,
                    metadata={"histogram": current_histogram}
                )
            elif prev_histogram >= 0 and current_histogram < 0:  # Bearish crossover
                return ConfluenceSignal(
                    name="MACD_BEARISH_CROSS",
                    strength=min(abs(current_histogram) * 1000, 1.0),
                    direction="BEARISH",
                    timestamp=current_time,
                    metadata={"histogram": current_histogram}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating MACD signal: {e}")
            return None
    
    def _generate_bollinger_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate Bollinger Bands signal"""
        try:
            # Calculate Bollinger Bands
            sma = df['close'].rolling(self.bb_period).mean()
            std = df['close'].rolling(self.bb_period).std()
            upper_band = sma + (std * self.bb_std)
            lower_band = sma - (std * self.bb_std)
            
            current_price = df['close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_sma = sma.iloc[-1]
            
            if pd.isna(current_upper) or pd.isna(current_lower):
                return None
            
            # Band touch signals
            band_width = current_upper - current_lower
            if band_width > 0:
                if current_price <= current_lower:  # Touch lower band
                    strength = min((current_lower - current_price) / band_width * 4, 1.0)
                    return ConfluenceSignal(
                        name="BB_LOWER_TOUCH",
                        strength=strength,
                        direction="BULLISH",
                        timestamp=current_time,
                        metadata={"price_position": (current_price - current_sma) / band_width}
                    )
                elif current_price >= current_upper:  # Touch upper band
                    strength = min((current_price - current_upper) / band_width * 4, 1.0)
                    return ConfluenceSignal(
                        name="BB_UPPER_TOUCH",
                        strength=strength,
                        direction="BEARISH",
                        timestamp=current_time,
                        metadata={"price_position": (current_price - current_sma) / band_width}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating Bollinger signal: {e}")
            return None
    
    def _generate_volume_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate volume-based signal"""
        try:
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            
            if pd.isna(avg_volume) or avg_volume <= 0:
                return None
            
            volume_ratio = current_volume / avg_volume
            
            if volume_ratio > 2.0:  # High volume
                # Determine direction based on price movement
                price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
                
                if price_change > 0.001:
                    return ConfluenceSignal(
                        name="VOLUME_BREAKOUT_BULL",
                        strength=min((volume_ratio - 1) / 2, 1.0),
                        direction="BULLISH",
                        timestamp=current_time,
                        metadata={"volume_ratio": volume_ratio, "price_change": price_change}
                    )
                elif price_change < -0.001:
                    return ConfluenceSignal(
                        name="VOLUME_BREAKOUT_BEAR",
                        strength=min((volume_ratio - 1) / 2, 1.0),
                        direction="BEARISH",
                        timestamp=current_time,
                        metadata={"volume_ratio": volume_ratio, "price_change": price_change}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating volume signal: {e}")
            return None
    
    def _generate_price_action_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate price action signal"""
        try:
            # Calculate recent price momentum
            short_momentum = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3]
            medium_momentum = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
            
            # Strong momentum in same direction
            if short_momentum > 0.005 and medium_momentum > 0.005:  # Both positive
                strength = min((short_momentum + medium_momentum) * 50, 1.0)
                return ConfluenceSignal(
                    name="PRICE_MOMENTUM_BULL",
                    strength=strength,
                    direction="BULLISH",
                    timestamp=current_time,
                    metadata={"short_momentum": short_momentum, "medium_momentum": medium_momentum}
                )
            elif short_momentum < -0.005 and medium_momentum < -0.005:  # Both negative
                strength = min(abs(short_momentum + medium_momentum) * 50, 1.0)
                return ConfluenceSignal(
                    name="PRICE_MOMENTUM_BEAR",
                    strength=strength,
                    direction="BEARISH",
                    timestamp=current_time,
                    metadata={"short_momentum": short_momentum, "medium_momentum": medium_momentum}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating price action signal: {e}")
            return None
    
    def _generate_moving_average_signal(self, df: pd.DataFrame, current_time: datetime) -> Optional[ConfluenceSignal]:
        """Generate moving average signal"""
        try:
            # Calculate moving averages
            ma_short = df['close'].rolling(10).mean()
            ma_long = df['close'].rolling(20).mean()
            
            current_short = ma_short.iloc[-1]
            current_long = ma_long.iloc[-1]
            prev_short = ma_short.iloc[-2]
            prev_long = ma_long.iloc[-2]
            
            if pd.isna(current_short) or pd.isna(current_long):
                return None
            
            # Moving average crossover
            if prev_short <= prev_long and current_short > current_long:  # Golden cross
                return ConfluenceSignal(
                    name="MA_GOLDEN_CROSS",
                    strength=0.8,
                    direction="BULLISH",
                    timestamp=current_time,
                    metadata={"ma_diff": current_short - current_long}
                )
            elif prev_short >= prev_long and current_short < current_long:  # Death cross
                return ConfluenceSignal(
                    name="MA_DEATH_CROSS",
                    strength=0.8,
                    direction="BEARISH",
                    timestamp=current_time,
                    metadata={"ma_diff": current_short - current_long}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating moving average signal: {e}")
            return None
    
    def _update_confluence_state(self, state: ConfluenceState, signals: List[ConfluenceSignal], 
                               current_time: datetime):
        """Update confluence state with new signals"""
        try:
            # Filter out old signals
            cutoff_time = current_time - timedelta(minutes=self.confluence_window_minutes)
            state.active_signals = [s for s in state.active_signals if s.timestamp >= cutoff_time]
            
            # Add new signals
            state.active_signals.extend(signals)
            
            # Calculate confluence score and direction
            if state.active_signals:
                bullish_signals = [s for s in state.active_signals if s.direction == "BULLISH"]
                bearish_signals = [s for s in state.active_signals if s.direction == "BEARISH"]
                
                bullish_score = sum(s.strength for s in bullish_signals)
                bearish_score = sum(s.strength for s in bearish_signals)
                
                state.signal_count = len(state.active_signals)
                
                if bullish_score > bearish_score and bullish_score >= self.min_confluence_score:
                    state.confluence_score = bullish_score
                    state.dominant_direction = "BULLISH"
                elif bearish_score > bullish_score and bearish_score >= self.min_confluence_score:
                    state.confluence_score = bearish_score
                    state.dominant_direction = "BEARISH"
                else:
                    state.confluence_score = max(bullish_score, bearish_score)
                    state.dominant_direction = "NEUTRAL"
            else:
                state.confluence_score = 0.0
                state.dominant_direction = "NEUTRAL"
                state.signal_count = 0
                
        except Exception as e:
            logger.error(f"Error updating confluence state: {e}")
    
    def _check_confluence_opportunity(self, df: pd.DataFrame, state: ConfluenceState, 
                                    current_time: datetime) -> Optional[Dict]:
        """Check for confluence trading opportunity"""
        try:
            # Check minimum requirements
            if (state.signal_count < self.min_confluence_signals or 
                state.confluence_score < self.min_confluence_score or
                state.dominant_direction == "NEUTRAL"):
                return None
            
            # Check cooldown
            if state.last_confluence_time:
                time_diff = (current_time - state.last_confluence_time).total_seconds()
                if time_diff < 300:  # 5 minute cooldown
                    return None
            
            current_price = df['close'].iloc[-1]
            
            # Create confluence signal
            signal = self._create_confluence_signal(df, state, current_time)
            
            if signal:
                state.last_confluence_time = current_time
            
            return signal
            
        except Exception as e:
            logger.error(f"Error checking confluence opportunity: {e}")
            return None
    
    def _create_confluence_signal(self, df: pd.DataFrame, state: ConfluenceState, 
                                current_time: datetime) -> Optional[Dict]:
        """Create confluence trading signal"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Determine option type based on direction
            if state.dominant_direction == "BULLISH":
                option_type = "CALL"
                signal_direction = "BUY"
            elif state.dominant_direction == "BEARISH":
                option_type = "PUT"
                signal_direction = "SELL"
            else:
                return None
            
            # Calculate quality score (higher for confluence)
            quality_score = self._calculate_confluence_quality_score(state)
            
            # Calculate amplified position sizing
            quantity = self._calculate_amplified_quantity(df['close'].iloc[0], current_price, state.confluence_score)
            
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
                'setup_type': "CONFLUENCE_AMPLIFIED",
                'confluence_score': state.confluence_score,
                'signal_count': state.signal_count,
                'dominant_direction': state.dominant_direction,
                'active_signals': [s.name for s in state.active_signals],
                'amplification_factor': self.amplification_factor,
                'timestamp': current_time,
                'strategy': self.name
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating confluence signal: {e}")
            return None
    
    def _calculate_confluence_quality_score(self, state: ConfluenceState) -> float:
        """Calculate confluence quality score"""
        try:
            base_score = 7.0  # Higher base for confluence
            
            # Signal count bonus
            if state.signal_count >= 5:
                base_score += 1.5
            elif state.signal_count >= 4:
                base_score += 1.0
            elif state.signal_count >= 3:
                base_score += 0.5
            
            # Confluence score bonus
            if state.confluence_score >= 3.0:
                base_score += 1.5
            elif state.confluence_score >= 2.0:
                base_score += 1.0
            elif state.confluence_score >= 1.5:
                base_score += 0.5
            
            return min(base_score, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 7.0
    
    def _get_atm_strike(self, price: float) -> float:
        """Get at-the-money strike price"""
        return round(price / 50) * 50  # Round to nearest 50
    
    def _calculate_amplified_quantity(self, symbol_proxy: float, price: float, confluence_score: float) -> int:
        """Calculate amplified position quantity based on confluence"""
        try:
            # Default lot sizes (approximation based on price)
            if price > 40000:  # Likely BANKNIFTY
                base_lot_size = 25
            elif price > 15000:  # Likely NIFTY
                base_lot_size = 50
            else:  # Likely FINNIFTY or others
                base_lot_size = 40
            
            # Base calculation
            capital = 500000  # Default capital
            base_allocation = capital * self.allocation
            estimated_premium = price * 0.012  # Moderate premium estimate
            
            base_lots = max(1, int(base_allocation / (estimated_premium * base_lot_size)))
            
            # Apply amplification based on confluence score
            amplification = min(1 + (confluence_score - 1) * 0.3, self.amplification_factor)
            amplified_lots = int(base_lots * amplification)
            
            return max(base_lots, amplified_lots * base_lot_size)
            
        except Exception as e:
            logger.error(f"Error calculating amplified quantity: {e}")
            return 50
    
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours"""
        current_time = datetime.now().time()
        return time(9, 15) <= current_time <= time(15, 30)
    
    def get_strategy_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        total_active_signals = sum(len(state.active_signals) for state in self.confluence_states.values())
        active_confluences = sum(1 for state in self.confluence_states.values() 
                               if state.confluence_score >= self.min_confluence_score)
        
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'allocation': self.allocation,
            'active_symbols': len(self.confluence_states),
            'total_active_signals': total_active_signals,
            'active_confluences': active_confluences,
            'parameters': {
                'min_confluence_signals': self.min_confluence_signals,
                'min_confluence_score': self.min_confluence_score,
                'amplification_factor': self.amplification_factor,
                'profit_target': self.profit_target_percent,
                'stop_loss': self.stop_loss_percent
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if strategy is healthy"""
        return self.is_enabled and len(self.confluence_states) >= 0
