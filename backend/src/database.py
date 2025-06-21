import logging
import asyncpg
import aiosqlite
import redis.asyncio as redis
from typing import Any, Optional, Tuple, List

# Import AppSettings for type hinting and settings access
# from .config import AppSettings # This would be used if settings were passed to every function
# Import app_state for temporary global access to db_pool
from .app_state import app_state # Temporary for transition

logger = logging.getLogger(__name__)

# Store references to the database pool and Redis client at the module level,
# but they will be initialized by init_database and ideally accessed via app_state.
# These module-level globals are for internal use within this module if direct app_state import is slow/problematic
# or as a fallback during transition. The primary way should be via app_state.clients.
_db_pool: Optional[Any] = None
_redis_client: Optional[redis.Redis] = None

async def init_database(settings: Any) -> Tuple[Optional[Any], Optional[redis.Redis]]:
    """
    Initializes the database connection pool (PostgreSQL or SQLite) and Redis client.
    Uses settings from the provided AppSettings instance.
    Returns a tuple of (db_pool, redis_client).
    """
    global _db_pool, _redis_client # Allow modification of module-level placeholders

    db_url = settings.DATABASE_URL
    redis_url = settings.REDIS_URL

    db_pool_instance: Optional[Any] = None
    redis_client_instance: Optional[redis.Redis] = None

    logger.info(f"Initializing database with URL: {'present' if db_url else 'not present'}")
    if db_url:
        try:
            if db_url.startswith("sqlite"): # Assume aiosqlite for sqlite
                # For aiosqlite, the "pool" is typically just the connection path or a Connection object.
                # We'll use the path and connect on each query, or maintain a single connection if simple.
                # For this structure, let's assume db_url is the path like "sqlite+aiosqlite:///./test_db.sqlite3"
                sqlite_path = db_url.split("///")[-1]
                # Test connection
                async with aiosqlite.connect(sqlite_path) as db_conn:
                    await db_conn.execute("SELECT 1")
                db_pool_instance = sqlite_path # Store path as "pool" for SQLite
                logger.info(f"SQLite database initialized at {sqlite_path}")
                # Schema creation should be called after this in startup
            elif db_url.startswith("postgresql"): # Assume asyncpg for postgresql
                db_pool_instance = await asyncpg.create_pool(db_url)
                if db_pool_instance:
                    logger.info("PostgreSQL connection pool established.")
                else:
                    logger.error("Failed to create PostgreSQL connection pool.")
            else:
                logger.error(f"Unsupported database URL scheme: {db_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            db_pool_instance = None # Ensure it's None on error
    else:
        logger.warning("DATABASE_URL not provided. Database not initialized.")

    logger.info(f"Initializing Redis with URL: {'present' if redis_url else 'not present'}")
    if redis_url:
        try:
            redis_client_instance = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await redis_client_instance.ping()
            logger.info("Redis client connected successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            redis_client_instance = None # Ensure it's None on error
    else:
        logger.warning("REDIS_URL not provided. Redis client not initialized.")

    _db_pool = db_pool_instance # Update module-level variable
    _redis_client = redis_client_instance # Update module-level variable
    return db_pool_instance, redis_client_instance

async def create_database_schema(db_conn_or_path: Any):
    """
    Creates the necessary database schema if it doesn't exist.
    Accepts either a connection/pool object (for asyncpg) or a path string (for SQLite).
    """
    if not db_conn_or_path:
        logger.error("Cannot create schema: database connection/path not provided.")
        return

    # Define schema queries (idempotent CREATE TABLE IF NOT EXISTS)
    # These should match the table structures used throughout the application.
    # This is a simplified version; complex migrations might need Alembic or similar.
    schema_queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            full_name TEXT,
            password_hash TEXT, -- Should be securely hashed
            paper_trading BOOLEAN DEFAULT TRUE,
            autonomous_trading BOOLEAN DEFAULT FALSE,
            max_daily_loss REAL, -- Max loss percentage or absolute value
            status TEXT DEFAULT 'active', -- e.g., active, pending_verification, suspended, terminated
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS user_credentials (
            user_id TEXT PRIMARY KEY REFERENCES users(user_id),
            zerodha_user_id TEXT UNIQUE,
            zerodha_password_encrypted TEXT, -- Encrypted
            totp_secret_encrypted TEXT,      -- Encrypted
            access_token TEXT,               -- Stored temporarily if needed, ideally managed by client
            refresh_token TEXT,
            login_status TEXT, -- e.g., logged_in, logged_out, error
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS auth_tokens ( -- For storing API access tokens if needed by app itself
            provider TEXT PRIMARY KEY, -- e.g., 'zerodha', 'truedata_api'
            user_id TEXT, -- Optional, if token is user-specific
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            token_type TEXT DEFAULT 'bearer',
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trading_signals (
            signal_id TEXT PRIMARY KEY,
            strategy_name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL, -- BUY, SELL, SHORT, COVER
            price REAL, -- Entry price for limit orders
            quantity INTEGER,
            order_type TEXT DEFAULT 'MARKET', -- MARKET, LIMIT
            stop_loss REAL,
            take_profit REAL,
            quality_score REAL, -- Confidence or quality of the signal
            status TEXT DEFAULT 'GENERATED', -- e.g., GENERATED, VALIDATED, EXECUTED, CANCELLED, FAILED
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            validated_at TIMESTAMP,
            executed_at TIMESTAMP,
            metadata TEXT -- JSON blob for extra info (e.g., indicators, setup_type, market_regime)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, -- Can be broker order_id or internal UUID
            user_id TEXT REFERENCES users(user_id),
            signal_id TEXT REFERENCES trading_signals(signal_id), -- Optional link to a signal
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            filled_quantity INTEGER DEFAULT 0,
            order_type TEXT NOT NULL, -- MARKET, LIMIT, SL, SL-M
            side TEXT NOT NULL, -- BUY, SELL
            price REAL, -- Limit price or trigger price for SL
            average_price REAL, -- Average execution price
            status TEXT NOT NULL, -- e.g., PENDING, OPEN, FILLED, CANCELLED, REJECTED, FAILED
            strategy_name TEXT, -- Strategy that placed this order
            trade_reason TEXT, -- e.g., Entry, Exit, SL Hit, TP Hit, Manual
            broker_order_id TEXT UNIQUE,
            exchange_order_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            filled_at TIMESTAMP,
            metadata TEXT -- JSON blob for broker messages, error details, tags
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS positions (
            position_id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES users(user_id),
            symbol TEXT NOT NULL,
            quantity INTEGER NOT NULL, -- Positive for long, negative for short
            average_entry_price REAL NOT NULL,
            total_investment REAL, -- Cost basis
            current_price REAL, -- Last traded price, updated frequently
            current_value REAL, -- quantity * current_price
            unrealized_pnl REAL DEFAULT 0,
            realized_pnl REAL DEFAULT 0,
            status TEXT DEFAULT 'OPEN', -- OPEN, CLOSED
            strategy_name TEXT,
            entry_reason TEXT,
            exit_reason TEXT,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP,
            metadata TEXT -- JSON blob for notes, related order_ids
        );
        """,
         """
        CREATE TABLE IF NOT EXISTS elite_recommendations (
            recommendation_id TEXT PRIMARY KEY, -- Changed from id to recommendation_id for clarity
            symbol TEXT NOT NULL,
            strategy TEXT, -- Name of the elite strategy generating this
            direction TEXT, -- e.g., LONG, SHORT, Bullish, Bearish
            entry_price REAL,
            stop_loss REAL,
            primary_target REAL,
            secondary_target REAL,
            confidence_score REAL, -- 0.0 to 1.0
            timeframe TEXT, -- e.g., 15MIN, 1H, 1D
            scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            valid_until TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE', -- ACTIVE, ACHIEVED_TP1, ACHIEVED_TP2, STOPPED_OUT, EXPIRED, CANCELLED
            notes TEXT,
            metadata TEXT -- JSON for additional details like chart patterns, indicator values
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS system_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Using AUTOINCREMENT for SQLite compatibility
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tags TEXT -- JSON for key-value tags
        );
        """
        # Add more tables as needed: market_data_historical, strategy_performance_logs, etc.
    ]

    try:
        if isinstance(db_conn_or_path, str) and "sqlite" in db_conn_or_path: # SQLite path
            async with aiosqlite.connect(db_conn_or_path) as db:
                for query in schema_queries:
                    await db.execute(query)
                await db.commit()
            logger.info("SQLite schema created/verified successfully.")
        elif hasattr(db_conn_or_path, 'execute'): # Assumed asyncpg pool or connection
            # For asyncpg, it's better to acquire a connection to run multiple statements
            # If db_conn_or_path is a pool:
            if hasattr(db_conn_or_path, 'acquire'):
                async with db_conn_or_path.acquire() as conn:
                    async with conn.transaction(): # Group schema changes in a transaction
                        for query in schema_queries:
                            await conn.execute(query)
            else: # Assuming it's already a connection
                async with db_conn_or_path.transaction():
                    for query in schema_queries:
                        await db_conn_or_path.execute(query)
            logger.info("PostgreSQL schema created/verified successfully.")
        else:
            logger.error(f"Unsupported database connection type for schema creation: {type(db_conn_or_path)}")
    except Exception as e:
        logger.error(f"Error creating database schema: {e}", exc_info=True)
        raise # Re-raise after logging if schema creation is critical

async def execute_db_query(query: str, *params, db_conn_or_path: Optional[Any] = None) -> Optional[List[Any]]:
    """
    Executes a database query that doesn't necessarily return rows (e.g., INSERT, UPDATE, DELETE).
    Can accept an active connection/pool or use the global app_state pool.
    Returns list of rows for SELECT, or rowcount/status for other operations if supported by driver.
    For simplicity, make it always return Optional[List[Any]] for now.
    """
    conn_to_use = db_conn_or_path or app_state.clients.db_pool # Use passed one, fallback to app_state

    if not conn_to_use:
        logger.error("Database connection/pool not available for query execution.")
        return None # Or raise an exception

    try:
        if isinstance(conn_to_use, str): # SQLite path
            async with aiosqlite.connect(conn_to_use) as db:
                db.row_factory = aiosqlite.Row  # This makes rows dict-like
                cursor = await db.execute(query, params)
                # For SELECT, fetch rows. For INSERT/UPDATE/DELETE, rowcount might be useful.
                if query.strip().upper().startswith("SELECT"):
                    rows = await cursor.fetchall()
                    await cursor.close()
                    return rows
                else:
                    await db.commit()
                    await cursor.close()
                    return [{"rowcount": cursor.rowcount}] # Return rowcount for non-SELECT
        elif hasattr(conn_to_use, 'execute'): # Assumed asyncpg pool or connection
            # For asyncpg, pool.execute() is fine for simple queries.
            # For pool.fetch() or if conn_to_use is a Connection object:
            if query.strip().upper().startswith("SELECT"):
                return await conn_to_use.fetch(query, *params)
            else: # INSERT, UPDATE, DELETE
                status = await conn_to_use.execute(query, *params)
                # status for asyncpg execute is like 'INSERT 0 1'
                # We can parse rowcount from it if needed, or just return a success indicator
                return [{"status": status}]
        else:
            logger.error(f"Unsupported database connection type for query: {type(conn_to_use)}")
            return None
    except Exception as e:
        log_params = params
        if "auth_tokens" in query.lower() and params:
            # Mask sensitive data for auth_tokens table queries
            # Assuming access_token is the 3rd param (idx 2) for INSERT/UPDATE
            # and other potentially sensitive params.
            try:
                temp_params = list(params)
                if "access_token" in query.lower() and len(temp_params) > 2 and isinstance(temp_params[2], str): # access_token
                    temp_params[2] = f"***REDACTED_TOKEN_LEN_{len(temp_params[2])}***"
                if "refresh_token" in query.lower() and len(temp_params) > 3 and isinstance(temp_params[3], str): # refresh_token
                    temp_params[3] = f"***REDACTED_TOKEN_LEN_{len(temp_params[3])}***"
                log_params = tuple(temp_params)
            except Exception as log_mask_err:
                logger.warning(f"Error masking params for logging: {log_mask_err}")
        logger.error(f"Database query error: {query} with params {log_params} - {e}", exc_info=True)
        # Depending on policy, you might want to raise specific DB exceptions here
        return None # Or re-raise e

async def fetch_one_db(query: str, *params, db_conn_or_path: Optional[Any] = None) -> Optional[Any]:
    """
    Executes a query expected to return a single row or None.
    Can accept an active connection/pool or use the global app_state pool.
    """
    conn_to_use = db_conn_or_path or app_state.clients.db_pool

    if not conn_to_use:
        logger.error("Database connection/pool not available for fetch_one.")
        return None

    try:
        if isinstance(conn_to_use, str): # SQLite path
            async with aiosqlite.connect(conn_to_use) as db:
                db.row_factory = aiosqlite.Row  # This makes rows dict-like
                cursor = await db.execute(query, params)
                row = await cursor.fetchone()
                await cursor.close()
                return row
        elif hasattr(conn_to_use, 'fetchrow'): # Assumed asyncpg pool or connection
            return await conn_to_use.fetchrow(query, *params)
        else:
            logger.error(f"Unsupported database connection type for fetch_one: {type(conn_to_use)}")
            return None
    except Exception as e:
        log_params = params
        if "auth_tokens" in query.lower() and params: # Potentially sensitive if querying by token value
            # Avoid logging parameters if the query might involve searching by token.
            # For auth_tokens, primary key is provider, so params are less likely to be the token itself for fetch_one.
            # This is a simpler check for fetch_one.
            pass # Keep params as is for fetch_one if table is auth_tokens, but be mindful.
                 # More specific redaction could be added if needed.

        logger.error(f"Database fetch_one error: {query} with params {log_params} - {e}", exc_info=True)
        return None

# Example utility to be called from server.py's startup to set up schema
async def setup_database_on_startup(settings_obj: Any, app_state_obj: Any):
    """
    Called from server startup. Initializes DB and creates schema.
    Stores pool/client in app_state.
    """
    logger.info("Executing setup_database_on_startup...")
    db_pool_instance, redis_client_instance = await init_database(settings_obj)

    app_state_obj.clients.db_pool = db_pool_instance
    app_state_obj.clients.redis_client = redis_client_instance
    app_state_obj.system_status.database_connected = bool(db_pool_instance)
    app_state_obj.system_status.redis_connected = bool(redis_client_instance)

    if app_state_obj.system_status.database_connected:
        # Pass the correct pool or path to schema creation
        conn_for_schema = app_state_obj.clients.db_pool
        await create_database_schema(conn_for_schema)
    else:
        logger.error("Database not connected, skipping schema creation.")

    logger.info(f"Database setup complete. DB Connected: {app_state_obj.system_status.database_connected}, Redis Connected: {app_state_obj.system_status.redis_connected}")

