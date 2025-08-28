# Swing Sage MVP - Product Requirements Document

**Version:** 1.0  
**Date:** August 27, 2025  
**Status:** Draft  
**Author:** Claude Code Development Team

---

## Executive Summary

### Vision
Create the world's first Claude Code native trading platform that enables natural language trading conversations with persistent memory and real market data integration.

### Mission Statement
Transform Claude Code into a sophisticated trading advisor through MCP server integration, enabling users to have intelligent trading conversations that learn and improve over time.

### Success Metrics
- **Functional**: Complete trading conversation cycle (data → analysis → recommendation → memory storage)
- **Technical**: Sub-5 second response time for trading queries
- **User Experience**: Natural conversation flow without technical complexity
- **Learning**: Successful storage and retrieval of trading insights for future conversations

---

## Product Overview

### What We're Building
A **Claude Code MCP server** that provides 3 essential trading tools:

1. **`get_market_data`** - Real-time market data retrieval
2. **`query_trading_memories`** - Search past trading insights from PostgreSQL
3. **`store_trading_memory`** - Save new analysis/recommendations to database

### Core User Journey
```
User: "What's a good swing trade setup today?"
↓
Claude Code → get_market_data(['AAPL', 'NVDA', 'MSFT', 'GOOGL'])
↓
Claude Code → query_trading_memories('swing trade momentum breakout')  
↓
Claude Code → [Synthesizes data + memories into recommendation]
↓
Claude Code → store_trading_memory(recommendation_details)
↓
Response: "Based on current market data and past insights, NVDA shows strong momentum breakout at $885 resistance with 2.1x volume. Entry: $885.50, Stop: $880, Target: $895. This setup has historically performed well based on our May 15th analysis showing similar patterns."
```

### Why This Approach
- **Leverages July 2025 Claude Code capabilities** - Custom subagents + MCP integration now possible
- **Builds on existing infrastructure** - Reuses proven PostgreSQL schema and broker integrations
- **Natural user experience** - Pure conversation interface, no UI complexity
- **Learning system** - Each conversation improves future recommendations

---

## Technical Requirements

### Architecture Overview
```
Claude Code (User Interface)
    ↓ MCP Protocol
Trading MCP Server (Node.js)
    ↓ Python Scripts
Existing Infrastructure (PostgreSQL + Market Data)
```

### MCP Server Specifications

#### Technology Stack
- **Runtime**: Node.js 16+ 
- **Protocol**: MCP (Model Context Protocol)
- **Integration**: Python spawn processes for existing codebase
- **Database**: PostgreSQL via existing connection.py
- **Port**: 3001 (configurable)

#### Tool Specifications

##### 1. get_market_data
**Purpose**: Retrieve current market data for specified symbols

**Input Schema**:
```json
{
  "symbols": ["AAPL", "NVDA", "MSFT", "GOOGL"],  // Array of stock symbols
  "include_technical": true                       // Optional: include RSI, EMA
}
```

**Output Schema**:
```json
{
  "AAPL": {
    "symbol": "AAPL",
    "current_price": 187.50,
    "change_percent": 0.8,
    "volume_ratio": 1.3,
    "momentum_score": 0.75,
    "setup_quality": "good",
    "trend_direction": "bullish",
    "key_levels": "Support: $185.00, Resistance: $190.00",
    "volume_profile": "Above average (1.3x)",
    "pattern": "momentum_breakout",
    "indicators": {
      "rsi": 64.2,
      "ema_20": 186.50,
      "ema_50": 184.75
    },
    "timestamp": "2025-08-27T15:30:00Z",
    "data_source": "database_fallback"
  }
}
```

**Data Sources** (Priority Order):
1. **PostgreSQL Database** - Latest cached market data from existing market_data table
2. **Minimal Fallback** - Static base prices for development/testing

**Performance Requirements**:
- Response time: < 3 seconds
- Supports up to 10 symbols per request
- Graceful degradation if database unavailable

##### 2. query_trading_memories
**Purpose**: Search PostgreSQL for relevant trading insights and past analysis

**Input Schema**:
```json
{
  "query": "NVDA momentum breakout",   // Search terms
  "limit": 5,                         // Max results
  "memory_types": ["trading_insight", "market_analysis"]  // Optional filter
}
```

**Output Schema**:
```json
{
  "query": "NVDA momentum breakout",
  "memories_found": 3,
  "memories": [
    {
      "memory_id": "uuid-123",
      "type": "long_term",
      "category": "trading_insight", 
      "title": "NVDA momentum breakouts work best with volume confirmation",
      "content": "Historical analysis shows NVDA breakouts above $880 with >2x volume have 73% success rate...",
      "importance_score": 0.90,
      "tags": ["NVDA", "momentum", "breakout", "volume"],
      "created_at": "2025-05-15T14:30:00Z"
    }
  ],
  "database_status": "connected",
  "timestamp": "2025-08-27T15:30:00Z"
}
```

