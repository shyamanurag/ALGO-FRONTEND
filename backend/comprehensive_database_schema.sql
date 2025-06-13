-- ===================================================================
-- COMPREHENSIVE DATABASE SCHEMA FOR ELITE TRADING PLATFORM
-- Supports complete order and trade flow with real data
-- ===================================================================

-- ===================================================================
-- 1. USERS & AUTHENTICATION
-- ===================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR,
    phone VARCHAR,
    status VARCHAR DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'CLOSED')),
    risk_level VARCHAR DEFAULT 'MODERATE' CHECK (risk_level IN ('LOW', 'MODERATE', 'HIGH', 'EXTREME')),
    
    -- Trading Config
    paper_trading BOOLEAN DEFAULT TRUE,
    autonomous_trading BOOLEAN DEFAULT FALSE,
    max_daily_loss FLOAT DEFAULT 50000.0,
    max_position_size FLOAT DEFAULT 100000.0,
    max_positions INTEGER DEFAULT 10,
    
    -- Broker Integration
    zerodha_user_id VARCHAR,
    zerodha_api_key VARCHAR,
    zerodha_access_token VARCHAR,
    broker_connected BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ===================================================================
-- 2. CAPITAL & RISK MANAGEMENT
-- ===================================================================

CREATE TABLE IF NOT EXISTS user_capital (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    
    -- Capital Tracking
    opening_capital FLOAT NOT NULL DEFAULT 0.0,
    current_capital FLOAT NOT NULL DEFAULT 0.0,
    available_capital FLOAT NOT NULL DEFAULT 0.0,
    blocked_capital FLOAT NOT NULL DEFAULT 0.0,
    
    -- P&L Tracking
    daily_pnl FLOAT DEFAULT 0.0,
    daily_pnl_percent FLOAT DEFAULT 0.0,
    total_pnl FLOAT DEFAULT 0.0,
    total_pnl_percent FLOAT DEFAULT 0.0,
    
    -- Drawdown Tracking
    max_drawdown FLOAT DEFAULT 0.0,
    current_drawdown FLOAT DEFAULT 0.0,
    peak_capital FLOAT DEFAULT 0.0,
    
    -- Risk Metrics
    risk_score FLOAT DEFAULT 0.0,
    hard_stop_triggered BOOLEAN DEFAULT FALSE,
    hard_stop_reason VARCHAR,
    hard_stop_at TIMESTAMP,
    
    -- Timestamps
    updated_at TIMESTAMP DEFAULT NOW(),
    trade_date DATE DEFAULT CURRENT_DATE,
    
    UNIQUE(user_id, trade_date)
);

-- ===================================================================
-- 3. MARKET DATA (Real-time & Historical)
-- ===================================================================

CREATE TABLE IF NOT EXISTS market_data_live (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    exchange VARCHAR DEFAULT 'NFO',
    
    -- Price Data
    ltp FLOAT NOT NULL,
    bid FLOAT,
    ask FLOAT,
    bid_size INTEGER DEFAULT 0,
    ask_size INTEGER DEFAULT 0,
    
    -- OHLC Data
    open_price FLOAT,
    high_price FLOAT,
    low_price FLOAT,
    close_price FLOAT,
    prev_close FLOAT,
    
    -- Volume & OI
    volume BIGINT DEFAULT 0,
    oi BIGINT DEFAULT 0,
    oi_change INTEGER DEFAULT 0,
    
    -- Derived Metrics
    change_percent FLOAT DEFAULT 0.0,
    volatility FLOAT DEFAULT 0.0,
    vwap FLOAT,
    
    -- Timestamps
    timestamp TIMESTAMP NOT NULL,
    market_timestamp TIMESTAMP,
    
    -- Indexing for performance
    INDEX idx_market_data_symbol_time (symbol, timestamp DESC),
    INDEX idx_market_data_timestamp (timestamp DESC)
);

