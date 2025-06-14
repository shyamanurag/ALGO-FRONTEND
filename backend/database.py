"""
Enhanced Database Module for Elite Trading Platform
Supports both SQLite (development) and PostgreSQL (production)
"""
import os
import asyncio
import asyncpg
import aiosqlite
import redis
from typing import Optional, Any, List, Dict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_pool = None
        self.redis_client = None
        self.db_type = None
        
    async def initialize(self, database_url: str, redis_url: Optional[str] = None):
        """Initialize database connections based on environment"""
        try:
            if database_url.startswith('postgresql://'):
                await self._init_postgresql(database_url)
            elif database_url.startswith('sqlite://'):
                await self._init_sqlite(database_url)
            else:
                raise ValueError(f"Unsupported database URL: {database_url}")
            
            if redis_url:
                await self._init_redis(redis_url)
                
            await self.create_schema()
            logger.info(f"Database initialized successfully: {self.db_type}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _init_postgresql(self, database_url: str):
        """Initialize PostgreSQL connection pool"""
        self.db_pool = await asyncpg.create_pool(
            database_url,
            min_size=3,
            max_size=20,
            command_timeout=60,
            server_settings={
                'jit': 'off'
            }
        )
        self.db_type = 'postgresql'
        logger.info("PostgreSQL connection pool created")
    
    async def _init_sqlite(self, database_url: str):
        """Initialize SQLite connection"""
        db_path = database_url.replace('sqlite:///', '')
        # Test connection
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        self.db_pool = db_path
        self.db_type = 'sqlite'
        logger.info(f"SQLite database connected: {db_path}")
    
    async def _init_redis(self, redis_url: str):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def execute_query(self, query: str, *params) -> List[Any]:
        """Execute query and return results"""
        if self.db_type == 'postgresql':
            async with self.db_pool.acquire() as conn:
                return await conn.fetch(query, *params)
        elif self.db_type == 'sqlite':
            async with aiosqlite.connect(self.db_pool) as db:
                async with db.execute(query, params) as cursor:
                    return await cursor.fetchall()
    
    async def execute_one(self, query: str, *params) -> Optional[Any]:
        """Execute query and return single result"""
        if self.db_type == 'postgresql':
            async with self.db_pool.acquire() as conn:
                return await conn.fetchrow(query, *params)
        elif self.db_type == 'sqlite':
            async with aiosqlite.connect(self.db_pool) as db:
                async with db.execute(query, params) as cursor:
                    return await cursor.fetchone()
    
    async def execute_write(self, query: str, *params) -> bool:
        """Execute write query (INSERT, UPDATE, DELETE)"""
        try:
            if self.db_type == 'postgresql':
                async with self.db_pool.acquire() as conn:
                    await conn.execute(query, *params)
            elif self.db_type == 'sqlite':
                async with aiosqlite.connect(self.db_pool) as db:
                    await db.execute(query, params)
                    await db.commit()
            return True
        except Exception as e:
            logger.error(f"Database write error: {e}")
            return False
    
    async def create_schema(self):
        """Create database schema based on database type"""
        if self.db_type == 'postgresql':
            await self._create_postgresql_schema()
        elif self.db_type == 'sqlite':
            await self._create_sqlite_schema()
    
    async def _create_postgresql_schema(self):
        """Create PostgreSQL schema with advanced features"""
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(100),
                phone_number VARCHAR(20),
                account_type VARCHAR(20) DEFAULT 'INDIVIDUAL',
                capital_allocation DECIMAL(15,2) DEFAULT 0.00,
                risk_percentage DECIMAL(5,2) DEFAULT 1.00,
                max_positions INTEGER DEFAULT 5,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trading_signals (
                signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(user_id),
                strategy_name VARCHAR(50) NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                action VARCHAR(10) NOT NULL,
                quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 10),
                confidence_level DECIMAL(5,2),
                entry_price DECIMAL(10,2),
                stop_loss_price DECIMAL(10,2),
                target_price DECIMAL(10,2),
                stop_loss_percent DECIMAL(5,2),
                target_percent DECIMAL(5,2),
                timeframe VARCHAR(10),
                entry_reason TEXT,
                technical_indicators JSONB,
                status VARCHAR(20) DEFAULT 'GENERATED',
                generated_at TIMESTAMP DEFAULT NOW(),
                executed_at TIMESTAMP,
                expired_at TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id VARCHAR(50) PRIMARY KEY,
                user_id UUID REFERENCES users(user_id),
                signal_id UUID REFERENCES trading_signals(signal_id),
                symbol VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                filled_quantity INTEGER DEFAULT 0,
                remaining_quantity INTEGER,
                order_type VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                price DECIMAL(10,2),
                average_fill_price DECIMAL(10,2),
                broker_order_id VARCHAR(100),
                exchange VARCHAR(20),
                status VARCHAR(20) DEFAULT 'PENDING',
                rejection_reason TEXT,
                strategy_name VARCHAR(50),
                order_tag VARCHAR(50),
                validity VARCHAR(20) DEFAULT 'DAY',
                disclosed_quantity INTEGER DEFAULT 0,
                trigger_price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                filled_at TIMESTAMP,
                cancelled_at TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS positions (
                position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(user_id),
                order_id VARCHAR(50) REFERENCES orders(order_id),
                symbol VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                average_entry_price DECIMAL(10,2) NOT NULL,
                total_investment DECIMAL(15,2) GENERATED ALWAYS AS (ABS(quantity) * average_entry_price) STORED,
                current_price DECIMAL(10,2) DEFAULT 0.00,
                current_value DECIMAL(15,2) GENERATED ALWAYS AS (ABS(quantity) * current_price) STORED,
                unrealized_pnl DECIMAL(15,2) GENERATED ALWAYS AS (
                    CASE 
                        WHEN quantity > 0 THEN (current_price - average_entry_price) * quantity
                        ELSE (average_entry_price - current_price) * ABS(quantity)
                    END
                ) STORED,
                pnl_percent DECIMAL(10,4) GENERATED ALWAYS AS (
                    CASE 
                        WHEN average_entry_price > 0 THEN 
                            ((current_price - average_entry_price) / average_entry_price) * 100
                        ELSE 0
                    END
                ) STORED,
                realized_pnl DECIMAL(15,2) DEFAULT 0.00,
                brokerage DECIMAL(10,2) DEFAULT 0.00,
                taxes DECIMAL(10,2) DEFAULT 0.00,
                net_pnl DECIMAL(15,2) GENERATED ALWAYS AS (unrealized_pnl - brokerage - taxes) STORED,
                status VARCHAR(20) DEFAULT 'OPEN',
                strategy_name VARCHAR(50),
                entry_reason TEXT,
                exit_reason TEXT,
                stop_loss DECIMAL(10,2),
                target DECIMAL(10,2),
                entry_time TIMESTAMP DEFAULT NOW(),
                exit_time TIMESTAMP,
                last_updated TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trades (
                trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                position_id UUID REFERENCES positions(position_id),
                user_id UUID REFERENCES users(user_id),
                symbol VARCHAR(50) NOT NULL,
                entry_order_id VARCHAR(50),
                exit_order_id VARCHAR(50),
                quantity INTEGER NOT NULL,
                entry_price DECIMAL(10,2) NOT NULL,
                exit_price DECIMAL(10,2),
                gross_pnl DECIMAL(15,2),
                brokerage DECIMAL(10,2) DEFAULT 0.00,
                taxes DECIMAL(10,2) DEFAULT 0.00,
                net_pnl DECIMAL(15,2),
                holding_period INTERVAL,
                strategy_name VARCHAR(50),
                trade_type VARCHAR(20),
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS market_data (
                data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                symbol VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                close_price DECIMAL(10,2),
                volume BIGINT,
                ltp DECIMAL(10,2),
                change_amount DECIMAL(10,2),
                change_percent DECIMAL(5,2),
                bid_price DECIMAL(10,2),
                ask_price DECIMAL(10,2),
                bid_qty INTEGER,
                ask_qty INTEGER,
                oi BIGINT,
                oi_change BIGINT,
                data_source VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(15,4),
                metric_data JSONB,
                category VARCHAR(50),
                timestamp TIMESTAMP DEFAULT NOW()
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(user_id),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(100),
                old_values JSONB,
                new_values JSONB,
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        
        # Create indexes for performance
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_symbol ON trading_signals(strategy_name, symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_status_generated ON trading_signals(status, generated_at);",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON orders(symbol, status);",
            "CREATE INDEX IF NOT EXISTS idx_positions_user_status ON positions(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol_status ON positions(symbol, status);",
            "CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, entry_time);",
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);"
        ]
        
        async with self.db_pool.acquire() as conn:
            for query in schema_queries + index_queries:
                await conn.execute(query)
        
        logger.info("PostgreSQL schema created successfully")
    
    async def _create_sqlite_schema(self):
        """Create SQLite schema"""
        schema_queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                phone_number TEXT,
                account_type TEXT DEFAULT 'INDIVIDUAL',
                capital_allocation REAL DEFAULT 0.00,
                risk_percentage REAL DEFAULT 1.00,
                max_positions INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trading_signals (
                signal_id TEXT PRIMARY KEY,
                user_id TEXT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quality_score INTEGER CHECK (quality_score >= 1 AND quality_score <= 10),
                confidence_level REAL,
                entry_price REAL,
                stop_loss_price REAL,
                target_price REAL,
                stop_loss_percent REAL,
                target_percent REAL,
                timeframe TEXT,
                entry_reason TEXT,
                technical_indicators TEXT,
                status TEXT DEFAULT 'GENERATED',
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                executed_at TEXT,
                expired_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT,
                signal_id TEXT,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                filled_quantity INTEGER DEFAULT 0,
                remaining_quantity INTEGER,
                order_type TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL,
                average_fill_price REAL,
                broker_order_id TEXT,
                exchange TEXT,
                status TEXT DEFAULT 'PENDING',
                rejection_reason TEXT,
                strategy_name TEXT,
                order_tag TEXT,
                validity TEXT DEFAULT 'DAY',
                disclosed_quantity INTEGER DEFAULT 0,
                trigger_price REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                filled_at TEXT,
                cancelled_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (signal_id) REFERENCES trading_signals (signal_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                user_id TEXT,
                order_id TEXT,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                average_entry_price REAL NOT NULL,
                total_investment REAL,
                current_price REAL DEFAULT 0.00,
                current_value REAL,
                unrealized_pnl REAL,
                pnl_percent REAL,
                realized_pnl REAL DEFAULT 0.00,
                brokerage REAL DEFAULT 0.00,
                taxes REAL DEFAULT 0.00,
                net_pnl REAL,
                status TEXT DEFAULT 'OPEN',
                strategy_name TEXT,
                entry_reason TEXT,
                exit_reason TEXT,
                stop_loss REAL,
                target REAL,
                entry_time TEXT DEFAULT CURRENT_TIMESTAMP,
                exit_time TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                position_id TEXT,
                user_id TEXT,
                symbol TEXT NOT NULL,
                entry_order_id TEXT,
                exit_order_id TEXT,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                gross_pnl REAL,
                brokerage REAL DEFAULT 0.00,
                taxes REAL DEFAULT 0.00,
                net_pnl REAL,
                holding_period TEXT,
                strategy_name TEXT,
                trade_type TEXT,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (position_id) REFERENCES positions (position_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS market_data (
                data_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                ltp REAL,
                change_amount REAL,
                change_percent REAL,
                bid_price REAL,
                ask_price REAL,
                bid_qty INTEGER,
                ask_qty INTEGER,
                oi INTEGER,
                oi_change INTEGER,
                data_source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                metric_id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_data TEXT,
                category TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            """
        ]
        
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_strategy_symbol ON trading_signals(strategy_name, symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_status_generated ON trading_signals(status, generated_at);",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_status ON orders(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON orders(symbol, status);",
            "CREATE INDEX IF NOT EXISTS idx_positions_user_status ON positions(user_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol_status ON positions(symbol, status);",
            "CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, entry_time);",
            "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp ON audit_logs(user_id, timestamp);"
        ]
        
        async with aiosqlite.connect(self.db_pool) as db:
            for query in schema_queries + index_queries:
                await db.execute(query)
            await db.commit()
        
        logger.info("SQLite schema created successfully")
    
    async def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set value in Redis cache"""
        if self.redis_client:
            try:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                await asyncio.to_thread(self.redis_client.setex, key, ttl, value)
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if self.redis_client:
            try:
                value = await asyncio.to_thread(self.redis_client.get, key)
                if value:
                    try:
                        return json.loads(value)
                    except:
                        return value
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        return None
    
    async def close(self):
        """Close database connections"""
        if self.db_type == 'postgresql' and self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await asyncio.to_thread(self.redis_client.close)
        logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()