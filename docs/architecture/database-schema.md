# Database Schema

Swing Sage uses PostgreSQL to maintain a complete audit trail of all trading analysis, decisions, and market data. The schema is designed around a logical flow: **Sessions → Deliberations → Actions → Memories**.

## Schema Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ agent_sessions  │───▶│agent_deliberations│───▶│  agent_actions  │
│                 │    │                 │    │                 │
│ • Session mgmt  │    │ • LLM analysis  │    │ • Order execution│
│ • Conversation  │    │ • Reasoning     │    │ • Broker calls  │
│ • State tracking│    │ • Confidence    │    │ • Results       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ agent_memories  │
                       │                 │
                       │ • Learning data │
                       │ • Pattern recog │
                       │ • Success stories│
                       └─────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   market_data   │    │technical_indicators│  │  options_data   │
│                 │    │                 │    │                 │
│ • Price/volume  │    │ • RSI, MACD     │    │ • Strikes       │
│ • Multi-symbol  │    │ • Moving avgs   │    │ • Greeks        │
│ • Real-time     │    │ • Support/resist│    │ • IV data       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Tables

### agent_sessions
Top-level container for trading conversations.

```sql
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, error
    metadata JSONB DEFAULT '{}'
);
```

**Purpose**: Track individual trading sessions (e.g., "morning-scan", "earnings-week")  
**Key Features**:
- UUID primary keys for global uniqueness
- Session lifecycle management
- Flexible metadata in JSONB format

### agent_deliberations
All LLM reasoning and analysis in one table.

```sql
CREATE TABLE agent_deliberations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id),
    
    -- Agent and flow tracking
    agent_type VARCHAR(50) NOT NULL, -- 'claude_code', 'price_analyst', etc.
    cycle_number INTEGER NOT NULL,
    deliberation_step INTEGER NOT NULL,
    parent_deliberation_id UUID REFERENCES agent_deliberations(id),
    
    -- Context and reasoning  
    input_context JSONB NOT NULL, -- what the agent received
    reasoning TEXT NOT NULL, -- the agent's thinking process
    decision JSONB, -- structured decision/conclusion
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- LLM metadata
    llm_model VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    
    metadata JSONB DEFAULT '{}'
);
```

**Purpose**: Capture every piece of AI reasoning and analysis  
**Key Features**:
- Single table for all agent types (unified schema)
- Parent-child relationships for multi-turn conversations
- Complete LLM call metadata for cost tracking
- JSONB for flexible context and decision storage

**Example Data**:
```json
{
  "input_context": {
    "user_query": "Should I buy AAPL?",
    "symbols_analyzed": ["AAPL", "NVDA", "MSFT"],
    "portfolio_cash": 25000
  },
  "reasoning": "AAPL showing strength above 50-day MA with RSI at 64...",
  "decision": {
    "recommendation": "BUY",
    "entry_zone": "187.50-188.00",
    "stop_loss": "185.00",
    "target": "192.00",
    "position_size": 50
  },
  "confidence_score": 0.75
}
```

### agent_actions
Concrete actions taken by the system.

```sql
CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id),
    deliberation_id UUID REFERENCES agent_deliberations(id),
    
    -- Action details
    action_type VARCHAR(100) NOT NULL, -- place_order, cancel_order, query_data
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
    external_id VARCHAR(255), -- broker order ID, API call ID
    external_system VARCHAR(100) -- 'ibkr', 'yahoo_finance'
);
```

**Purpose**: Track all system actions and their outcomes  
**Key Features**:
- Links actions to the deliberations that caused them
- Tracks external system interactions (broker orders, API calls)
- Complete success/failure tracking with error details

**Example Data**:
```json
{
  "action_type": "place_order",
  "action_data": {
    "symbol": "AAPL",
    "qty": 50,
    "side": "BUY",
    "order_type": "LIMIT",
    "limit_price": 187.75
  },
  "expected_outcome": {
    "fill_price": 187.75,
    "total_cost": 9387.50
  },
  "actual_outcome": {
    "fill_price": 187.72,
    "total_cost": 9386.00,
    "fill_time": "2025-01-30T14:23:15Z"
  },
  "success": true,
  "external_id": "IBKR-12345678",
  "external_system": "ibkr"
}
```

### agent_memories
Persistent knowledge across sessions.

```sql
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
    
    related_memories UUID[]
);
```

**Purpose**: Learning system that gets smarter over time  
**Key Features**:
- Multiple memory types for different use cases
- Importance scoring for relevance ranking
- Tag-based searching and retrieval
- Expiration for short-term memories

**Memory Types**:
- **short_term**: Recent market context, current positions (expires)
- **long_term**: Strategy lessons, performance patterns (persistent)
- **episodic**: Specific trade narratives and outcomes (searchable)

**Example Data**:
```json
{
  "memory_type": "long_term",
  "memory_category": "strategy_lesson",
  "title": "NVDA momentum breakouts work best with volume confirmation",
  "content": "Analysis of 12 NVDA trades shows 85% win rate when breakout has >1.5x volume vs 45% without volume confirmation. Best results when RSI 45-65 range.",
  "structured_data": {
    "sample_size": 12,
    "win_rate_with_volume": 0.85,
    "win_rate_without_volume": 0.45,
    "optimal_rsi_range": [45, 65]
  },
  "importance_score": 0.90,
  "relevance_tags": ["NVDA", "momentum", "volume", "breakout", "lesson"]
}
```

