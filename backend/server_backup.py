from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
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
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import websockets
import aiohttp
import numpy as np
from kiteconnect import KiteConnect
import pyotp

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
REDIS_URL = os.environ.get('REDIS_URL')

# API credentials
ZERODHA_API_KEY = os.environ.get('ZERODHA_API_KEY')
ZERODHA_API_SECRET = os.environ.get('ZERODHA_API_SECRET')
ZERODHA_CLIENT_ID = os.environ.get('ZERODHA_CLIENT_ID')

TRUEDATA_USERNAME = os.environ.get('TRUEDATA_USERNAME')
TRUEDATA_PASSWORD = os.environ.get('TRUEDATA_PASSWORD')
TRUEDATA_URL = os.environ.get('TRUEDATA_URL')
TRUEDATA_PORT = int(os.environ.get('TRUEDATA_PORT', 8086))

# Trading configuration
PAPER_TRADING = os.environ.get('PAPER_TRADING', 'true').lower() == 'true'
AUTONOMOUS_TRADING_ENABLED = os.environ.get('AUTONOMOUS_TRADING_ENABLED', 'true').lower() == 'true'
DAILY_STOP_LOSS_PERCENT = 2.0

# Create the main app
app = FastAPI(title="Autonomous Algo Trading Platform", version="1.0.0")

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import core strategies
import sys
sys.path.append('/app/backend')

logger = logging.getLogger(__name__)

# Initialize advanced strategies
ADVANCED_STRATEGIES_AVAILABLE = False
try:
    from src.core.momentum_surfer import MomentumSurfer
    from src.core.news_impact_scalper import NewsImpactScalper
    from src.core.volatility_explosion import VolatilityExplosion
    from src.core.confluence_amplifier import ConfluenceAmplifier
    from src.core.pattern_hunter import PatternHunter
    from src.core.liquidity_magnet import LiquidityMagnet
    from src.core.volume_profile_scalper import VolumeProfileScalper
    ADVANCED_STRATEGIES_AVAILABLE = True
    logger.info("Advanced trading strategies loaded successfully")
except ImportError as e:
    logger.warning(f"Advanced strategies not available: {e}")
    MomentumSurfer = None
    NewsImpactScalper = None
    VolatilityExplosion = None
    ConfluenceAmplifier = None
    PatternHunter = None
    LiquidityMagnet = None
    VolumeProfileScalper = None
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
db_pool = None
redis_client = None
kite = None
scheduler = AsyncIOScheduler()
websocket_connections = set()
active_strategies = {}
strategy_instances = {}  # Store advanced strategy instances
daily_pnl = 0.0
positions = {}
market_data = {}

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    risk_tolerance: float = 1.0
    max_position_size: float = 100000.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Strategy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    parameters: Dict
    is_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    order_id: Optional[str] = None
    status: str = "PENDING"

class Position(BaseModel):
    symbol: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MarketTick(BaseModel):
    symbol: str
    ltp: float
    volume: int
    bid: float
    ask: float
    oi: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Database initialization
