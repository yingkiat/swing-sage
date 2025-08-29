# Swing Sage MVP3: Memory & Event Engine
## Product Requirements Document

**Version:** 1.0  
**Status:** Ready for Implementation  
**Owner:** Swing Sage Core Team  
**Last Updated:** 2025-01-28  

---

## Executive Summary

MVP3 delivers a **user-triggered, context-aware memory system** built on a unified event engine. Users control what gets preserved through natural commands like "push this" while the AI intelligently determines event type, extracts context, and generates correlation keys. This eliminates storage clutter while ensuring all valuable insights—analysis, recommendations, observations—are retained with full traceability.

**Core Innovation:** Single unified event storage with AI-driven context extraction and flexible event categorization.

---

## Business Objectives

### Primary Goals
1. **User-Controlled Quality** - Only valuable analysis gets stored via explicit user commands
2. **Context-Aware Capture** - AI extracts symbols, parameters, and reasoning from conversation context  
3. **Exact Recall** - Retrieve prior analysis by stable key to avoid redundant computation
4. **Traceable Recommendations** - Every action proposal links to its source analysis

### Success Metrics
- **User Satisfaction**: >90% of pushed memories rated as valuable after 1 week
- **Storage Efficiency**: <100 events/month per active trader (high signal/noise ratio)
- **Reuse Rate**: >40% of pushed analysis referenced in future conversations
- **Context Accuracy**: >95% of auto-extracted symbols/parameters correct

---

## User Experience & Workflows

### 1. Memory Capture Workflow

#### Trigger Commands (Natural Language)
```
User: "push this"                    → AI determines event type from context
User: "save this swing analysis"     → event_type: 'analysis', category: 'swing_setup'  
User: "remember this recommendation" → event_type: 'proposal', category: 'trade_rec'
User: "store this risk insight"      → event_type: 'insight', category: 'risk_mgmt'
User: "push this for NVDA only"      → Override symbol extraction
```

#### AI Context Extraction Process
1. **Event Type Classification**: Determine if analysis, proposal, insight, or observation
2. **Symbol Detection**: Parse recent conversation for ticker mentions
3. **Parameter Canonicalization**: Extract timeframes, thresholds, lookback periods
4. **Reasoning Capture**: Summarize agent's analysis logic and conclusions
5. **Confidence Assessment**: Evaluate certainty based on data quality and agent confidence
6. **Analysis Key Generation**: Build stable correlation identifier

#### Example Interaction
```
Agent: "NVDA shows strong momentum above $500 with RSI at 65, 
        volume 2x average. Good swing setup for 3-5 day hold."

User: "push this"

System: ✅ Stored event: analysis|swing_setup|NVDA|price_threshold=500;rsi=65;volume_ratio=2x|v1
        Event ID: evt_545a7f2b
        Type: analysis/swing_setup
        Confidence: 0.85
```

### 2. Memory Retrieval Workflow

#### Automatic Context Matching
- System checks for similar analysis when new requests come in
- Presents existing insights: "I analyzed NVDA swing setups 2 days ago..."
- User can choose to reuse or request fresh analysis

#### Manual Memory Queries
```
User: "what did I save about NVDA?"
User: "show me recent analysis memories"  
User: "find that risk insight from last week"
User: "get my NVDA swing setup from yesterday"
```

### 3. Event Cross-Referencing

When agents make recommendations, they can reference stored events:
```
Agent: "Based on your saved NVDA analysis (evt_545a7f2b), 
        I recommend entering long position at $505 with stop at $485."

User: "push this recommendation"

→ Creates new proposal event that references the analysis event
```

---

## Technical Architecture

### MCP Tool Implementation

#### Same stdio.js → Python Architecture
Leverages existing proven MCP server pattern:
```
Claude Code → stdio.js MCP Server → Python CLI Scripts → PostgreSQL
```

**New Python Scripts:**
- `emit_event.py` - Store any user-triggered memory (unified)
- `get_events.py` - Retrieve and search stored events (unified)
- `canonicalize_key.py` - Utility for analysis key generation

