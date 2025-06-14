"""
Pattern Hunter Strategy
Advanced pattern recognition and harmonic trading system that identifies
classic chart patterns, harmonic patterns, and order flow patterns.
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

class PatternType(Enum):
    HARMONIC = "harmonic"
    CLASSIC = "classic"
    CANDLESTICK = "candlestick"
    ORDER_FLOW = "order_flow"

@dataclass
class PatternSignal:
    """Pattern detection result"""
    pattern_name: str
    pattern_type: PatternType
    signal: str  # BUY/SELL
    confidence: float
    completion_point: float
    target_levels: List[float]
    stop_loss: float
    pattern_points: Dict
    formation_quality: float

class PatternHunter:
    """
    Pattern Hunter Strategy
    
    This strategy identifies and trades various patterns:
    - Harmonic patterns (Gartley, Butterfly, Bat, Crab)
    - Classic patterns (Head & Shoulders, Double Top/Bottom, Triangles)
    - Candlestick patterns (Complex formations)
    - Order flow patterns (Supply/Demand zones)
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'min_pattern_completion': 0.8,  # 80% pattern completion
            'fibonacci_tolerance': 0.05,  # 5% tolerance for Fibonacci ratios
            'pattern_age_limit_bars': 50,
            'min_pattern_height_percent': 2.0,  # 2% minimum pattern height
            'harmonic_patterns_enabled': True,
            'classic_patterns_enabled': True,
            'candlestick_patterns_enabled': True,
            'order_flow_patterns_enabled': True,
            'pattern_strength_threshold': 0.7
        }
        
        self.active_patterns = {}
        self.pattern_history = {}
        self.fibonacci_ratios = {
            'gartley': {'XB': 0.618, 'AC': 0.382, 'BD': 1.272},
            'butterfly': {'XB': 0.786, 'AC': 0.382, 'BD': 1.618},
            'bat': {'XB': 0.382, 'AC': 0.382, 'BD': 2.24},
            'crab': {'XB': 0.382, 'AC': 0.382, 'BD': 3.618}
        }
        
    async def analyze(self, symbol: str, price_data: List[float],
                     volume_data: List[float], 
                     timestamp: datetime) -> Optional[Dict]:
        """
        Analyze price data for pattern formations
        
        Returns:
            Dict with pattern-based trading signal
        """
        try:
            if len(price_data) < 20:
                return None
                
            detected_patterns = []
            
            # Detect harmonic patterns
            if self.config['harmonic_patterns_enabled']:
                harmonic_patterns = await self._detect_harmonic_patterns(
                    symbol, price_data, timestamp
                )
                detected_patterns.extend(harmonic_patterns)
            
            # Detect classic chart patterns
            if self.config['classic_patterns_enabled']:
                classic_patterns = await self._detect_classic_patterns(
                    symbol, price_data, timestamp
                )
                detected_patterns.extend(classic_patterns)
            
            # Detect candlestick patterns
            if self.config['candlestick_patterns_enabled']:
                candlestick_patterns = await self._detect_candlestick_patterns(
                    symbol, price_data, timestamp
                )
                detected_patterns.extend(candlestick_patterns)
            
            # Detect order flow patterns
            if self.config['order_flow_patterns_enabled']:
                order_flow_patterns = await self._detect_order_flow_patterns(
                    symbol, price_data, volume_data, timestamp
                )
                detected_patterns.extend(order_flow_patterns)
            
            # Select best pattern for trading
            best_pattern = await self._select_best_pattern(detected_patterns)
            
            if best_pattern:
                return {
                    'strategy': 'pattern_hunter',
                    'symbol': symbol,
                    'signal': best_pattern.signal,
                    'confidence': best_pattern.confidence,
                    'entry_price': price_data[-1],
                    'stop_loss': best_pattern.stop_loss,
                    'take_profit_levels': best_pattern.target_levels,
                    'pattern_name': best_pattern.pattern_name,
                    'pattern_type': best_pattern.pattern_type.value,
                    'completion_point': best_pattern.completion_point,
                    'formation_quality': best_pattern.formation_quality,
                    'pattern_points': best_pattern.pattern_points,
                    'all_detected_patterns': [
                        {
                            'name': p.pattern_name,
                            'type': p.pattern_type.value,
                            'confidence': p.confidence,
                            'signal': p.signal
                        } for p in detected_patterns
                    ],
                    'timestamp': timestamp.isoformat()
                }
                
            return None
            
        except Exception as e:
            logger.error(f"Error in PatternHunter analysis for {symbol}: {e}")
            return None
    
    async def _detect_harmonic_patterns(self, symbol: str, 
                                      prices: List[float],
                                      timestamp: datetime) -> List[PatternSignal]:
        """Detect harmonic patterns (Gartley, Butterfly, Bat, Crab)"""
        patterns = []
        
        if len(prices) < 30:
            return patterns
        
        # Find potential XABCD pattern points
        swing_points = await self._find_swing_points(prices)
        
        if len(swing_points) >= 5:  # Need at least X, A, B, C, D points
            
            for pattern_name, ratios in self.fibonacci_ratios.items():
                pattern_signal = await self._validate_harmonic_pattern(
                    swing_points[-5:], ratios, pattern_name, prices
                )
                
                if pattern_signal:
                    patterns.append(pattern_signal)
        
        return patterns
    
    async def _find_swing_points(self, prices: List[float], 
                               lookback: int = 5) -> List[Tuple[int, float, str]]:
        """Find swing highs and lows in price data"""
        swing_points = []
        
        for i in range(lookback, len(prices) - lookback):
            # Check for swing high
            is_high = all(prices[i] >= prices[j] for j in range(i - lookback, i + lookback + 1) if j != i)
            
            # Check for swing low
            is_low = all(prices[i] <= prices[j] for j in range(i - lookback, i + lookback + 1) if j != i)
            
            if is_high:
                swing_points.append((i, prices[i], 'HIGH'))
            elif is_low:
                swing_points.append((i, prices[i], 'LOW'))
        
        return swing_points
    
    async def _validate_harmonic_pattern(self, swing_points: List[Tuple[int, float, str]],
                                       ratios: Dict, pattern_name: str,
                                       prices: List[float]) -> Optional[PatternSignal]:
        """Validate if swing points form a valid harmonic pattern"""
        
        if len(swing_points) < 5:
            return None
        
        # Extract XABCD points
        X = swing_points[0]
        A = swing_points[1] 
        B = swing_points[2]
        C = swing_points[3]
        D = swing_points[4]
        
        # Calculate retracement ratios
        XA_range = abs(A[1] - X[1])
        AB_range = abs(B[1] - A[1])
        BC_range = abs(C[1] - B[1])
        CD_range = abs(D[1] - C[1])
        
        if XA_range == 0:
            return None
        
        # Fibonacci ratio checks
        XB_ratio = AB_range / XA_range
        AC_ratio = abs(C[1] - A[1]) / XA_range
        BD_ratio = CD_range / BC_range
        
        # Check ratios against pattern requirements
        tolerance = self.config['fibonacci_tolerance']
        
        xb_valid = abs(XB_ratio - ratios['XB']) <= tolerance
        ac_valid = abs(AC_ratio - ratios['AC']) <= tolerance
        bd_valid = abs(BD_ratio - ratios['BD']) <= tolerance * 2  # More tolerance for D point
        
        if xb_valid and ac_valid and bd_valid:
            # Pattern is valid, determine signal
            
            # Calculate completion percentage
            completion = min(1.0, 
                           (1 - abs(XB_ratio - ratios['XB']) / tolerance) * 
                           (1 - abs(AC_ratio - ratios['AC']) / tolerance) * 
                           (1 - abs(BD_ratio - ratios['BD']) / (tolerance * 2)))
            
            if completion >= self.config['min_pattern_completion']:
                
                # Determine signal based on pattern orientation
                if A[1] > X[1]:  # Bullish pattern (potential buy at D)
                    signal = 'BUY'
                    stop_loss = D[1] * 0.99  # Just below D point
                    targets = [
                        D[1] + (C[1] - D[1]) * 0.382,  # 38.2% retracement
                        D[1] + (C[1] - D[1]) * 0.618,  # 61.8% retracement
                        C[1]  # Full retracement to C
                    ]
                else:  # Bearish pattern (potential sell at D)
                    signal = 'SELL'
                    stop_loss = D[1] * 1.01  # Just above D point
                    targets = [
                        D[1] - (D[1] - C[1]) * 0.382,
                        D[1] - (D[1] - C[1]) * 0.618,
                        C[1]
                    ]
                
                return PatternSignal(
                    pattern_name=f"{pattern_name.title()} Harmonic",
                    pattern_type=PatternType.HARMONIC,
                    signal=signal,
                    confidence=completion * 0.9,  # Max 90% confidence
                    completion_point=D[1],
                    target_levels=targets,
                    stop_loss=stop_loss,
                    pattern_points={
                        'X': {'index': X[0], 'price': X[1]},
                        'A': {'index': A[0], 'price': A[1]},
                        'B': {'index': B[0], 'price': B[1]},
                        'C': {'index': C[0], 'price': C[1]},
                        'D': {'index': D[0], 'price': D[1]}
                    },
                    formation_quality=completion
                )
        
        return None
    
    async def _detect_classic_patterns(self, symbol: str,
                                     prices: List[float],
                                     timestamp: datetime) -> List[PatternSignal]:
        """Detect classic chart patterns"""
        patterns = []
        
        # Head and Shoulders
        h_and_s = await self._detect_head_and_shoulders(prices)
        if h_and_s:
            patterns.append(h_and_s)
        
        # Double Top/Bottom
        double_pattern = await self._detect_double_top_bottom(prices)
        if double_pattern:
            patterns.append(double_pattern)
        
        # Triangle patterns
        triangle = await self._detect_triangle_patterns(prices)
        if triangle:
            patterns.append(triangle)
        
        # Flag and Pennant
        flag_pennant = await self._detect_flag_pennant(prices)
        if flag_pennant:
            patterns.append(flag_pennant)
        
        return patterns
    
    async def _detect_head_and_shoulders(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect Head and Shoulders pattern"""
        if len(prices) < 20:
            return None
        
        # Find three consecutive peaks
        swing_points = await self._find_swing_points(prices, 3)
        highs = [point for point in swing_points if point[2] == 'HIGH']
        
        if len(highs) >= 3:
            # Check last three highs for H&S pattern
            left_shoulder = highs[-3]
            head = highs[-2]
            right_shoulder = highs[-1]
            
            # H&S criteria: head higher than both shoulders, shoulders roughly equal
            head_higher = head[1] > left_shoulder[1] and head[1] > right_shoulder[1]
            shoulders_similar = abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05
            
            if head_higher and shoulders_similar:
                # Calculate neckline (simplified as average of valley lows)
                valleys = [point for point in swing_points if point[2] == 'LOW']
                if len(valleys) >= 2:
                    recent_valleys = valleys[-2:]
                    neckline = np.mean([v[1] for v in recent_valleys])
                    
                    # Pattern target: neckline - (head - neckline)
                    pattern_height = head[1] - neckline
                    target = neckline - pattern_height
                    
                    return PatternSignal(
                        pattern_name="Head and Shoulders",
                        pattern_type=PatternType.CLASSIC,
                        signal='SELL',
                        confidence=0.75,
                        completion_point=right_shoulder[1],
                        target_levels=[target],
                        stop_loss=head[1] * 1.02,
                        pattern_points={
                            'left_shoulder': left_shoulder[1],
                            'head': head[1],
                            'right_shoulder': right_shoulder[1],
                            'neckline': neckline
                        },
                        formation_quality=0.8
                    )
        
        return None
    
    async def _detect_double_top_bottom(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect Double Top or Double Bottom pattern"""
        if len(prices) < 15:
            return None
        
        swing_points = await self._find_swing_points(prices, 3)
        
        # Double Top
        highs = [point for point in swing_points if point[2] == 'HIGH']
        if len(highs) >= 2:
            last_two_highs = highs[-2:]
            price_similarity = abs(last_two_highs[0][1] - last_two_highs[1][1]) / last_two_highs[0][1]
            
            if price_similarity < 0.03:  # Within 3%
                # Find valley between the tops
                valleys = [point for point in swing_points if point[2] == 'LOW']
                if valleys:
                    valley_between = None
                    for valley in valleys:
                        if last_two_highs[0][0] < valley[0] < last_two_highs[1][0]:
                            valley_between = valley
                            break
                    
                    if valley_between:
                        support_level = valley_between[1]
                        pattern_height = last_two_highs[0][1] - support_level
                        target = support_level - pattern_height
                        
                        return PatternSignal(
                            pattern_name="Double Top",
                            pattern_type=PatternType.CLASSIC,
                            signal='SELL',
                            confidence=0.7,
                            completion_point=last_two_highs[1][1],
                            target_levels=[target],
                            stop_loss=last_two_highs[1][1] * 1.02,
                            pattern_points={
                                'first_top': last_two_highs[0][1],
                                'second_top': last_two_highs[1][1],
                                'support': support_level
                            },
                            formation_quality=1 - price_similarity
                        )
        
        # Double Bottom (similar logic, inverted)
        lows = [point for point in swing_points if point[2] == 'LOW']
        if len(lows) >= 2:
            last_two_lows = lows[-2:]
            price_similarity = abs(last_two_lows[0][1] - last_two_lows[1][1]) / last_two_lows[0][1]
            
            if price_similarity < 0.03:
                highs = [point for point in swing_points if point[2] == 'HIGH']
                if highs:
                    peak_between = None
                    for high in highs:
                        if last_two_lows[0][0] < high[0] < last_two_lows[1][0]:
                            peak_between = high
                            break
                    
                    if peak_between:
                        resistance_level = peak_between[1]
                        pattern_height = resistance_level - last_two_lows[0][1]
                        target = resistance_level + pattern_height
                        
                        return PatternSignal(
                            pattern_name="Double Bottom",
                            pattern_type=PatternType.CLASSIC,
                            signal='BUY',
                            confidence=0.7,
                            completion_point=last_two_lows[1][1],
                            target_levels=[target],
                            stop_loss=last_two_lows[1][1] * 0.98,
                            pattern_points={
                                'first_bottom': last_two_lows[0][1],
                                'second_bottom': last_two_lows[1][1],
                                'resistance': resistance_level
                            },
                            formation_quality=1 - price_similarity
                        )
        
        return None
    
    async def _detect_triangle_patterns(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        if len(prices) < 20:
            return None
        
        # Simple triangle detection using linear regression on highs and lows
        swing_points = await self._find_swing_points(prices, 2)
        highs = [point for point in swing_points if point[2] == 'HIGH']
        lows = [point for point in swing_points if point[2] == 'LOW']
        
        if len(highs) >= 3 and len(lows) >= 3:
            # Recent highs and lows
            recent_highs = highs[-3:]
            recent_lows = lows[-3:]
            
            # Calculate trend lines
            high_trend = await self._calculate_trend_slope([h[1] for h in recent_highs])
            low_trend = await self._calculate_trend_slope([l[1] for l in recent_lows])
            
            # Ascending triangle: flat resistance, rising support
            if abs(high_trend) < 0.001 and low_trend > 0.001:
                return PatternSignal(
                    pattern_name="Ascending Triangle",
                    pattern_type=PatternType.CLASSIC,
                    signal='BUY',
                    confidence=0.65,
                    completion_point=prices[-1],
                    target_levels=[recent_highs[-1][1] * 1.05],
                    stop_loss=recent_lows[-1][1] * 0.98,
                    pattern_points={'type': 'ascending_triangle'},
                    formation_quality=0.7
                )
            
            # Descending triangle: declining resistance, flat support
            elif high_trend < -0.001 and abs(low_trend) < 0.001:
                return PatternSignal(
                    pattern_name="Descending Triangle",
                    pattern_type=PatternType.CLASSIC,
                    signal='SELL',
                    confidence=0.65,
                    completion_point=prices[-1],
                    target_levels=[recent_lows[-1][1] * 0.95],
                    stop_loss=recent_highs[-1][1] * 1.02,
                    pattern_points={'type': 'descending_triangle'},
                    formation_quality=0.7
                )
        
        return None
    
    async def _detect_flag_pennant(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect flag and pennant patterns"""
        if len(prices) < 15:
            return None
        
        # Look for strong move followed by consolidation
        recent_prices = prices[-15:]
        strong_move_threshold = 0.03  # 3% move
        
        # Check for strong initial move
        initial_move = (recent_prices[5] - recent_prices[0]) / recent_prices[0]
        
        if abs(initial_move) >= strong_move_threshold:
            # Check for consolidation in recent 10 periods
            consolidation_range = max(recent_prices[-10:]) - min(recent_prices[-10:])
            consolidation_percent = consolidation_range / recent_prices[-10]
            
            if consolidation_percent < 0.02:  # Less than 2% range = consolidation
                signal = 'BUY' if initial_move > 0 else 'SELL'
                
                return PatternSignal(
                    pattern_name="Flag Pattern",
                    pattern_type=PatternType.CLASSIC,
                    signal=signal,
                    confidence=0.6,
                    completion_point=prices[-1],
                    target_levels=[prices[-1] * (1 + initial_move)],
                    stop_loss=prices[-1] * (0.98 if signal == 'BUY' else 1.02),
                    pattern_points={
                        'flagpole_start': recent_prices[0],
                        'flagpole_end': recent_prices[5],
                        'consolidation_range': consolidation_percent
                    },
                    formation_quality=1 - consolidation_percent
                )
        
        return None
    
    async def _detect_candlestick_patterns(self, symbol: str,
                                         prices: List[float],
                                         timestamp: datetime) -> List[PatternSignal]:
        """Detect complex candlestick patterns"""
        patterns = []
        
        if len(prices) < 5:
            return patterns
        
        # Three White Soldiers / Three Black Crows
        three_pattern = await self._detect_three_soldiers_crows(prices)
        if three_pattern:
            patterns.append(three_pattern)
        
        # Morning/Evening Star
        star_pattern = await self._detect_star_patterns(prices)
        if star_pattern:
            patterns.append(star_pattern)
        
        return patterns
    
    async def _detect_three_soldiers_crows(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect Three White Soldiers or Three Black Crows"""
        if len(prices) < 4:
            return None
        
        last_four = prices[-4:]
        
        # Three White Soldiers: three consecutive rising periods
        if all(last_four[i] > last_four[i-1] for i in range(1, 4)):
            total_rise = (last_four[-1] - last_four[0]) / last_four[0]
            if total_rise > 0.02:  # At least 2% rise
                return PatternSignal(
                    pattern_name="Three White Soldiers",
                    pattern_type=PatternType.CANDLESTICK,
                    signal='BUY',
                    confidence=0.7,
                    completion_point=prices[-1],
                    target_levels=[prices[-1] * 1.03],
                    stop_loss=prices[-1] * 0.97,
                    pattern_points={'pattern_strength': total_rise},
                    formation_quality=min(1.0, total_rise * 10)
                )
        
        # Three Black Crows: three consecutive falling periods
        elif all(last_four[i] < last_four[i-1] for i in range(1, 4)):
            total_fall = (last_four[0] - last_four[-1]) / last_four[0]
            if total_fall > 0.02:  # At least 2% fall
                return PatternSignal(
                    pattern_name="Three Black Crows",
                    pattern_type=PatternType.CANDLESTICK,
                    signal='SELL',
                    confidence=0.7,
                    completion_point=prices[-1],
                    target_levels=[prices[-1] * 0.97],
                    stop_loss=prices[-1] * 1.03,
                    pattern_points={'pattern_strength': total_fall},
                    formation_quality=min(1.0, total_fall * 10)
                )
        
        return None
    
    async def _detect_star_patterns(self, prices: List[float]) -> Optional[PatternSignal]:
        """Detect Morning Star and Evening Star patterns"""
        if len(prices) < 3:
            return None
        
        last_three = prices[-3:]
        
        # Morning Star: down, small body, up
        if (last_three[1] < last_three[0] and 
            last_three[2] > last_three[1] and
            last_three[2] > last_three[0]):
            
            return PatternSignal(
                pattern_name="Morning Star",
                pattern_type=PatternType.CANDLESTICK,
                signal='BUY',
                confidence=0.65,
                completion_point=prices[-1],
                target_levels=[prices[-1] * 1.025],
                stop_loss=min(last_three) * 0.98,
                pattern_points={'star_body': last_three[1]},
                formation_quality=0.7
            )
        
        # Evening Star: up, small body, down
        elif (last_three[1] > last_three[0] and
              last_three[2] < last_three[1] and
              last_three[2] < last_three[0]):
            
            return PatternSignal(
                pattern_name="Evening Star",
                pattern_type=PatternType.CANDLESTICK,
                signal='SELL',
                confidence=0.65,
                completion_point=prices[-1],
                target_levels=[prices[-1] * 0.975],
                stop_loss=max(last_three) * 1.02,
                pattern_points={'star_body': last_three[1]},
                formation_quality=0.7
            )
        
        return None
    
    async def _detect_order_flow_patterns(self, symbol: str,
                                        prices: List[float],
                                        volumes: List[float],
                                        timestamp: datetime) -> List[PatternSignal]:
        """Detect order flow and supply/demand patterns"""
        patterns = []
        
        if len(prices) < 10 or len(volumes) < 10:
            return patterns
        
        # Supply/Demand zone detection
        supply_demand = await self._detect_supply_demand_zones(prices, volumes)
        if supply_demand:
            patterns.append(supply_demand)
        
        # Volume profile anomalies
        volume_anomaly = await self._detect_volume_anomalies(prices, volumes)
        if volume_anomaly:
            patterns.append(volume_anomaly)
        
        return patterns
    
    async def _detect_supply_demand_zones(self, prices: List[float],
                                        volumes: List[float]) -> Optional[PatternSignal]:
        """Detect supply and demand zones"""
        
        # Look for rapid price moves with high volume (supply/demand imbalance)
        if len(prices) < 10:
            return None
        
        recent_prices = prices[-10:]
        recent_volumes = volumes[-10:]
        
        # Find largest single-period move
        max_move_idx = 0
        max_move_percent = 0
        
        for i in range(1, len(recent_prices)):
            move_percent = abs(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            if move_percent > max_move_percent:
                max_move_percent = move_percent
                max_move_idx = i
        
        # Check if move was accompanied by high volume
        if max_move_percent > 0.015:  # 1.5% move
            avg_volume = np.mean(recent_volumes)
            move_volume = recent_volumes[max_move_idx]
            
            if move_volume > avg_volume * 1.5:  # 50% above average volume
                move_direction = 'up' if recent_prices[max_move_idx] > recent_prices[max_move_idx-1] else 'down'
                
                # Supply zone (after upward move)
                if move_direction == 'up':
                    zone_price = recent_prices[max_move_idx]
                    return PatternSignal(
                        pattern_name="Supply Zone",
                        pattern_type=PatternType.ORDER_FLOW,
                        signal='SELL',
                        confidence=0.6,
                        completion_point=zone_price,
                        target_levels=[zone_price * 0.98],
                        stop_loss=zone_price * 1.015,
                        pattern_points={
                            'zone_price': zone_price,
                            'volume_ratio': move_volume / avg_volume,
                            'move_percent': max_move_percent
                        },
                        formation_quality=min(1.0, move_volume / avg_volume / 3)
                    )
                
                # Demand zone (after downward move)
                else:
                    zone_price = recent_prices[max_move_idx]
                    return PatternSignal(
                        pattern_name="Demand Zone",
                        pattern_type=PatternType.ORDER_FLOW,
                        signal='BUY',
                        confidence=0.6,
                        completion_point=zone_price,
                        target_levels=[zone_price * 1.02],
                        stop_loss=zone_price * 0.985,
                        pattern_points={
                            'zone_price': zone_price,
                            'volume_ratio': move_volume / avg_volume,
                            'move_percent': max_move_percent
                        },
                        formation_quality=min(1.0, move_volume / avg_volume / 3)
                    )
        
        return None
    
    async def _detect_volume_anomalies(self, prices: List[float],
                                     volumes: List[float]) -> Optional[PatternSignal]:
        """Detect volume anomalies that might indicate institutional activity"""
        
        if len(volumes) < 20:
            return None
        
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:-1])  # Exclude current volume
        
        # Unusual volume spike
        if current_volume > avg_volume * 3:  # 3x average volume
            price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
            
            # High volume with minimal price change (accumulation/distribution)
            if abs(price_change) < 0.005:  # Less than 0.5% price move
                return PatternSignal(
                    pattern_name="Volume Anomaly",
                    pattern_type=PatternType.ORDER_FLOW,
                    signal='BUY' if price_change >= 0 else 'SELL',
                    confidence=0.5,
                    completion_point=prices[-1],
                    target_levels=[prices[-1] * (1.01 if price_change >= 0 else 0.99)],
                    stop_loss=prices[-1] * (0.995 if price_change >= 0 else 1.005),
                    pattern_points={
                        'volume_ratio': current_volume / avg_volume,
                        'price_change': price_change
                    },
                    formation_quality=min(1.0, current_volume / avg_volume / 5)
                )
        
        return None
    
    async def _select_best_pattern(self, patterns: List[PatternSignal]) -> Optional[PatternSignal]:
        """Select the best pattern from detected patterns"""
        
        if not patterns:
            return None
        
        # Filter patterns by strength threshold
        strong_patterns = [p for p in patterns if p.confidence >= self.config['pattern_strength_threshold']]
        
        if not strong_patterns:
            return None
        
        # Score patterns based on confidence and formation quality
        scored_patterns = []
        for pattern in strong_patterns:
            score = pattern.confidence * 0.7 + pattern.formation_quality * 0.3
            scored_patterns.append((score, pattern))
        
        # Return highest scoring pattern
        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        return scored_patterns[0][1]
    
    # Helper methods
    async def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using linear regression"""
        if len(values) < 2:
            return 0
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope / np.mean(values)  # Normalize by average value
    
    def get_strategy_info(self) -> Dict:
        """Get strategy information"""
        return {
            'name': 'Pattern Hunter',
            'description': 'Advanced pattern recognition for harmonic, classic, and order flow patterns',
            'risk_level': 'Medium',
            'best_market_conditions': 'All market conditions with clear pattern formations',
            'parameters': self.config,
            'signals_generated': ['BUY', 'SELL'],
            'features': [
                'Harmonic pattern detection (Gartley, Butterfly, Bat, Crab)',
                'Classic chart patterns (H&S, Double Top/Bottom, Triangles)',
                'Complex candlestick patterns',
                'Supply/demand zone identification',
                'Order flow analysis',
                'Pattern quality scoring',
                'Multi-target profit levels'
            ],
            'pattern_types': {
                'harmonic': list(self.fibonacci_ratios.keys()),
                'classic': ['Head & Shoulders', 'Double Top/Bottom', 'Triangles', 'Flags'],
                'candlestick': ['Three Soldiers/Crows', 'Morning/Evening Star'],
                'order_flow': ['Supply/Demand Zones', 'Volume Anomalies']
            }
        }
