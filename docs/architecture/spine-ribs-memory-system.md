# Spine/Ribs Memory Architecture

## Overview

The Swing Sage trading platform implements a **Spine/Ribs Memory Architecture** that separates immutable event storage (spine) from domain-specific projections (ribs). This design provides both comprehensive event history and optimized portfolio operations.

## Architecture Principles

### Write Once, Project Many
- **Spine**: Immutable, append-only event log storing ALL platform interactions
- **Ribs**: Derived, mutable views optimized for specific domain operations
- **Single Source of Truth**: Spine events are the authoritative record
- **Projection Consistency**: Ribs can be rebuilt from spine events if needed

### Event-Driven Updates
- Events written to spine trigger projections to ribs
- Portfolio materiality detection determines which ribs to update
- Manual user transactions vs automated analysis handled differently

## Spine: Immutable Event Storage

### Events Table Schema
```sql
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    ts_event TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,        -- analysis | proposal | insight | observation
    category VARCHAR(100),                   -- price_check | swing_setup | earnings | risk_mgmt
    session_id VARCHAR(255) NOT NULL,       -- Conversation correlation
    event_key VARCHAR(500) NOT NULL,        -- Stable correlation key
    sequence_num INTEGER NOT NULL,          -- Event ordering within session
    topic VARCHAR(255) NOT NULL,            -- Main subject: SBET, market_analysis, earnings_season
    symbols TEXT[],                         -- Related ticker symbols
    confidence_score DECIMAL(3,2),          -- 0.00 to 1.00
    payload JSONB NOT NULL,                 -- Event-specific data
    cross_references UUID[],                -- Related event IDs
    labels TEXT[]                           -- Optional tags
);
```

### Event Types & Categories

**Event Types:**
- `analysis`: Technical/fundamental analysis of securities
- `proposal`: Trading recommendations with entry/exit levels
- `insight`: Strategic observations and market commentary  
- `observation`: Price checks, market updates, general notes

**Categories:**
- `price_check`: Simple price/status queries
- `swing_setup`: Multi-day trading opportunities
- `day_trade`: Intraday trading opportunities
- `earnings`: Earnings-related analysis
- `risk_mgmt`: Risk assessment and position sizing
- `technical_analysis`: Chart patterns, indicators
- `sentiment`: News, social media, catalyst analysis

### Topic-Based Organization
Topics provide semantic grouping of related events:
- **Single Symbol**: `AAPL`, `NVDA`, `SBET`
- **Multi-Symbol**: `AAPL_NVDA`, `MEGA_CAPS`
- **Thematic**: `market_analysis`, `earnings_season`, `fed_meeting`

## Ribs: Domain Projections

### Portfolio Management Tables

#### v_positions: Current Holdings
```sql
CREATE TABLE v_positions (
    position_id UUID PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    shares INTEGER NOT NULL DEFAULT 0,
    avg_cost DECIMAL(10,2),
    current_value DECIMAL(12,2),
    unrealized_pnl DECIMAL(12,2),
    realized_pnl DECIMAL(12,2),
    sector VARCHAR(50),
    first_entry TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    source_events UUID[]                    -- Spine event IDs
);
```

#### v_trades: Trade Execution History
```sql
CREATE TABLE v_trades (
    trade_id UUID PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,               -- BUY/SELL
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total_value DECIMAL(12,2) NOT NULL,
    commission DECIMAL(8,2) DEFAULT 0,
    execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    strategy VARCHAR(50),                   -- swing, day, position
    source_event_id UUID REFERENCES events(event_id)
);
```

#### v_funding: Account Funding History
```sql
CREATE TABLE v_funding (
    funding_id UUID PRIMARY KEY,
    transaction_type VARCHAR(20) NOT NULL,  -- DEPOSIT/WITHDRAWAL
    amount DECIMAL(15,2) NOT NULL,
    transaction_time TIMESTAMP WITH TIME ZONE NOT NULL,
    description VARCHAR(255),
    running_balance DECIMAL(15,2) NOT NULL, -- Cash balance after transaction
    source_event_id UUID REFERENCES events(event_id)
);
```

#### v_analyses: Analysis Outcome Tracking
```sql
CREATE TABLE v_analyses (
    analysis_id UUID PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    recommendation VARCHAR(20),             -- BUY/SELL/HOLD/AVOID
    confidence_score DECIMAL(3,2),
    target_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    timeframe VARCHAR(20),
    created_time TIMESTAMP WITH TIME ZONE NOT NULL,
    outcome VARCHAR(20),                    -- pending/hit_target/hit_stop/expired
    outcome_time TIMESTAMP WITH TIME ZONE,
    actual_return DECIMAL(8,4),
    source_event_id UUID REFERENCES events(event_id)
);
```

#### v_portfolio_snapshots: Point-in-Time Portfolio State
```sql
CREATE TABLE v_portfolio_snapshots (
    snapshot_id UUID PRIMARY KEY,
    snapshot_time TIMESTAMP WITH TIME ZONE NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL,
    invested_value DECIMAL(15,2) NOT NULL,
    unrealized_pnl DECIMAL(12,2) NOT NULL,
    realized_pnl DECIMAL(12,2) NOT NULL,
    num_positions INTEGER NOT NULL,
    largest_position_pct DECIMAL(5,2),
    sector_concentration JSONB,
    risk_metrics JSONB,
    trigger_event_id UUID REFERENCES events(event_id)
);
```

### Portfolio-Focused Views (3 Consolidated Views)

The Portfolio Strategist queries exactly 3 comprehensive views that consolidate all ribs data:

