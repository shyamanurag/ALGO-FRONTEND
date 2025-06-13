"""
LIVE Autonomous Trading Engine
Real-time execution engine for production trading with real money
Multi-account support, NSE compliance, and full automation
"""

import asyncio
import uuid
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
import aiosqlite
import os
from decimal import Decimal
import threading
import time as time_module

# Import TrueData and Zerodha clients
from truedata_client import initialize_truedata, get_live_data, is_connected as truedata_connected
from zerodha_integration import ZerodhaClient

logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    signal_id: str
    strategy_name: str
    symbol: str
    action: str  # BUY/SELL
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    confidence: float
    reasoning: str
    valid_until: datetime
    risk_amount: float
    expected_return: float
    market_regime: str
    setup_type: str

@dataclass
class ActivePosition:
    position_id: str
    account_id: str
    signal_id: str
    strategy_name: str
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    stop_loss: float
    target: float
    entry_time: datetime
    status: str  # OPEN, PARTIAL, CLOSED
    broker_order_id: str = None

@dataclass
class AccountWallet:
    account_id: str
    account_name: str
    start_balance: float
    current_balance: float
    daily_pnl: float
    used_margin: float
    available_margin: float
    max_daily_loss: float
    trades_today: int
    positions_count: int
    status: str  # ACTIVE, STOPPED, EMERGENCY