**Query Strategy**:
- Search `agent_memories` table where `memory_category` = 'trading_insight' OR 'market_analysis'
- ILIKE search on content field for query terms
- Order by importance_score DESC, created_at DESC
- Fallback to general trading principles if no results

**Performance Requirements**:
- Response time: < 2 seconds
- Full-text search capability
- Handles empty results gracefully

##### 3. store_trading_memory
**Purpose**: Save new trading analysis/recommendations to PostgreSQL for future reference

**Input Schema**:
```json
{
  "memory_type": "long_term",                    // short_term, long_term, episodic
  "memory_category": "trading_insight",          // trading_insight, market_analysis
  "title": "NVDA breakout setup - Aug 27 2025",
  "content": "NVDA showing strong momentum breakout at $885 resistance...",
  "importance_score": 0.85,                      // 0.0 to 1.0
  "relevance_tags": ["NVDA", "breakout", "momentum", "swing_trade"],
  "context_metadata": {                          // Optional additional data
    "symbols_analyzed": ["NVDA", "AAPL", "MSFT"],
    "market_conditions": "bullish_momentum",
    "confidence_level": "high"
  }
}
```

**Output Schema**:
```json
{
  "success": true,
  "memory_id": "uuid-456", 
  "stored_at": "2025-08-27T15:35:00Z",
  "database_status": "inserted",
  "memory_count": 127    // Total memories in database
}
```

**Storage Strategy**:
- Insert into `agent_memories` table using existing schema
- Auto-generate session_id if not provided
- JSON serialize metadata and tags fields
- Handle duplicate detection (same title within 24 hours)

**Performance Requirements**:
- Response time: < 1 second
- Atomic database operations
- Error handling for connection failures

### System Integration Requirements

#### Database Integration
- **Existing Schema**: Must work with current `agent_memories` table structure
- **Connection Management**: Reuse existing `db_manager` from `database/connection.py`
- **Session Handling**: Proper database session context management
- **Error Handling**: Graceful fallback when database unavailable

#### Market Data Integration  
- **Primary Source**: PostgreSQL `market_data` and `technical_indicators` tables
- **Fallback Strategy**: Static base prices for development
- **Data Freshness**: Use most recent available data, note timestamp
- **Error Handling**: Clear indication of data source and quality

#### Python Integration
- **Execution Method**: Node.js spawn Python processes
- **Code Reuse**: Leverage existing `db_manager` and market data code
- **Path Management**: Proper Python path configuration
- **Error Handling**: Capture Python stderr and provide meaningful errors

---

## Non-Functional Requirements

### Performance
- **Tool Response Time**: < 5 seconds for any single tool call
- **Database Queries**: < 2 seconds for memory search
- **Python Integration**: < 3 seconds for market data retrieval  
- **Concurrent Requests**: Support 3+ simultaneous tool calls

### Reliability  
- **Uptime Target**: 99% availability during development/testing
- **Error Handling**: No tool call should crash the MCP server
- **Graceful Degradation**: Provide fallback responses when services unavailable
- **Recovery**: Automatic restart capability

### Security
- **Database Access**: Use existing credentials and connection security
- **Input Validation**: Sanitize all user inputs before Python execution
- **Error Messages**: Don't expose sensitive system information
- **Network**: Local-only operation (localhost binding)

### Monitoring
- **Logging**: Console logging of all tool calls with timestamps
- **Health Check**: HTTP GET endpoint for server status
- **Error Tracking**: Log all errors with context information
- **Performance Metrics**: Track tool execution times

---

## Implementation Plan

### Phase 1: Core MCP Server (Week 1)
**Goal**: Basic MCP server with 3 working tools

**Tasks**:
1. **Create MCP server structure** (`mcp-server/trading-mcp-server.js`)
2. **Implement tool handlers** for all 3 tools with Python integration
3. **Database integration** using existing connection.py
4. **Basic error handling** and logging
5. **Health check endpoint** for monitoring

**Deliverables**:
- Working MCP server on port 3001
- All 3 tools respond to test calls
- Basic logging and health monitoring

**Success Criteria**:
- Server starts without errors
- Tools return valid JSON responses
- Database connection established
- Python integration working

### Phase 2: Claude Code Integration (Week 2)  
**Goal**: Register with Claude Code and test trading conversations

**Tasks**:
1. **Register MCP server** with Claude Code CLI
2. **Test individual tools** through Claude Code interface
3. **Test complete trading conversation** flow
4. **Debug integration issues** and improve error handling
5. **Performance optimization** and response time improvements

**Deliverables**:
- MCP server registered with Claude Code
- Successful trading conversation examples
- Performance benchmarks
- Integration troubleshooting guide

**Success Criteria**:
- Claude Code can call all 3 tools successfully
- Complete trading conversation works end-to-end
- Response times meet requirements
- Stable performance over multiple conversations

### Phase 3: Documentation & Testing (Week 3)
**Goal**: Production-ready documentation and testing suite

**Tasks**:
1. **Complete setup documentation** with step-by-step instructions
2. **Create testing guide** for MCP server validation
3. **Performance monitoring** and optimization
4. **Error scenario testing** and improved fallbacks
5. **User experience refinement** based on testing