#### Tool Specifications

### 1. `emit_event` (Unified Storage)
**Trigger**: User commands like "push this", "save this", "remember this"
**Intelligence**: AI determines event type and extracts all context

```typescript
interface EmitEventInput {
  // User command interpretation
  user_command: string;          // "push this", "save this analysis"  
  type_hint?: string;            // Optional: "analysis", "proposal", "insight"
  symbol_override?: string[];    // "push this for NVDA only"
  
  // AI Context Extraction (automatic)
  conversation_context: {
    recent_symbols: string[];    // Auto-extracted from conversation
    agent_reasoning: string;     // Last agent analysis/conclusion
    parameters_used: Record<string, any>; // Timeframes, thresholds, etc.
    confidence_indicators: any; // Data quality, agent certainty
    timestamp_context: string;  // When analysis was performed
  };
  
  // Metadata
  session_id: string;           // Current conversation ID
  data_version: string;         // Default: 'v1'
}

interface EmitEventOutput {
  success: boolean;
  event_id: string;             // UUID for the event
  event_key: string;            // Generated correlation key  
  event_type: string;           // Determined type (analysis/proposal/insight)
  category: string;             // Sub-category (swing_setup, earnings, etc.)
  symbols_captured: string[];   // What was stored
  summary: string;              // Human-readable description
  confidence_score: number;     // 0.0 to 1.0
}
```

### 2. `get_events` (Unified Retrieval)
**Purpose**: Search, filter, and retrieve stored events

```typescript
interface GetEventsInput {
  // Exact lookup
  event_key?: string;           // Specific event by correlation key
  event_id?: string;            // Specific event by UUID
  
  // Filtering options
  filters?: {
    symbols?: string[];         // Filter by tickers
    event_types?: string[];     // Filter by type (analysis/proposal/insight)
    categories?: string[];      // Filter by category (swing_setup, earnings, etc.)
    min_confidence?: number;    // Quality threshold
    hours_back?: number;        // Time window (default 168 = 1 week)
    session_id?: string;        // Specific conversation
    referenced_events?: string[]; // Events that reference these IDs
  };
  
  // Output control
  limit?: number;               // Default 10, max 50
  sort_by?: 'timestamp' | 'confidence' | 'relevance';
  include_cross_references?: boolean; // Show related events
}

interface GetEventsOutput {
  events: Array<{
    event_id: string;
    event_key: string;
    event_type: string;         // analysis/proposal/insight/observation
    category: string;           // swing_setup/earnings/risk_mgmt/etc.
    symbols: string[];
    summary: string;
    confidence_score: number;
    stored_at: string;
    age_hours: number;
    agent_reasoning?: string;   // Full reasoning if requested
    parameters?: any;           // Canonicalized inputs
    cross_references?: string[]; // Related event IDs
  }>;
  total_found: number;
  filters_applied: any;
}
```

---

## Data Model & Storage

### Event Schema (Clean Implementation)
**From Scratch - No Migration from Existing Tables**

```sql
-- Single events table - unified and flexible
CREATE TABLE events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts_event TIMESTAMP WITH TIME ZONE NOT NULL,
    ts_recorded TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,        -- 'analysis' | 'proposal' | 'insight' | 'observation'
    category VARCHAR(100),                   -- 'swing_setup' | 'earnings' | 'risk_mgmt' | etc.
    session_id VARCHAR(255) NOT NULL,       -- Conversation correlation
    event_key VARCHAR(500) NOT NULL,        -- Stable correlation key
    sequence_num INTEGER NOT NULL,          -- Event ordering within session
    symbols TEXT[] NOT NULL,                -- Tickers involved
    confidence_score DECIMAL(3,2),          -- 0.00 to 1.00
    payload JSONB NOT NULL,                 -- Event-specific data
    cross_references UUID[],                -- Related event IDs
    labels TEXT[],                          -- Optional tags
    
    -- Constraints
    UNIQUE(session_id, sequence_num),       -- Session event ordering
    CHECK(event_type IN ('analysis', 'proposal', 'insight', 'observation')),
    CHECK(confidence_score BETWEEN 0.0 AND 1.0)
);

-- Performance indexes
CREATE INDEX idx_events_key ON events(event_key);
CREATE INDEX idx_events_type_time ON events(event_type, ts_event DESC);
CREATE INDEX idx_events_symbols ON events USING GIN(symbols);
CREATE INDEX idx_events_session_time ON events(session_id, ts_event DESC);
CREATE INDEX idx_events_category ON events(event_type, category, ts_event DESC);
CREATE INDEX idx_events_confidence ON events(confidence_score DESC, ts_event DESC);
CREATE INDEX idx_events_cross_refs ON events USING GIN(cross_references);
```

