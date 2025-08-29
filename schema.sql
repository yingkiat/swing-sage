-- MVP3 Unified Events Schema for Swing Sage Trading Platform
-- User-triggered, context-aware memory system built on unified event engine
-- Note: Database creation is handled by setup_database.py

-- Drop existing objects (for teardown and reset)  
DROP VIEW IF EXISTS analysis_performance CASCADE;
DROP VIEW IF EXISTS recent_performance CASCADE;
DROP VIEW IF EXISTS portfolio_overview CASCADE;
DROP VIEW IF EXISTS session_timeline CASCADE;
DROP VIEW IF EXISTS session_summary CASCADE;
DROP VIEW IF EXISTS current_session_summary CASCADE;
DROP VIEW IF EXISTS recent_events CASCADE;
DROP VIEW IF EXISTS event_summary CASCADE;
DROP VIEW IF EXISTS session_activity CASCADE;

-- Drop ribs tables (portfolio projections)
DROP TABLE IF EXISTS v_analyses CASCADE;
DROP TABLE IF EXISTS v_funding CASCADE;
DROP TABLE IF EXISTS v_portfolio_snapshots CASCADE;
DROP TABLE IF EXISTS v_trades CASCADE;
DROP TABLE IF EXISTS v_positions CASCADE;

-- Legacy tables removed - market data now comes from real-time IBKR API
-- DROP TABLE IF EXISTS market_data CASCADE;
-- DROP TABLE IF EXISTS technical_indicators CASCADE; 
-- DROP TABLE IF EXISTS options_data CASCADE;
DROP TABLE IF EXISTS agent_actions CASCADE;
DROP TABLE IF EXISTS agent_memories CASCADE;
DROP TABLE IF EXISTS agent_deliberations CASCADE;
DROP TABLE IF EXISTS agent_sessions CASCADE;
DROP TABLE IF EXISTS events CASCADE;

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- MVP3 UNIFIED EVENT SYSTEM
-- ============================================================================

-- Single events table - unified and flexible (topic-based)
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts_event TIMESTAMP WITH TIME ZONE NOT NULL,
    ts_recorded TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,        -- 'analysis' | 'proposal' | 'insight' | 'observation'
    category VARCHAR(100),                   -- 'price_check' | 'swing_setup' | 'earnings' | 'risk_mgmt' | etc.
    session_id VARCHAR(255) NOT NULL,       -- Conversation correlation
    event_key VARCHAR(500) NOT NULL,        -- Stable correlation key
    sequence_num INTEGER NOT NULL,          -- Event ordering within session
    topic VARCHAR(255) NOT NULL,            -- Main subject: 'SBET', 'market_volatility', 'earnings_season'
    symbols TEXT[],                         -- Optional ticker symbols related to topic
    confidence_score DECIMAL(3,2),          -- 0.00 to 1.00
    payload JSONB NOT NULL,                 -- Event-specific data
    cross_references UUID[],                -- Related event IDs
    labels TEXT[],                          -- Optional tags
    
    -- Constraints
    UNIQUE(session_id, sequence_num),       -- Session event ordering
    CHECK(event_type IN ('analysis', 'proposal', 'insight', 'observation')),
    CHECK(confidence_score BETWEEN 0.0 AND 1.0)
);

-- ============================================================================
-- LEGACY MARKET DATA TABLES (REMOVED)
-- ============================================================================
-- All market data now comes from real-time IBKR API via get_market_data.py
-- 
-- REMOVED TABLES:
-- - market_data: Real-time prices/volumes fetched fresh, not stored
-- - technical_indicators: RSI, MACD, EMAs calculated by IBKR API  
-- - options_data: Greeks, IV, strikes available through IBKR when needed
--
-- Why removed: Trading requires real-time data, not stale database snapshots

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX idx_events_key ON events(event_key);
CREATE INDEX idx_events_type_time ON events(event_type, ts_event DESC);
CREATE INDEX idx_events_topic ON events(topic, ts_event DESC);
CREATE INDEX idx_events_symbols ON events USING GIN(symbols);
CREATE INDEX idx_events_session_time ON events(session_id, ts_event DESC);
CREATE INDEX idx_events_category ON events(event_type, category, ts_event DESC);
CREATE INDEX idx_events_topic_category ON events(topic, category, ts_event DESC);
CREATE INDEX idx_events_confidence ON events(confidence_score DESC, ts_event DESC);
CREATE INDEX idx_events_cross_refs ON events USING GIN(cross_references);

-- REMOVED: Indexes for deleted market data tables
-- (No longer needed since market data comes from real-time IBKR API)

-- ============================================================================
-- PORTFOLIO RIBS: DOMAIN PROJECTIONS FROM SPINE EVENTS
-- ============================================================================

-- Portfolio positions derived from events
CREATE TABLE v_positions (
    position_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    shares INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10,2),
    current_value DECIMAL(12,2),
    unrealized_pnl DECIMAL(12,2),
    realized_pnl DECIMAL(12,2),
    sector VARCHAR(50),
    first_entry TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    source_events UUID[],  -- Spine event IDs that created this position
    
    UNIQUE(symbol)
);