CREATE TABLE IF NOT EXISTS market_data_historical (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    timeframe VARCHAR NOT NULL, -- '1min', '5min', '15min', '1hour', '1day'
    
    -- OHLCV Data
    open_price FLOAT NOT NULL,
    high_price FLOAT NOT NULL,
    low_price FLOAT NOT NULL,
    close_price FLOAT NOT NULL,
    volume BIGINT NOT NULL,
    oi BIGINT DEFAULT 0,
    
    -- Derived Data
    vwap FLOAT,
    typical_price FLOAT,
    
    -- Timestamps
    candle_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(symbol, timeframe, candle_time),
    INDEX idx_historical_symbol_timeframe_time (symbol, timeframe, candle_time DESC)
);

-- ===================================================================
-- 4. SIGNALS GENERATION
-- ===================================================================

CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id VARCHAR PRIMARY KEY,
    strategy_name VARCHAR NOT NULL,
    
    -- Signal Details
    symbol VARCHAR NOT NULL,
    option_type VARCHAR CHECK (option_type IN ('CE', 'PE', 'FUTURES')),
    strike FLOAT,
    action VARCHAR NOT NULL CHECK (action IN ('BUY', 'SELL')),
    
    -- Signal Quality
    quality_score FLOAT NOT NULL CHECK (quality_score >= 0 AND quality_score <= 10),
    confidence_level FLOAT NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
    
    -- Trade Parameters
    quantity INTEGER NOT NULL,
    entry_price FLOAT,
    stop_loss_percent FLOAT,
    target_percent FLOAT,
    
    -- Signal Lifecycle
    status VARCHAR DEFAULT 'GENERATED' CHECK (status IN ('GENERATED', 'VALIDATED', 'EXECUTED', 'EXPIRED', 'CANCELLED')),
    valid_until TIMESTAMP,
    time_stop TIMESTAMP,
    
    -- Risk Assessment
    risk_score FLOAT DEFAULT 0.0,
    max_loss FLOAT,
    max_profit FLOAT,
    risk_reward_ratio FLOAT,
    
    -- Strategy Context
    setup_type VARCHAR,
    market_regime VARCHAR,
    volatility_regime VARCHAR,
    confluence_factors JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_signals_strategy_time (strategy_name, generated_at DESC),
    INDEX idx_signals_symbol_time (symbol, generated_at DESC),
    INDEX idx_signals_quality (quality_score DESC, generated_at DESC)
);

-- ===================================================================
-- 5. ORDER MANAGEMENT
-- ===================================================================

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    signal_id VARCHAR REFERENCES trading_signals(signal_id),
    
    -- Order Identification
    broker_order_id VARCHAR, -- Actual broker order ID
    parent_order_id VARCHAR REFERENCES orders(order_id),
    
    -- Order Details
    symbol VARCHAR NOT NULL,
    exchange VARCHAR DEFAULT 'NFO',
    option_type VARCHAR CHECK (option_type IN ('CE', 'PE', 'FUTURES')),
    strike FLOAT,
    expiry_date DATE,
    
    -- Order Parameters
    quantity INTEGER NOT NULL,
    order_type VARCHAR NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'SL', 'SL-M', 'BRACKET')),
    side VARCHAR NOT NULL CHECK (side IN ('BUY', 'SELL')),
    price FLOAT,
    trigger_price FLOAT,
    disclosed_quantity INTEGER DEFAULT 0,
    
    -- Execution Strategy
    execution_strategy VARCHAR DEFAULT 'IMMEDIATE' CHECK (execution_strategy IN ('IMMEDIATE', 'TWAP', 'VWAP', 'ICEBERG', 'SMART')),
    time_in_force VARCHAR DEFAULT 'DAY' CHECK (time_in_force IN ('DAY', 'GTC', 'IOC', 'FOK')),
    
    -- Order State & Status
    state VARCHAR DEFAULT 'CREATED' CHECK (state IN ('CREATED', 'QUEUED', 'SENT', 'PLACED', 'FILLED', 'CANCELLED', 'REJECTED')),
    status VARCHAR DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PLACED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED')),
    
    -- Fill Information
    filled_quantity INTEGER DEFAULT 0,
    remaining_quantity INTEGER DEFAULT 0,
    average_price FLOAT DEFAULT 0.0,
    
    -- Costs & Fees
    brokerage FLOAT DEFAULT 0.0,
    taxes FLOAT DEFAULT 0.0,
    total_charges FLOAT DEFAULT 0.0,
    
    -- Execution Quality Metrics
    slippage FLOAT DEFAULT 0.0,
    market_impact FLOAT DEFAULT 0.0,
    execution_time_ms INTEGER DEFAULT 0,
    
    -- Strategy Context
    strategy_name VARCHAR,
    position_id VARCHAR,
    trade_reason VARCHAR,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    queued_at TIMESTAMP,
    sent_at TIMESTAMP,
    placed_at TIMESTAMP,
    filled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_orders_user_time (user_id, created_at DESC),
    INDEX idx_orders_status_time (status, created_at DESC),
    INDEX idx_orders_broker_id (broker_order_id),
    INDEX idx_orders_signal (signal_id)
);