### Event Key Generation
**Canonical Format:**
```
{event_type}|{category}|{SYMBOLS_SORTED}|{CANONICAL_PARAMS}|{data_version}
```

**Examples:**
- `analysis|swing_setup|NVDA|price_threshold=500;rsi=65;volume_ratio=2x|v1`
- `proposal|trade_rec|AAPL|action=enter_long;target=195;stop=185|v1`
- `insight|risk_mgmt|AMD,NVDA|correlation=high;sector=semiconductor|v1`

**Python Implementation:**
```python
def generate_event_key(event_type: str, category: str, symbols: List[str], 
                      params: Dict[str, Any], data_version: str = 'v1') -> str:
    # Canonicalize symbols
    symbols_canon = ','.join(sorted([s.upper() for s in symbols]))
    
    # Canonicalize parameters
    param_pairs = []
    for key in sorted(params.keys()):
        value = normalize_param_value(params[key])
        param_pairs.append(f"{key}={value}")
    params_canon = ';'.join(param_pairs)
    
    # Build key
    return f"{event_type}|{category}|{symbols_canon}|{params_canon}|{data_version}"
```

---

## Context Extraction Intelligence

### Symbol Detection Algorithm
```python
def extract_symbols_from_context(conversation_context: str) -> List[str]:
    # 1. Regex for ticker patterns ($AAPL, NVDA, etc.)
    # 2. Recent agent tool calls (get_market_data symbols)
    # 3. User mentions in last 5 messages
    # 4. Deduplicate and validate against known tickers
    pass
```

### Parameter Canonicalization
```python
def extract_parameters(agent_reasoning: str, tool_calls: List[Dict]) -> Dict[str, Any]:
    # 1. Parse timeframes (1d, 5m, weekly, etc.)
    # 2. Extract thresholds (RSI > 70, price above $500)
    # 3. Volume ratios (2x average, above 1M shares)
    # 4. Lookback periods (90 days, 6 months)
    # 5. Normalize formats for consistency
    pass
```

### Event Type & Category Classification
```python
def classify_event(user_command: str, context: str) -> Tuple[str, str]:
    # Event Type Classification
    if 'recommendation' in user_command.lower() or 'buy' in context or 'sell' in context:
        event_type = 'proposal'
    elif 'risk' in user_command.lower() or 'insight' in user_command.lower():
        event_type = 'insight'
    elif 'analysis' in user_command.lower() or 'setup' in context:
        event_type = 'analysis'
    else:
        event_type = 'observation'  # Default
    
    # Category Classification
    if 'swing' in context or 'day' in context:
        category = 'swing_setup' if 'swing' in context else 'day_trade'
    elif 'earnings' in context:
        category = 'earnings'
    elif 'risk' in context:
        category = 'risk_mgmt'
    else:
        category = 'general'
    
    return event_type, category
```

---

## Implementation Strategy

### Phase 1: Clean Build (Weeks 1-2)
- ✅ **New event table** - No migration from existing schema
- ✅ **Python CLI scripts** - 2 unified memory tools (`emit_event.py`, `get_events.py`)
- ✅ **stdio.js integration** - Add new tools to existing MCP architecture  
- ✅ **Context extraction** - AI interpretation and event classification

### Phase 2: User Testing (Week 3)
- ✅ **Command interpretation** - Refine natural language triggers
- ✅ **Context accuracy** - Validate symbol/parameter extraction
- ✅ **Key generation** - Test canonicalization with real scenarios

