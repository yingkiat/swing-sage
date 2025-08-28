# System Overview

## High-Level Architecture

Swing Sage is a **conversation-driven trading analysis platform** that uses Large Language Models (LLMs) to provide sophisticated market analysis through natural language interaction.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     User        │    │   Claude Code    │    │    Swing Sage   │
│  (You asking    │───▶│  (As an IDE/     │───▶│   (This system  │
│   questions)    │    │   Assistant)     │    │   we've built)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Swing Sage Architecture                       │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Conversation    │  │  Market Data     │  │    Broker       │ │
│  │   Interface     │  │   Providers      │  │  Integration    │ │
│  │                 │  │                  │  │                 │ │
│  │ • Natural Lang  │  │ • Yahoo Finance  │  │ • IBKR API      │ │
│  │ • Context Mgmt  │  │ • Technical Calc │  │ • Paper Trading │ │
│  │ • Session State │  │ • Multi-Symbol   │  │ • Order Mgmt    │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 ▼                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               LLM Analysis Engine (GPT-4/Claude)           │ │
│  │                                                             │ │
│  │ • Synthesizes market data + portfolio + memories           │ │
│  │ • Provides specific trading recommendations                 │ │
│  │ • Calculates position sizing and risk management          │ │
│  │ • Explains reasoning in natural language                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                 │                               │
│                                 ▼                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 PostgreSQL Database                         │ │
│  │                                                             │ │
│  │ • Session & conversation history                            │ │
│  │ • Market data cache                                         │ │  
│  │ • Trading analysis memories                                 │ │
│  │ • Complete audit trail                                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Conversation Interface (`core/claude_orchestrator.py`)

The main orchestrator that handles natural language queries and coordinates all system components.

**Key Methods:**
- `analyze_market_opportunity(user_query)` - Main entry point for trading questions
- `gather_market_intelligence()` - Fetches data across multiple symbols  
- `perform_claude_analysis()` - Uses GPT-4 to analyze everything and provide recommendations

**Example Flow:**
```python
# User asks: "What's the best swing trade today?"
analysis = await claude_trading_platform.analyze_market_opportunity(
    "What's the best swing trade today?"
)

# System:
# 1. Fetches market data for [NVDA, AMD, MSFT, GOOGL, AAPL, TSLA]
# 2. Gets portfolio context (cash, positions, risk limits)
# 3. Retrieves relevant memories from past successful analyses
# 4. Prompts GPT-4 with comprehensive context
# 5. Returns specific trade recommendation with entry/exit levels
```

### 2. Market Data System (`market_data/`)

Provides real-time and historical market data from multiple sources.

**Components:**
- `YFinanceProvider` - Yahoo Finance integration for free market data
- `MarketData` models - Structured data representations  
- Technical analysis calculations (RSI, MACD, moving averages)
- Multi-symbol screening and comparison

**Data Flow:**
```
Yahoo Finance API → YFinanceProvider → MarketData objects → PostgreSQL cache → LLM Analysis
```

### 3. Broker Integration (`brokers/`)

Handles order execution and portfolio management.

**Current Implementation:**
- `IBKRBroker` - Interactive Brokers TWS/Gateway integration
- Paper trading support for safe testing
- Order management with status tracking
- Position and account information retrieval

**Future Brokers:**
- Schwab, Fidelity, E*TRADE adapters could be added using the same `BrokerAdapter` interface

### 4. LLM Analysis Engine (`core/llm_utils.py`)

Powers the intelligent analysis using GPT-4 or Claude.

**Capabilities:**
- Synthesizes market data, portfolio context, and historical insights
- Provides specific trading recommendations with reasoning
- Calculates position sizing based on risk tolerance
- Explains market analysis in natural language
- Learns from successful trades through the memory system

**Example Prompt Structure:**
```
System: You are a sophisticated trading platform providing specific, actionable advice...

User Query: "Should I buy AAPL?"

Market Data: [Real-time data for 6 symbols with technical indicators]
Portfolio: [Current positions, available cash, risk limits]
Memories: [Past successful AAPL analyses and outcomes]

→ Provide specific entry/exit levels, position sizing, and risk analysis
```

### 5. Memory & Learning System (`core/postgres_manager.py`)

PostgreSQL-based system that stores and retrieves trading insights.

**Tables:**
- `agent_sessions` - Trading sessions and conversation history
- `agent_deliberations` - LLM analysis and reasoning
- `agent_memories` - Long-term insights from successful trades
- `market_data` - Cached market data and technical indicators

**Memory Types:**
- **Short-term**: Current market context, recent positions
- **Long-term**: Strategy insights, pattern recognition  
- **Episodic**: Specific trade narratives and outcomes

## Data Flow Example

Here's what happens when you ask: **"Find me a swing trade for $5000"**

```
1. User Query Processing
   ├─ Start/resume trading session
   ├─ Parse intent: swing trade, $5000 budget
   └─ Initialize context

2. Market Intelligence Gathering  
   ├─ Fetch real-time data: NVDA, AMD, MSFT, GOOGL, AAPL, TSLA
   ├─ Calculate technical indicators: RSI, MACD, EMA
   ├─ Screen for momentum and volume patterns
   └─ Cache data in PostgreSQL

3. Portfolio Context Analysis
   ├─ Get current positions and cash balance
   ├─ Calculate available risk budget
   ├─ Check correlation with existing positions
   └─ Review recent trading activity

4. Memory Retrieval
   ├─ Search for relevant swing trade insights
   ├─ Find successful $5000 position examples
   ├─ Retrieve market pattern memories
   └─ Access sector-specific knowledge

5. LLM Analysis (GPT-4)
   ├─ Process comprehensive context
   ├─ Identify best setup from screened symbols
   ├─ Calculate optimal position size
   ├─ Determine entry/exit levels and stops
   └─ Generate natural language explanation

6. Response & Learning
   ├─ Return specific trade recommendation
   ├─ Log analysis and reasoning to database
   ├─ Create memory if high confidence (>70%)
   └─ Update session context for follow-ups
```

## Why This Architecture Works

### 1. **Natural Language Interface**
No complex UIs to learn. Just ask questions in plain English.

### 2. **Comprehensive Context**  
Every analysis considers market data, portfolio state, and historical insights together.

### 3. **Specific Recommendations**
Not generic advice - exact entry prices, stop levels, and position sizes.

### 4. **Learning System**
Gets smarter over time by remembering what worked in similar market conditions.

### 5. **Complete Audit Trail**
Every decision and its reasoning is logged for analysis and improvement.

## Current Limitations

1. **No Real-Time UI** - Currently API/command-line based
2. **Limited to Paper Trading** - Real money execution needs more testing
3. **Single LLM Provider** - Primarily uses OpenAI GPT-4
4. **Manual Position Tracking** - No automatic P&L updates
5. **No Web Interface** - Requires Python environment to run

## Integration with Claude Code

**Reality Check**: This system doesn't actually integrate with Claude Code (Anthropic's coding assistant). 

**What we have**: A sophisticated trading analysis system that uses LLMs and could potentially be used within Claude Code as a tool/library, but it's not a native Claude Code extension.

**What's possible**: You could use this system to provide trading analysis within Claude Code sessions by importing and calling the functions, but it's not a "Claude Code becomes a trading platform" integration.

See [Claude Code Integration Reality](../technical/claude-code-integration.md) for detailed technical explanation.

---

**Next**: Review [Database Schema](./database-schema.md) to understand how data flows through the system.