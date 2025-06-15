"""
Autonomous Trading Engine
Real-time execution engine for the 7 trading strategies
"""

import asyncio
import uuid
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
import logging
import json
import random
import numpy as np

logger = logging.getLogger(__name__)

class AutonomousTradeEngine:
    def __init__(self):
        self.strategies = {
            "MomentumSurfer": {
                "active": True,
                "allocation": 15,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 5,
                "parameters": {"fast_period": 8, "slow_period": 21}
            },
            "NewsImpactScalper": {
                "active": True,
                "allocation": 12,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 3,
                "parameters": {"scalp_duration_seconds": 300}
            },
            "VolatilityExplosion": {
                "active": True,
                "allocation": 18,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 8,
                "parameters": {"volatility_lookback": 30}
            },
            "ConfluenceAmplifier": {
                "active": True,
                "allocation": 20,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 10,
                "parameters": {"min_confluence_signals": 3}
            },
            "PatternHunter": {
                "active": True,
                "allocation": 16,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 7,
                "parameters": {"harmonic_patterns_enabled": True}
            },
            "LiquidityMagnet": {
                "active": True,
                "allocation": 14,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 6,
                "parameters": {"liquidity_strength_threshold": 0.7}
            },
            "VolumeProfileScalper": {
                "active": True,
                "allocation": 5,
                "trades_today": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "pnl": 0.0,
                "last_signal_time": None,
                "cooldown_minutes": 2,
                "parameters": {"scalp_timeframe_seconds": 30}
            }
        }
        
        self.active_positions = {}
        self.trade_history = []
        self.daily_pnl = 0.0
        self.total_capital = 5000000  # 50 lakh starting capital
        self.used_capital = 0.0
        self.risk_per_trade = 0.02  # 2% risk per trade
        self.running = False
        self.market_data_buffer = {}
        
    async def start_autonomous_trading(self):
        """Start the autonomous trading engine"""
        if not self.running:
            self.running = True
            asyncio.create_task(self._trading_loop())
            logger.info("🤖 Autonomous Trading Engine started")
            
    async def stop_autonomous_trading(self):
        """Stop autonomous trading"""
        self.running = False
        logger.info("⏹️ Autonomous Trading Engine stopped")
        
    async def _trading_loop(self):
        """Main trading loop - analyzes market and executes trades"""
        while self.running:
            try:
                # Only trade during market hours
                if self._is_market_open():
                    await self._analyze_and_trade()
                    await self._manage_positions()
                
                # Check every 30 seconds during market hours, 5 minutes after hours
                sleep_time = 30 if self._is_market_open() else 300
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in autonomous trading loop: {e}")
                await asyncio.sleep(60)
                
    def update_market_data(self, market_data: Dict):
        """Update market data for strategy analysis"""
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
                "change_percent": data.get("change_percent", 0),
                "open": data.get("open", 0)
            }
            
            self.market_data_buffer[symbol].append(data_point)
            
            # Keep only last 100 data points (about 50 minutes)
            if len(self.market_data_buffer[symbol]) > 100:
                self.market_data_buffer[symbol] = self.market_data_buffer[symbol][-100:]
    
    async def _analyze_and_trade(self):
        """Analyze market data with each strategy and execute trades"""
        for strategy_name, strategy_data in self.strategies.items():
            if not strategy_data["active"]:
                continue
                
            try:
                # Check cooldown period
                if self._is_strategy_in_cooldown(strategy_name):
                    continue
                
                # Analyze market for trading signals
                signal = await self._run_strategy_analysis(strategy_name)
                
                if signal and signal["confidence"] >= 70:
                    # Execute the trade
                    trade_result = await self._execute_autonomous_trade(strategy_name, signal)
                    
                    if trade_result:
                        # Update strategy performance
                        self._update_strategy_stats(strategy_name, trade_result)
                        
                        # Log the trade
                        logger.info(f"🎯 {strategy_name} executed trade: {signal['action']} {signal['symbol']} @ {signal['price']}")
                        
            except Exception as e:
                logger.error(f"Error in strategy {strategy_name}: {e}")
    
    async def _run_strategy_analysis(self, strategy_name: str) -> Optional[Dict]:
        """Run strategy-specific analysis on market data"""
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
        
        for symbol in symbols:
            if symbol not in self.market_data_buffer or len(self.market_data_buffer[symbol]) < 20:
                continue
                
            data = self.market_data_buffer[symbol]
            current_price = data[-1]["ltp"]
            
            if current_price == 0:
                continue
            
            # Strategy-specific analysis
            if strategy_name == "MomentumSurfer":
                signal = await self._momentum_surfer_analysis(symbol, data)
            elif strategy_name == "NewsImpactScalper":
                signal = await self._news_impact_scalper_analysis(symbol, data)
            elif strategy_name == "VolatilityExplosion":
                signal = await self._volatility_explosion_analysis(symbol, data)
            elif strategy_name == "ConfluenceAmplifier":
                signal = await self._confluence_amplifier_analysis(symbol, data)
            elif strategy_name == "PatternHunter":
                signal = await self._pattern_hunter_analysis(symbol, data)
            elif strategy_name == "LiquidityMagnet":
                signal = await self._liquidity_magnet_analysis(symbol, data)
            elif strategy_name == "VolumeProfileScalper":
                signal = await self._volume_profile_scalper_analysis(symbol, data)
            else:
                continue
                
            if signal:
                return signal
                
        return None
    
    async def _momentum_surfer_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Momentum Surfer strategy analysis"""
        try:
            prices = [d["ltp"] for d in data[-20:]]
            volumes = [d["volume"] for d in data[-20:]]
            
            # Calculate moving averages
            sma_8 = np.mean(prices[-8:])
            sma_21 = np.mean(prices[-21:]) if len(prices) >= 21 else np.mean(prices)
            
            current_price = prices[-1]
            price_momentum = (current_price - prices[-10]) / prices[-10] * 100
            volume_avg = np.mean(volumes[-5:])
            volume_current = volumes[-1]
            
            # Momentum signals
            bullish_signals = 0
            if sma_8 > sma_21:
                bullish_signals += 1
            if price_momentum > 0.3:
                bullish_signals += 1
            if volume_current > volume_avg * 1.2:
                bullish_signals += 1
            if current_price > max(prices[-5:]):
                bullish_signals += 1
            
            confidence = 60 + bullish_signals * 8
            
            if bullish_signals >= 3:
                return {
                    "symbol": symbol,
                    "action": "BUY",
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * 0.995,
                    "target": current_price * 1.01,
                    "reasoning": f"Momentum detected: {bullish_signals}/4 signals, SMA crossover, price momentum: {price_momentum:.2f}%"
                }
                
        except Exception as e:
            logger.error(f"Error in momentum surfer analysis: {e}")
            
        return None
    
    async def _news_impact_scalper_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """News Impact Scalper strategy analysis"""
        try:
            # Look for sudden price movements (news impact)
            recent_changes = [d["change_percent"] for d in data[-10:]]
            current_change = recent_changes[-1]
            avg_change = np.mean(recent_changes[:-1])
            
            # Detect news impact
            if abs(current_change) > abs(avg_change) * 2 and abs(current_change) > 0.5:
                current_price = data[-1]["ltp"]
                confidence = min(75 + abs(current_change) * 5, 95)
                
                action = "BUY" if current_change > 0 else "SELL"
                target_multiplier = 1.008 if action == "BUY" else 0.992
                stop_multiplier = 0.997 if action == "BUY" else 1.003
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": f"News impact detected: {current_change:.2f}% vs avg {avg_change:.2f}%"
                }
                
        except Exception as e:
            logger.error(f"Error in news impact scalper analysis: {e}")
            
        return None
    
    async def _volatility_explosion_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Volatility Explosion strategy analysis"""
        try:
            prices = [d["ltp"] for d in data[-30:]]
            
            # Calculate volatility
            returns = np.diff(prices) / prices[:-1]
            current_volatility = np.std(returns[-10:])
            avg_volatility = np.std(returns)
            
            # Detect volatility explosion
            if current_volatility > avg_volatility * 1.5:
                current_price = prices[-1]
                confidence = min(70 + (current_volatility / avg_volatility) * 10, 95)
                
                # Direction based on recent price movement
                recent_movement = (current_price - prices[-5]) / prices[-5]
                action = "BUY" if recent_movement > 0 else "SELL"
                
                target_multiplier = 1.015 if action == "BUY" else 0.985
                stop_multiplier = 0.992 if action == "BUY" else 1.008
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": f"Volatility explosion: {current_volatility:.4f} vs avg {avg_volatility:.4f}"
                }
                
        except Exception as e:
            logger.error(f"Error in volatility explosion analysis: {e}")
            
        return None
    
    async def _confluence_amplifier_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Confluence Amplifier strategy analysis"""
        try:
            prices = [d["ltp"] for d in data[-20:]]
            volumes = [d["volume"] for d in data[-10:]]
            
            current_price = prices[-1]
            confluence_signals = 0
            
            # Signal 1: Price above recent high
            if current_price > max(prices[-10:-1]):
                confluence_signals += 1
                
            # Signal 2: Volume surge
            if volumes[-1] > np.mean(volumes[:-1]) * 1.3:
                confluence_signals += 1
                
            # Signal 3: Consistent upward movement
            upward_candles = sum(1 for i in range(-5, -1) if prices[i] > prices[i-1])
            if upward_candles >= 3:
                confluence_signals += 1
                
            # Signal 4: Price momentum
            momentum = (current_price - prices[-10]) / prices[-10] * 100
            if abs(momentum) > 0.4:
                confluence_signals += 1
            
            if confluence_signals >= 3:
                confidence = 65 + confluence_signals * 7
                action = "BUY" if momentum > 0 else "SELL"
                
                target_multiplier = 1.012 if action == "BUY" else 0.988
                stop_multiplier = 0.994 if action == "BUY" else 1.006
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": f"Confluence detected: {confluence_signals}/4 signals aligned"
                }
                
        except Exception as e:
            logger.error(f"Error in confluence amplifier analysis: {e}")
            
        return None
    
    async def _pattern_hunter_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Pattern Hunter strategy analysis"""
        try:
            prices = [d["ltp"] for d in data[-15:]]
            
            # Simple pattern detection
            if self._detect_breakout_pattern(prices):
                current_price = prices[-1]
                confidence = 75
                
                # Determine direction
                recent_trend = (current_price - prices[-5]) / prices[-5]
                action = "BUY" if recent_trend > 0 else "SELL"
                
                target_multiplier = 1.018 if action == "BUY" else 0.982
                stop_multiplier = 0.991 if action == "BUY" else 1.009
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": "Breakout pattern detected"
                }
                
        except Exception as e:
            logger.error(f"Error in pattern hunter analysis: {e}")
            
        return None
    
    async def _liquidity_magnet_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Liquidity Magnet strategy analysis"""
        try:
            prices = [d["ltp"] for d in data[-15:]]
            volumes = [d["volume"] for d in data[-10:]]
            
            current_price = prices[-1]
            
            # Look for support/resistance levels
            resistance_level = max(prices[-10:])
            support_level = min(prices[-10:])
            
            # Check if price is near key levels with high volume
            near_resistance = abs(current_price - resistance_level) / resistance_level < 0.002
            near_support = abs(current_price - support_level) / support_level < 0.002
            high_volume = volumes[-1] > np.mean(volumes[:-1]) * 1.4
            
            if (near_resistance or near_support) and high_volume:
                confidence = 72
                
                # Direction based on level and volume
                if near_resistance:
                    action = "SELL"  # Expect rejection
                    target_multiplier = 0.992
                    stop_multiplier = 1.004
                else:
                    action = "BUY"  # Expect bounce
                    target_multiplier = 1.008
                    stop_multiplier = 0.996
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": f"Liquidity magnet at {'resistance' if near_resistance else 'support'} with high volume"
                }
                
        except Exception as e:
            logger.error(f"Error in liquidity magnet analysis: {e}")
            
        return None
    
    async def _volume_profile_scalper_analysis(self, symbol: str, data: List[Dict]) -> Optional[Dict]:
        """Volume Profile Scalper strategy analysis"""
        try:
            recent_data = data[-10:]
            volumes = [d["volume"] for d in recent_data]
            prices = [d["ltp"] for d in recent_data]
            
            current_price = prices[-1]
            current_volume = volumes[-1]
            avg_volume = np.mean(volumes[:-1])
            
            # Look for volume spikes with price movement
            volume_spike = current_volume > avg_volume * 2
            price_movement = abs((current_price - prices[-5]) / prices[-5]) > 0.003
            
            if volume_spike and price_movement:
                confidence = 78
                
                # Direction based on price movement
                movement_direction = (current_price - prices[-3]) / prices[-3]
                action = "BUY" if movement_direction > 0 else "SELL"
                
                # Quick scalp targets
                target_multiplier = 1.005 if action == "BUY" else 0.995
                stop_multiplier = 0.998 if action == "BUY" else 1.002
                
                return {
                    "symbol": symbol,
                    "action": action,
                    "price": current_price,
                    "confidence": confidence,
                    "quantity": self._calculate_position_size(current_price, symbol),
                    "stop_loss": current_price * stop_multiplier,
                    "target": current_price * target_multiplier,
                    "reasoning": f"Volume spike: {current_volume/avg_volume:.1f}x avg with price movement"
                }
                
        except Exception as e:
            logger.error(f"Error in volume profile scalper analysis: {e}")
            
        return None
    
    def _detect_breakout_pattern(self, prices: List[float]) -> bool:
        """Detect simple breakout patterns"""
        if len(prices) < 10:
            return False
            
        # Look for consolidation followed by breakout
        recent_high = max(prices[-10:-2])
        recent_low = min(prices[-10:-2])
        current_price = prices[-1]
        
        consolidation_range = (recent_high - recent_low) / recent_low
        
        # Tight consolidation followed by breakout
        if consolidation_range < 0.01 and (current_price > recent_high * 1.002 or current_price < recent_low * 0.998):
            return True
            
        return False
    
    def _calculate_position_size(self, price: float, symbol: str) -> int:
        """Calculate position size based on risk management"""
        try:
            # Base quantity calculation
            if symbol == "NIFTY":
                base_qty = 50
            elif symbol == "BANKNIFTY":
                base_qty = 25
            else:  # FINNIFTY
                base_qty = 40
            
            # Adjust based on available capital and risk
            risk_amount = self.total_capital * self.risk_per_trade
            position_value = price * base_qty
            
            if position_value > risk_amount:
                adjusted_qty = int(risk_amount / price)
                return max(adjusted_qty, 1)
            
            return base_qty
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 25  # Default safe quantity
    
    async def _execute_autonomous_trade(self, strategy_name: str, signal: Dict) -> Optional[Dict]:
        """Execute an autonomous trade based on strategy signal"""
        try:
            trade_id = f"AUTO_{strategy_name[:3]}_{int(datetime.now().timestamp())}"
            current_time = datetime.now()
            
            # Create trade record
            trade = {
                "trade_id": trade_id,
                "strategy": strategy_name,
                "symbol": signal["symbol"],
                "action": signal["action"],
                "quantity": signal["quantity"],
                "entry_price": signal["price"],
                "stop_loss": signal["stop_loss"],
                "target": signal["target"],
                "confidence": signal["confidence"],
                "reasoning": signal["reasoning"],
                "entry_time": current_time,
                "status": "OPEN",
                "pnl": 0.0,
                "exit_price": None,
                "exit_time": None
            }
            
            # Add to active positions
            self.active_positions[trade_id] = trade
            
            # Add to trade history
            self.trade_history.append(trade.copy())
            
            # Update strategy stats
            self.strategies[strategy_name]["trades_today"] += 1
            self.strategies[strategy_name]["total_trades"] += 1
            self.strategies[strategy_name]["last_signal_time"] = current_time
            
            # Update used capital
            position_value = signal["price"] * signal["quantity"]
            self.used_capital += position_value
            
            logger.info(f"✅ Trade executed: {trade_id} - {signal['action']} {signal['quantity']} {signal['symbol']} @ {signal['price']}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing autonomous trade: {e}")
            return None
    
    async def _manage_positions(self):
        """Manage open positions - check for stop loss and target hits"""
        positions_to_close = []
        
        for trade_id, position in self.active_positions.items():
            try:
                symbol = position["symbol"]
                if symbol not in self.market_data_buffer or not self.market_data_buffer[symbol]:
                    continue
                
                current_price = self.market_data_buffer[symbol][-1]["ltp"]
                if current_price == 0:
                    continue
                
                # Check for exit conditions
                should_exit, exit_reason = self._check_exit_conditions(position, current_price)
                
                if should_exit:
                    await self._close_position(trade_id, current_price, exit_reason)
                    positions_to_close.append(trade_id)
                
            except Exception as e:
                logger.error(f"Error managing position {trade_id}: {e}")
        
        # Remove closed positions
        for trade_id in positions_to_close:
            if trade_id in self.active_positions:
                del self.active_positions[trade_id]
    
    def _check_exit_conditions(self, position: Dict, current_price: float) -> tuple:
        """Check if position should be exited"""
        action = position["action"]
        entry_price = position["entry_price"]
        stop_loss = position["stop_loss"]
        target = position["target"]
        entry_time = position["entry_time"]
        
        # Time-based exit (max 4 hours)
        time_elapsed = (datetime.now() - entry_time).total_seconds() / 3600
        if time_elapsed > 4:
            return True, "TIME_EXIT"
        
        if action == "BUY":
            # Check stop loss
            if current_price <= stop_loss:
                return True, "STOP_LOSS"
            # Check target
            if current_price >= target:
                return True, "TARGET_HIT"
        else:  # SELL
            # Check stop loss
            if current_price >= stop_loss:
                return True, "STOP_LOSS"
            # Check target
            if current_price <= target:
                return True, "TARGET_HIT"
        
        return False, None
    
    async def _close_position(self, trade_id: str, exit_price: float, exit_reason: str):
        """Close a position and update P&L"""
        try:
            position = self.active_positions[trade_id]
            
            # Calculate P&L
            entry_price = position["entry_price"]
            quantity = position["quantity"]
            action = position["action"]
            
            if action == "BUY":
                pnl = (exit_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - exit_price) * quantity
            
            # Update position
            position["exit_price"] = exit_price
            position["exit_time"] = datetime.now()
            position["pnl"] = pnl
            position["status"] = "CLOSED"
            position["exit_reason"] = exit_reason
            
            # Update daily P&L
            self.daily_pnl += pnl
            
            # Update strategy P&L
            strategy_name = position["strategy"]
            self.strategies[strategy_name]["pnl"] += pnl
            
            # Update win rate
            if pnl > 0:
                wins = sum(1 for t in self.trade_history if t["strategy"] == strategy_name and t.get("pnl", 0) > 0)
                total = self.strategies[strategy_name]["total_trades"]
                self.strategies[strategy_name]["win_rate"] = (wins / total) * 100 if total > 0 else 0
            
            # Update used capital
            position_value = entry_price * quantity
            self.used_capital -= position_value
            
            logger.info(f"💰 Position closed: {trade_id} - P&L: ₹{pnl:.2f} ({exit_reason})")
            
        except Exception as e:
            logger.error(f"Error closing position {trade_id}: {e}")
    
    def _update_strategy_stats(self, strategy_name: str, trade_result: Dict):
        """Update strategy statistics after trade execution"""
        pass  # Stats are updated in _close_position
    
    def _is_strategy_in_cooldown(self, strategy_name: str) -> bool:
        """Check if strategy is in cooldown period"""
        last_signal_time = self.strategies[strategy_name]["last_signal_time"]
        if not last_signal_time:
            return False
        
        cooldown_minutes = self.strategies[strategy_name]["cooldown_minutes"]
        time_elapsed = (datetime.now() - last_signal_time).total_seconds() / 60
        
        return time_elapsed < cooldown_minutes
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open"""
        from datetime import datetime, time
        
        # Get current time in IST (Indian Standard Time)
        current_time = datetime.now().time()
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        # Market is closed on weekends (Saturday=5, Sunday=6)
        if current_day >= 5:  # Saturday or Sunday
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = time(9, 15)
        market_close = time(15, 30)
        
        return market_open <= current_time <= market_close
    
    def get_strategy_performance(self) -> Dict:
        """Get current strategy performance data"""
        strategies_data = []
        for name, data in self.strategies.items():
            strategies_data.append({
                "name": name,
                "status": "ACTIVE" if data["active"] else "INACTIVE",
                "trades_today": data["trades_today"],
                "win_rate": round(data["win_rate"], 1),
                "pnl": round(data["pnl"], 2),
                "allocation": data["allocation"]
            })
        
        return {
            "strategies": strategies_data,
            "message": "Real autonomous trading performance - live metrics",
            "data_source": "AUTONOMOUS_ENGINE"
        }
    
    def get_active_orders(self) -> Dict:
        """Get active positions as orders"""
        orders = []
        for trade_id, position in self.active_positions.items():
            orders.append({
                "order_id": trade_id,
                "symbol": position["symbol"],
                "side": position["action"],
                "quantity": position["quantity"],
                "price": position["entry_price"],
                "status": "OPEN",
                "strategy": position["strategy"],
                "entry_time": position["entry_time"].strftime("%H:%M:%S"),
                "pnl": self._calculate_unrealized_pnl(position),
                "stop_loss": position["stop_loss"],
                "target": position["target"]
            })
        
        return {
            "orders": orders,
            "message": f"Active autonomous positions: {len(orders)}",
            "data_source": "AUTONOMOUS_ENGINE"
        }
    
    def _calculate_unrealized_pnl(self, position: Dict) -> float:
        """Calculate unrealized P&L for open position"""
        try:
            symbol = position["symbol"]
            if symbol not in self.market_data_buffer or not self.market_data_buffer[symbol]:
                return 0.0
            
            current_price = self.market_data_buffer[symbol][-1]["ltp"]
            entry_price = position["entry_price"]
            quantity = position["quantity"]
            action = position["action"]
            
            if action == "BUY":
                return (current_price - entry_price) * quantity
            else:
                return (entry_price - current_price) * quantity
                
        except Exception as e:
            logger.error(f"Error calculating unrealized P&L: {e}")
            return 0.0
    
    def get_system_metrics(self) -> Dict:
        """Get overall system metrics"""
        total_trades_today = sum(s["trades_today"] for s in self.strategies.values())
        active_positions_count = len(self.active_positions)
        
        return {
            "daily_pnl": round(self.daily_pnl, 2),
            "total_capital": self.total_capital,
            "used_capital": round(self.used_capital, 2),
            "available_capital": round(self.total_capital - self.used_capital, 2),
            "capital_utilization": round((self.used_capital / self.total_capital) * 100, 1),
            "trades_today": total_trades_today,
            "active_positions": active_positions_count,
            "strategies_active": sum(1 for s in self.strategies.values() if s["active"])
        }

# Global autonomous trading engine
autonomous_engine = AutonomousTradeEngine()

def get_autonomous_engine():
    """Get the global autonomous trading engine"""
    return autonomous_engine