-- ===================================================================
-- 6. POSITION TRACKING
-- ===================================================================

CREATE TABLE IF NOT EXISTS positions (
    position_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    
    -- Position Details
    symbol VARCHAR NOT NULL,
    exchange VARCHAR DEFAULT 'NFO',
    option_type VARCHAR CHECK (option_type IN ('CE', 'PE', 'FUTURES')),
    strike FLOAT,
    expiry_date DATE,
    
    -- Position Size
    quantity INTEGER NOT NULL,
    average_entry_price FLOAT NOT NULL,
    total_investment FLOAT NOT NULL,
    
    -- Current Market Data
    current_price FLOAT DEFAULT 0.0,
    current_value FLOAT DEFAULT 0.0,
    
    -- P&L Tracking
    unrealized_pnl FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    pnl_percent FLOAT DEFAULT 0.0,
    
    -- P&L Extremes
    max_profit FLOAT DEFAULT 0.0,
    max_loss FLOAT DEFAULT 0.0,
    max_profit_percent FLOAT DEFAULT 0.0,
    max_loss_percent FLOAT DEFAULT 0.0,
    
    -- Risk Management
    stop_loss FLOAT,
    target FLOAT,
    trailing_stop FLOAT,
    
    -- Position Lifecycle
    status VARCHAR DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'PARTIALLY_CLOSED', 'CLOSED')),
    position_type VARCHAR DEFAULT 'LONG' CHECK (position_type IN ('LONG', 'SHORT')),
    
    -- Strategy Context
    strategy_name VARCHAR,
    signal_id VARCHAR REFERENCES trading_signals(signal_id),
    entry_reason VARCHAR,
    exit_reason VARCHAR,
    
    -- Timestamps
    entry_time TIMESTAMP DEFAULT NOW(),
    exit_time TIMESTAMP,
    hold_duration INTERVAL,
    
    -- Associated Orders
    entry_orders JSONB DEFAULT '[]'::jsonb,  -- Array of order IDs
    exit_orders JSONB DEFAULT '[]'::jsonb,   -- Array of order IDs
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_positions_user_status (user_id, status),
    INDEX idx_positions_symbol_time (symbol, entry_time DESC),
    INDEX idx_positions_strategy (strategy_name, entry_time DESC)
);

-- ===================================================================
-- 7. TRADE EXECUTION LOG
-- ===================================================================

CREATE TABLE IF NOT EXISTS trade_executions (
    execution_id VARCHAR PRIMARY KEY,
    order_id VARCHAR NOT NULL REFERENCES orders(order_id),
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    
    -- Trade Details
    symbol VARCHAR NOT NULL,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL,
    side VARCHAR NOT NULL CHECK (side IN ('BUY', 'SELL')),
    
    -- Trade Value
    trade_value FLOAT NOT NULL,
    brokerage FLOAT DEFAULT 0.0,
    taxes FLOAT DEFAULT 0.0,
    net_value FLOAT NOT NULL,
    
    -- Execution Details
    exchange VARCHAR,
    broker_trade_id VARCHAR,
    execution_timestamp TIMESTAMP NOT NULL,
    
    -- Quality Metrics
    price_improvement FLOAT DEFAULT 0.0,
    execution_delay_ms INTEGER DEFAULT 0,
    
    -- Context
    market_price_at_execution FLOAT,
    bid_at_execution FLOAT,
    ask_at_execution FLOAT,
    spread_at_execution FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_executions_order (order_id),
    INDEX idx_executions_user_time (user_id, execution_timestamp DESC),
    INDEX idx_executions_symbol_time (symbol, execution_timestamp DESC)
);