#### 1. portfolio_overview - Complete Portfolio State
```sql
CREATE VIEW portfolio_overview AS
-- Combines v_positions, v_funding, v_portfolio_snapshots
-- Provides: positions count, total invested, cash balance, P&L,
--          funding totals, concentration alerts, snapshot history
-- Includes all funding data: deposits, withdrawals, current cash balance
```

#### 2. recent_performance - Trading & Position Performance
```sql
CREATE VIEW recent_performance AS
-- Combines v_trades + v_positions for activity analysis  
-- Provides: trading activity by symbol, position weights,
--          P&L per position, strategy performance
```

#### 3. analysis_performance - Analysis Success Tracking
```sql
CREATE VIEW analysis_performance AS  
-- Comprehensive v_analyses outcomes tracking
-- Provides: success rates by analysis type, symbol performance,
--          recommendation accuracy, overall trading statistics
```

## Smart Event Routing System

### Portfolio Materiality Detection

The `emit_event` MCP tool uses intelligent pattern matching to detect when events represent actual portfolio transactions vs theoretical analysis:

#### Funding Detection Patterns
```python
funding_patterns = [
    r'(?:loaded|deposited|added|funded)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
    r'(?:withdrew|withdrawal|took out)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
    r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:into|to)\s+(?:my\s+)?account'
]
```

#### Trade Detection Patterns
```python
trade_patterns = [
    r'(?:bought|purchased)\s+(\d+)\s+([A-Z]{1,5})\s+(?:at|@)\s+\$?(\d+(?:\.\d{2})?)',
    r'(?:sold|short)\s+(\d+)\s+([A-Z]{1,5})\s+(?:at|@)\s+\$?(\d+(?:\.\d{2})?)'
]
```

### Automatic Routing Logic

```
User Input → emit_event() → Portfolio Detection → Smart Routing

Analysis/Insight:
"push this AAPL analysis" → Spine Only (events table)

Funding Transaction:
"I loaded $10,000" → Spine (events) + Ribs (v_funding)

Trade Transaction:  
"I bought 100 AAPL at $150" → Spine (events) + Ribs (v_trades + v_positions)
```

## Integration with Trading Agents

### Portfolio Strategist Integration

The Portfolio Strategist agent queries exactly 3 consolidated views for complete portfolio context:

```sql
-- 1. Complete portfolio overview (positions, funding, cash, P&L, concentration)
SELECT * FROM portfolio_overview;

-- 2. Trading activity and position performance
SELECT * FROM recent_performance;

-- 3. Analysis outcomes and success tracking  
SELECT * FROM analysis_performance;
```

These 3 views provide comprehensive coverage of all v_* ribs tables while maintaining clean separation of concerns.

### Memory Context for Other Agents

Trading agents receive both:
1. **Portfolio Context**: Current positions, cash, constraints from ribs
2. **Historical Context**: Related analysis, patterns from spine events

## Operational Benefits

### For Users
- **Complete History**: Never lose analysis or trading context
- **Portfolio Awareness**: All decisions consider current holdings
- **Performance Tracking**: Success rates and patterns visible
- **Manual Control**: Only actual trades update portfolio state

### For Development
- **Audit Trail**: Complete record of all platform interactions
- **Debugging**: Event replay and analysis capabilities
- **Testing**: Isolated projections can be rebuilt/validated
- **Evolution**: New domain projections can be added without migration

## Data Flow Examples

### Analysis Workflow
```
1. User: "Analyze AAPL for swing trading"
2. emit_event() → events table (spine)
3. Analysis agents query spine for AAPL context
4. Portfolio Strategist provides portfolio constraints from ribs
5. Final recommendation stored back to spine
6. No ribs update (theoretical analysis only)
```

### Transaction Workflow
```
1. User: "I bought 100 AAPL at $150.25"
2. emit_event() detects trade execution
3. Spine: Insert event into events table
4. Ribs: Insert into v_trades table
5. Ribs: Update/create position in v_positions
6. Return: "Stored + Updated portfolio ribs (trade)"
```

### Funding Workflow
```
1. User: "I loaded $25,000 into my account"
2. emit_event() detects funding transaction
3. Spine: Insert event into events table
4. Ribs: Insert into v_funding with new running_balance
5. Portfolio Strategist has updated cash balance for next session
```

## Implementation Considerations

### Data Consistency
- Spine events are append-only (immutable)
- Ribs projections are eventually consistent
- Source event IDs provide full traceability
- Rebuild capability ensures data integrity

### Performance Optimization
- Ribs tables optimized for query patterns
- Appropriate indexing on time-series and symbol queries
- Portfolio views pre-aggregate common calculations
- Event spine indexed by session, topic, and time

### Scalability Patterns
- Event partitioning by time period
- Ribs archival for old positions/trades  
- Snapshot compression for portfolio history
- Asynchronous projection updates for high-volume scenarios

## Future Extensions

### Additional Ribs Domains
- **Options Tracking**: Strike, expiration, Greeks
- **Sector Analysis**: Industry rotation patterns
- **Risk Management**: VaR calculations, correlation matrices
- **Performance Attribution**: Strategy-specific returns

### Advanced Event Processing
- **Event Correlation**: Pattern detection across sessions
- **Predictive Analytics**: Success rate modeling
- **Alert Generation**: Risk threshold breaches
- **Automated Rebalancing**: Portfolio optimization triggers

---

This architecture provides Swing Sage with both the comprehensive memory of a professional trading platform and the flexibility to evolve new capabilities while maintaining data integrity and user control.