## Market Data Tables

### market_data
Real-time market data for individual symbols.

```sql
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
```

**Purpose**: Cache real-time market data for analysis  
**Key Features**:
- Multi-symbol support
- Volume analysis (current vs 10-day average)
- Data source tracking for quality control

### technical_indicators
Technical analysis indicators for symbols.

```sql
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
    volume_ratio DECIMAL(6,2)
);
```

**Purpose**: Store calculated technical indicators  
**Key Features**:
- Standard indicators (RSI, MACD, Bollinger Bands)
- Support/resistance levels as arrays
- Volume-based indicators

### options_data
Options contract data with Greeks and implied volatility.

```sql
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
    implied_volatility DECIMAL(6,4)
);
```

## Database Views

### session_timeline
Chronological view of all session activity.

```sql
CREATE VIEW session_timeline AS
SELECT 
    s.id as session_id,
    s.session_name,
    'deliberation' as event_type,
    d.id as event_id,
    d.agent_type,
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
    m.content as event_data,
    m.importance_score as confidence_score,
    m.created_at as event_time
FROM agent_sessions s
JOIN agent_memories m ON s.id = m.session_id

ORDER BY event_time DESC;
```

### session_summary
Key metrics per session.

```sql
CREATE VIEW session_summary AS
SELECT 
    s.id,
    s.session_name,
    s.status,
    s.created_at,
    s.ended_at,
    
    -- Deliberation counts
    COUNT(DISTINCT d.id) as total_deliberations,
    COUNT(DISTINCT a.id) as total_actions,
    COUNT(DISTINCT m.id) as total_memories,
    
    -- Performance metrics
    AVG(d.confidence_score) as avg_confidence,
    MAX(d.cycle_number) as max_cycle

FROM agent_sessions s
LEFT JOIN agent_deliberations d ON s.id = d.session_id
LEFT JOIN agent_actions a ON s.id = a.session_id  
LEFT JOIN agent_memories m ON s.id = m.session_id

GROUP BY s.id, s.session_name, s.status, s.created_at, s.ended_at;
```

## Performance Optimization

### Indexes
Strategic indexes for common query patterns:

```sql
-- Deliberation queries
CREATE INDEX idx_deliberations_session_cycle ON agent_deliberations(session_id, cycle_number);
CREATE INDEX idx_deliberations_agent_type ON agent_deliberations(agent_type);
CREATE INDEX idx_deliberations_timestamp ON agent_deliberations(started_at);

-- Memory searches
CREATE INDEX idx_memories_type_category ON agent_memories(memory_type, memory_category);
CREATE INDEX idx_memories_importance ON agent_memories(importance_score);
CREATE INDEX idx_memories_tags ON agent_memories USING GIN(relevance_tags);

-- Market data lookups
CREATE INDEX idx_market_data_symbol_time ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_technical_indicators_symbol_time ON technical_indicators(symbol, timestamp DESC);
```

## Common Queries

### Trading Session Analysis
```sql
-- Complete session timeline
SELECT * FROM session_timeline 
WHERE session_id = 'your-session-id' 
ORDER BY event_time ASC;

-- Session performance summary
SELECT * FROM session_summary 
WHERE created_at >= '2025-01-01'
ORDER BY avg_confidence DESC;
```

### Memory Retrieval  
```sql
-- Get trading insights for a symbol
SELECT * FROM agent_memories 
WHERE 'AAPL' = ANY(relevance_tags)
AND memory_category = 'trading_insight'
ORDER BY importance_score DESC
LIMIT 5;

-- High-confidence strategy lessons
SELECT title, content, importance_score 
FROM agent_memories
WHERE memory_type = 'long_term' 
AND importance_score > 0.8
ORDER BY importance_score DESC;
```

### Market Data Analysis
```sql
-- Recent market data for analysis
SELECT m.symbol, m.current_price, m.change_percent, 
       t.rsi, t.macd_line 
FROM market_data m
LEFT JOIN technical_indicators t ON m.symbol = t.symbol 
WHERE m.timestamp > NOW() - INTERVAL '1 hour'
ORDER BY m.change_percent DESC;
```

## Schema Management

### Re-runnable Setup
The schema includes `DROP IF EXISTS` statements for complete rebuilds:

```bash
# Complete database reset and rebuild
psql -h 127.0.0.1 -U postgres -d swing_sage -f schema.sql
```

### Migration Strategy
For production deployments:
1. Use Alembic for incremental migrations
2. Test migrations on copy of production data
3. Backup before major schema changes
4. Use feature flags for gradual rollouts

## Data Retention

### Automatic Cleanup
- **Short-term memories**: Expire based on `expires_at` timestamp
- **Market data**: Archive data older than 1 year to separate tables  
- **Session data**: Keep indefinitely for learning purposes
- **Action logs**: Retain for audit compliance requirements

---

**Next**: Review [API Integrations](./api-integrations.md) to understand how external data flows into the database.