-- Trade executions derived from events
CREATE TABLE v_trades (
    trade_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,  -- BUY/SELL
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_value DECIMAL(12,2) NOT NULL,
    commission DECIMAL(8,2) DEFAULT 0,
    execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    strategy VARCHAR(50),  -- swing, day, position
    source_event_id UUID NOT NULL REFERENCES events(event_id),
    
    CHECK(side IN ('BUY', 'SELL'))
);

-- Portfolio snapshots at key moments
CREATE TABLE v_portfolio_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL,
    invested_value DECIMAL(15,2) NOT NULL,
    unrealized_pnl DECIMAL(12,2) NOT NULL,
    realized_pnl DECIMAL(12,2) NOT NULL,
    num_positions INTEGER NOT NULL,
    largest_position_pct DECIMAL(5,2),
    sector_concentration JSONB,  -- {"tech": 0.4, "finance": 0.3, ...}
    risk_metrics JSONB,  -- {"sharpe": 1.2, "max_drawdown": -0.15, ...}
    trigger_event_id UUID REFERENCES events(event_id)
);

-- Account funding tracking (deposits/withdrawals)
CREATE TABLE v_funding (
    funding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_type VARCHAR(20) NOT NULL,  -- DEPOSIT/WITHDRAWAL
    amount DECIMAL(15,2) NOT NULL,
    transaction_time TIMESTAMP WITH TIME ZONE NOT NULL,
    description VARCHAR(255),  -- "Initial funding", "Profit withdrawal", etc.
    running_balance DECIMAL(15,2) NOT NULL,  -- Cash balance after this transaction
    source_event_id UUID REFERENCES events(event_id),
    
    CHECK(transaction_type IN ('DEPOSIT', 'WITHDRAWAL')),
    CHECK(amount != 0)
);

-- Analysis outcomes tracking
CREATE TABLE v_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,  -- swing_setup, earnings_play, risk_check
    recommendation VARCHAR(20),  -- BUY/SELL/HOLD/AVOID
    confidence_score DECIMAL(3,2),
    target_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    timeframe VARCHAR(20),
    created_time TIMESTAMP WITH TIME ZONE NOT NULL,
    outcome VARCHAR(20),  -- pending/hit_target/hit_stop/expired
    outcome_time TIMESTAMP WITH TIME ZONE,
    actual_return DECIMAL(8,4),  -- If traded
    source_event_id UUID NOT NULL REFERENCES events(event_id)
);

-- Indexes for ribs
CREATE INDEX idx_positions_symbol ON v_positions(symbol);
CREATE INDEX idx_trades_symbol_time ON v_trades(symbol, execution_time DESC);
CREATE INDEX idx_trades_source_event ON v_trades(source_event_id);
CREATE INDEX idx_funding_time ON v_funding(transaction_time DESC);
CREATE INDEX idx_funding_type ON v_funding(transaction_type, transaction_time DESC);
CREATE INDEX idx_snapshots_time ON v_portfolio_snapshots(snapshot_time DESC);
CREATE INDEX idx_analyses_symbol ON v_analyses(symbol, created_time DESC);
CREATE INDEX idx_analyses_source_event ON v_analyses(source_event_id);

-- ============================================================================
-- EVENT VIEWS FOR EASY QUERYING
-- ============================================================================

-- Recent events view
CREATE VIEW recent_events AS
SELECT 
    event_id,
    event_key,
    event_type,
    category,
    symbols,
    confidence_score,
    ts_event,
    EXTRACT(EPOCH FROM (NOW() - ts_event))/3600 as age_hours,
    payload->'summary' as summary,
    payload->'agent_reasoning' as reasoning
FROM events
ORDER BY ts_event DESC
LIMIT 100;

-- Event summary by type
CREATE VIEW event_summary AS
SELECT 
    event_type,
    category,
    COUNT(*) as event_count,
    AVG(confidence_score) as avg_confidence,
    MAX(ts_event) as last_event,
    ARRAY(SELECT DISTINCT unnest(ARRAY_AGG(symbols))) as all_symbols
FROM events
GROUP BY event_type, category
ORDER BY event_count DESC;

-- Session activity view
CREATE VIEW session_activity AS
SELECT 
    session_id,
    COUNT(*) as total_events,
    COUNT(DISTINCT event_type) as event_types,
    ARRAY(SELECT DISTINCT unnest(ARRAY_AGG(symbols))) as session_symbols,
    MIN(ts_event) as session_start,
    MAX(ts_event) as last_activity,
    AVG(confidence_score) as avg_confidence
FROM events
GROUP BY session_id
ORDER BY last_activity DESC;

-- ============================================================================
-- PORTFOLIO STRATEGIST VIEWS (3 CONSOLIDATED VIEWS)
-- ============================================================================