### Phase 3: Integration (Week 4)
- ✅ **Agent workflows** - Cross-reference events and build contextual memory
- ✅ **Event browsing** - Unified search and filtering
- ✅ **Performance optimization** - Index tuning for fast retrieval

### No Migration Complexity
- Existing `agent_memories` table remains for reference
- New system operates independently
- Users manually re-push valuable old insights if desired

---

## Quality Control & Validation

### Context Extraction Accuracy
```python
# Validation tests for AI context extraction
def test_context_extraction():
    conversation = """
    Agent: NVDA at $520 with RSI 68, volume 2.1x average.
           Looking good for 3-day swing above $500 support.
    User: push this swing analysis
    """
    
    extracted = extract_context(conversation)
    assert extracted.symbols == ['NVDA']
    assert extracted.analysis_type == 'swing_setup' 
    assert extracted.parameters['price_level'] == 520
    assert extracted.parameters['rsi'] == 68
```

### Analysis Key Consistency
```python
def test_key_generation():
    # Same inputs should always generate same key
    params1 = {'rsi': 70, 'timeframe': '1d', 'volume_ratio': 2.0}
    params2 = {'volume_ratio': 2.0, 'timeframe': '1d', 'rsi': 70}  # Different order
    
    key1 = generate_analysis_key('swing_setup', ['NVDA'], params1)
    key2 = generate_analysis_key('swing_setup', ['NVDA'], params2)
    assert key1 == key2  # Order independence
```

---

## Success Criteria

### MVP3 Complete When:
1. ✅ **User Commands Work**: "push this" stores events correctly with AI classification
2. ✅ **Context Extraction Accurate**: >95% symbol/parameter detection  
3. ✅ **Stable Keys Generated**: Same context produces same event key
4. ✅ **Event Cross-References**: Related events link correctly via IDs
5. ✅ **Performance Targets Met**: <100ms retrieval, <50ms key lookup
6. ✅ **Integration Complete**: Works seamlessly with existing stdio.js architecture

### User Acceptance Tests
```
Test 1: Unified Event Storage
  Agent analyzes AAPL swing setup
  User: "push this" 
  System stores as event_type='analysis', category='swing_setup'
  
Test 2: Event Retrieval  
  User: "what did I save about AAPL?"
  System retrieves all AAPL events with age/confidence indicators
  
Test 3: Event Cross-Referencing
  Agent references stored event in new recommendation
  User: "push this recommendation"
  System creates new event with cross_reference to original
```

---

## Resource Requirements

### Development Effort
- **Event Classification Logic**: 1 week
- **Python MCP Scripts**: 1 week (2 unified tools vs 4 separate)
- **stdio.js Integration**: 3 days  
- **Testing & Validation**: 1 week
- **Total**: 3-4 weeks (reduced from original 4+ week estimate)

### Performance Expectations
- **Storage Growth**: ~50 events/month per active trader
- **Query Performance**: <100ms for memory browsing
- **Context Processing**: <200ms for command interpretation

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|---------|------------|
| **Context Extraction Errors** | Medium | Extensive testing + user feedback loops |
| **Analysis Key Collisions** | Low | Robust canonicalization + validation |  
| **User Adoption** | High | Natural language commands + clear value |
| **Performance Issues** | Medium | Proper indexing + query optimization |

---

## Conclusion

MVP3's **user-triggered approach** solves the fundamental problem of signal vs. noise in automated memory systems. By letting users control what gets stored while leveraging AI for intelligent context extraction, we achieve high-quality memory persistence without storage bloat.

The **clean implementation strategy** avoids migration complexity while the **proven stdio.js architecture** ensures reliable integration with existing workflows.

**Ready for implementation** with clear user workflows, technical specifications, and success criteria.

---

**Next Steps:**
1. Implement context extraction algorithms
2. Build Python CLI scripts for 4 memory tools
3. Integrate with existing stdio.js MCP server
4. User testing with real trading conversations
5. Performance optimization and production deployment