class LiveAutonomousEngine:
    """Production-grade autonomous trading engine"""
    
    def __init__(self):
        # Core system state
        self.running = False
        self.emergency_stop = False
        self.market_open = False
        
        # Trading accounts (multi-account support)
        self.accounts: Dict[str, AccountWallet] = {}
        self.active_positions: Dict[str, ActivePosition] = {}
        self.completed_trades: List[Dict] = []
        
        # Strategy engine
        self.strategies = self._initialize_strategies()
        
        # Market data
        self.live_market_data = {}
        self.market_data_buffer = {}
        self.last_data_update = None
        
        # Risk management
        self.daily_stop_loss_percent = float(os.getenv('DAILY_STOP_LOSS_PERCENT', 2.0))
        self.max_trades_per_second = int(os.getenv('MAX_TRADES_PER_SECOND', 7))
        self.trade_rate_limiter = []
        
        # Zerodha integration
        self.zerodha_client = ZerodhaClient()
        
        # Database
        self.db_path = "/app/trading_system.db"
        
        # Market hours
        self.market_open_time = time(9, 15)
        self.market_close_time = time(15, 30)
        self.position_cutoff_time = time(15, 15)
        self.square_off_start = time(15, 15)
        self.square_off_end = time(15, 25)
        
        # NSE stocks universe (NIFTY 50)
        self.nifty_50_stocks = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK",
            "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN", "LT", "AXISBANK",
            "ASIANPAINT", "MARUTI", "BAJFINANCE", "NTPC", "TITAN", "ULTRACEMCO",
            "NESTLEIND", "WIPRO", "POWERGRID", "TECHM", "HCLTECH", "ONGC",
            "COALINDIA", "BAJAJFINSV", "SUNPHARMA", "TATASTEEL", "JSWSTEEL",
            "GRASIM", "DIVISLAB", "BPCL", "CIPLA", "DRREDDY", "INDUSINDBK",
            "EICHERMOT", "ADANIENT", "TATAMOTORS", "APOLLOHOSP", "HEROMOTOCO",
            "BAJAJ-AUTO", "BRITANNIA", "HINDALCO", "SHREECEM", "UPL", "TATACONSUM",
            "ADANIPORTS", "SBILIFE", "HDFCLIFE", "M&M"
        ]
        
    def _initialize_strategies(self) -> Dict:
        """Initialize the 7 trading strategies with their configurations"""
        return {
            "MomentumSurfer": {
                "active": True,
                "allocation_percent": 15,
                "cooldown_minutes": 5,
                "timeframe": "1min",
                "parameters": {"fast_period": 8, "slow_period": 21, "volume_threshold": 1.2},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "NewsImpactScalper": {
                "active": True,
                "allocation_percent": 12,
                "cooldown_minutes": 3,
                "timeframe": "1min",
                "parameters": {"impact_threshold": 2.0, "scalp_duration": 300},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "VolatilityExplosion": {
                "active": True,
                "allocation_percent": 18,
                "cooldown_minutes": 8,
                "timeframe": "2min",
                "parameters": {"volatility_multiplier": 1.5, "lookback_period": 30},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "ConfluenceAmplifier": {
                "active": True,
                "allocation_percent": 20,
                "cooldown_minutes": 10,
                "timeframe": "3min",
                "parameters": {"min_confluence": 3, "signal_strength": 0.7},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "PatternHunter": {
                "active": True,
                "allocation_percent": 16,
                "cooldown_minutes": 7,
                "timeframe": "5min",
                "parameters": {"pattern_confidence": 0.8, "harmonic_enabled": True},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "LiquidityMagnet": {
                "active": True,
                "allocation_percent": 14,
                "cooldown_minutes": 6,
                "timeframe": "2min",
                "parameters": {"liquidity_strength": 0.7, "volume_surge": 1.4},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            },
            "VolumeProfileScalper": {
                "active": True,
                "allocation_percent": 5,
                "cooldown_minutes": 2,
                "timeframe": "30sec",
                "parameters": {"volume_spike": 2.0, "price_movement": 0.003},
                "trades_today": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "daily_pnl": 0.0,
                "last_signal_time": None
            }
        }
    
    async def initialize_system(self):
        """Initialize the complete autonomous trading system"""
        try:
            logger.info("🚀 Initializing Live Autonomous Trading Engine...")
            
            # Initialize database
            await self._initialize_database()
            
            # Load account configurations
            await self._initialize_accounts()
            
            # Initialize TrueData connection
            if initialize_truedata():
                logger.info("✅ TrueData connection initialized")
            else:
                logger.error("❌ TrueData connection failed")
                return False
            
            # Initialize Zerodha connection
            if await self.zerodha_client.initialize():
                logger.info("✅ Zerodha broker connection initialized")
            else:
                logger.warning("⚠️ Zerodha connection failed - running in data-only mode")
            
            # Load existing positions
            await self._load_existing_positions()
            
            logger.info("✅ Live Autonomous Trading Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize trading engine: {e}")
            return False
    
    async def start_autonomous_trading(self):
        """Start the autonomous trading engine"""
        if not await self.initialize_system():
            logger.error("System initialization failed - cannot start trading")
            return False
        
        if self.running:
            logger.warning("Trading engine already running")
            return True
        
        self.running = True
        self.emergency_stop = False
        
        # Start background tasks
        asyncio.create_task(self._market_data_loop())
        asyncio.create_task(self._trading_loop())
        asyncio.create_task(self._position_management_loop())
        asyncio.create_task(self._risk_monitoring_loop())
        asyncio.create_task(self._market_hours_monitor())
        
        logger.info("🤖 AUTONOMOUS TRADING ENGINE STARTED - LIVE MODE")
        return True
    
    async def stop_autonomous_trading(self, emergency: bool = False):
        """Stop autonomous trading"""
        self.running = False
        if emergency:
            self.emergency_stop = True
            logger.critical("🛑 EMERGENCY STOP ACTIVATED")
            # Close all positions immediately
            await self._emergency_close_all_positions()
        else:
            logger.info("⏹️ Autonomous trading stopped normally")
    
    async def _market_data_loop(self):
        """Continuous market data updates"""
        while self.running:
            try:
                if truedata_connected():
                    # Get live data for all NIFTY 50 stocks
                    for symbol in self.nifty_50_stocks + ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
                        data = get_live_data(symbol)
                        if data:
                            self._update_market_data_buffer(symbol, data)
                    
                    self.last_data_update = datetime.now()
                
                # Update every 1 second during market hours, 30 seconds after hours
                sleep_time = 1 if self.market_open else 30
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Market data loop error: {e}")
                await asyncio.sleep(5)
    
    async def _trading_loop(self):
        """Main trading loop - analyze and execute trades"""
        while self.running:
            try:
                if not self.market_open or self.emergency_stop:
                    await asyncio.sleep(30)
                    continue
                
                # Check if within trading hours (not in square-off period)
                current_time = datetime.now().time()
                if current_time >= self.position_cutoff_time:
                    await asyncio.sleep(30)
                    continue
                
                # Analyze market with all strategies
                for strategy_name, strategy_config in self.strategies.items():
                    if not strategy_config["active"]:
                        continue
                    
                    try:
                        # Check cooldown
                        if self._is_in_cooldown(strategy_name):
                            continue
                        
                        # Analyze all symbols for this strategy
                        await self._analyze_strategy(strategy_name)
                        
                    except Exception as e:
                        logger.error(f"Strategy {strategy_name} error: {e}")
                
                # Sleep based on strategy frequency (fastest is 30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_strategy(self, strategy_name: str):
        """Analyze market data for a specific strategy"""
        strategy_config = self.strategies[strategy_name]
        
        # Analyze each symbol in NIFTY 50
        for symbol in self.nifty_50_stocks:
            if symbol not in self.market_data_buffer:
                continue
            
            try:
                # Get historical data buffer for analysis
                data_buffer = self.market_data_buffer[symbol]
                if len(data_buffer) < 50:  # Need minimum data points
                    continue
                
                # Run strategy-specific analysis
                signal = await self._run_strategy_analysis(strategy_name, symbol, data_buffer)
                
                if signal and signal.confidence >= 70:
                    # Execute trade if signal is strong enough
                    await self._execute_autonomous_trade(signal)
                    
                    # Update strategy timestamp
                    self.strategies[strategy_name]["last_signal_time"] = datetime.now()
                    
                    # Rate limiting - NSE allows max 7 trades/second
                    await self._enforce_rate_limit()
                    
            except Exception as e:
                logger.error(f"Analysis error for {strategy_name} on {symbol}: {e}")
    
    async def _run_strategy_analysis(self, strategy_name: str, symbol: str, data_buffer: List) -> Optional[TradingSignal]:
        """Run specific strategy analysis"""
        try:
            if strategy_name == "MomentumSurfer":
                return await self._momentum_surfer_analysis(symbol, data_buffer)
            elif strategy_name == "NewsImpactScalper":
                return await self._news_impact_analysis(symbol, data_buffer)
            elif strategy_name == "VolatilityExplosion":
                return await self._volatility_analysis(symbol, data_buffer)
            elif strategy_name == "ConfluenceAmplifier":
                return await self._confluence_analysis(symbol, data_buffer)
            elif strategy_name == "PatternHunter":
                return await self._pattern_analysis(symbol, data_buffer)
            elif strategy_name == "LiquidityMagnet":
                return await self._liquidity_analysis(symbol, data_buffer)
            elif strategy_name == "VolumeProfileScalper":
                return await self._volume_profile_analysis(symbol, data_buffer)
            
        except Exception as e:
            logger.error(f"Strategy analysis error: {e}")
            
        return None
    
    async def _momentum_surfer_analysis(self, symbol: str, data: List) -> Optional[TradingSignal]:
        """Advanced Momentum Surfer strategy"""
        try:
            if len(data) < 21:
                return None
            
            # Extract price and volume data
            prices = [d["ltp"] for d in data[-50:]]
            volumes = [d["volume"] for d in data[-20:]]
            
            # Calculate technical indicators
            sma_8 = np.mean(prices[-8:])
            sma_21 = np.mean(prices[-21:])
            current_price = prices[-1]
            
            # Momentum calculation
            price_momentum = (current_price - prices[-10]) / prices[-10] * 100
            volume_ratio = volumes[-1] / np.mean(volumes[:-1]) if len(volumes) > 1 else 1
            
            # RSI calculation
            rsi = self._calculate_rsi(prices, 14)
            
            # Signal generation
            bullish_signals = 0
            
            # Technical signals
            if sma_8 > sma_21:
                bullish_signals += 1
            if price_momentum > 0.5:
                bullish_signals += 1
            if volume_ratio > 1.3:
                bullish_signals += 1
            if rsi > 50 and rsi < 70:
                bullish_signals += 1
            if current_price > max(prices[-5:]):
                bullish_signals += 1
            
            confidence = 60 + bullish_signals * 6
            
            if bullish_signals >= 4 and confidence >= 80:
                quantity = self._calculate_position_size(symbol, current_price)
                
                return TradingSignal(
                    signal_id=f"MOM_{symbol}_{int(datetime.now().timestamp())}",
                    strategy_name="MomentumSurfer",
                    symbol=symbol,
                    action="BUY",
                    quantity=quantity,
                    entry_price=current_price,
                    stop_loss=current_price * 0.995,
                    target=current_price * 1.015,
                    confidence=confidence,
                    reasoning=f"Momentum surge: {bullish_signals}/5 signals, momentum: {price_momentum:.2f}%",
                    valid_until=datetime.now() + timedelta(minutes=30),
                    risk_amount=quantity * current_price * 0.005,
                    expected_return=quantity * current_price * 0.015,
                    market_regime="TRENDING",
                    setup_type="MOMENTUM_BREAKOUT"
                )
                
        except Exception as e:
            logger.error(f"Momentum analysis error: {e}")
            
        return None
    
    async def _news_impact_analysis(self, symbol: str, data: List) -> Optional[TradingSignal]:
        """News Impact Scalper - detects sudden price movements"""
        try:
            if len(data) < 15:
                return None
            
            # Analyze recent price changes
            recent_changes = [d.get("change_percent", 0) for d in data[-10:]]
            current_change = recent_changes[-1]
            avg_change = np.mean(recent_changes[:-1])
            
            # Volume surge detection
            volumes = [d["volume"] for d in data[-10:]]
            volume_surge = volumes[-1] / np.mean(volumes[:-1]) if len(volumes) > 1 else 1
            
            # News impact detection
            if abs(current_change) > abs(avg_change) * 2.5 and abs(current_change) > 1.0 and volume_surge > 1.5:
                current_price = data[-1]["ltp"]
                confidence = min(85 + abs(current_change) * 3, 95)
                
                action = "BUY" if current_change > 0 else "SELL"
                quantity = self._calculate_position_size(symbol, current_price)
                
                # Quick scalp targets
                target_mult = 1.008 if action == "BUY" else 0.992
                stop_mult = 0.996 if action == "BUY" else 1.004
                
                return TradingSignal(
                    signal_id=f"NEWS_{symbol}_{int(datetime.now().timestamp())}",
                    strategy_name="NewsImpactScalper",
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    entry_price=current_price,
                    stop_loss=current_price * stop_mult,
                    target=current_price * target_mult,
                    confidence=confidence,
                    reasoning=f"News impact: {current_change:.2f}% change, {volume_surge:.1f}x volume",
                    valid_until=datetime.now() + timedelta(minutes=5),
                    risk_amount=quantity * current_price * 0.004,
                    expected_return=quantity * current_price * 0.008,
                    market_regime="VOLATILE",
                    setup_type="NEWS_REACTION"
                )
                
        except Exception as e:
            logger.error(f"News impact analysis error: {e}")
            
        return None
    
    # Additional strategy methods would be implemented similarly...
    
    async def _execute_autonomous_trade(self, signal: TradingSignal):
        """Execute trade based on signal with full automation"""
        try:
            # Pre-trade validation
            if not await self._validate_trade_signal(signal):
                return False
            
            # Select account with available balance
            account = await self._select_account_for_trade(signal)
            if not account:
                logger.warning(f"No account available for trade: {signal.symbol}")
                return False
            
            # Calculate exact position size based on account balance
            adjusted_quantity = self._calculate_final_position_size(account, signal)
            
            # Execute the trade
            if os.getenv('PAPER_TRADING', 'true').lower() == 'true':
                # Paper trading execution
                order_result = await self._execute_paper_trade(signal, account, adjusted_quantity)
            else:
                # Live trading execution via Zerodha
                order_result = await self._execute_live_trade(signal, account, adjusted_quantity)
            
            if order_result:
                # Create position record
                position = ActivePosition(
                    position_id=f"POS_{signal.signal_id}",
                    account_id=account.account_id,
                    signal_id=signal.signal_id,
                    strategy_name=signal.strategy_name,
                    symbol=signal.symbol,
                    side=signal.action,
                    quantity=adjusted_quantity,
                    entry_price=signal.entry_price,
                    current_price=signal.entry_price,
                    unrealized_pnl=0.0,
                    stop_loss=signal.stop_loss,
                    target=signal.target,
                    entry_time=datetime.now(),
                    status="OPEN",
                    broker_order_id=order_result.get("order_id")
                )
                
                # Store position
                self.active_positions[position.position_id] = position
                
                # Update account
                account.used_margin += adjusted_quantity * signal.entry_price
                account.trades_today += 1
                
                # Update strategy stats
                strategy = self.strategies[signal.strategy_name]
                strategy["trades_today"] += 1
                strategy["total_trades"] += 1
                
                # Save to database
                await self._save_position_to_db(position)
                await self._save_signal_to_db(signal)
                
                logger.info(f"✅ TRADE EXECUTED: {signal.action} {adjusted_quantity} {signal.symbol} @ {signal.entry_price} (Strategy: {signal.strategy_name})")
                
                return True
                
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            
        return False
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return 50.0
    
    def _calculate_position_size(self, symbol: str, price: float) -> int:
        """Calculate position size based on symbol and price"""
        try:
            # Base quantities for different symbols
            if symbol in ["NIFTY", "BANKNIFTY", "FINNIFTY"]:
                if symbol == "NIFTY":
                    return 50
                elif symbol == "BANKNIFTY":
                    return 25
                else:  # FINNIFTY
                    return 40
            else:
                # For individual stocks, calculate based on price
                if price <= 100:
                    return 100
                elif price <= 500:
                    return 50
                elif price <= 1000:
                    return 25
                elif price <= 2000:
                    return 15
                else:
                    return 10
                    
        except Exception:
            return 10  # Default safe quantity
    
    # ... Additional methods for position management, risk monitoring, etc. ...
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "engine_status": "RUNNING" if self.running else "STOPPED",
            "emergency_stop": self.emergency_stop,
            "market_open": self.market_open,
            "accounts_count": len(self.accounts),
            "active_positions": len(self.active_positions),
            "strategies_active": sum(1 for s in self.strategies.values() if s["active"]),
            "data_connection": truedata_connected(),
            "last_data_update": self.last_data_update.isoformat() if self.last_data_update else None,
            "total_daily_pnl": sum(acc.daily_pnl for acc in self.accounts.values()),
            "total_trades_today": sum(acc.trades_today for acc in self.accounts.values())
        }

# Global instance
live_engine = LiveAutonomousEngine()

async def get_live_engine():
    """Get the global live trading engine"""
    return live_engine