async def init_database():
    global db_pool, redis_client
    
    try:
        # PostgreSQL connection
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=3,
            max_size=10,
            command_timeout=60
        )
        
        # Redis connection  
        redis_client = redis.from_url(REDIS_URL)
        
        # Create tables
        async with db_pool.acquire() as conn:
            # Drop and recreate positions table to ensure correct schema
            await conn.execute("DROP TABLE IF EXISTS positions")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR PRIMARY KEY,
                    email VARCHAR UNIQUE NOT NULL,
                    name VARCHAR NOT NULL,
                    risk_tolerance FLOAT DEFAULT 1.0,
                    max_position_size FLOAT DEFAULT 100000.0,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    parameters JSONB,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id VARCHAR PRIMARY KEY,
                    strategy_id VARCHAR,
                    symbol VARCHAR NOT NULL,
                    action VARCHAR NOT NULL,
                    quantity INTEGER NOT NULL,
                    price FLOAT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    order_id VARCHAR,
                    status VARCHAR DEFAULT 'PENDING'
                )
            """)
            
            await conn.execute("""
                CREATE TABLE positions (
                    symbol VARCHAR PRIMARY KEY,
                    quantity INTEGER NOT NULL,
                    average_price FLOAT NOT NULL,
                    current_price FLOAT NOT NULL,
                    pnl FLOAT NOT NULL DEFAULT 0.0,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# Zerodha Kite Connect initialization
def init_kite():
    global kite
    try:
        kite = KiteConnect(api_key=ZERODHA_API_KEY)
        logger.info("Kite Connect initialized")
        return kite
    except Exception as e:
        logger.error(f"Kite initialization error: {e}")
        return None

# Trading Strategies Implementation
class TradingStrategies:
    
    @staticmethod
    async def moving_average_crossover(symbol: str, short_period: int = 5, long_period: int = 20):
        """Strategy 1: Moving Average Crossover"""
        try:
            # Get historical data from cache or fetch
            prices = await get_historical_prices(symbol, long_period + 5)
            
            if len(prices) < long_period:
                return None
                
            short_ma = np.mean(prices[-short_period:])
            long_ma = np.mean(prices[-long_period:])
            prev_short_ma = np.mean(prices[-(short_period+1):-1])
            prev_long_ma = np.mean(prices[-(long_period+1):-1])
            
            # Crossover detection
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                return {"action": "BUY", "confidence": 0.8}
            elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                return {"action": "SELL", "confidence": 0.8}
                
            return None
        except Exception as e:
            logger.error(f"MA Crossover error for {symbol}: {e}")
            return None
    
    @staticmethod
    async def rsi_strategy(symbol: str, period: int = 14, oversold: int = 30, overbought: int = 70):
        """Strategy 2: RSI Momentum"""
        try:
            prices = await get_historical_prices(symbol, period + 10)
            
            if len(prices) < period + 1:
                return None
                
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return None
                
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            if rsi < oversold:
                return {"action": "BUY", "confidence": 0.75}
            elif rsi > overbought:
                return {"action": "SELL", "confidence": 0.75}
                
            return None
        except Exception as e:
            logger.error(f"RSI Strategy error for {symbol}: {e}")
            return None
    
    @staticmethod
    async def breakout_strategy(symbol: str, lookback: int = 20):
        """Strategy 3: Price Breakout"""
        try:
            prices = await get_historical_prices(symbol, lookback + 5)
            
            if len(prices) < lookback:
                return None
                
            recent_high = max(prices[-lookback:-1])
            recent_low = min(prices[-lookback:-1])
            current_price = prices[-1]
            
            if current_price > recent_high * 1.02:  # 2% breakout
                return {"action": "BUY", "confidence": 0.9}
            elif current_price < recent_low * 0.98:  # 2% breakdown
                return {"action": "SELL", "confidence": 0.9}
                
            return None
        except Exception as e:
            logger.error(f"Breakout Strategy error for {symbol}: {e}")
            return None
    
    @staticmethod
    async def mean_reversion_strategy(symbol: str, lookback: int = 15, threshold: float = 2.0):
        """Strategy 4: Mean Reversion"""
        try:
            prices = await get_historical_prices(symbol, lookback + 5)
            
            if len(prices) < lookback:
                return None
                
            mean_price = np.mean(prices[-lookback:])
            std_price = np.std(prices[-lookback:])
            current_price = prices[-1]
            
            z_score = (current_price - mean_price) / std_price
            
            if z_score < -threshold:
                return {"action": "BUY", "confidence": 0.7}
            elif z_score > threshold:
                return {"action": "SELL", "confidence": 0.7}
                
            return None
        except Exception as e:
            logger.error(f"Mean Reversion error for {symbol}: {e}")
            return None
    
    @staticmethod
    async def volume_breakout_strategy(symbol: str, volume_threshold: float = 1.5):
        """Strategy 5: Volume Breakout"""
        try:
            # Get volume data from market_data
            if symbol not in market_data:
                return None
                
            current_tick = market_data[symbol]
            avg_volume = await get_average_volume(symbol, 20)
            
            if avg_volume == 0:
                return None
                
            volume_ratio = current_tick.volume / avg_volume
            
            if volume_ratio > volume_threshold:
                # High volume, check price direction
                price_change = await get_price_change_percent(symbol, 5)
                if price_change > 1:
                    return {"action": "BUY", "confidence": 0.8}
                elif price_change < -1:
                    return {"action": "SELL", "confidence": 0.8}
                    
            return None
        except Exception as e:
            logger.error(f"Volume Breakout error for {symbol}: {e}")
            return None
    
    @staticmethod
    async def bollinger_bands_strategy(symbol: str, period: int = 20, std_dev: float = 2.0):
        """Strategy 6: Bollinger Bands"""
        try:
            prices = await get_historical_prices(symbol, period + 5)
            
            if len(prices) < period:
                return None
                
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            current_price = prices[-1]
            
            if current_price < lower_band:
                return {"action": "BUY", "confidence": 0.8}
            elif current_price > upper_band:
                return {"action": "SELL", "confidence": 0.8}
                
            return None
        except Exception as e:
            logger.error(f"Bollinger Bands error for {symbol}: {e}")
            return None

# Helper functions
async def get_historical_prices(symbol: str, periods: int) -> List[float]:
    """Get historical prices from cache or external source"""
    try:
        cache_key = f"prices:{symbol}:{periods}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # In a real implementation, fetch from TrueData or Kite
        # For now, simulate with current price variations
        if symbol in market_data:
            base_price = market_data[symbol].ltp
            # Generate mock historical data
            prices = []
            for i in range(periods):
                variation = np.random.normal(0, 0.01)  # 1% std deviation
                price = base_price * (1 + variation)
                prices.append(price)
            
            await redis_client.setex(cache_key, 300, json.dumps(prices))  # 5 min cache
            return prices
        
        return []
    except Exception as e:
        logger.error(f"Error getting historical prices for {symbol}: {e}")
        return []

async def get_average_volume(symbol: str, periods: int) -> float:
    """Get average volume for a symbol"""
    try:
        # Mock implementation - replace with real data
        return 1000000.0
    except Exception as e:
        logger.error(f"Error getting average volume for {symbol}: {e}")
        return 0.0

async def get_price_change_percent(symbol: str, periods: int) -> float:
    """Get price change percentage"""
    try:
        prices = await get_historical_prices(symbol, periods + 1)
        if len(prices) >= 2:
            return ((prices[-1] - prices[0]) / prices[0]) * 100
        return 0.0
    except Exception as e:
        logger.error(f"Error getting price change for {symbol}: {e}")
        return 0.0

# Position sizing and risk management
async def calculate_position_size(symbol: str, strategy_confidence: float, risk_amount: float) -> int:
    """Calculate optimal position size based on risk management"""
    try:
        if symbol not in market_data:
            return 0
            
        current_price = market_data[symbol].ltp
        
        # Basic position sizing: risk_amount / (price * risk_per_share)
        risk_per_share = current_price * 0.02  # 2% risk per share
        max_quantity = int(risk_amount / risk_per_share)
        
        # Adjust by strategy confidence
        adjusted_quantity = int(max_quantity * strategy_confidence)
        
        # Ensure minimum lot size for F&O (typically 25, 50, or 75)
        lot_size = 25  # Default lot size
        adjusted_quantity = (adjusted_quantity // lot_size) * lot_size
        
        return max(adjusted_quantity, lot_size) if adjusted_quantity > 0 else 0
        
    except Exception as e:
        logger.error(f"Error calculating position size for {symbol}: {e}")
        return 0

# Order management
async def place_order(symbol: str, action: str, quantity: int, order_type: str = "MARKET") -> Dict:
    """Place order through Zerodha Kite or paper trading"""
    try:
        if PAPER_TRADING:
            # Paper trading simulation
            order_id = str(uuid.uuid4())
            current_price = 0
            
            if symbol in market_data:
                current_price = market_data[symbol].ltp
            else:
                # Default prices for simulation
                default_prices = {"NIFTY": 19500, "BANKNIFTY": 45000, "FINNIFTY": 19000}
                current_price = default_prices.get(symbol, 100)
            
            order_details = {
                "order_id": order_id,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": current_price,
                "status": "COMPLETED",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update positions
            await update_position(symbol, action, quantity, current_price)
            
            logger.info(f"Paper trade executed: {order_details}")
            return order_details
        else:
            # Real trading through Kite Connect
            if not kite:
                raise HTTPException(400, "Kite Connect not initialized")
                
            transaction_type = kite.TRANSACTION_TYPE_BUY if action == "BUY" else kite.TRANSACTION_TYPE_SELL
            
            order_id = kite.place_order(
                variety=kite.VARIETY_REGULAR,
                exchange=kite.EXCHANGE_NFO,  # F&O exchange
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=kite.PRODUCT_MIS,  # Intraday
                order_type=kite.ORDER_TYPE_MARKET
            )
            
            return {
                "order_id": order_id,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "status": "PLACED"
            }
            
    except Exception as e:
        logger.error(f"Error placing order for {symbol}: {e}")
        raise HTTPException(400, f"Order placement failed: {str(e)}")

async def update_position(symbol: str, action: str, quantity: int, price: float):
    """Update position in database"""
    try:
        async with db_pool.acquire() as conn:
            # Get existing position
            existing = await conn.fetchrow(
                "SELECT * FROM positions WHERE symbol = $1", symbol
            )
            
            if existing:
                current_qty = existing['quantity']
                avg_price = existing['average_price']
                
                if action == "BUY":
                    new_qty = current_qty + quantity
                    new_avg_price = ((current_qty * avg_price) + (quantity * price)) / new_qty
                else:  # SELL
                    new_qty = current_qty - quantity
                    new_avg_price = avg_price  # Keep same average for sells
                
                current_price = market_data.get(symbol, {}).get('ltp', price)
                pnl = (current_price - new_avg_price) * new_qty
                
                await conn.execute("""
                    UPDATE positions 
                    SET quantity = $2, average_price = $3, current_price = $4, pnl = $5, timestamp = NOW()
                    WHERE symbol = $1
                """, symbol, new_qty, new_avg_price, current_price, pnl)
            else:
                # New position
                pnl = 0.0  # No P&L for new position
                sign = 1 if action == "BUY" else -1
                
                await conn.execute("""
                    INSERT INTO positions (symbol, quantity, average_price, current_price, pnl)
                    VALUES ($1, $2, $3, $4, $5)
                """, symbol, quantity * sign, price, price, pnl)
                
        logger.info(f"Position updated for {symbol}: {action} {quantity} @ {price}")
        
    except Exception as e:
        logger.error(f"Error updating position for {symbol}: {e}")

# Auto square-off implementation
async def execute_real_zerodha_order(order_params: Dict):
    """Execute real order through Zerodha API"""
    try:
        # Initialize Zerodha connection
        from src.core.zerodha import ZerodhaIntegration
        
        zerodha_config = {
            'api_key': ZERODHA_API_KEY,
            'api_secret': ZERODHA_API_SECRET,
            'user_id': ZERODHA_CLIENT_ID,
            'redis_url': REDIS_URL
        }
        
        zerodha = ZerodhaIntegration(zerodha_config)
        await zerodha.initialize()
        
        if not await zerodha.is_connected():
            logger.error("❌ Zerodha not connected - falling back to paper trading")
            return await execute_paper_order(order_params)
        
        # Place real order
        order_result = await zerodha.place_order(
            symbol=order_params['symbol'],
            quantity=order_params['quantity'],
            order_type=order_params['order_type'],
            side=order_params['side'],
            price=order_params.get('price')
        )
        
        if order_result.get('success'):
            logger.info(f"🚀 REAL ZERODHA ORDER PLACED: {order_result['order_id']}")
            
            # Store in database
            if db_pool:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO orders (
                            order_id, user_id, symbol, quantity, order_type, side,
                            price, broker_order_id, status, strategy_name, created_at,
                            trade_reason, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, 
                    order_result['order_id'], order_params['user_id'], order_params['symbol'],
                    order_params['quantity'], order_params['order_type'], order_params['side'],
                    order_params.get('price'), order_result.get('broker_order_id'), 
                    'PLACED', order_params['strategy_name'], datetime.utcnow(),
                    order_params['trade_reason'], json.dumps(order_result, default=str))
            
            return order_result
        else:
            logger.error(f"❌ Zerodha order failed: {order_result}")
            return {'success': False, 'error': order_result}
        
    except Exception as e:
        logger.error(f"Error executing real Zerodha order: {e}")
        return {'success': False, 'error': str(e)}

async def execute_paper_order(order_params: Dict) -> Dict:
    """Execute order in paper trading mode"""
    try:
        # Simulate realistic order execution
        order_id = f"PAPER_{uuid.uuid4().hex[:8]}"
        
        # Get current market price for execution
        current_data = await get_real_market_data(order_params['symbol'])
        execution_price = current_data['ltp'] if current_data else order_params.get('price', 0)
        
        # Simulate small slippage for market orders
        if order_params.get('order_type') == 'MARKET':
            slippage = 0.05 / 100  # 0.05% slippage
            if order_params['side'] == 'BUY':
                execution_price *= (1 + slippage)
            else:
                execution_price *= (1 - slippage)
        
        # Store paper order in database
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO orders (
                        order_id, user_id, symbol, quantity, order_type, side,
                        price, average_price, status, strategy_name, created_at, filled_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """, order_id, order_params['user_id'], order_params['symbol'],
                order_params['quantity'], order_params['order_type'], order_params['side'],
                order_params.get('price', execution_price), execution_price, 'FILLED',
                order_params['strategy_name'], datetime.utcnow(), datetime.utcnow())
        
        return {
            'success': True,
            'order_id': order_id,
            'execution_price': execution_price,
            'status': 'FILLED'
        }
        
    except Exception as e:
        logger.error(f"Error executing paper order: {e}")
        return {'success': False, 'error': str(e)}

async def get_real_market_data(symbol: str) -> Optional[Dict]:
    """Get real market data from database or API"""
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                # Get latest market data from database
                result = await conn.fetchrow("""
                    SELECT symbol, ltp, bid, ask, volume, oi, timestamp, 
                           open_price, high_price, low_price, change_percent
                    FROM market_data_live 
                    WHERE symbol = $1 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, symbol)
                
                if result:
                    return {
                        'symbol': result['symbol'],
                        'ltp': result['ltp'],
                        'bid': result['bid'],
                        'ask': result['ask'], 
                        'volume': result['volume'],
                        'oi': result['oi'],
                        'open': result['open_price'],
                        'high': result['high_price'],
                        'low': result['low_price'],
                        'change_percent': result['change_percent'],
                        'timestamp': result['timestamp']
                    }
        
        # Fallback: Try to get from Zerodha API
        try:
            from src.core.zerodha import ZerodhaIntegration
            zerodha_config = {
                'api_key': ZERODHA_API_KEY,
                'api_secret': ZERODHA_API_SECRET,
                'user_id': ZERODHA_CLIENT_ID,
                'redis_url': REDIS_URL
            }
            
            zerodha = ZerodhaIntegration(zerodha_config)
            await zerodha.initialize()
            
            if await zerodha.is_connected():
                quotes = await zerodha.get_quote([symbol])
                if symbol in quotes:
                    quote = quotes[symbol]
                    
                    # Store in database for future use
                    if db_pool:
                        async with db_pool.acquire() as conn:
                            await conn.execute("""
                                INSERT INTO market_data_live (
                                    symbol, ltp, bid, ask, volume, oi, 
                                    open_price, high_price, low_price, timestamp
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                                    ltp = EXCLUDED.ltp,
                                    bid = EXCLUDED.bid,
                                    ask = EXCLUDED.ask,
                                    volume = EXCLUDED.volume
                            """, symbol, quote['ltp'], quote.get('bid', 0), 
                            quote.get('ask', 0), quote.get('volume', 0), 
                            quote.get('oi', 0), quote.get('open', 0),
                            quote.get('high', 0), quote.get('low', 0), 
                            datetime.utcnow())
                    
                    return quote
            
        except Exception as e:
            logger.warning(f"Failed to get real market data from API: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting real market data: {e}")
        return None

async def create_square_off_order(position_id: str, symbol: str, quantity: int, reason: str):
    """Create square-off order for position"""
    try:
        # Create opposite order to close position
        side = 'SELL' if quantity > 0 else 'BUY'
        abs_quantity = abs(quantity)
        
        order_params = {
            'user_id': 'autonomous_system',
            'symbol': symbol,
            'order_type': 'MARKET',
            'quantity': abs_quantity,
            'side': side,
            'strategy_name': 'AUTO_SQUARE_OFF',
            'signal_id': f'CLOSE_{position_id}',
            'trade_reason': reason
        }
        
        if PAPER_TRADING:
            return await execute_paper_order(order_params)
        else:
            return await execute_real_zerodha_order(order_params)
        
    except Exception as e:
        logger.error(f"Error creating square-off order: {e}")
        return {'success': False, 'error': str(e)}

async def auto_square_off():
    """Auto square off all positions at market close"""
    try:
        logger.info("🔔 Auto square-off initiated - Market closing")
        
        if not db_pool:
            return
        
        async with db_pool.acquire() as conn:
            # Get all open positions
            positions = await conn.fetch("""
                SELECT position_id, user_id, symbol, quantity, average_entry_price,
                       strategy_name, entry_reason
                FROM positions 
                WHERE status = 'OPEN'
            """)
            
            if not positions:
                logger.info("No open positions to square off")
                return
            
            for position in positions:
                try:
                    # Create square-off order
                    square_off_result = await create_square_off_order(
                        position['position_id'],
                        position['symbol'],
                        position['quantity'],
                        'AUTO_SQUARE_OFF'
                    )
                    
                    if square_off_result['success']:
                        logger.info(f"✅ Auto squared off {position['symbol']} - Position: {position['position_id']}")
                    else:
                        logger.error(f"❌ Failed to square off {position['symbol']}: {square_off_result}")
                        
                except Exception as e:
                    logger.error(f"Error squaring off position {position['position_id']}: {e}")
        
        logger.info("Auto square-off completed")
        
    except Exception as e:
        logger.error(f"Error in auto square-off: {e}")

# Daily P&L monitoring and stop loss
async def check_daily_stop_loss():
    """Check if daily stop loss is hit"""
    try:
        global daily_pnl
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT SUM(pnl) FROM positions")
            daily_pnl = result or 0.0
            
            # Get user's risk capital (assuming $100,000 for now)
            risk_capital = 100000.0
            stop_loss_amount = risk_capital * (DAILY_STOP_LOSS_PERCENT / 100)
            
            if daily_pnl <= -stop_loss_amount:
                logger.warning(f"Daily stop loss hit! P&L: {daily_pnl}, Stop loss: {-stop_loss_amount}")
                
                # Square off all positions
                await auto_square_off()
                
                # Disable autonomous trading for the day
                global AUTONOMOUS_TRADING_ENABLED
                AUTONOMOUS_TRADING_ENABLED = False
                
                # Broadcast to all connected clients
                await broadcast_message({
                    "type": "stop_loss_alert",
                    "message": f"Daily stop loss hit. All positions squared off.",
                    "pnl": daily_pnl
                })
        
    except Exception as e:
        logger.error(f"Error checking daily stop loss: {e}")

# Strategy execution engine - Updated to use advanced src/core strategies
async def execute_strategies():
    """Execute all active trading strategies using advanced src/core implementations"""
    try:
        if not AUTONOMOUS_TRADING_ENABLED:
            return
            
        if not ADVANCED_STRATEGIES_AVAILABLE:
            logger.warning("Advanced strategies not available, falling back to basic strategies")
            await execute_basic_strategies()
            return
            
        # Get active strategies from database
        async with db_pool.acquire() as conn:
            strategies = await conn.fetch("SELECT * FROM strategies WHERE is_active = TRUE")
            
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]  # Main F&O symbols
        
        for symbol in symbols:
            if symbol not in market_data:
                continue
                
            # Execute advanced strategies using src/core implementations
            strategy_results = []
            current_time = datetime.utcnow()
            
            # Get price and volume data for strategies
            price_data = await get_historical_prices(symbol, 100)
            volume_data = await get_historical_prices(symbol, 100)  # Using same function for volume
            
            if len(price_data) < 50 or len(volume_data) < 50:
                continue
            
            # Execute each advanced strategy
            try:
                # Execute all 6 strategies
                strategy_results = []
                
                # Strategy 1: Moving Average Crossover
                ma_result = await TradingStrategies.moving_average_crossover(symbol)
                if ma_result:
                    strategy_results.append(("MA_Crossover", ma_result))
                
                # Strategy 2: RSI
                rsi_result = await TradingStrategies.rsi_strategy(symbol)
                if rsi_result:
                    strategy_results.append(("RSI", rsi_result))
                
                # Strategy 3: Breakout
                breakout_result = await TradingStrategies.breakout_strategy(symbol)
                if breakout_result:
                    strategy_results.append(("Breakout", breakout_result))
                
                # Strategy 4: Mean Reversion
                mr_result = await TradingStrategies.mean_reversion_strategy(symbol)
                if mr_result:
                    strategy_results.append(("Mean_Reversion", mr_result))
                
                # Strategy 5: Volume Breakout
                vol_result = await TradingStrategies.volume_breakout_strategy(symbol)
                if vol_result:
                    strategy_results.append(("Volume_Breakout", vol_result))
                
                # Strategy 6: Bollinger Bands
                bb_result = await TradingStrategies.bollinger_bands_strategy(symbol)
                if bb_result:
                    strategy_results.append(("Bollinger_Bands", bb_result))
                
            except Exception as e:
                logger.error(f"Error executing advanced strategy for {symbol}: {e}")
                continue
            
            # Process strategy results with enhanced decision making
            if strategy_results:
                await make_trading_decision(symbol, strategy_results)
        
    except Exception as e:
        logger.error(f"Error executing advanced strategies: {e}")

async def execute_basic_strategies():
    """Fallback to basic strategies if advanced ones are not available"""
    try:
        # Get active strategies from database
        async with db_pool.acquire() as conn:
            strategies = await conn.fetch("SELECT * FROM strategies WHERE is_active = TRUE")
            
        symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]  # Main F&O symbols
        
        for symbol in symbols:
            if symbol not in market_data:
                continue
                
            # Execute all 6 basic strategies
            strategy_results = []
            
            # Strategy 1: Moving Average Crossover
            ma_result = await TradingStrategies.moving_average_crossover(symbol)
            if ma_result:
                strategy_results.append(("MA_Crossover", ma_result))
            
            # Strategy 2: RSI
            rsi_result = await TradingStrategies.rsi_strategy(symbol)
            if rsi_result:
                strategy_results.append(("RSI", rsi_result))
            
            # Strategy 3: Breakout
            breakout_result = await TradingStrategies.breakout_strategy(symbol)
            if breakout_result:
                strategy_results.append(("Breakout", breakout_result))
            
            # Strategy 4: Mean Reversion
            mr_result = await TradingStrategies.mean_reversion_strategy(symbol)
            if mr_result:
                strategy_results.append(("Mean_Reversion", mr_result))
            
            # Strategy 5: Volume Breakout
            vol_result = await TradingStrategies.volume_breakout_strategy(symbol)
            if vol_result:
                strategy_results.append(("Volume_Breakout", vol_result))
            
            # Strategy 6: Bollinger Bands
            bb_result = await TradingStrategies.bollinger_bands_strategy(symbol)
            if bb_result:
                strategy_results.append(("Bollinger_Bands", bb_result))
            
            # Consensus decision making
            if strategy_results:
                await make_trading_decision(symbol, strategy_results)
        
    except Exception as e:
        logger.error(f"Error executing basic strategies: {e}")

async def make_trading_decision(symbol: str, strategy_results: List):
    """Make final trading decision based on multiple strategy signals"""
    try:
        buy_signals = [r for r in strategy_results if r[1]["action"] == "BUY"]
        sell_signals = [r for r in strategy_results if r[1]["action"] == "SELL"]
        
        # Simple majority voting with confidence weighting
        buy_confidence = sum([r[1]["confidence"] for r in buy_signals])
        sell_confidence = sum([r[1]["confidence"] for r in sell_signals])
        
        decision_threshold = 1.5  # Require decent confidence
        
        if buy_confidence > decision_threshold and buy_confidence > sell_confidence:
            # Execute BUY
            avg_confidence = buy_confidence / len(buy_signals)
            quantity = await calculate_position_size(symbol, avg_confidence, 50000.0)
            
            if quantity > 0:
                order_result = await place_order(symbol, "BUY", quantity)
                logger.info(f"Strategy decision: BUY {quantity} {symbol} - Confidence: {avg_confidence}")
                
        elif sell_confidence > decision_threshold and sell_confidence > buy_confidence:
            # Execute SELL
            avg_confidence = sell_confidence / len(sell_signals)
            quantity = await calculate_position_size(symbol, avg_confidence, 50000.0)
            
            if quantity > 0:
                order_result = await place_order(symbol, "SELL", quantity)
                logger.info(f"Strategy decision: SELL {quantity} {symbol} - Confidence: {avg_confidence}")
        
    except Exception as e:
        logger.error(f"Error making trading decision for {symbol}: {e}")

# WebSocket management
async def broadcast_message(message: Dict):
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

# WebSocket management
async def broadcast_message(message: Dict):
    """Broadcast message to all connected WebSocket clients"""
    global websocket_connections
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
    return {"message": "Autonomous Algo Trading Platform API", "status": "running"}

@api_router.get("/status")
async def get_status():
    """Get system status"""
    return {
        "autonomous_trading": AUTONOMOUS_TRADING_ENABLED,
        "paper_trading": PAPER_TRADING,
        "daily_pnl": daily_pnl,
        "active_connections": len(websocket_connections),
        "market_data_symbols": len(market_data)
    }

@api_router.get("/positions")
async def get_positions():
    """Get current positions"""
    try:
        async with db_pool.acquire() as conn:
            positions_data = await conn.fetch("SELECT * FROM positions WHERE quantity != 0")
            return [dict(pos) for pos in positions_data]
    except Exception as e:
        raise HTTPException(500, f"Error fetching positions: {str(e)}")

@api_router.get("/strategies")
async def get_strategies():
    """Get all trading strategies"""
    try:
        async with db_pool.acquire() as conn:
            strategies_data = await conn.fetch("SELECT * FROM strategies")
            return [dict(strategy) for strategy in strategies_data]
    except Exception as e:
        raise HTTPException(500, f"Error fetching strategies: {str(e)}")

@api_router.post("/strategies")
async def create_strategy(strategy: Strategy):
    """Create a new trading strategy"""
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO strategies (id, name, description, parameters, is_active)
                VALUES ($1, $2, $3, $4, $5)
            """, strategy.id, strategy.name, strategy.description, 
                json.dumps(strategy.parameters), strategy.is_active)
            
        return {"message": "Strategy created successfully", "strategy_id": strategy.id}
    except Exception as e:
        raise HTTPException(500, f"Error creating strategy: {str(e)}")

@api_router.put("/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: str):
    """Toggle strategy active status"""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE strategies 
                SET is_active = NOT is_active 
                WHERE id = $1
            """, strategy_id)
            
            if result == "UPDATE 0":
                raise HTTPException(404, "Strategy not found")
                
        return {"message": "Strategy status toggled successfully"}
    except Exception as e:
        raise HTTPException(500, f"Error toggling strategy: {str(e)}")

