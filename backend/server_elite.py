"""
Elite Autonomous Algo Trading Platform
Comprehensive integration of all src/core components with elite trading system
"""

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
import asyncio
import json
from datetime import datetime, time, timedelta
import asyncpg
import redis.asyncio as redis
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import core components with error handling
CORE_COMPONENTS_AVAILABLE = False
try:
    import sys
    sys.path.append('/app/backend')
    
    # Core system components
    from src.core.config import settings
    from src.core.models import OrderAction, OrderType, OrderStatus, PositionType
    
    # Advanced strategies
    from src.core.momentum_surfer import MomentumSurfer
    from src.core.news_impact_scalper import NewsImpactScalper
    from src.core.volatility_explosion import VolatilityExplosion
    from src.core.confluence_amplifier import ConfluenceAmplifier
    from src.core.pattern_hunter import PatternHunter
    from src.core.liquidity_magnet import LiquidityMagnet
    from src.core.volume_profile_scalper import VolumeProfileScalper
    
    # Elite trading system
    from src.recommendations import (
        EliteRecommendationEngine,
        PerfectTechnicalAnalyzer,
        PerfectVolumeAnalyzer,
        PerfectPatternAnalyzer,
        PerfectRegimeAnalyzer,
        PerfectMomentumAnalyzer,
        SmartMoneyAnalyzer
    )
    
    CORE_COMPONENTS_AVAILABLE = True
    logger.info("All core components loaded successfully")
    
except ImportError as e:
    logger.warning(f"Core components not available: {e}")
    # Fallback imports
    from kiteconnect import KiteConnect
    import pyotp

# Environment configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
REDIS_URL = os.environ.get('REDIS_URL')
ZERODHA_API_KEY = os.environ.get('ZERODHA_API_KEY')
ZERODHA_API_SECRET = os.environ.get('ZERODHA_API_SECRET')
ZERODHA_CLIENT_ID = os.environ.get('ZERODHA_CLIENT_ID')

# Trading configuration
PAPER_TRADING = os.environ.get('PAPER_TRADING', 'true').lower() == 'true'
AUTONOMOUS_TRADING_ENABLED = os.environ.get('AUTONOMOUS_TRADING_ENABLED', 'true').lower() == 'true'
DAILY_STOP_LOSS_PERCENT = 2.0

# Create FastAPI application
app = FastAPI(title="Elite Autonomous Algo Trading Platform", version="2.0.0")
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
db_pool = None
redis_client = None
scheduler = AsyncIOScheduler()
websocket_connections = set()

# Elite trading components
elite_engine = None
analyzers = {}
strategy_instances = {}

# System state
system_state = {
    'initialized': False,
    'trading_active': AUTONOMOUS_TRADING_ENABLED,
    'emergency_mode': False,
    'daily_pnl': 0.0,
    'active_positions': {},
    'market_data': {},
    'system_health': 'HEALTHY',
    'start_time': datetime.utcnow()
}

# Pydantic models for API
class SystemStatus(BaseModel):
    status: str
    trading_active: bool
    paper_trading: bool
    daily_pnl: float
    active_positions: int
    market_data_symbols: int
    components_health: Dict[str, str]
    uptime: Optional[str] = None

class TradeRequest(BaseModel):
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    order_type: Optional[str] = "MARKET"
    price: Optional[float] = None

class StrategyConfig(BaseModel):
    name: str
    enabled: bool
    parameters: Dict = Field(default_factory=dict)
    allocation: float = 0.2

class EliteRecommendationResponse(BaseModel):
    recommendation_id: str
    symbol: str
    strategy: str
    direction: str
    entry_price: float
    stop_loss: float
    primary_target: float
    confidence_score: float
    timeframe: str
    summary: str

