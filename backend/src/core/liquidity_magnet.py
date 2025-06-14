"""
Liquidity Magnet Strategy
Advanced liquidity-based trading system that identifies and exploits
liquidity pools, order book imbalances, and institutional order flow.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LiquidityEvent(Enum):
    SWEEP = "liquidity_sweep"
    HUNT = "stop_hunt"
    GRAB = "liquidity_grab"
    BUILDUP = "liquidity_buildup"
    VOID = "liquidity_void"

@dataclass
class LiquidityLevel:
    """Liquidity level information"""
    price: float
    liquidity_strength: float
    level_type: str  # "support", "resistance", "pivot"
    touch_count: int
    last_touch_time: datetime
    volume_at_level: float
    rejection_strength: float

class LiquidityMagnet:
    """
    Liquidity Magnet Strategy
    
    This strategy identifies and trades based on liquidity concepts:
    - Stop loss hunting and liquidity sweeps
    - Order book imbalances and liquidity pools
    - Institutional order flow patterns
    - Liquidity voids and gaps
    - Fair value gaps and displacement
    - Smart money vs retail sentiment divergence
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'liquidity_strength_threshold': 0.7,
            'stop_hunt_detection_periods': 20,
            'order_flow_window': 10,
            'liquidity_void_min_size': 0.005,  # 0.5% minimum void size
            'fair_value_gap_threshold': 0.003,  # 0.3% FVG threshold
            'institutional_volume_threshold': 2.0,  # 2x average volume
            'liquidity_level_tolerance': 0.002,  # 0.2% price tolerance
            'min_level_touches': 2,
            'max_level_age_hours': 24,
            'smart_money_confirmation_required': True
        }
        
        self.liquidity_levels = {}
        self.order_flow_history = {}
        self.stop_hunt_signals = {}
        self.liquidity_events = {}
        self.fair_value_gaps = {}
        
    async def analyze(self, symbol: str, price_data: List[float],
                     volume_data: List[float], 
                     timestamp: datetime,
                     order_book_data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Analyze liquidity patterns and generate magnet-based signals
        
        Returns:
            Dict with liquidity-based trading signal
        """
        try:
            if len(price_data) < self.config['stop_hunt_detection_periods']:
                return None
                
            # Update liquidity levels
            await self._update_liquidity_levels(symbol, price_data, volume_data, timestamp)
            
            # Detect stop hunting patterns
            stop_hunt = await self._detect_stop_hunting(
                symbol, price_data, volume_data, timestamp
            )
            
            # Analyze order flow imbalances
            order_flow_signal = await self._analyze_order_flow_imbalance(
                symbol, price_data, volume_data, order_book_data
            )
            
            # Detect liquidity sweeps
            liquidity_sweep = await self._detect_liquidity_sweep(
                symbol, price_data, timestamp
            )
            
            # Identify fair value gaps
            fvg_signal = await self._detect_fair_value_gaps(
                symbol, price_data, timestamp
            )
            
            # Detect liquidity voids
            liquidity_void = await self._detect_liquidity_voids(
                symbol, price_data, volume_data
            )
            
            # Analyze smart money vs retail sentiment
            smart_money_signal = await self._analyze_smart_money_flow(
                symbol, price_data, volume_data, timestamp
            )
            
            # Generate consolidated liquidity signal
            liquidity_signal = await self._generate_liquidity_signal(
                symbol, stop_hunt, order_flow_signal, liquidity_sweep,
                fvg_signal, liquidity_void, smart_money_signal,
                price_data, timestamp
            )
            
            if liquidity_signal:
                return {
                    'strategy': 'liquidity_magnet',
                    'symbol': symbol,
                    'signal': liquidity_signal['action'],
                    'confidence': liquidity_signal['confidence'],
                    'entry_price': price_data[-1],
                    'stop_loss': liquidity_signal['stop_loss'],
                    'take_profit': liquidity_signal['take_profit'],
                    'liquidity_event': liquidity_signal['event_type'],
                    'liquidity_strength': liquidity_signal['strength'],
                    'stop_hunt_detected': stop_hunt is not None,
                    'order_flow_imbalance': order_flow_signal['imbalance'] if order_flow_signal else 0,
                    'liquidity_sweep_level': liquidity_sweep['level'] if liquidity_sweep else 0,
                    'fair_value_gap': fvg_signal['gap_size'] if fvg_signal else 0,
                    'liquidity_void_detected': liquidity_void is not None,
                    'smart_money_alignment': smart_money_signal['aligned'] if smart_money_signal else False,
                    'active_liquidity_levels': len(self.liquidity_levels.get(symbol, {})),
                    'timestamp': timestamp.isoformat()
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error in LiquidityMagnet analysis for {symbol}: {e}")
            return None
    
    async def _update_liquidity_levels(self, symbol: str, prices: List[float],
                                     volumes: List[float], timestamp: datetime):
        """Update and maintain liquidity levels"""
        
        if symbol not in self.liquidity_levels:
            self.liquidity_levels[symbol] = {}
        
        current_price = prices[-1]
        
        # Identify significant levels (support/resistance)
        significant_levels = await self._identify_significant_levels(prices, volumes)
        
        for level_price, level_data in significant_levels.items():
            level_key = f"{level_price:.2f}"
            
            if level_key in self.liquidity_levels[symbol]:
                # Update existing level
                existing_level = self.liquidity_levels[symbol][level_key]
                
                # Check if price touched this level recently
                if abs(current_price - level_price) / level_price < self.config['liquidity_level_tolerance']:
                    existing_level.touch_count += 1
                    existing_level.last_touch_time = timestamp
                    existing_level.volume_at_level += volumes[-1]
                    
                    # Calculate rejection strength
                    if len(prices) >= 3:
                        pre_touch = prices[-3]
                        at_touch = prices[-2]
                        post_touch = prices[-1]
                        
                        if existing_level.level_type == "resistance":
                            rejection = max(0, (at_touch - post_touch) / at_touch)
                        else:  # support
                            rejection = max(0, (post_touch - at_touch) / at_touch)
                        
                        existing_level.rejection_strength = max(existing_level.rejection_strength, rejection)
            else:
                # Create new level
                self.liquidity_levels[symbol][level_key] = LiquidityLevel(
                    price=level_price,
                    liquidity_strength=level_data['strength'],
                    level_type=level_data['type'],
                    touch_count=1,
                    last_touch_time=timestamp,
                    volume_at_level=level_data['volume'],
                    rejection_strength=0.0
                )
        
        # Clean up old levels
        await self._cleanup_old_levels(symbol, timestamp)
    
    async def _identify_significant_levels(self, prices: List[float],
                                         volumes: List[float]) -> Dict[float, Dict]:
        """Identify significant support/resistance levels"""
        levels = {}
        
        if len(prices) < 20:
            return levels
        
        # Find swing highs and lows
        for i in range(5, len(prices) - 5):
            # Check for swing high
            is_high = all(prices[i] >= prices[j] for j in range(i-5, i+6) if j != i)
            
            # Check for swing low
            is_low = all(prices[i] <= prices[j] for j in range(i-5, i+6) if j != i)
            
            if is_high:
                strength = await self._calculate_level_strength(prices, volumes, i, "resistance")
                levels[prices[i]] = {
                    'type': 'resistance',
                    'strength': strength,
                    'volume': volumes[i] if i < len(volumes) else 0
                }
            elif is_low:
                strength = await self._calculate_level_strength(prices, volumes, i, "support")
                levels[prices[i]] = {
                    'type': 'support',
                    'strength': strength,
                    'volume': volumes[i] if i < len(volumes) else 0
                }
        
        return levels
    
    async def _calculate_level_strength(self, prices: List[float], volumes: List[float],
                                      index: int, level_type: str) -> float:
        """Calculate the strength of a support/resistance level"""
        
        # Base strength factors
        volume_strength = 0
        price_significance = 0
        
        # Volume at the level
        if index < len(volumes):
            avg_volume = np.mean(volumes[max(0, index-10):index+10])
            if avg_volume > 0:
                volume_strength = min(2.0, volumes[index] / avg_volume)
        
        # Price significance (how far from recent prices)
        recent_prices = prices[max(0, index-20):index+20]
        price_range = max(recent_prices) - min(recent_prices)
        if price_range > 0:
            if level_type == "resistance":
                price_significance = (prices[index] - min(recent_prices)) / price_range
            else:  # support
                price_significance = (max(recent_prices) - prices[index]) / price_range
        
        # Combined strength (0-1 scale)
        strength = (volume_strength * 0.6 + price_significance * 0.4) / 2
        return min(1.0, strength)
    
    async def _detect_stop_hunting(self, symbol: str, prices: List[float],
                                 volumes: List[float], timestamp: datetime) -> Optional[Dict]:
        """Detect stop hunting patterns"""
        
        periods = self.config['stop_hunt_detection_periods']
        if len(prices) < periods:
            return None
        
        current_price = prices[-1]
        recent_prices = prices[-periods:]
        recent_volumes = volumes[-periods:] if len(volumes) >= periods else volumes
        
        # Look for quick spike beyond significant level followed by reversal
        
        # Find recent significant levels
        if symbol in self.liquidity_levels:
            for level_key, level in self.liquidity_levels[symbol].items():
                level_price = level.price
                
                # Check for stop hunt pattern
                hunt_detected = await self._check_stop_hunt_pattern(
                    recent_prices, recent_volumes, level_price, level.level_type
                )
                
                if hunt_detected:
                    return {
                        'detected': True,
                        'hunted_level': level_price,
                        'level_type': level.level_type,
                        'strength': hunt_detected['strength'],
                        'reversal_signal': hunt_detected['reversal_direction'],
                        'volume_confirmation': hunt_detected['volume_confirmed']
                    }
        
        return None
    
    async def _check_stop_hunt_pattern(self, prices: List[float], volumes: List[float],
                                     level_price: float, level_type: str) -> Optional[Dict]:
        """Check for specific stop hunt pattern"""
        
        if len(prices) < 5:
            return None
        
        current_price = prices[-1]
        tolerance = self.config['liquidity_level_tolerance']
        
        # Pattern: approach level, spike through, quick reversal
        for i in range(len(prices) - 3, len(prices)):
            if i >= 2:
                approach_price = prices[i-2]
                spike_price = prices[i-1]
                reversal_price = prices[i]
                
                if level_type == "resistance":
                    # Hunt above resistance
                    approach_near = abs(approach_price - level_price) / level_price < tolerance
                    spike_through = spike_price > level_price * (1 + tolerance)
                    reversal_back = reversal_price < spike_price * 0.998  # At least 0.2% reversal
                    
                    if approach_near and spike_through and reversal_back:
                        spike_strength = (spike_price - level_price) / level_price
                        reversal_strength = (spike_price - reversal_price) / spike_price
                        
                        # Volume confirmation
                        volume_confirmed = False
                        if i-1 < len(volumes) and i-2 < len(volumes):
                            volume_confirmed = volumes[i-1] > volumes[i-2] * 1.2
                        
                        return {
                            'strength': min(1.0, spike_strength * 10),
                            'reversal_direction': 'SELL',
                            'volume_confirmed': volume_confirmed
                        }
                
                else:  # support
                    # Hunt below support
                    approach_near = abs(approach_price - level_price) / level_price < tolerance
                    spike_through = spike_price < level_price * (1 - tolerance)
                    reversal_back = reversal_price > spike_price * 1.002  # At least 0.2% reversal
                    
                    if approach_near and spike_through and reversal_back:
                        spike_strength = (level_price - spike_price) / level_price
                        reversal_strength = (reversal_price - spike_price) / spike_price
                        
                        # Volume confirmation
                        volume_confirmed = False
                        if i-1 < len(volumes) and i-2 < len(volumes):
                            volume_confirmed = volumes[i-1] > volumes[i-2] * 1.2
                        
                        return {
                            'strength': min(1.0, spike_strength * 10),
                            'reversal_direction': 'BUY',
                            'volume_confirmed': volume_confirmed
                        }
        
        return None
    
    async def _analyze_order_flow_imbalance(self, symbol: str, prices: List[float],
                                          volumes: List[float],
                                          order_book_data: Optional[Dict]) -> Optional[Dict]:
        """Analyze order flow imbalances"""
        
        window = self.config['order_flow_window']
        if len(prices) < window or len(volumes) < window:
            return None
        
        recent_prices = prices[-window:]
        recent_volumes = volumes[-window:]
        
        # Calculate buying vs selling pressure (simplified)
        buying_pressure = 0
        selling_pressure = 0
        
        for i in range(1, len(recent_prices)):
            price_change = recent_prices[i] - recent_prices[i-1]
            volume = recent_volumes[i]
            
            if price_change > 0:
                buying_pressure += volume * price_change
            elif price_change < 0:
                selling_pressure += volume * abs(price_change)
        
        total_pressure = buying_pressure + selling_pressure
        if total_pressure == 0:
            return None
        
        # Calculate imbalance
        net_pressure = buying_pressure - selling_pressure
        imbalance_ratio = net_pressure / total_pressure
        
        # Significant imbalance threshold
        if abs(imbalance_ratio) > 0.3:  # 30% imbalance
            return {
                'imbalance': imbalance_ratio,
                'direction': 'BUY' if imbalance_ratio > 0 else 'SELL',
                'strength': min(1.0, abs(imbalance_ratio) * 2),
                'buying_pressure': buying_pressure,
                'selling_pressure': selling_pressure
            }
        
        return None
    
    async def _detect_liquidity_sweep(self, symbol: str, prices: List[float],
                                    timestamp: datetime) -> Optional[Dict]:
        """Detect liquidity sweep events"""
        
        if symbol not in self.liquidity_levels or len(prices) < 5:
            return None
        
        current_price = prices[-1]
        prev_price = prices[-2]
        
        # Check if price has swept through any liquidity level
        for level_key, level in self.liquidity_levels[symbol].items():
            level_price = level.price
            
            # Check for sweep
            if level.level_type == "resistance":
                # Sweep above resistance
                if prev_price <= level_price and current_price > level_price:
                    sweep_strength = (current_price - level_price) / level_price
                    
                    return {
                        'detected': True,
                        'level': level_price,
                        'direction': 'upward_sweep',
                        'strength': min(1.0, sweep_strength * 20),
                        'level_strength': level.liquidity_strength
                    }
            
            else:  # support
                # Sweep below support
                if prev_price >= level_price and current_price < level_price:
                    sweep_strength = (level_price - current_price) / level_price
                    
                    return {
                        'detected': True,
                        'level': level_price,
                        'direction': 'downward_sweep',
                        'strength': min(1.0, sweep_strength * 20),
                        'level_strength': level.liquidity_strength
                    }
        
        return None
    
    async def _detect_fair_value_gaps(self, symbol: str, prices: List[float],
                                    timestamp: datetime) -> Optional[Dict]:
        """Detect fair value gaps (FVG)"""
        
        if len(prices) < 3:
            return None
        
        # Three-candle pattern for FVG
        candle1 = prices[-3]
        candle2 = prices[-2]  # Gap candle
        candle3 = prices[-1]
        
        # Bullish FVG: gap up where candle1 high < candle3 low
        if candle2 > candle1 and candle3 > candle2:
            gap_size = (candle3 - candle1) / candle1
            
            if gap_size >= self.config['fair_value_gap_threshold']:
                return {
                    'detected': True,
                    'type': 'bullish_fvg',
                    'gap_size': gap_size,
                    'gap_low': candle1,
                    'gap_high': candle3,
                    'strength': min(1.0, gap_size * 50)
                }
        
        # Bearish FVG: gap down where candle1 low > candle3 high
        elif candle2 < candle1 and candle3 < candle2:
            gap_size = (candle1 - candle3) / candle1
            
            if gap_size >= self.config['fair_value_gap_threshold']:
                return {
                    'detected': True,
                    'type': 'bearish_fvg',
                    'gap_size': gap_size,
                    'gap_low': candle3,
                    'gap_high': candle1,
                    'strength': min(1.0, gap_size * 50)
                }
        
        return None
    
    async def _detect_liquidity_voids(self, symbol: str, prices: List[float],
                                    volumes: List[float]) -> Optional[Dict]:
        """Detect liquidity voids (areas with low volume/activity)"""
        
        if len(prices) < 10 or len(volumes) < 10:
            return None
        
        current_price = prices[-1]
        
        # Look for price ranges with unusually low volume
        window = 10
        recent_prices = prices[-window:]
        recent_volumes = volumes[-window:]
        
        # Find price range with lowest volume density
        min_volume_density = float('inf')
        void_range = None
        
        for i in range(len(recent_prices) - 2):
            price_range = abs(recent_prices[i+2] - recent_prices[i])
            volume_in_range = sum(recent_volumes[i:i+3])
            
            if price_range > 0:
                volume_density = volume_in_range / price_range
                
                if volume_density < min_volume_density:
                    min_volume_density = volume_density
                    void_range = (min(recent_prices[i:i+3]), max(recent_prices[i:i+3]))
        
        if void_range:
            void_size = (void_range[1] - void_range[0]) / void_range[0]
            
            if void_size >= self.config['liquidity_void_min_size']:
                # Check if current price is approaching the void
                distance_to_void = min(
                    abs(current_price - void_range[0]) / current_price,
                    abs(current_price - void_range[1]) / current_price
                )
                
                if distance_to_void < 0.01:  # Within 1% of void
                    return {
                        'detected': True,
                        'void_low': void_range[0],
                        'void_high': void_range[1],
                        'void_size': void_size,
                        'volume_density': min_volume_density,
                        'distance': distance_to_void
                    }
        
        return None
    
    async def _analyze_smart_money_flow(self, symbol: str, prices: List[float],
                                      volumes: List[float], timestamp: datetime) -> Optional[Dict]:
        """Analyze smart money vs retail sentiment"""
        
        if len(prices) < 20 or len(volumes) < 20:
            return None
        
        # Detect institutional volume patterns
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        
        # Smart money indicators
        institutional_volume = current_volume > avg_volume * self.config['institutional_volume_threshold']
        
        # Price action vs volume divergence
        price_change = (prices[-1] - prices[-10]) / prices[-10]
        volume_change = (np.mean(volumes[-5:]) - np.mean(volumes[-10:-5])) / np.mean(volumes[-10:-5])
        
        # Smart money often moves price with less volume (efficiency)
        # Retail often creates volume spikes with minimal price movement
        
        smart_money_behavior = False
        if abs(price_change) > 0.02 and volume_change < 0.5:  # Price moved significantly with moderate volume
            smart_money_behavior = True
        
        # Off-hours or unusual timing patterns (simplified)
        is_off_hours = timestamp.hour < 9 or timestamp.hour > 15  # Simplified market hours
        
        if institutional_volume or smart_money_behavior:
            signal_direction = 'BUY' if price_change > 0 else 'SELL'
            
            return {
                'aligned': True,
                'direction': signal_direction,
                'institutional_volume': institutional_volume,
                'smart_money_behavior': smart_money_behavior,
                'off_hours_activity': is_off_hours,
                'confidence': 0.7 if smart_money_behavior else 0.5
            }
        
        return None
    
    async def _generate_liquidity_signal(self, symbol: str, stop_hunt: Optional[Dict],
                                       order_flow: Optional[Dict], liquidity_sweep: Optional[Dict],
                                       fvg_signal: Optional[Dict], liquidity_void: Optional[Dict],
                                       smart_money: Optional[Dict], prices: List[float],
                                       timestamp: datetime) -> Optional[Dict]:
        """Generate consolidated liquidity-based signal"""
        
        current_price = prices[-1]
        signal = None
        confidence = 0.5
        event_type = "none"
        strength = 0
        
        # Priority 1: Stop hunting (highest confidence)
        if stop_hunt and stop_hunt['volume_confirmation']:
            signal = stop_hunt['reversal_signal']
            confidence = 0.8
            event_type = LiquidityEvent.HUNT.value
            strength = stop_hunt['strength']
        
        # Priority 2: Liquidity sweep with reversal
        elif liquidity_sweep and liquidity_sweep['level_strength'] > 0.7:
            if liquidity_sweep['direction'] == 'upward_sweep':
                signal = 'SELL'  # Fade the sweep
            else:
                signal = 'BUY'  # Fade the sweep
            
            confidence = 0.75
            event_type = LiquidityEvent.SWEEP.value
            strength = liquidity_sweep['strength']
        
        # Priority 3: Order flow imbalance with confirmation
        elif order_flow and abs(order_flow['imbalance']) > 0.5:
            signal = order_flow['direction']
            confidence = 0.65
            event_type = LiquidityEvent.GRAB.value
            strength = order_flow['strength']
            
            # Boost confidence with smart money alignment
            if smart_money and smart_money['direction'] == signal:
                confidence += 0.1
        
        # Priority 4: Fair value gap
        elif fvg_signal and fvg_signal['strength'] > 0.6:
            if fvg_signal['type'] == 'bullish_fvg':
                signal = 'BUY'
            else:
                signal = 'SELL'
            
            confidence = 0.6
            event_type = "fair_value_gap"
            strength = fvg_signal['strength']
        
        # Priority 5: Liquidity void
        elif liquidity_void:
            # Expect price to move quickly through void
            if current_price < (liquidity_void['void_low'] + liquidity_void['void_high']) / 2:
                signal = 'BUY'  # Price below void midpoint
            else:
                signal = 'SELL'  # Price above void midpoint
            
            confidence = 0.55
            event_type = LiquidityEvent.VOID.value
            strength = liquidity_void['void_size'] * 10
        
        # Apply smart money confirmation if required
        if self.config['smart_money_confirmation_required'] and smart_money:
            if signal and smart_money['direction'] != signal:
                # Conflicting signals - reduce confidence or cancel
                confidence *= 0.7
                if confidence < 0.6:
                    return None
        
        if signal and confidence >= self.config['liquidity_strength_threshold']:
            
            # Calculate stops and targets based on liquidity levels
            atr = np.std(prices[-14:]) if len(prices) >= 14 else current_price * 0.01
            
            if signal == 'BUY':
                stop_loss = current_price - (atr * 1.5)
                take_profit = current_price + (atr * 2.5)
            else:
                stop_loss = current_price + (atr * 1.5)
                take_profit = current_price - (atr * 2.5)
            
            # Adjust stops based on nearby liquidity levels
            if symbol in self.liquidity_levels:
                await self._adjust_stops_for_liquidity(
                    symbol, signal, current_price, stop_loss, take_profit
                )
            
            return {
                'action': signal,
                'confidence': min(0.95, confidence),
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'event_type': event_type,
                'strength': strength,
                'reasoning': f"Liquidity {event_type}: {strength:.2f} strength, "
                           f"Smart money aligned: {smart_money is not None}"
            }
        
        return None
    
    async def _adjust_stops_for_liquidity(self, symbol: str, signal: str,
                                        current_price: float, stop_loss: float,
                                        take_profit: float) -> Tuple[float, float]:
        """Adjust stops based on nearby liquidity levels"""
        
        levels = self.liquidity_levels[symbol]
        
        for level_key, level in levels.items():
            level_price = level.price
            
            # Adjust stop loss to respect liquidity levels
            if signal == 'BUY':
                # For buy signals, place stop below nearest support
                if level.level_type == 'support' and level_price < current_price:
                    if level_price < stop_loss:  # Level is below current stop
                        stop_loss = level_price * 0.995  # Just below support
            else:  # SELL
                # For sell signals, place stop above nearest resistance
                if level.level_type == 'resistance' and level_price > current_price:
                    if level_price > stop_loss:  # Level is above current stop
                        stop_loss = level_price * 1.005  # Just above resistance
        
        return stop_loss, take_profit
    
    async def _cleanup_old_levels(self, symbol: str, current_time: datetime):
        """Clean up old liquidity levels"""
        
        if symbol not in self.liquidity_levels:
            return
        
        max_age = timedelta(hours=self.config['max_level_age_hours'])
        levels_to_remove = []
        
        for level_key, level in self.liquidity_levels[symbol].items():
            age = current_time - level.last_touch_time
            
            # Remove old levels or levels with insufficient touches
            if (age > max_age or 
                level.touch_count < self.config['min_level_touches']):
                levels_to_remove.append(level_key)
        
        for level_key in levels_to_remove:
            del self.liquidity_levels[symbol][level_key]
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': 'Liquidity Magnet',
            'description': 'Advanced liquidity-based trading using order flow and institutional patterns',
            'risk_level': 'Medium-High',
            'best_market_conditions': 'High liquidity markets with clear institutional activity',
            'parameters': self.config,
            'signals_generated': ['BUY', 'SELL'],
            'features': [
                'Stop loss hunting detection',
                'Liquidity sweep identification',
                'Order flow imbalance analysis',
                'Fair value gap detection',
                'Liquidity void identification',
                'Smart money flow analysis',
                'Dynamic liquidity level tracking',
                'Institutional vs retail sentiment'
            ],
            'liquidity_events': [event.value for event in LiquidityEvent],
            'detection_methods': {
                'stop_hunting': 'Pattern recognition with volume confirmation',
                'liquidity_sweeps': 'Level penetration with reversal analysis',
                'order_flow': 'Buying/selling pressure calculation',
                'fair_value_gaps': 'Three-candle gap pattern detection',
                'liquidity_voids': 'Low volume density identification',
                'smart_money': 'Volume efficiency and timing analysis'
            }
        }