@api_router.post("/manual-order")
async def manual_order(
    symbol: str,
    action: str, 
    quantity: int
):
    """Place manual order"""
    try:
        order_result = await place_order(symbol, action.upper(), quantity)
        return order_result
    except Exception as e:
        raise HTTPException(500, f"Error placing manual order: {str(e)}")

@api_router.post("/square-off-all")
async def square_off_all_positions():
    """Manually square off all positions"""
    try:
        await auto_square_off()
        return {"message": "All positions squared off successfully"}
    except Exception as e:
        raise HTTPException(500, f"Error squaring off positions: {str(e)}")

@api_router.websocket("/ws/market-data")
async def websocket_market_data(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    global websocket_connections
    await websocket.accept()
    websocket_connections.add(websocket)
    
    try:
        # Get current positions
        current_positions = []
        try:
            async with db_pool.acquire() as conn:
                positions_data = await conn.fetch("SELECT * FROM positions WHERE quantity != 0")
                current_positions = [dict(pos) for pos in positions_data]
        except Exception as e:
            logger.error(f"Error fetching positions for websocket: {e}")
        
        # Send initial data
        initial_data = {
            "type": "initial_data",
            "positions": current_positions,
            "market_data": {
                k: {
                    "symbol": v.symbol,
                    "ltp": v.ltp,
                    "volume": v.volume,
                    "bid": v.bid,
                    "ask": v.ask,
                    "oi": v.oi,
                    "timestamp": v.timestamp.isoformat()
                } for k, v in market_data.items()
            },
            "daily_pnl": daily_pnl
        }
        
        await websocket.send_text(json.dumps(initial_data))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(5)
            # Send periodic heartbeat
            heartbeat = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(heartbeat))
            
    except WebSocketDisconnect:
        websocket_connections.discard(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_connections.discard(websocket)

# Mock TrueData feed simulation
async def simulate_market_data():
    """Simulate real-time market data (replace with actual TrueData integration)"""
    global websocket_connections
    symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
    base_prices = {"NIFTY": 19500, "BANKNIFTY": 45000, "FINNIFTY": 19000}
    
    while True:
        try:
            for symbol in symbols:
                # Simulate price movements
                if symbol not in market_data:
                    price = base_prices[symbol]
                else:
                    last_price = market_data[symbol].ltp
                    change = np.random.normal(0, 0.002)  # 0.2% volatility
                    price = last_price * (1 + change)
                
                # Create market tick
                tick = MarketTick(
                    symbol=symbol,
                    ltp=round(price, 2),
                    volume=np.random.randint(10000, 100000),
                    bid=round(price - 0.25, 2),
                    ask=round(price + 0.25, 2),
                    oi=np.random.randint(500000, 2000000)
                )
                
                market_data[symbol] = tick
                
                # Broadcast to clients
                await broadcast_message({
                    "type": "market_tick",
                    "data": {
                        "symbol": tick.symbol,
                        "ltp": tick.ltp,
                        "volume": tick.volume,
                        "bid": tick.bid,
                        "ask": tick.ask,
                        "oi": tick.oi,
                        "timestamp": tick.timestamp.isoformat()
                    }
                })
            
            await asyncio.sleep(1)  # Update every second
            
        except Exception as e:
            logger.error(f"Error in market data simulation: {e}")
            await asyncio.sleep(5)

# Scheduler setup
def setup_scheduler():
    """Setup scheduled tasks"""
    try:
        # Auto square-off at 3:15 PM
        scheduler.add_job(
            auto_square_off,
            CronTrigger(hour=15, minute=15, timezone='Asia/Kolkata'),
            id='auto_square_off'
        )
        
        # Strategy execution every 30 seconds during market hours
        scheduler.add_job(
            execute_strategies,
            'interval',
            seconds=30,
            id='strategy_execution'
        )
        
        # Stop loss check every 10 seconds
        scheduler.add_job(
            check_daily_stop_loss,
            'interval',
            seconds=10,
            id='stop_loss_check'
        )
        
        scheduler.start()
        logger.info("Scheduler started with all jobs")
        
    except Exception as e:
        logger.error(f"Error setting up scheduler: {e}")

# Initialize default strategies
async def init_default_strategies():
    """Initialize the 6 default trading strategies"""
    strategies = [
        {
            "name": "Moving Average Crossover",
            "description": "Buy when short MA crosses above long MA, sell when crosses below",
            "parameters": {"short_period": 5, "long_period": 20}
        },
        {
            "name": "RSI Momentum",
            "description": "Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought)",
            "parameters": {"period": 14, "oversold": 30, "overbought": 70}
        },
        {
            "name": "Price Breakout",
            "description": "Buy on upward breakout, sell on downward breakout",
            "parameters": {"lookback": 20}
        },
        {
            "name": "Mean Reversion",
            "description": "Buy when price is below mean, sell when above mean",
            "parameters": {"lookback": 15, "threshold": 2.0}
        },
        {
            "name": "Volume Breakout",
            "description": "Trade in direction of high volume moves",
            "parameters": {"volume_threshold": 1.5}
        },
        {
            "name": "Bollinger Bands",
            "description": "Buy at lower band, sell at upper band",
            "parameters": {"period": 20, "std_dev": 2.0}
        }
    ]
    
    try:
        async with db_pool.acquire() as conn:
            for strategy_config in strategies:
                strategy = Strategy(
                    name=strategy_config["name"],
                    description=strategy_config["description"],
                    parameters=strategy_config["parameters"],
                    is_active=True
                )
                
                # Check if strategy already exists
                existing = await conn.fetchval(
                    "SELECT id FROM strategies WHERE name = $1", strategy.name
                )
                
                if not existing:
                    await conn.execute("""
                        INSERT INTO strategies (id, name, description, parameters, is_active)
                        VALUES ($1, $2, $3, $4, $5)
                    """, strategy.id, strategy.name, strategy.description,
                        json.dumps(strategy.parameters), strategy.is_active)
                    
                    logger.info(f"Initialized strategy: {strategy.name}")
        
    except Exception as e:
        logger.error(f"Error initializing default strategies: {e}")

# Include the router in the main app
app.include_router(api_router)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize everything on startup"""
    try:
        logger.info("Starting Autonomous Algo Trading Platform...")
        
        # Initialize database
        await init_database()
        
        # Initialize Kite Connect
        init_kite()
        
        # Initialize default strategies
        await init_default_strategies()
        
        # Setup scheduler
        setup_scheduler()
        
        # Start market data simulation
        asyncio.create_task(simulate_market_data())
        
        logger.info("Platform started successfully!")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if scheduler.running:
            scheduler.shutdown()
        
        if redis_client:
            await redis_client.close()
            
        if db_pool:
            await db_pool.close()
            
        logger.info("Platform shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