-- ===================================================================
-- 8. PERFORMANCE & ANALYTICS
-- ===================================================================

CREATE TABLE IF NOT EXISTS daily_performance (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    trade_date DATE NOT NULL,
    
    -- Daily Trading Stats
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- P&L Stats
    gross_pnl FLOAT DEFAULT 0.0,
    net_pnl FLOAT DEFAULT 0.0,
    brokerage_paid FLOAT DEFAULT 0.0,
    taxes_paid FLOAT DEFAULT 0.0,
    
    -- Performance Metrics
    win_rate FLOAT DEFAULT 0.0,
    average_win FLOAT DEFAULT 0.0,
    average_loss FLOAT DEFAULT 0.0,
    profit_factor FLOAT DEFAULT 0.0,
    largest_win FLOAT DEFAULT 0.0,
    largest_loss FLOAT DEFAULT 0.0,
    
    -- Risk Metrics
    max_drawdown_intraday FLOAT DEFAULT 0.0,
    max_open_positions INTEGER DEFAULT 0,
    total_volume_traded FLOAT DEFAULT 0.0,
    
    -- Strategy Performance
    strategy_performance JSONB DEFAULT '{}'::jsonb,
    
    -- Capital Movement
    starting_capital FLOAT DEFAULT 0.0,
    ending_capital FLOAT DEFAULT 0.0,
    capital_utilization FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, trade_date),
    INDEX idx_daily_perf_user_date (user_id, trade_date DESC)
);

-- ===================================================================
-- 9. RISK MANAGEMENT & LIMITS
-- ===================================================================

CREATE TABLE IF NOT EXISTS risk_limits (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    
    -- Position Limits
    max_position_size FLOAT DEFAULT 100000.0,
    max_positions INTEGER DEFAULT 10,
    max_positions_per_symbol INTEGER DEFAULT 3,
    
    -- Loss Limits
    daily_stop_loss FLOAT DEFAULT 50000.0,
    total_stop_loss FLOAT DEFAULT 200000.0,
    max_drawdown_limit FLOAT DEFAULT 0.15, -- 15%
    
    -- Exposure Limits
    max_portfolio_exposure FLOAT DEFAULT 0.8, -- 80% of capital
    max_single_position_exposure FLOAT DEFAULT 0.2, -- 20% of capital
    max_sector_exposure FLOAT DEFAULT 0.4, -- 40% of capital
    
    -- Risk Parameters
    var_limit FLOAT DEFAULT 50000.0, -- Value at Risk
    correlation_limit FLOAT DEFAULT 0.7,
    concentration_limit FLOAT DEFAULT 0.3,
    
    -- Market Regime Limits
    high_vix_limit FLOAT DEFAULT 25.0,
    extreme_vix_limit FLOAT DEFAULT 35.0,
    reduce_size_above_vix BOOLEAN DEFAULT TRUE,
    
    -- Time-based Limits
    no_trading_after TIME DEFAULT '15:00:00',
    square_off_time TIME DEFAULT '15:15:00',
    weekend_trading BOOLEAN DEFAULT FALSE,
    
    -- Validation
    enforce_limits BOOLEAN DEFAULT TRUE,
    override_allowed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_risk_limits_user (user_id)
);

-- ===================================================================
-- 10. STRATEGY MANAGEMENT
-- ===================================================================