# Database operations
async def init_database():
    """Initialize database connections"""
    global db_pool, redis_client
    
    try:
        # PostgreSQL connection
        if DATABASE_URL:
            db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=3,
                max_size=10,
                command_timeout=60
            )
            logger.info("PostgreSQL database connected")
        
        # Redis connection  
        if REDIS_URL:
            redis_client = redis.from_url(REDIS_URL)
            await redis_client.ping()
            logger.info("Redis cache connected")
        
        # Create database schema
        await create_database_schema()
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

async def create_database_schema():
    """Create or update database schema"""
    if not db_pool:
        return
        
    try:
        async with db_pool.acquire() as conn:
            # Elite recommendations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS elite_recommendations (
                    id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    strategy VARCHAR NOT NULL,
                    direction VARCHAR NOT NULL,
                    entry_price FLOAT NOT NULL,
                    stop_loss FLOAT NOT NULL,
                    primary_target FLOAT NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    timeframe VARCHAR NOT NULL,
                    valid_until TIMESTAMP NOT NULL,
                    metadata JSONB,
                    status VARCHAR DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Strategy performance table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_performance (
                    id VARCHAR PRIMARY KEY,
                    strategy_name VARCHAR NOT NULL,
                    symbol VARCHAR NOT NULL,
                    action VARCHAR NOT NULL,
                    entry_price FLOAT,
                    exit_price FLOAT,
                    pnl FLOAT DEFAULT 0,
                    win BOOLEAN,
                    trade_duration INTERVAL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # System metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR NOT NULL,
                    metric_value FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
            logger.info("Database schema created/updated successfully")
            
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")

# Elite trading system initialization
async def initialize_elite_trading_system():
    """Initialize elite trading recommendation system"""
    global elite_engine, analyzers
    
    try:
        # Initialize analyzers
        analyzers = {
            'technical': PerfectTechnicalAnalyzer(),
            'volume': PerfectVolumeAnalyzer(),
            'pattern': PerfectPatternAnalyzer(),
            'regime': PerfectRegimeAnalyzer(),
            'momentum': PerfectMomentumAnalyzer(),
            'smart_money': SmartMoneyAnalyzer()
        }
        
        # Mock data provider for demonstration
        class EliteDataProvider:
            async def get_historical_data(self, symbol, timeframe, periods):
                """Generate realistic market data for analysis"""
                dates = pd.date_range(start='2023-01-01', periods=periods, freq='1min')
                
                # Generate realistic OHLCV data
                base_price = 19000 if 'NIFTY' in symbol else 45000 if 'BANK' in symbol else 19000
                
                # Random walk with some trend
                returns = np.random.normal(0, 0.001, periods)  # 0.1% volatility
                prices = base_price * np.cumprod(1 + returns)
                
                # Create OHLC from prices
                high = prices * (1 + np.random.uniform(0, 0.01, periods))
                low = prices * (1 - np.random.uniform(0, 0.01, periods))
                open_prices = np.roll(prices, 1)
                open_prices[0] = prices[0]
                
                data = pd.DataFrame({
                    'open': open_prices,
                    'high': high,
                    'low': low,
                    'close': prices,
                    'volume': np.random.randint(1000, 10000, periods)
                }, index=dates)
                
                return data
            
            async def get_order_book(self, symbol):
                return {"bids": [], "asks": []}
            
            async def get_recent_trades(self, symbol):
                return []
            
            async def get_option_chain(self, symbol, expiry):
                return pd.DataFrame()
            
            async def get_market_breadth(self):
                return {"advance_decline_ratio": 1.2, "new_highs": 150, "new_lows": 50}
            
            async def get_vix_data(self):
                return {"current": 18, "ma_20": 16}
        
        # Initialize elite recommendation engine
        elite_engine = EliteRecommendationEngine(
            data_provider=EliteDataProvider(),
            greeks_manager=None,
            config={
                'scan_symbols': ['NIFTY', 'BANKNIFTY', 'FINNIFTY'],
                'timeframes': ['15min', '1hour', '4hour', 'daily'],
                'min_confidence': 9.5
            }
        )
        
        logger.info("Elite trading system initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing elite trading system: {e}")

async def initialize_trading_strategies():
    """Initialize all trading strategies"""
    global strategy_instances
    
    if not CORE_COMPONENTS_AVAILABLE:
        logger.warning("Core components not available, skipping strategy initialization")
        return
    
    try:
        strategy_configs = {
            'momentum_surfer': {
                'class': MomentumSurfer,
                'config': {'fast_period': 8, 'slow_period': 21}
            },
            'news_impact_scalper': {
                'class': NewsImpactScalper,
                'config': {'scalp_duration_seconds': 300}
            },
            'volatility_explosion': {
                'class': VolatilityExplosion,
                'config': {'volatility_lookback': 30}
            },
            'confluence_amplifier': {
                'class': ConfluenceAmplifier,
                'config': {'min_confluence_signals': 3}
            },
            'pattern_hunter': {
                'class': PatternHunter,
                'config': {'harmonic_patterns_enabled': True}
            },
            'liquidity_magnet': {
                'class': LiquidityMagnet,
                'config': {'liquidity_strength_threshold': 0.7}
            },
            'volume_profile_scalper': {
                'class': VolumeProfileScalper,
                'config': {'scalp_timeframe_seconds': 30}
            }
        }
        
        for strategy_name, strategy_config in strategy_configs.items():
            try:
                strategy_class = strategy_config['class']
                config = strategy_config.get('config', {})
                config['name'] = strategy_name
                config['enabled'] = True
                
                # Create strategy instance
                strategy_instance = strategy_class(config)
                strategy_instances[strategy_name] = strategy_instance
                
                logger.info(f"Strategy initialized: {strategy_name}")
                
            except Exception as e:
                logger.error(f"Error initializing strategy {strategy_name}: {e}")
        
        logger.info(f"Initialized {len(strategy_instances)} trading strategies")
        
    except Exception as e:
        logger.error(f"Error initializing trading strategies: {e}")

# Scheduler setup
def setup_scheduler():
    """Setup scheduled tasks"""
    try:
        # Elite recommendations scan every 5 minutes
        scheduler.add_job(
            scan_elite_recommendations,
            'interval',
            seconds=300,
            id='elite_scan'
        )
        
        # System health check every minute
        scheduler.add_job(
            system_health_check,
            'interval',
            seconds=60,
            id='health_check'
        )
        
        # Strategy execution every 30 seconds during market hours
        if CORE_COMPONENTS_AVAILABLE:
            scheduler.add_job(
                execute_strategy_loop,
                'interval',
                seconds=30,
                id='strategy_execution'
            )
        
        scheduler.start()
        logger.info("Scheduler started with all jobs")
        
    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")

# Scheduled tasks
async def scan_elite_recommendations():
    """Scan for elite trade recommendations"""
    if not elite_engine:
        return
        
    try:
        recommendations = await elite_engine.scan_for_elite_trades()
        
        if recommendations:
            logger.info(f"Found {len(recommendations)} elite trade opportunities")
            
            # Store recommendations in database
            if db_pool:
                async with db_pool.acquire() as conn:
                    for rec in recommendations:
                        await conn.execute("""
                            INSERT INTO elite_recommendations (
                                id, symbol, strategy, direction, entry_price,
                                stop_loss, primary_target, confidence_score,
                                timeframe, valid_until, metadata
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT (id) DO NOTHING
                        """, 
                        rec.recommendation_id, rec.symbol, rec.strategy,
                        rec.direction, rec.entry_price, rec.stop_loss,
                        rec.primary_target, rec.confidence_score,
                        rec.timeframe, rec.valid_until,
                        json.dumps(rec.__dict__, default=str))
            
            # Broadcast to websocket clients
            await broadcast_elite_recommendations(recommendations)
        
    except Exception as e:
        logger.error(f"Error scanning elite recommendations: {e}")

async def system_health_check():
    """Perform system health check"""
    try:
        health_status = {}
        
        # Check core components
        health_status['elite_engine'] = 'HEALTHY' if elite_engine else 'NOT_INITIALIZED'
        health_status['strategies'] = 'HEALTHY' if strategy_instances else 'NOT_INITIALIZED'
        
        # Check database connections
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health_status['database'] = 'HEALTHY'
            except:
                health_status['database'] = 'UNHEALTHY'
        
        if redis_client:
            try:
                await redis_client.ping()
                health_status['redis'] = 'HEALTHY'
            except:
                health_status['redis'] = 'UNHEALTHY'
        
        # Update system health
        unhealthy_components = [k for k, v in health_status.items() if v != 'HEALTHY']
        if unhealthy_components:
            system_state['system_health'] = 'DEGRADED'
            logger.warning(f"Unhealthy components: {unhealthy_components}")
        else:
            system_state['system_health'] = 'HEALTHY'
        
        # Store health metrics in database
        if db_pool:
            async with db_pool.acquire() as conn:
                for component, status in health_status.items():
                    await conn.execute("""
                        INSERT INTO system_metrics (metric_name, metric_value)
                        VALUES ($1, $2)
                    """, f"health_{component}", 1.0 if status == 'HEALTHY' else 0.0)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        system_state['system_health'] = 'ERROR'

async def execute_strategy_loop():
    """Execute all active trading strategies"""
    if not system_state['trading_active'] or not CORE_COMPONENTS_AVAILABLE:
        return
        
    try:
        # Check if market is open
        if not is_market_open():
            return
            
        # Execute each strategy
        for strategy_name, strategy_instance in strategy_instances.items():
            try:
                # Get market data for strategy symbols
                symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
                
                for symbol in symbols:
                    # Generate mock market data
                    market_data = {
                        'symbol': symbol,
                        'ltp': 19000 + np.random.random() * 1000,
                        'volume': np.random.randint(10000, 100000),
                        'timestamp': datetime.utcnow()
                    }
                    
                    # Generate signals
                    if hasattr(strategy_instance, 'analyze'):
                        # Get price and volume data
                        price_data = [market_data['ltp'] + np.random.random() * 100 for _ in range(100)]
                        volume_data = [market_data['volume'] + np.random.randint(-1000, 1000) for _ in range(100)]
                        
                        signal = await strategy_instance.analyze(
                            symbol, price_data, volume_data, datetime.utcnow()
                        )
                        
                        if signal:
                            logger.info(f"Signal generated by {strategy_name}: {signal}")
                            
                            # Store signal in database
                            if db_pool:
                                async with db_pool.acquire() as conn:
                                    await conn.execute("""
                                        INSERT INTO strategy_performance (
                                            id, strategy_name, symbol, action, entry_price
                                        ) VALUES ($1, $2, $3, $4, $5)
                                    """, str(uuid.uuid4()), strategy_name, symbol,
                                    signal['signal'], price_data[-1])
                            
            except Exception as e:
                logger.error(f"Error executing strategy {strategy_name}: {e}")
        
    except Exception as e:
        logger.error(f"Error in strategy execution loop: {e}")

def is_market_open() -> bool:
    """Check if market is currently open"""
    current_time = datetime.now().time()
    return time(9, 15) <= current_time <= time(15, 30)

async def broadcast_elite_recommendations(recommendations):
    """Broadcast elite recommendations to websocket clients"""
    if not websocket_connections:
        return
        
    message = {
        "type": "elite_recommendations",
        "count": len(recommendations),
        "recommendations": [rec.generate_summary() for rec in recommendations[:3]],  # Top 3
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await broadcast_websocket_message(message)

async def broadcast_websocket_message(message: Dict):
    """Broadcast message to all connected WebSocket clients"""
    if websocket_connections:
        disconnected = set()
        for websocket in websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except:
                disconnected.add(websocket)
        
        # Remove disconnected clients
        websocket_connections -= disconnected

# API Routes
@api_router.get("/")
async def root():
    return {
        "message": "Elite Autonomous Algo Trading Platform API", 
        "status": "running",
        "version": "2.0.0",
        "core_components": CORE_COMPONENTS_AVAILABLE,
        "elite_system": elite_engine is not None
    }

@api_router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Calculate component health
        components_health = {}
        
        components_health['elite_engine'] = 'HEALTHY' if elite_engine else 'NOT_INITIALIZED'
        components_health['strategies'] = f'{len(strategy_instances)} active'
        components_health['database'] = 'HEALTHY' if db_pool else 'NOT_CONNECTED'
        components_health['redis'] = 'HEALTHY' if redis_client else 'NOT_CONNECTED'
        components_health['websocket'] = f'{len(websocket_connections)} connected'
        
        return SystemStatus(
            status=system_state['system_health'],
            trading_active=system_state['trading_active'],
            paper_trading=PAPER_TRADING,
            daily_pnl=system_state['daily_pnl'],
            active_positions=len(system_state['active_positions']),
            market_data_symbols=len(system_state['market_data']),
            components_health=components_health,
            uptime=str(datetime.utcnow() - system_state['start_time'])
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(500, f"Error getting system status: {str(e)}")

@api_router.get("/elite-recommendations")
async def get_elite_recommendations():
    """Get current elite trade recommendations (10/10 only)"""
    try:
        if not elite_engine:
            raise HTTPException(503, "Elite recommendation engine not available")
        
        # Scan for elite trades
        elite_trades = await elite_engine.scan_for_elite_trades()
        
        # Convert to JSON serializable format
        recommendations = []
        for trade in elite_trades:
            recommendations.append({
                "recommendation_id": trade.recommendation_id,
                "timestamp": trade.timestamp.isoformat(),
                "symbol": trade.symbol,
                "strategy": trade.strategy,
                "direction": trade.direction,
                "entry_price": trade.entry_price,
                "stop_loss": trade.stop_loss,
                "primary_target": trade.primary_target,
                "secondary_target": trade.secondary_target,
                "tertiary_target": trade.tertiary_target,
                "confidence_score": trade.confidence_score,
                "timeframe": trade.timeframe,
                "valid_until": trade.valid_until.isoformat(),
                "confluence_factors": trade.confluence_factors[:5],  # Top 5
                "entry_conditions": trade.entry_conditions,
                "risk_metrics": trade.risk_metrics,
                "position_sizing": trade.position_sizing,
                "summary": trade.generate_summary()
            })
        
        return {
            "status": "success",
            "count": len(recommendations),
            "recommendations": recommendations,
            "scan_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting elite recommendations: {e}")
        raise HTTPException(500, f"Error getting elite recommendations: {str(e)}")

@api_router.get("/market-analysis")
async def get_market_analysis():
    """Get comprehensive market analysis using perfect analyzers"""
    try:
        if not analyzers:
            raise HTTPException(503, "Market analyzers not available")
        
        # Mock data for analysis
        periods = 100
        dates = pd.date_range(start='2023-01-01', periods=periods, freq='1min')
        mock_data = pd.DataFrame({
            'open': np.random.random(periods) * 100 + 19000,
            'high': np.random.random(periods) * 100 + 19100,
            'low': np.random.random(periods) * 100 + 18900,
            'close': np.random.random(periods) * 100 + 19000,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        # Mock timeframes data
        all_timeframes = {
            '15min': mock_data,
            '1hour': mock_data,
            '4hour': mock_data,
            'daily': mock_data
        }
        
        # Mock additional data
        microstructure = {
            'order_book': {'bids': [], 'asks': []},
            'recent_trades': []
        }
        
        options_data = pd.DataFrame()
        
        market_internals = {
            'breadth': {'advance_decline_ratio': 1.2, 'new_highs': 150, 'new_lows': 50},
            'vix': {'current': 18, 'ma_20': 16}
        }
        
        # Run all analyzers
        analysis_results = {}
        
        try:
            # Technical Analysis
            tech_result = await analyzers['technical'].analyze(mock_data, all_timeframes)
            analysis_results['technical'] = tech_result
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            analysis_results['technical'] = {'score': 0, 'error': str(e)}
        
        try:
            # Volume Analysis
            volume_result = await analyzers['volume'].analyze(mock_data, microstructure)
            analysis_results['volume'] = volume_result
        except Exception as e:
            logger.error(f"Volume analysis error: {e}")
            analysis_results['volume'] = {'score': 0, 'error': str(e)}
        
        try:
            # Pattern Analysis
            pattern_result = await analyzers['pattern'].analyze(mock_data, all_timeframes)
            analysis_results['pattern'] = pattern_result
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            analysis_results['pattern'] = {'score': 0, 'error': str(e)}
        
        try:
            # Regime Analysis
            regime_result = await analyzers['regime'].analyze(market_internals, mock_data)
            analysis_results['regime'] = regime_result
        except Exception as e:
            logger.error(f"Regime analysis error: {e}")
            analysis_results['regime'] = {'score': 0, 'error': str(e)}
        
        try:
            # Momentum Analysis
            momentum_result = await analyzers['momentum'].analyze(all_timeframes)
            analysis_results['momentum'] = momentum_result
        except Exception as e:
            logger.error(f"Momentum analysis error: {e}")
            analysis_results['momentum'] = {'score': 0, 'error': str(e)}
        
        try:
            # Smart Money Analysis
            smart_money_result = await analyzers['smart_money'].analyze(options_data, microstructure)
            analysis_results['smart_money'] = smart_money_result
        except Exception as e:
            logger.error(f"Smart money analysis error: {e}")
            analysis_results['smart_money'] = {'score': 0, 'error': str(e)}
        
        # Calculate overall market score
        scores = [result.get('score', 0) for result in analysis_results.values()]
        overall_score = np.mean(scores) if scores else 0
        
        return {
            "status": "success",
            "overall_score": round(overall_score, 2),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "market_condition": "EXCELLENT" if overall_score >= 9 else "GOOD" if overall_score >= 7 else "FAIR" if overall_score >= 5 else "POOR",
            "detailed_analysis": analysis_results
        }
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        raise HTTPException(500, f"Error in market analysis: {str(e)}")

@api_router.get("/strategies")
async def get_strategies():
    """Get all trading strategies with their status"""
    try:
        strategies = []
        
        for name, strategy_instance in strategy_instances.items():
            strategy_data = {
                'name': name,
                'enabled': getattr(strategy_instance, 'is_enabled', True),
                'allocation': getattr(strategy_instance, 'allocation', 0.2),
                'type': strategy_instance.__class__.__name__,
                'health': 'healthy'
            }
            
            # Add metrics if available
            if hasattr(strategy_instance, 'get_strategy_metrics'):
                try:
                    strategy_data['metrics'] = strategy_instance.get_strategy_metrics()
                except:
                    strategy_data['metrics'] = {}
            
            strategies.append(strategy_data)
        
        return {
            "strategies": strategies,
            "total_strategies": len(strategies),
            "active_strategies": len([s for s in strategies if s['enabled']]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(500, f"Error getting strategies: {str(e)}")

@api_router.post("/strategy/{strategy_name}/toggle")
async def toggle_strategy(strategy_name: str):
    """Toggle strategy enabled/disabled status"""
    try:
        if strategy_name not in strategy_instances:
            raise HTTPException(404, f"Strategy {strategy_name} not found")
        
        strategy = strategy_instances[strategy_name]
        
        # Toggle enabled status
        current_status = getattr(strategy, 'is_enabled', True)
        new_status = not current_status
        
        if hasattr(strategy, 'is_enabled'):
            strategy.is_enabled = new_status
        
        logger.info(f"Strategy {strategy_name} {'enabled' if new_status else 'disabled'}")
        
        return {
            "success": True,
            "strategy": strategy_name,
            "enabled": new_status,
            "message": f"Strategy {'enabled' if new_status else 'disabled'} successfully"
        }
        
    except Exception as e:
        logger.error(f"Error toggling strategy: {e}")
        raise HTTPException(500, f"Error toggling strategy: {str(e)}")

@api_router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop all trading activities"""
    try:
        logger.critical("EMERGENCY STOP initiated via API")
        
        # Stop all trading
        system_state['trading_active'] = False
        system_state['emergency_mode'] = True
        
        # Disable all strategies
        for strategy in strategy_instances.values():
            if hasattr(strategy, 'is_enabled'):
                strategy.is_enabled = False
        
        results = {
            'trading_stopped': True,
            'strategies_disabled': len(strategy_instances),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast emergency stop to all clients
        await broadcast_websocket_message({
            "type": "emergency_stop",
            "message": "Emergency stop activated - All trading halted",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "message": "Emergency stop executed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(500, f"Error during emergency stop: {str(e)}")

@api_router.post("/resume-trading")
async def resume_trading():
    """Resume trading activities after emergency stop"""
    try:
        logger.info("Resuming trading activities")
        
        # Resume trading
        system_state['trading_active'] = True
        system_state['emergency_mode'] = False
        
        # Re-enable strategies
        enabled_count = 0
        for strategy in strategy_instances.values():
            if hasattr(strategy, 'is_enabled'):
                strategy.is_enabled = True
                enabled_count += 1
        
        results = {
            'trading_resumed': True,
            'strategies_enabled': enabled_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast resume to all clients
        await broadcast_websocket_message({
            "type": "trading_resumed",
            "message": "Trading activities resumed",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "message": "Trading resumed successfully",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error resuming trading: {e}")
        raise HTTPException(500, f"Error resuming trading: {str(e)}")

@api_router.websocket("/ws/trading-data")
async def websocket_trading_data(websocket: WebSocket):
    """WebSocket endpoint for real-time trading data"""
    await websocket.accept()
    websocket_connections.add(websocket)
    
    try:
        # Send initial data
        initial_data = {
            "type": "initial_data",
            "system_status": system_state,
            "market_open": is_market_open(),
            "strategies": len(strategy_instances),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(10)
            
            # Send system update
            update = {
                "type": "system_update",
                "system_health": system_state['system_health'],
                "trading_active": system_state['trading_active'],
                "daily_pnl": system_state['daily_pnl'],
                "active_strategies": len([s for s in strategy_instances.values() 
                                        if getattr(s, 'is_enabled', True)]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_text(json.dumps(update))
            
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_connections.discard(websocket)

# Include the router in the main app
app.include_router(api_router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize everything on startup"""
    try:
        logger.info("Starting Elite Autonomous Algo Trading Platform...")
        
        system_state['start_time'] = datetime.utcnow()
        
        # Initialize database
        await init_database()
        
        # Initialize elite trading system
        if CORE_COMPONENTS_AVAILABLE:
            await initialize_elite_trading_system()
            await initialize_trading_strategies()
        
        # Setup scheduler
        setup_scheduler()
        
        # Mark system as initialized
        system_state['initialized'] = True
        
        logger.info("Elite Trading Platform started successfully!")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        system_state['system_health'] = 'ERROR'
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down Elite Trading Platform...")
        
        # Stop scheduler
        if scheduler.running:
            scheduler.shutdown()
        
        # Stop all trading activities
        system_state['trading_active'] = False
        
        # Close database connections
        if redis_client:
            await redis_client.close()
            
        if db_pool:
            await db_pool.close()
        
        logger.info("Elite Trading Platform shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
