-- ALGO-FRONTEND Trading Platform Database Initialization
-- PostgreSQL Database Schema for Production

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create trading_signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quality_score DECIMAL(3,1) NOT NULL CHECK (quality_score >= 0 AND quality_score <= 10),
    confidence_level DECIMAL(3,2) NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 1),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    entry_price DECIMAL(10,2) NOT NULL CHECK (entry_price > 0),
    stop_loss_percent DECIMAL(5,2) NOT NULL CHECK (stop_loss_percent >= 0),
    target_percent DECIMAL(5,2) NOT NULL CHECK (target_percent >= 0),
    status VARCHAR(20) DEFAULT 'GENERATED' CHECK (status IN ('GENERATED', 'ACTIVE', 'EXECUTED', 'CANCELLED', 'EXPIRED')),
    setup_type VARCHAR(50),
    market_regime VARCHAR(30),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_trading_signals_symbol (symbol),
    INDEX idx_trading_signals_strategy (strategy_name),
    INDEX idx_trading_signals_status (status),
    INDEX idx_trading_signals_generated_at (generated_at),
    INDEX idx_trading_signals_quality_score (quality_score)
);

-- Create elite_recommendations table
CREATE TABLE IF NOT EXISTS elite_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    entry_price DECIMAL(10,2) NOT NULL CHECK (entry_price > 0),
    stop_loss DECIMAL(10,2) NOT NULL CHECK (stop_loss > 0),
    primary_target DECIMAL(10,2) NOT NULL CHECK (primary_target > 0),
    confidence_score DECIMAL(3,1) DEFAULT 10.0 CHECK (confidence_score >= 9.5 AND confidence_score <= 10),
    timeframe VARCHAR(20) NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    scan_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'EXECUTED', 'EXPIRED', 'CANCELLED')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_elite_recommendations_symbol (symbol),
    INDEX idx_elite_recommendations_status (status),
    INDEX idx_elite_recommendations_valid_until (valid_until),
    INDEX idx_elite_recommendations_scan_timestamp (scan_timestamp)
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES trading_signals(signal_id),
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(20) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS')),
    price DECIMAL(10,2),
    status VARCHAR(30) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PLACED', 'FILLED', 'CANCELLED', 'REJECTED')),
    exchange_order_id VARCHAR(50),
    placed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    filled_at TIMESTAMP WITH TIME ZONE,
    filled_price DECIMAL(10,2),
    filled_quantity INTEGER,
    commission DECIMAL(8,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_orders_symbol (symbol),
    INDEX idx_orders_status (status),
    INDEX idx_orders_placed_at (placed_at),
    INDEX idx_orders_signal_id (signal_id)
);

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    position_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(20) NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL CHECK (entry_price > 0),
    current_price DECIMAL(10,2),
    unrealized_pnl DECIMAL(12,2) DEFAULT 0,
    realized_pnl DECIMAL(12,2) DEFAULT 0,
    stop_loss DECIMAL(10,2),
    target DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'PARTIALLY_CLOSED')),
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate positions
    UNIQUE(symbol, side, status),
    
    -- Indexes
    INDEX idx_positions_symbol (symbol),
    INDEX idx_positions_status (status),
    INDEX idx_positions_opened_at (opened_at)
);

-- Create trade_executions table
CREATE TABLE IF NOT EXISTS trade_executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(order_id),
    position_id UUID REFERENCES positions(position_id),
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(20) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    commission DECIMAL(8,2) DEFAULT 0,
    pnl DECIMAL(12,2) DEFAULT 0,
    execution_type VARCHAR(20) CHECK (execution_type IN ('ENTRY', 'EXIT', 'STOP_LOSS', 'TARGET')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_trade_executions_symbol (symbol),
    INDEX idx_trade_executions_execution_time (execution_time),
    INDEX idx_trade_executions_order_id (order_id),
    INDEX idx_trade_executions_position_id (position_id)
);

-- Create system_metrics table
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4) NOT NULL,
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('COUNTER', 'GAUGE', 'HISTOGRAM')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    -- Indexes
    INDEX idx_system_metrics_name (metric_name),
    INDEX idx_system_metrics_timestamp (timestamp),
    INDEX idx_system_metrics_type (metric_type)
);

-- Create market_data_live table (for caching live data)
CREATE TABLE IF NOT EXISTS market_data_live (
    symbol VARCHAR(50) PRIMARY KEY,
    last_price DECIMAL(10,2) NOT NULL,
    change_percent DECIMAL(5,2),
    volume BIGINT,
    open_price DECIMAL(10,2),
    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index
    INDEX idx_market_data_live_timestamp (timestamp)
);

-- Create users table (for authentication)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'USER' CHECK (role IN ('USER', 'ADMIN', 'TRADER')),
    is_active BOOLEAN DEFAULT true,
    api_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_users_username (username),
    INDEX idx_users_email (email),
    INDEX idx_users_api_key (api_key)
);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_trading_signals_updated_at BEFORE UPDATE ON trading_signals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_elite_recommendations_updated_at BEFORE UPDATE ON elite_recommendations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create security trigger to prevent mock data (same as before but with UUID)
CREATE OR REPLACE FUNCTION prevent_mock_signals()
RETURNS TRIGGER AS $$
BEGIN
    -- Prevent suspicious mock signals
    IF NEW.strategy_name IN ('PATTERN_RECOGNITION', 'VOLUME_SPIKE', 'MOMENTUM_BREAKOUT') 
       AND NEW.quality_score = 10.0 THEN
        RAISE EXCEPTION 'MOCK DATA DETECTED: Suspicious signal with perfect score from non-existent strategy';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_mock_signals_trigger 
    BEFORE INSERT ON trading_signals 
    FOR EACH ROW 
    EXECUTE FUNCTION prevent_mock_signals();

-- Insert initial admin user (password: 'admin123' - CHANGE THIS!)
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@algo-frontend.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewP6VUMaD/QNh.5i', 'ADMIN')
ON CONFLICT (username) DO NOTHING;

-- Create database functions for common operations
CREATE OR REPLACE FUNCTION get_active_positions()
RETURNS TABLE(
    symbol VARCHAR(50),
    side VARCHAR(20),
    quantity INTEGER,
    entry_price DECIMAL(10,2),
    current_pnl DECIMAL(12,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT p.symbol, p.side, p.quantity, p.entry_price, p.unrealized_pnl
    FROM positions p
    WHERE p.status = 'OPEN'
    ORDER BY p.opened_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_daily_pnl(trade_date DATE DEFAULT CURRENT_DATE)
RETURNS DECIMAL(12,2) AS $$
DECLARE
    daily_pnl DECIMAL(12,2);
BEGIN
    SELECT COALESCE(SUM(pnl), 0) INTO daily_pnl
    FROM trade_executions
    WHERE DATE(execution_time) = trade_date;
    
    RETURN daily_pnl;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your user)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- Create indexes for performance optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trading_signals_composite ON trading_signals(status, quality_score, generated_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_composite ON orders(status, placed_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_positions_composite ON positions(status, symbol);

-- Analyze tables for query optimization
ANALYZE;