CREATE TABLE IF NOT EXISTS strategy_configs (
    strategy_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    
    -- Strategy Details
    strategy_name VARCHAR NOT NULL,
    strategy_type VARCHAR NOT NULL,
    description TEXT,
    
    -- Strategy Status
    enabled BOOLEAN DEFAULT TRUE,
    auto_execute BOOLEAN DEFAULT FALSE,
    
    -- Allocation & Sizing
    allocation_percent FLOAT DEFAULT 0.2, -- 20% of capital
    max_position_size FLOAT DEFAULT 50000.0,
    position_sizing_method VARCHAR DEFAULT 'FIXED' CHECK (position_sizing_method IN ('FIXED', 'PERCENT_CAPITAL', 'VOLATILITY_ADJUSTED', 'RISK_PARITY')),
    
    -- Risk Parameters
    max_daily_trades INTEGER DEFAULT 10,
    cooldown_minutes INTEGER DEFAULT 5,
    min_quality_score FLOAT DEFAULT 7.0,
    
    -- Strategy Parameters
    parameters JSONB DEFAULT '{}'::jsonb,
    
    -- Performance Tracking
    total_signals INTEGER DEFAULT 0,
    executed_signals INTEGER DEFAULT 0,
    winning_signals INTEGER DEFAULT 0,
    total_pnl FLOAT DEFAULT 0.0,
    win_rate FLOAT DEFAULT 0.0,
    
    -- Risk Metrics
    max_drawdown FLOAT DEFAULT 0.0,
    sharpe_ratio FLOAT DEFAULT 0.0,
    sortino_ratio FLOAT DEFAULT 0.0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_executed TIMESTAMP,
    
    INDEX idx_strategy_configs_user (user_id),
    INDEX idx_strategy_configs_name (strategy_name)
);

-- ===================================================================
-- 11. SYSTEM MONITORING
-- ===================================================================

CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    
    -- Component Health
    component_name VARCHAR NOT NULL,
    status VARCHAR NOT NULL CHECK (status IN ('HEALTHY', 'DEGRADED', 'DOWN', 'MAINTENANCE')),
    
    -- Metrics
    response_time_ms INTEGER DEFAULT 0,
    cpu_usage FLOAT DEFAULT 0.0,
    memory_usage FLOAT DEFAULT 0.0,
    error_rate FLOAT DEFAULT 0.0,
    
    -- Details
    message TEXT,
    error_details JSONB,
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_system_health_component_time (component_name, timestamp DESC),
    INDEX idx_system_health_status_time (status, timestamp DESC)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    
    -- Event Details
    event_type VARCHAR NOT NULL,
    component VARCHAR NOT NULL,
    user_id VARCHAR,
    
    -- Event Data
    event_description TEXT,
    event_data JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR,
    
    -- Severity
    severity VARCHAR DEFAULT 'INFO' CHECK (severity IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_audit_log_type_time (event_type, timestamp DESC),
    INDEX idx_audit_log_user_time (user_id, timestamp DESC),
    INDEX idx_audit_log_severity_time (severity, timestamp DESC)
);

-- ===================================================================
-- 12. ELITE RECOMMENDATIONS
-- ===================================================================

CREATE TABLE IF NOT EXISTS elite_recommendations (
    recommendation_id VARCHAR PRIMARY KEY,
    
    -- Recommendation Details
    symbol VARCHAR NOT NULL,
    strategy VARCHAR NOT NULL,
    direction VARCHAR NOT NULL CHECK (direction IN ('BULLISH', 'BEARISH')),
    
    -- Price Levels
    entry_price FLOAT NOT NULL,
    stop_loss FLOAT NOT NULL,
    primary_target FLOAT NOT NULL,
    secondary_target FLOAT,
    tertiary_target FLOAT,
    
    -- Quality Metrics
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 9.5 AND confidence_score <= 10.0),
    confluence_count INTEGER DEFAULT 0,
    confluence_factors JSONB DEFAULT '[]'::jsonb,
    
    -- Trade Parameters
    timeframe VARCHAR NOT NULL,
    hold_duration_estimate INTERVAL,
    risk_reward_ratio FLOAT,
    
    -- Risk Metrics
    max_risk_percent FLOAT DEFAULT 2.0,
    position_sizing JSONB DEFAULT '{}'::jsonb,
    
    -- Validity
    valid_until TIMESTAMP NOT NULL,
    scan_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Status Tracking
    status VARCHAR DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'EXECUTED', 'EXPIRED', 'CANCELLED')),
    execution_details JSONB,
    
    -- Entry Conditions
    entry_conditions JSONB DEFAULT '[]'::jsonb,
    market_conditions JSONB DEFAULT '{}'::jsonb,
    
    -- Performance (if executed)
    actual_entry_price FLOAT,
    actual_exit_price FLOAT,
    actual_pnl FLOAT,
    execution_quality FLOAT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_elite_recs_symbol_time (symbol, scan_timestamp DESC),
    INDEX idx_elite_recs_confidence (confidence_score DESC, scan_timestamp DESC),
    INDEX idx_elite_recs_status_time (status, scan_timestamp DESC)
);

