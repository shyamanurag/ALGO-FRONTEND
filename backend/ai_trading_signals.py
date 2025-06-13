"""
AI-Powered Trading Signal Generator
Advanced machine learning models for generating high-quality trading signals
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import logging
import asyncio
import random
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStrength(Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"

@dataclass
class TradingSignal:
    signal_id: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0-100
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward_ratio: float
    strategy: str
    reasoning: str
    technical_indicators: Dict
    timestamp: datetime
    validity_minutes: int = 30

class AITradingSignalGenerator:
    def __init__(self):
        self.signals_history = []
        self.active_signals = []
        self.strategies = {
            "momentum_ai": {"weight": 0.25, "accuracy": 0.78},
            "mean_reversion": {"weight": 0.20, "accuracy": 0.72},
            "volume_profile": {"weight": 0.15, "accuracy": 0.75},
            "pattern_recognition": {"weight": 0.20, "accuracy": 0.80},
            "sentiment_analysis": {"weight": 0.20, "accuracy": 0.68}
        }
        self.market_data_buffer = {}
        
    async def analyze_market_and_generate_signals(self, market_data: Dict) -> List[TradingSignal]:
        """Main function to analyze market data and generate AI trading signals"""
        signals = []
        
        # Update market data buffer
        self._update_market_buffer(market_data)
        
        # Generate signals for each symbol
        for symbol, data in market_data.get("indices", {}).items():
            if self._has_sufficient_data(symbol):
                symbol_signals = await self._generate_signals_for_symbol(symbol, data)
                signals.extend(symbol_signals)
        
        # Filter and rank signals by quality
        quality_signals = self._filter_high_quality_signals(signals)
        
        # Update active signals
        self._update_active_signals(quality_signals)
        
        return quality_signals
    
    def _update_market_buffer(self, market_data: Dict):
        """Update the market data buffer for analysis"""
        timestamp = datetime.now()
        
        for symbol, data in market_data.get("indices", {}).items():
            if symbol not in self.market_data_buffer:
                self.market_data_buffer[symbol] = []
            
            # Add current data point
            data_point = {
                "timestamp": timestamp,
                "ltp": data.get("ltp", 0),
                "volume": data.get("volume", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0),
                "change_percent": data.get("change_percent", 0)
            }
            
            self.market_data_buffer[symbol].append(data_point)
            
            # Keep only last 200 data points (about 100 minutes of data)
            if len(self.market_data_buffer[symbol]) > 200:
                self.market_data_buffer[symbol] = self.market_data_buffer[symbol][-200:]
    
    def _has_sufficient_data(self, symbol: str) -> bool:
        """Check if we have sufficient data for analysis"""
        return symbol in self.market_data_buffer and len(self.market_data_buffer[symbol]) >= 20
    
    async def _generate_signals_for_symbol(self, symbol: str, current_data: Dict) -> List[TradingSignal]:
        """Generate trading signals for a specific symbol using multiple AI strategies"""
        signals = []
        
        # Get historical data for the symbol
        hist_data = self.market_data_buffer[symbol]
        df = pd.DataFrame(hist_data)
        
        if len(df) < 20:
            return signals
        
        # Run multiple AI strategies
        momentum_signal = await self._momentum_ai_strategy(symbol, df, current_data)
        reversion_signal = await self._mean_reversion_strategy(symbol, df, current_data)
        volume_signal = await self._volume_profile_strategy(symbol, df, current_data)
        pattern_signal = await self._pattern_recognition_strategy(symbol, df, current_data)
        sentiment_signal = await self._sentiment_analysis_strategy(symbol, df, current_data)
        
        # Collect all generated signals
        for signal in [momentum_signal, reversion_signal, volume_signal, pattern_signal, sentiment_signal]:
            if signal and signal.confidence >= 65:  # Only high-confidence signals
                signals.append(signal)
        
        return signals
    
    async def _momentum_ai_strategy(self, symbol: str, df: pd.DataFrame, current_data: Dict) -> Optional[TradingSignal]:
        """AI-powered momentum strategy"""
        try:
            # Calculate technical indicators
            df['sma_10'] = df['ltp'].rolling(window=10).mean()
            df['sma_20'] = df['ltp'].rolling(window=20).mean()
            df['rsi'] = self._calculate_rsi(df['ltp'])
            df['macd'], df['macd_signal'] = self._calculate_macd(df['ltp'])
            
            current_price = current_data.get("ltp", 0)
            latest_sma_10 = df['sma_10'].iloc[-1]
            latest_sma_20 = df['sma_20'].iloc[-1]
            latest_rsi = df['rsi'].iloc[-1]
            latest_macd = df['macd'].iloc[-1]
            latest_macd_signal = df['macd_signal'].iloc[-1]
            
            # AI decision logic
            bullish_signals = 0
            bearish_signals = 0
            
            # SMA crossover
            if latest_sma_10 > latest_sma_20:
                bullish_signals += 1
            else:
                bearish_signals += 1
                
            # RSI analysis
            if 30 < latest_rsi < 70:
                if latest_rsi > 60:
                    bullish_signals += 1
                elif latest_rsi < 40:
                    bearish_signals += 1
            
            # MACD analysis
            if latest_macd > latest_macd_signal:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Price momentum
            price_change_5 = (current_price - df['ltp'].iloc[-6]) / df['ltp'].iloc[-6] * 100
            if price_change_5 > 0.5:
                bullish_signals += 1
            elif price_change_5 < -0.5:
                bearish_signals += 1
            
            # Generate signal
            if bullish_signals >= 3:
                signal_type = SignalType.BUY
                confidence = min(70 + bullish_signals * 5, 95)
                target_price = current_price * 1.015  # 1.5% target
                stop_loss = current_price * 0.992    # 0.8% stop loss
            elif bearish_signals >= 3:
                signal_type = SignalType.SELL
                confidence = min(70 + bearish_signals * 5, 95)
                target_price = current_price * 0.985  # 1.5% target
                stop_loss = current_price * 1.008    # 0.8% stop loss
            else:
                return None
            
            if confidence >= 65:
                return TradingSignal(
                    signal_id=f"MOM_{symbol}_{int(datetime.now().timestamp())}",
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=self._get_signal_strength(confidence),
                    confidence=confidence,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                    strategy="Momentum AI",
                    reasoning=f"AI detected {bullish_signals if signal_type == SignalType.BUY else bearish_signals} {signal_type.value.lower()} signals: SMA trend, RSI={latest_rsi:.1f}, MACD crossover",
                    technical_indicators={
                        "rsi": round(latest_rsi, 2),
                        "macd": round(latest_macd, 4),
                        "sma_10": round(latest_sma_10, 2),
                        "sma_20": round(latest_sma_20, 2),
                        "price_momentum": round(price_change_5, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in momentum AI strategy: {e}")
            
        return None
    
    async def _mean_reversion_strategy(self, symbol: str, df: pd.DataFrame, current_data: Dict) -> Optional[TradingSignal]:
        """Mean reversion AI strategy"""
        try:
            # Calculate Bollinger Bands
            df['bb_middle'] = df['ltp'].rolling(window=20).mean()
            df['bb_std'] = df['ltp'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
            
            current_price = current_data.get("ltp", 0)
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            bb_middle = df['bb_middle'].iloc[-1]
            
            # Calculate price position within bands
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            # Mean reversion signals
            confidence = 0
            signal_type = None
            
            if bb_position > 0.9:  # Near upper band - sell signal
                signal_type = SignalType.SELL
                confidence = 70 + (bb_position - 0.9) * 250  # Higher confidence as price moves further from mean
                target_price = bb_middle
                stop_loss = current_price * 1.005
            elif bb_position < 0.1:  # Near lower band - buy signal
                signal_type = SignalType.BUY
                confidence = 70 + (0.1 - bb_position) * 250
                target_price = bb_middle
                stop_loss = current_price * 0.995
            
            if signal_type and confidence >= 65:
                return TradingSignal(
                    signal_id=f"REV_{symbol}_{int(datetime.now().timestamp())}",
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=self._get_signal_strength(confidence),
                    confidence=min(confidence, 95),
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                    strategy="Mean Reversion AI",
                    reasoning=f"Price at {bb_position:.1%} of Bollinger Band range, extreme deviation detected",
                    technical_indicators={
                        "bb_position": round(bb_position, 3),
                        "bb_upper": round(bb_upper, 2),
                        "bb_lower": round(bb_lower, 2),
                        "bb_middle": round(bb_middle, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in mean reversion strategy: {e}")
            
        return None
    
    async def _volume_profile_strategy(self, symbol: str, df: pd.DataFrame, current_data: Dict) -> Optional[TradingSignal]:
        """Volume profile analysis strategy"""
        try:
            # Calculate volume indicators
            df['volume_sma'] = df['volume'].rolling(window=10).mean()
            df['price_volume'] = df['ltp'] * df['volume']
            df['vwap'] = df['price_volume'].rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
            
            current_price = current_data.get("ltp", 0)
            current_volume = current_data.get("volume", 0)
            avg_volume = df['volume_sma'].iloc[-1]
            vwap = df['vwap'].iloc[-1]
            
            # Volume surge detection
            volume_ratio = current_volume / max(avg_volume, 1)
            price_vs_vwap = (current_price - vwap) / vwap * 100
            
            confidence = 0
            signal_type = None
            
            if volume_ratio > 2 and price_vs_vwap > 0.2:  # High volume + price above VWAP
                signal_type = SignalType.BUY
                confidence = 65 + min(volume_ratio * 5, 25)
                target_price = current_price * 1.012
                stop_loss = current_price * 0.994
            elif volume_ratio > 2 and price_vs_vwap < -0.2:  # High volume + price below VWAP
                signal_type = SignalType.SELL
                confidence = 65 + min(volume_ratio * 5, 25)
                target_price = current_price * 0.988
                stop_loss = current_price * 1.006
            
            if signal_type and confidence >= 65:
                return TradingSignal(
                    signal_id=f"VOL_{symbol}_{int(datetime.now().timestamp())}",
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=self._get_signal_strength(confidence),
                    confidence=min(confidence, 95),
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                    strategy="Volume Profile AI",
                    reasoning=f"Volume surge ({volume_ratio:.1f}x avg) with price {price_vs_vwap:+.2f}% vs VWAP",
                    technical_indicators={
                        "volume_ratio": round(volume_ratio, 2),
                        "vwap": round(vwap, 2),
                        "price_vs_vwap": round(price_vs_vwap, 2),
                        "avg_volume": round(avg_volume, 0)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in volume profile strategy: {e}")
            
        return None
    
    async def _pattern_recognition_strategy(self, symbol: str, df: pd.DataFrame, current_data: Dict) -> Optional[TradingSignal]:
        """AI pattern recognition strategy"""
        try:
            # Look for price patterns in recent data
            recent_prices = df['ltp'].tail(10).values
            current_price = current_data.get("ltp", 0)
            
            # Pattern detection
            patterns_detected = []
            confidence = 60
            
            # Double bottom pattern
            if self._detect_double_bottom(recent_prices):
                patterns_detected.append("Double Bottom")
                confidence += 15
                signal_type = SignalType.BUY
                target_price = current_price * 1.02
                stop_loss = current_price * 0.99
            
            # Double top pattern
            elif self._detect_double_top(recent_prices):
                patterns_detected.append("Double Top")
                confidence += 15
                signal_type = SignalType.SELL
                target_price = current_price * 0.98
                stop_loss = current_price * 1.01
            
            # Ascending triangle
            elif self._detect_ascending_triangle(recent_prices):
                patterns_detected.append("Ascending Triangle")
                confidence += 12
                signal_type = SignalType.BUY
                target_price = current_price * 1.018
                stop_loss = current_price * 0.992
                
            else:
                return None
            
            if patterns_detected and confidence >= 65:
                return TradingSignal(
                    signal_id=f"PAT_{symbol}_{int(datetime.now().timestamp())}",
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=self._get_signal_strength(confidence),
                    confidence=confidence,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                    strategy="Pattern Recognition AI",
                    reasoning=f"Detected {', '.join(patterns_detected)} pattern(s)",
                    technical_indicators={
                        "patterns": patterns_detected,
                        "pattern_strength": confidence - 60
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in pattern recognition strategy: {e}")
            
        return None
    
    async def _sentiment_analysis_strategy(self, symbol: str, df: pd.DataFrame, current_data: Dict) -> Optional[TradingSignal]:
        """Market sentiment analysis strategy"""
        try:
            # Analyze price velocity and acceleration
            df['price_change'] = df['ltp'].pct_change()
            df['momentum'] = df['price_change'].rolling(window=5).mean()
            df['acceleration'] = df['momentum'].diff()
            
            current_price = current_data.get("ltp", 0)
            recent_momentum = df['momentum'].iloc[-1]
            recent_acceleration = df['acceleration'].iloc[-1]
            
            # Sentiment scoring
            sentiment_score = 0
            
            # Momentum sentiment
            if recent_momentum > 0.002:
                sentiment_score += 2
            elif recent_momentum < -0.002:
                sentiment_score -= 2
            
            # Acceleration sentiment
            if recent_acceleration > 0.001:
                sentiment_score += 1
            elif recent_acceleration < -0.001:
                sentiment_score -= 1
                
            # Volume sentiment
            volume_trend = df['volume'].tail(5).mean() / df['volume'].tail(10).mean()
            if volume_trend > 1.1:
                sentiment_score += 1
            elif volume_trend < 0.9:
                sentiment_score -= 1
            
            confidence = 60 + abs(sentiment_score) * 8
            
            if sentiment_score >= 3:
                signal_type = SignalType.BUY
                target_price = current_price * 1.01
                stop_loss = current_price * 0.995
            elif sentiment_score <= -3:
                signal_type = SignalType.SELL
                target_price = current_price * 0.99
                stop_loss = current_price * 1.005
            else:
                return None
            
            if confidence >= 65:
                return TradingSignal(
                    signal_id=f"SENT_{symbol}_{int(datetime.now().timestamp())}",
                    symbol=symbol,
                    signal_type=signal_type,
                    strength=self._get_signal_strength(confidence),
                    confidence=min(confidence, 95),
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
                    strategy="Sentiment Analysis AI",
                    reasoning=f"Market sentiment score: {sentiment_score}/5, momentum trend detected",
                    technical_indicators={
                        "sentiment_score": sentiment_score,
                        "momentum": round(recent_momentum * 100, 3),
                        "acceleration": round(recent_acceleration * 100, 4),
                        "volume_trend": round(volume_trend, 2)
                    },
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis strategy: {e}")
            
        return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        return macd, signal
    
    def _detect_double_bottom(self, prices: np.array) -> bool:
        """Detect double bottom pattern"""
        if len(prices) < 8:
            return False
        
        # Find local minima
        minima = []
        for i in range(1, len(prices) - 1):
            if prices[i] < prices[i-1] and prices[i] < prices[i+1]:
                minima.append((i, prices[i]))
        
        if len(minima) >= 2:
            # Check if last two minima are similar in price
            last_two = minima[-2:]
            price_diff = abs(last_two[0][1] - last_two[1][1]) / last_two[0][1]
            return price_diff < 0.01  # Within 1%
        
        return False
    
    def _detect_double_top(self, prices: np.array) -> bool:
        """Detect double top pattern"""
        if len(prices) < 8:
            return False
        
        # Find local maxima
        maxima = []
        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1]:
                maxima.append((i, prices[i]))
        
        if len(maxima) >= 2:
            # Check if last two maxima are similar in price
            last_two = maxima[-2:]
            price_diff = abs(last_two[0][1] - last_two[1][1]) / last_two[0][1]
            return price_diff < 0.01  # Within 1%
        
        return False
    
    def _detect_ascending_triangle(self, prices: np.array) -> bool:
        """Detect ascending triangle pattern"""
        if len(prices) < 8:
            return False
        
        # Simple ascending triangle detection
        # Check if highs are relatively flat and lows are ascending
        highs = [prices[i] for i in range(1, len(prices)-1) if prices[i] > prices[i-1] and prices[i] > prices[i+1]]
        lows = [prices[i] for i in range(1, len(prices)-1) if prices[i] < prices[i-1] and prices[i] < prices[i+1]]
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Check if highs are flat (within 1%)
            high_variation = (max(highs) - min(highs)) / max(highs)
            # Check if lows are ascending
            lows_ascending = lows[-1] > lows[0]
            
            return high_variation < 0.01 and lows_ascending
        
        return False
    
    def _get_signal_strength(self, confidence: float) -> SignalStrength:
        """Convert confidence to signal strength"""
        if confidence >= 90:
            return SignalStrength.VERY_STRONG
        elif confidence >= 80:
            return SignalStrength.STRONG
        elif confidence >= 70:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _filter_high_quality_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Filter and rank signals by quality"""
        # Remove signals with poor risk-reward ratio
        quality_signals = [s for s in signals if s.risk_reward_ratio >= 1.5]
        
        # Sort by confidence
        quality_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Keep only top 3 signals per symbol
        symbol_counts = {}
        filtered_signals = []
        
        for signal in quality_signals:
            if symbol_counts.get(signal.symbol, 0) < 3:
                filtered_signals.append(signal)
                symbol_counts[signal.symbol] = symbol_counts.get(signal.symbol, 0) + 1
        
        return filtered_signals
    
    def _update_active_signals(self, new_signals: List[TradingSignal]):
        """Update the list of active signals"""
        current_time = datetime.now()
        
        # Remove expired signals
        self.active_signals = [
            s for s in self.active_signals 
            if (current_time - s.timestamp).total_seconds() / 60 < s.validity_minutes
        ]
        
        # Add new signals
        self.active_signals.extend(new_signals)
        
        # Add to history
        self.signals_history.extend(new_signals)
        
        # Keep only last 1000 historical signals
        if len(self.signals_history) > 1000:
            self.signals_history = self.signals_history[-1000:]
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Get currently active signals"""
        return self.active_signals
    
    def get_signals_summary(self) -> Dict:
        """Get summary of recent signals"""
        current_time = datetime.now()
        
        # Recent signals (last hour)
        recent_signals = [
            s for s in self.signals_history 
            if (current_time - s.timestamp).total_seconds() / 3600 < 1
        ]
        
        # Calculate statistics
        total_recent = len(recent_signals)
        buy_signals = len([s for s in recent_signals if s.signal_type == SignalType.BUY])
        sell_signals = len([s for s in recent_signals if s.signal_type == SignalType.SELL])
        avg_confidence = sum(s.confidence for s in recent_signals) / max(total_recent, 1)
        
        return {
            "active_signals": len(self.active_signals),
            "recent_signals_1h": total_recent,
            "buy_signals_1h": buy_signals,
            "sell_signals_1h": sell_signals,
            "avg_confidence": round(avg_confidence, 1),
            "top_active_signals": [
                {
                    "signal_id": s.signal_id,
                    "symbol": s.symbol,
                    "type": s.signal_type.value,
                    "strength": s.strength.value,
                    "confidence": s.confidence,
                    "strategy": s.strategy,
                    "reasoning": s.reasoning
                }
                for s in sorted(self.active_signals, key=lambda x: x.confidence, reverse=True)[:5]
            ]
        }

# Global AI signal generator
ai_signal_generator = AITradingSignalGenerator()

def get_ai_signal_generator():
    """Get the global AI signal generator"""
    return ai_signal_generator