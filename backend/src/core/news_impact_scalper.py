"""
News Impact Scalper Strategy - Clean Implementation
High-frequency scalping based on news sentiment and market volatility
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
class NewsEvent:
    """News event data structure"""
    title: str
    content: str
    timestamp: datetime
    severity: str = "medium"  # low, medium, high
    sentiment: float = 0.0  # -1 to 1
    symbols_mentioned: List[str] = field(default_factory=list)
    impact_score: float = 0.0

@dataclass
class NewsScalpingState:
    """News scalping state tracking"""
    active_news_events: List[NewsEvent] = field(default_factory=list)
    last_scalp_time: Optional[datetime] = None
    volatility_spike_detected: bool = False
    news_momentum: float = 0.0
    scalp_count_today: int = 0
    
    def reset_daily(self):
        """Reset daily counters"""
        self.scalp_count_today = 0
        self.active_news_events.clear()

class NewsImpactScalper:
    """
    News Impact Scalper Strategy
    High-frequency scalping based on news sentiment and immediate market reaction
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = "NewsImpactScalper"
        self.is_enabled = True
        self.allocation = 0.10
        
        # Strategy parameters
        self.volatility_threshold = self.config.get('volatility_threshold', 0.015)  # 1.5%
        self.news_reaction_window_seconds = self.config.get('news_reaction_window', 300)  # 5 minutes
        self.max_scalps_per_day = self.config.get('max_scalps_per_day', 10)
        self.min_volume_spike = self.config.get('min_volume_spike', 2.0)  # 2x normal volume
        self.profit_target_percent = self.config.get('profit_target', 0.5)
        self.stop_loss_percent = self.config.get('stop_loss', 0.3)
        self.scalp_duration_seconds = self.config.get('scalp_duration_seconds', 180)  # 3 minutes
        
        # State tracking
        self.scalping_state = NewsScalpingState()
        self.last_analysis_time = {}
        
        logger.info(f"NewsImpactScalper initialized with config: {self.config}")
    
    async def analyze(self, symbol: str, price_data: List[float], volume_data: List[float], 
                     current_time: datetime) -> Optional[Dict]:
        """
        Analyze for news-driven scalping opportunities
        """
        try:
            if len(price_data) < 20 or len(volume_data) < 20:
                return None
            
            # Check if within trading hours
            if not self._is_trading_hours():
                return None
            
            # Check daily scalp limit
            if self.scalping_state.scalp_count_today >= self.max_scalps_per_day:
                return None
            
            # Check cooldown between scalps
            if not self._check_scalp_cooldown(current_time):
                return None
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame({
                'close': price_data,
                'volume': volume_data
            })
            df.index = pd.date_range(end=current_time, periods=len(df), freq='1min')
            
            # Detect volatility spike
            volatility_spike = self._detect_volatility_spike(df)
            
            # Detect volume spike
            volume_spike = self._detect_volume_spike(df)
            
            # Simulate news event detection (in production, this would be real news feed)
            news_impact = self._simulate_news_impact(symbol, current_time)
            
            # Generate scalping signal if conditions met
            if volatility_spike and volume_spike and news_impact:
                signal = self._create_scalping_signal(symbol, df, current_time)
                if signal:
                    self.scalping_state.scalp_count_today += 1
                    self.scalping_state.last_scalp_time = current_time
                    logger.info(f"News scalping signal generated for {symbol}")
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _detect_volatility_spike(self, df: pd.DataFrame) -> bool:
        """Detect sudden volatility spike"""
        try:
            if len(df) < 10:
                return False
            
            # Calculate recent price volatility
            recent_returns = df['close'].pct_change().tail(5)
            recent_volatility = recent_returns.std()
            
            # Calculate baseline volatility
            baseline_returns = df['close'].pct_change().head(10)
            baseline_volatility = baseline_returns.std()
            
            # Check for volatility spike
            if baseline_volatility > 0:
                volatility_ratio = recent_volatility / baseline_volatility
                return volatility_ratio > 2.0  # 2x normal volatility
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting volatility spike: {e}")
            return False
    
    def _detect_volume_spike(self, df: pd.DataFrame) -> bool:
        """Detect volume spike indicating news reaction"""
        try:
            if len(df) < 10:
                return False
            
            # Current volume
            current_volume = df['volume'].iloc[-1]
            
            # Average volume baseline
            avg_volume = df['volume'].head(10).mean()
            
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                return volume_ratio >= self.min_volume_spike
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting volume spike: {e}")
            return False
    
    def _simulate_news_impact(self, symbol: str, current_time: datetime) -> bool:
        """
        Simulate news impact detection
        In production, this would connect to news feeds and sentiment analysis
        """
        # DISABLED: No simulation on weekends or when markets are closed
        current_day = current_time.weekday()  # 0=Monday, 6=Sunday
        if current_day >= 5:  # Weekend
            return False
            
        # Only generate news impact during actual trading hours
        if not self._is_trading_hours():
            return False
            
        # For now, return False until real news feed is implemented
        return False
    
    def _create_scalping_signal(self, symbol: str, df: pd.DataFrame, current_time: datetime) -> Optional[Dict]:
        """Create news scalping signal"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Determine direction based on recent price movement and news sentiment
            price_momentum = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
            
            # Get news sentiment (simplified)
            news_sentiment = 0.0
            if self.scalping_state.active_news_events:
                news_sentiment = np.mean([event.sentiment for event in self.scalping_state.active_news_events])
            
            # Combine price momentum and news sentiment
            combined_signal = price_momentum + (news_sentiment * 0.5)
            
            if combined_signal > 0.01:  # Bullish
                option_type = "CALL"
                signal_direction = "BUY"
            elif combined_signal < -0.01:  # Bearish
                option_type = "PUT"
                signal_direction = "SELL"
            else:
                return None
            
            # Calculate quality score
            quality_score = self._calculate_scalping_quality_score(df, news_sentiment)
            
            # Calculate position sizing
            quantity = self._calculate_quantity(symbol, current_price)
            
            signal = {
                'signal': signal_direction,
                'symbol': symbol,
                'option_type': option_type,
                'strike': self._get_atm_strike(current_price),
                'quality_score': quality_score,
                'quantity': quantity,
                'entry_price': current_price,
                'stop_loss_percent': self.stop_loss_percent,
                'profit_target_percent': self.profit_target_percent,
                'scalp_duration_seconds': self.scalp_duration_seconds,
                'setup_type': "NEWS_SCALP",
                'news_events': len(self.scalping_state.active_news_events),
                'price_momentum': price_momentum,
                'news_sentiment': news_sentiment,
                'timestamp': current_time,
                'strategy': self.name
            }
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating scalping signal: {e}")
            return None
    
    def _calculate_scalping_quality_score(self, df: pd.DataFrame, news_sentiment: float) -> float:
        """Calculate scalping signal quality score"""
        try:
            base_score = 6.0  # Higher base for news scalping
            
            # Volume spike bonus
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].head(10).mean()
            if avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                if volume_ratio > 3.0:
                    base_score += 1.5
                elif volume_ratio > 2.0:
                    base_score += 1.0
            
            # News sentiment clarity bonus
            if abs(news_sentiment) > 0.3:
                base_score += 1.0
            elif abs(news_sentiment) > 0.2:
                base_score += 0.5
            
            # Volatility spike bonus
            recent_volatility = df['close'].pct_change().tail(5).std()
            baseline_volatility = df['close'].pct_change().head(10).std()
            if baseline_volatility > 0:
                vol_ratio = recent_volatility / baseline_volatility
                if vol_ratio > 2.5:
                    base_score += 1.0
                elif vol_ratio > 2.0:
                    base_score += 0.5
            
            return min(base_score, 10.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 6.0
    
    def _get_atm_strike(self, price: float) -> float:
        """Get at-the-money strike price"""
        return round(price / 50) * 50  # Round to nearest 50
    
    def _calculate_quantity(self, symbol: str, price: float) -> int:
        """Calculate position quantity for scalping"""
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
            
            # Smaller position size for scalping
            capital = 500000  # Default capital
            allocation_amount = capital * self.allocation * 0.5  # Half allocation for scalping
            estimated_premium = price * 0.008  # Lower premium estimate for scalping
            
            lots = max(1, int(allocation_amount / (estimated_premium * base_lot_size)))
            return lots * base_lot_size
            
        except Exception as e:
            logger.error(f"Error calculating quantity: {e}")
            return 25  # Smaller default for scalping
    
    def _is_trading_hours(self) -> bool:
        """Check if within trading hours"""
        current_time = datetime.now().time()
        return time(9, 15) <= current_time <= time(15, 30)
    
    def _check_scalp_cooldown(self, current_time: datetime) -> bool:
        """Check cooldown between scalps"""
        if self.scalping_state.last_scalp_time is None:
            return True
        
        time_diff = (current_time - self.scalping_state.last_scalp_time).total_seconds()
        return time_diff >= 120  # 2 minute cooldown between scalps
    
    def get_strategy_metrics(self) -> Dict:
        """Get strategy performance metrics"""
        return {
            'name': self.name,
            'enabled': self.is_enabled,
            'allocation': self.allocation,
            'scalps_today': self.scalping_state.scalp_count_today,
            'max_scalps_per_day': self.max_scalps_per_day,
            'active_news_events': len(self.scalping_state.active_news_events),
            'parameters': {
                'volatility_threshold': self.volatility_threshold,
                'min_volume_spike': self.min_volume_spike,
                'profit_target': self.profit_target_percent,
                'stop_loss': self.stop_loss_percent,
                'scalp_duration': self.scalp_duration_seconds
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if strategy is healthy"""
        return self.is_enabled and self.scalping_state.scalp_count_today < self.max_scalps_per_day
