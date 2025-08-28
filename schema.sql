-- Simplified PostgreSQL Schema for Agentic Options Trading Bot
-- Single logical flow: Sessions -> Deliberations -> Actions -> Memories
-- Note: Database creation is handled by setup_database.py

-- Drop existing objects (for teardown and reset)
DROP VIEW IF EXISTS session_timeline CASCADE;
DROP VIEW IF EXISTS session_summary CASCADE;

DROP TABLE IF EXISTS market_data CASCADE;
DROP TABLE IF EXISTS technical_indicators CASCADE; 
DROP TABLE IF EXISTS options_data CASCADE;
DROP TABLE IF EXISTS agent_actions CASCADE;
DROP TABLE IF EXISTS agent_memories CASCADE;
DROP TABLE IF EXISTS agent_deliberations CASCADE;
DROP TABLE IF EXISTS agent_sessions CASCADE;

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- CORE AGENT SYSTEM TABLES
-- ============================================================================

-- Trading sessions - top level container
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, error
    metadata JSONB DEFAULT '{}'
);

-- Agent deliberations - ALL agent thinking/reasoning in ONE table
CREATE TABLE agent_deliberations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id),
    
    -- Agent and flow tracking
    agent_type VARCHAR(50) NOT NULL, -- planner, executor, reflector
    cycle_number INTEGER NOT NULL,
    deliberation_step INTEGER NOT NULL, -- allows multi-turn conversations
    parent_deliberation_id UUID REFERENCES agent_deliberations(id), -- for conversations
    
    -- Context and reasoning
    input_context JSONB NOT NULL, -- what the agent received as input
    reasoning TEXT NOT NULL, -- the agent's thinking process
    decision JSONB, -- structured decision/conclusion (if any)
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- Deliberation type and scope (expanded from agent_reflections)
    deliberation_type VARCHAR(100) DEFAULT 'decision', -- decision, analysis, reflection, debate
    scope VARCHAR(100), -- trade_planning, risk_assessment, performance_review, etc.
    analyzed_period_start TIMESTAMP WITH TIME ZONE, -- for reflections
    analyzed_period_end TIMESTAMP WITH TIME ZONE,   -- for reflections
    
    -- Memory integration
    referenced_memories UUID[], -- array of memory IDs referenced
    created_memories UUID[], -- array of memory IDs created
    
    -- Performance and insights (from agent_reflections)
    performance_metrics JSONB DEFAULT '{}',
    insights TEXT, -- key insights generated
    lessons_learned TEXT[], -- actionable lessons
    recommended_adjustments JSONB DEFAULT '{}',
    
    -- Timing and metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    
    -- LLM metadata
    llm_model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Agent actions - concrete actions taken by any agent
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id),
    deliberation_id UUID REFERENCES agent_deliberations(id), -- which deliberation led to this
    
    -- Action details
    action_type VARCHAR(100) NOT NULL, -- place_order, cancel_order, query_data, create_memory
    action_data JSONB NOT NULL,
    expected_outcome JSONB,
    
    -- Execution tracking
    status VARCHAR(50) DEFAULT 'planned', -- planned, executing, completed, failed
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    actual_outcome JSONB,
    success BOOLEAN,
    error_message TEXT,
    
    -- External system integration
    external_id VARCHAR(255), -- broker order ID, API call ID, etc.
    external_system VARCHAR(100) -- moomoo, yahoo_finance, etc.
);

-- Agent memories - persistent knowledge
CREATE TABLE agent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id),
    source_deliberation_id UUID REFERENCES agent_deliberations(id),
    
    -- Memory classification
    memory_type VARCHAR(50) NOT NULL, -- short_term, long_term, episodic
    memory_category VARCHAR(100), -- market_conditions, trade_outcome, strategy_lesson
    
    -- Content
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    structured_data JSONB DEFAULT '{}',
    
    -- Memory metadata
    importance_score DECIMAL(3,2) DEFAULT 0.50, -- 0.00 to 1.00
    relevance_tags TEXT[],
    
    -- Lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE, -- for short-term memories
    
    -- Vector embedding for semantic search (future)
    -- embedding VECTOR(1536), -- disabled on Windows
    related_memories UUID[]
);

-- ============================================================================
-- MARKET DATA TABLES
-- ============================================================================

-- Real-time market data for individual symbols
CREATE TABLE market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Price data
    current_price DECIMAL(10,4) NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4), 
    low_price DECIMAL(10,4),
    previous_close DECIMAL(10,4),
    change_amount DECIMAL(10,4),
    change_percent DECIMAL(8,4),
    
    -- Volume
    volume BIGINT,
    avg_volume_10d BIGINT,
    volume_ratio DECIMAL(6,2),
    
    -- Market cap and shares
    market_cap BIGINT,
    shares_outstanding BIGINT,
    
    -- Data source metadata
    data_source VARCHAR(50) DEFAULT 'yfinance',
    is_market_hours BOOLEAN DEFAULT false
);

-- Technical indicators for symbols
CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Moving averages
    sma_20 DECIMAL(10,4),
    sma_50 DECIMAL(10,4),
    ema_20 DECIMAL(10,4),
    ema_50 DECIMAL(10,4),
    
    -- Momentum indicators
    rsi DECIMAL(5,2),
    macd_line DECIMAL(10,6),
    macd_signal DECIMAL(10,6),
    macd_histogram DECIMAL(10,6),
    
    -- Bollinger Bands
    bb_upper DECIMAL(10,4),
    bb_middle DECIMAL(10,4),
    bb_lower DECIMAL(10,4),
    bb_width DECIMAL(6,4),
    
    -- Support and resistance
    support_levels DECIMAL(10,4)[],
    resistance_levels DECIMAL(10,4)[],
    
    -- Volume indicators
    volume_sma_10 BIGINT,
    volume_ratio DECIMAL(6,2),
    
    -- Calculation metadata
    data_source VARCHAR(50) DEFAULT 'calculated'
);