-- 1. PORTFOLIO: Complete portfolio overview combining positions, cash, and P&L
CREATE VIEW portfolio_overview AS
WITH position_summary AS (
    SELECT 
        COUNT(*) as total_positions,
        SUM(current_value) as total_invested,
        SUM(unrealized_pnl) as total_unrealized_pnl,
        AVG(CASE WHEN current_value > 0 THEN (current_value - (shares * avg_cost)) / (shares * avg_cost) END) as avg_return_pct,
        MAX(current_value) as largest_position_value,
        (MAX(current_value) / NULLIF(SUM(current_value), 0)) * 100 as largest_position_pct
    FROM v_positions WHERE shares != 0
),
funding_summary AS (
    SELECT 
        SUM(CASE WHEN transaction_type = 'DEPOSIT' THEN amount ELSE 0 END) as total_deposits,
        SUM(CASE WHEN transaction_type = 'WITHDRAWAL' THEN amount ELSE 0 END) as total_withdrawals,
        (SELECT running_balance FROM v_funding ORDER BY transaction_time DESC LIMIT 1) as current_cash_balance
    FROM v_funding
),
concentration_risks AS (
    SELECT 
        COUNT(*) as concentration_alerts
    FROM v_positions 
    WHERE shares != 0 AND (current_value / (SELECT SUM(current_value) FROM v_positions WHERE shares != 0)) > 0.15
)
SELECT 
    p.total_positions,
    p.total_invested,
    f.current_cash_balance,
    p.total_unrealized_pnl,
    f.total_deposits,
    f.total_withdrawals,
    p.avg_return_pct,
    p.largest_position_pct,
    c.concentration_alerts,
    (SELECT COUNT(*) FROM v_portfolio_snapshots) as historical_snapshots
FROM position_summary p, funding_summary f, concentration_risks c;

-- 2. RECENT_PERFORMANCE: Trading activity and position performance  
CREATE VIEW recent_performance AS
WITH trade_summary AS (
    SELECT 
        symbol,
        COUNT(*) as trade_count,
        SUM(CASE WHEN side = 'BUY' THEN quantity ELSE -quantity END) as net_shares,
        AVG(price) as avg_price,
        MAX(execution_time) as last_trade,
        STRING_AGG(DISTINCT strategy, ', ') as strategies_used,
        SUM(total_value) as total_volume
    FROM v_trades 
    WHERE execution_time >= NOW() - INTERVAL '30 days'
    GROUP BY symbol
),
position_performance AS (
    SELECT 
        symbol,
        shares,
        avg_cost,
        current_value,
        unrealized_pnl,
        realized_pnl,
        (current_value / NULLIF((SELECT SUM(current_value) FROM v_positions WHERE shares != 0), 0)) * 100 as portfolio_weight_pct
    FROM v_positions 
    WHERE shares != 0
)
SELECT 
    COALESCE(t.symbol, p.symbol) as symbol,
    t.trade_count,
    t.net_shares,
    t.avg_price,
    t.last_trade,
    t.strategies_used,
    t.total_volume,
    p.shares as current_shares,
    p.avg_cost,
    p.current_value,
    p.unrealized_pnl,
    p.portfolio_weight_pct
FROM trade_summary t
FULL OUTER JOIN position_performance p ON t.symbol = p.symbol
ORDER BY t.last_trade DESC NULLS LAST, p.symbol;

-- 3. ANALYSIS_PERFORMANCE: Analysis outcomes and success tracking
CREATE VIEW analysis_performance AS
WITH analysis_summary AS (
    SELECT 
        analysis_type,
        recommendation,
        symbol,
        COUNT(*) as total_analyses,
        COUNT(CASE WHEN outcome = 'hit_target' THEN 1 END) as successes,
        COUNT(CASE WHEN outcome = 'hit_stop' THEN 1 END) as failures,
        COUNT(CASE WHEN outcome = 'pending' THEN 1 END) as pending,
        AVG(CASE WHEN outcome IN ('hit_target', 'hit_stop') THEN actual_return END) as avg_return,
        MAX(created_time) as last_analysis
    FROM v_analyses 
    WHERE created_time >= NOW() - INTERVAL '90 days'
    GROUP BY analysis_type, recommendation, symbol
),
overall_stats AS (
    SELECT 
        COUNT(*) as total_analyses_all,
        COUNT(CASE WHEN outcome = 'hit_target' THEN 1 END) as total_successes,
        COUNT(CASE WHEN outcome = 'hit_stop' THEN 1 END) as total_failures,
        ROUND(
            COUNT(CASE WHEN outcome = 'hit_target' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(CASE WHEN outcome IN ('hit_target', 'hit_stop') THEN 1 END), 0), 
            2
        ) as overall_success_rate_pct
    FROM v_analyses 
    WHERE created_time >= NOW() - INTERVAL '90 days'
)
SELECT 
    a.analysis_type,
    a.recommendation,
    a.symbol,
    a.total_analyses,
    a.successes,
    a.failures,
    a.pending,
    ROUND(
        a.successes * 100.0 / NULLIF((a.successes + a.failures), 0), 2
    ) as success_rate_pct,
    a.avg_return,
    a.last_analysis,
    o.overall_success_rate_pct,
    o.total_analyses_all
FROM analysis_summary a
CROSS JOIN overall_stats o
ORDER BY a.total_analyses DESC, a.last_analysis DESC;