-- ===================================================================
-- VIEWS FOR COMMON QUERIES
-- ===================================================================

-- Active Positions Summary
CREATE OR REPLACE VIEW active_positions_summary AS
SELECT 
    p.user_id,
    COUNT(*) as total_positions,
    SUM(p.total_investment) as total_investment,
    SUM(p.current_value) as current_value,
    SUM(p.unrealized_pnl) as total_unrealized_pnl,
    AVG(p.pnl_percent) as avg_pnl_percent,
    MAX(p.max_profit) as best_position,
    MIN(p.max_loss) as worst_position
FROM positions p
WHERE p.status = 'OPEN'
GROUP BY p.user_id;

-- Daily Trading Summary
CREATE OR REPLACE VIEW daily_trading_summary AS
SELECT 
    o.user_id,
    DATE(o.created_at) as trade_date,
    COUNT(DISTINCT o.order_id) as total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'FILLED' THEN o.order_id END) as filled_orders,
    SUM(CASE WHEN o.status = 'FILLED' THEN o.quantity * o.average_price ELSE 0 END) as total_volume,
    COUNT(DISTINCT p.position_id) as positions_opened,
    SUM(CASE WHEN p.status = 'CLOSED' THEN p.realized_pnl ELSE 0 END) as realized_pnl
FROM orders o
LEFT JOIN positions p ON o.position_id = p.position_id
GROUP BY o.user_id, DATE(o.created_at);

-- Strategy Performance Summary
CREATE OR REPLACE VIEW strategy_performance_summary AS
SELECT 
    s.strategy_name,
    COUNT(*) as total_signals,
    COUNT(CASE WHEN s.status = 'EXECUTED' THEN 1 END) as executed_signals,
    AVG(s.quality_score) as avg_quality_score,
    COUNT(DISTINCT p.position_id) as positions_created,
    SUM(CASE WHEN p.status = 'CLOSED' AND p.realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN p.status = 'CLOSED' THEN p.realized_pnl ELSE 0 END) as total_pnl,
    AVG(CASE WHEN p.status = 'CLOSED' THEN p.pnl_percent ELSE NULL END) as avg_pnl_percent
FROM trading_signals s
LEFT JOIN positions p ON s.signal_id = p.signal_id
GROUP BY s.strategy_name;

-- ===================================================================
-- INDEXES FOR PERFORMANCE
-- ===================================================================

-- Critical performance indexes
CREATE INDEX IF NOT EXISTS idx_market_data_live_symbol_timestamp ON market_data_live(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orders_user_status_time ON orders(user_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_user_status_symbol ON positions(user_id, status, symbol);
CREATE INDEX IF NOT EXISTS idx_signals_strategy_quality_time ON trading_signals(strategy_name, quality_score DESC, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_user_symbol_time ON trade_executions(user_id, symbol, execution_timestamp DESC);

-- ===================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ===================================================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_capital_updated_at BEFORE UPDATE ON user_capital FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_daily_performance_updated_at BEFORE UPDATE ON daily_performance FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_strategy_configs_updated_at BEFORE UPDATE ON strategy_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================================
-- END OF COMPREHENSIVE SCHEMA
-- ===================================================================