-- Options data (strike prices, Greeks, implied volatility)
CREATE TABLE options_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    underlying_symbol VARCHAR(10) NOT NULL,
    contract_symbol VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contract details
    option_type VARCHAR(10) NOT NULL, -- CALL or PUT
    strike_price DECIMAL(10,4) NOT NULL,
    expiration_date DATE NOT NULL,
    
    -- Pricing
    bid DECIMAL(10,4),
    ask DECIMAL(10,4),
    last_price DECIMAL(10,4),
    mark_price DECIMAL(10,4),
    
    -- Volume and interest
    volume INTEGER DEFAULT 0,
    open_interest INTEGER DEFAULT 0,
    
    -- Greeks
    delta DECIMAL(8,6),
    gamma DECIMAL(8,6),
    theta DECIMAL(8,6),
    vega DECIMAL(8,6),
    rho DECIMAL(8,6),
    
    -- Volatility
    implied_volatility DECIMAL(6,4),
    
    -- Data source
    data_source VARCHAR(50) DEFAULT 'moomoo'
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Agent deliberations indexes
CREATE INDEX idx_deliberations_session_cycle ON agent_deliberations(session_id, cycle_number);
CREATE INDEX idx_deliberations_agent_type ON agent_deliberations(agent_type);
CREATE INDEX idx_deliberations_parent ON agent_deliberations(parent_deliberation_id);
CREATE INDEX idx_deliberations_timestamp ON agent_deliberations(started_at);

-- Agent actions indexes  
CREATE INDEX idx_actions_session ON agent_actions(session_id);
CREATE INDEX idx_actions_deliberation ON agent_actions(deliberation_id);
CREATE INDEX idx_actions_status ON agent_actions(status);

-- Agent memories indexes
CREATE INDEX idx_memories_session ON agent_memories(session_id);
CREATE INDEX idx_memories_type_category ON agent_memories(memory_type, memory_category);
CREATE INDEX idx_memories_importance ON agent_memories(importance_score);
CREATE INDEX idx_memories_tags ON agent_memories USING GIN(relevance_tags);

-- Market data indexes
CREATE INDEX idx_market_data_symbol_time ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_technical_indicators_symbol_time ON technical_indicators(symbol, timestamp DESC);
CREATE INDEX idx_options_data_underlying_exp ON options_data(underlying_symbol, expiration_date);

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- Complete session timeline - chronological view of all activity
CREATE VIEW session_timeline AS
SELECT 
    s.id as session_id,
    s.session_name,
    'deliberation' as event_type,
    d.id as event_id,
    d.agent_type,
    d.cycle_number,
    d.deliberation_step,
    d.deliberation_type,
    d.reasoning as event_data,
    d.confidence_score,
    d.started_at as event_time
FROM agent_sessions s
JOIN agent_deliberations d ON s.id = d.session_id

UNION ALL

SELECT 
    s.id as session_id,
    s.session_name,
    'action' as event_type,
    a.id as event_id,
    'executor' as agent_type,
    NULL as cycle_number,
    NULL as deliberation_step,
    a.action_type as deliberation_type,
    a.action_data::text as event_data,
    NULL as confidence_score,
    a.started_at as event_time
FROM agent_sessions s
JOIN agent_actions a ON s.id = a.session_id

UNION ALL

SELECT 
    s.id as session_id,
    s.session_name,
    'memory' as event_type,
    m.id as event_id,
    NULL as agent_type,
    NULL as cycle_number,
    NULL as deliberation_step,
    m.memory_type as deliberation_type,
    m.content as event_data,
    m.importance_score as confidence_score,
    m.created_at as event_time
FROM agent_sessions s
JOIN agent_memories m ON s.id = m.session_id

ORDER BY event_time DESC;

-- Session summary - key metrics per session
CREATE VIEW session_summary AS
SELECT 
    s.id,
    s.session_name,
    s.status,
    s.created_at,
    s.ended_at,
    
    -- Deliberation counts
    COUNT(DISTINCT d.id) as total_deliberations,
    COUNT(DISTINCT CASE WHEN d.agent_type = 'planner' THEN d.id END) as planner_deliberations,
    COUNT(DISTINCT CASE WHEN d.agent_type = 'executor' THEN d.id END) as executor_deliberations, 
    COUNT(DISTINCT CASE WHEN d.agent_type = 'reflector' THEN d.id END) as reflector_deliberations,
    
    -- Action counts
    COUNT(DISTINCT a.id) as total_actions,
    COUNT(DISTINCT CASE WHEN a.success = true THEN a.id END) as successful_actions,
    
    -- Memory counts  
    COUNT(DISTINCT m.id) as total_memories,
    COUNT(DISTINCT CASE WHEN m.memory_type = 'long_term' THEN m.id END) as long_term_memories,
    
    -- Cycle info
    MAX(d.cycle_number) as max_cycle,
    AVG(d.confidence_score) as avg_confidence

FROM agent_sessions s
LEFT JOIN agent_deliberations d ON s.id = d.session_id
LEFT JOIN agent_actions a ON s.id = a.session_id  
LEFT JOIN agent_memories m ON s.id = m.session_id

GROUP BY s.id, s.session_name, s.status, s.created_at, s.ended_at;

-- Current session summary (for active session)
CREATE VIEW current_session_summary AS
SELECT * FROM session_summary 
WHERE status = 'active' 
ORDER BY created_at DESC 
LIMIT 1;