**Deliverables**:
- Complete setup and testing documentation
- Performance benchmarks and optimization
- Comprehensive error handling
- User experience improvements

**Success Criteria**:
- New developers can set up MVP following documentation
- All error scenarios handled gracefully
- Performance meets all requirements
- User experience is smooth and natural

---

## Success Metrics & KPIs

### Functional Metrics
- **✅ Tool Success Rate**: 95%+ successful tool calls
- **✅ Database Integration**: 100% database operations work correctly
- **✅ Memory Persistence**: Trading insights stored and retrievable
- **✅ Complete Conversations**: Full trading recommendation cycle working

### Performance Metrics  
- **⚡ Response Time**: < 5 seconds for complete trading conversation
- **⚡ Database Queries**: < 2 seconds average
- **⚡ Market Data**: < 3 seconds retrieval time
- **⚡ Memory Storage**: < 1 second insertion time

### User Experience Metrics
- **💬 Conversation Flow**: Natural language trading conversations
- **🧠 Learning**: Relevant memories retrieved in subsequent conversations  
- **🔄 Iteration**: Ability to refine recommendations through follow-up questions
- **📈 Value**: Actionable trading insights with specific entry/exit levels

### Technical Metrics
- **🔧 Error Rate**: < 5% tool call failures  
- **📊 Uptime**: 99%+ server availability
- **🔄 Recovery**: < 30 seconds to restart after failures
- **📝 Logging**: Complete audit trail of all trading conversations

---

## Risk Assessment & Mitigation

### High Risk Items

#### 1. Python Integration Complexity
**Risk**: Node.js ↔ Python process spawning may be unreliable  
**Impact**: Tool calls fail, breaking trading conversations  
**Mitigation**: 
- Comprehensive error handling with timeouts
- Fallback responses when Python scripts fail
- Process monitoring and automatic restart
- Extensive testing of Python path and dependencies

#### 2. Database Connection Stability  
**Risk**: PostgreSQL connection failures break memory functionality  
**Impact**: No memory storage/retrieval, conversations lose context  
**Mitigation**:
- Connection retry logic with exponential backoff
- Graceful fallback to static trading principles  
- Health check monitoring of database status
- Clear error messages about database state

#### 3. Claude Code MCP Integration
**Risk**: MCP protocol changes or Claude Code compatibility issues  
**Impact**: Complete system failure, no Claude Code integration  
**Mitigation**:
- Follow official MCP protocol specifications exactly
- Test with multiple Claude Code versions
- Maintain compatibility with MCP protocol updates
- Fallback to direct API calls if MCP fails

### Medium Risk Items

#### 4. Performance Under Load
**Risk**: Slow response times hurt user experience  
**Impact**: Frustrating trading conversations, abandoned usage  
**Mitigation**:
- Performance benchmarking and optimization
- Caching of frequently accessed data
- Async processing where possible
- Load testing before production use

#### 5. Data Quality and Freshness
**Risk**: Stale or incorrect market data leads to bad recommendations  
**Impact**: Poor trading advice, user distrust  
**Mitigation**:
- Clear timestamps on all data sources
- Data freshness validation and warnings
- Multiple data source fallbacks
- Explicit data quality indicators in responses

### Low Risk Items

#### 6. Development Environment Setup
**Risk**: Complex setup process blocks adoption  
**Impact**: Developers can't contribute or test system  
**Mitigation**:
- Comprehensive documentation with examples
- Automated setup scripts where possible
- Docker containerization for consistent environments
- Troubleshooting guide for common issues

---

## Future Enhancements (Post-MVP)

### Phase 4: Advanced Tools
- `place_order` - IBKR broker integration for actual trading
- `get_portfolio_analysis` - Current positions and risk metrics
- `calculate_position_sizing` - Risk management and position sizing
- `analyze_technical_indicators` - Advanced technical analysis

### Phase 5: Specialized Subagents
- `@price-analyst` - Technical analysis specialist subagent
- `@risk-manager` - Position sizing and risk assessment subagent  
- `@sentiment-scanner` - News and market sentiment analysis subagent
- `@portfolio-manager` - Multi-position portfolio optimization subagent

### Phase 6: Advanced Features
- Real-time market data integration (IBKR subscription)
- Options chain analysis and strategies
- Backtesting and performance analytics
- Multi-timeframe analysis (5min, 15min, 1hr, daily)
- Integration with news and sentiment data sources

---

## Conclusion

This MVP creates the foundation for the world's first Claude Code native trading platform. By implementing 3 essential MCP tools, we enable complete trading conversations with persistent memory - transforming Claude Code into a sophisticated trading advisor.

The success of this MVP validates the core concept and provides the platform for advanced trading features, specialized subagents, and real-time market integration.

**Next Step**: Begin Phase 1 implementation with MCP server development and tool integration.

---

**Document Status**: ✅ Ready for Implementation  
**Review Date**: August 27, 2025  
**Approved By**: Development Team