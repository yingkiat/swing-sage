# Swing Sage: High-Speed Trading Platform

> **The Paradigm Shift**: Claude Code becomes your personal trading advisor through conversation with **70-80% faster responses**.

## The Concept

Instead of building traditional trading software, Swing Sage repurposes **Claude Code** (Anthropic's coding assistant) into a conversational trading platform. No UIs to learn, no complex setups—just chat with Claude Code and get specific trade recommendations.

### Traditional Trading Platform:
- Install TradingView → Connect broker → Configure scanners
- Learn complex UI → Set up indicators → Manage watchlists  
- Switch between apps for news, analysis, execution
- Months to become proficient

### Claude Code Trading Platform:
- Open Claude Code → Start chatting
- "What's moving today?" → Instant analysis
- "Put $5k in NVDA at 885" → Position sizing calculated
- Zero learning curve - just conversation

## How It Works (Performance Optimized)

When you ask a trading question, Claude Code uses **parallel execution** and **smart memory** to deliver responses in **60-90 seconds** vs the previous 5 minutes:

1. **Portfolio Strategist** - Session-level context and portfolio health assessment
2. **Market Intelligence** - Real-time IBKR data via optimized MCP tools  
3. **Smart Memory Check** - Retrieves recent analysis to avoid redundant work
4. **Parallel Analysis** - Price-analyst and risk-manager run simultaneously
5. **Trade Orchestrator** - Synthesizes parallel results into final recommendations
6. **Structured Storage** - Pre-parsed analysis stored for faster future retrieval

```python
# This runs when you ask "Should I buy AAPL?"
analysis = await claude_trading_platform.analyze_market_opportunity("Should I buy AAPL?")

# Claude Code returns:
{
  "primary_recommendation": {
    "symbol": "AAPL", 
    "action": "BUY",
    "entry_zone": "188.50-189.00",
    "stop_loss": "185.00",
    "target": "195.00",
    "position_size": "$5,000 (50 shares)",
    "reasoning": "Bouncing off 50-day MA with volume confirmation..."
  },
  "confidence_level": 8,
  "risk_analysis": {...},
  "alternative_setups": [...]
}
```

## Quick Start

### 1. Database Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/swing_sage

# Initialize database
python setup_database.py
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Keys (Optional)
```bash
# Add to .env for real LLM analysis
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 4. Start Trading with Claude Code
```python
from core.claude_orchestrator import claude_trading_platform

# Start a session
session_id = claude_trading_platform.start_session("morning-scan")

# Ask for trading opportunities
analysis = await claude_trading_platform.analyze_market_opportunity(
    "Find me the best swing trade setup for today"
)

print(analysis["analysis"]["primary_recommendation"])
```

## Core Components

### Market Intelligence (`market_data/`)
- **YFinance Provider**: Real-time market data from Yahoo Finance
- **Technical Analysis**: RSI, MACD, EMA calculations  
- **Multi-Symbol Screening**: Analyzes AMD, MSFT, GOOGL, AMZN simultaneously
- **Volume Analysis**: Compares current vs 10-day average volume

### Broker Integration (`brokers/`)
- **IBKR Adapter**: Interactive Brokers TWS/Gateway integration
- **Paper Trading**: Safe testing environment
- **Order Management**: Market/limit orders with status tracking
- **Position Tracking**: Real-time portfolio monitoring

### Claude Code Orchestrator (`core/`)
- **Market Intelligence Gathering**: Fetches data across multiple symbols
- **LLM Analysis**: GPT-4 powered comprehensive market analysis
- **Memory System**: Learns from past successful trades
- **PostgreSQL Logging**: Complete audit trail of all decisions

### Database Schema (`schema.sql`) - Performance Optimized
- **Events Table**: Unified spine with structured analysis payloads
- **Portfolio Ribs**: v_trades, v_positions, v_funding for efficient queries
- **Simplified Triggers**: JSON field access vs complex regex patterns
- **Market Data**: Real-time IBKR price and technical data via MCP
- **Technical Indicators**: RSI, MACD, moving averages with caching

## Example Conversations

### Morning Market Scan (High-Speed)
```
You: "Good morning, scan for setups"

[⚡ Response in 75 seconds via parallel analysis]

Claude Code: "📊 Portfolio health: Good (3.2% risk exposure, well diversified)

Found 3 high-conviction setups:

1. **NVDA** - Coiled at $885 resistance  
   Entry: $885.50 break | Stop: $882.00 | Target: $892.00
   Risk $350 to make $650 | Volume: 1.8x average
   
2. **AMD** - Bouncing off 50-day MA
   Entry: $140.20-$140.50 zone | Stop: $138.00 | Target: $144.00  
   Risk $200 to make $360 | Strong RSI divergence
   
3. **MSFT** - Momentum breakout
   Entry: $441.00 break | Stop: $438.50 | Target: $446.00
   Risk $250 to make $500 | Earnings catalyst next week

Want me to set position sizing for your $25k account?"
```

### Real-Time Analysis (Fast Response)
```
You: "Why is TSLA dumping?"

[⚡ Response in 45 seconds via optimized catalyst search]

Claude Code: "TSLA down 4.2% on:
- Reuters: 'Tesla recalls 120k vehicles' (20 mins ago)  
- Unusually high put volume at $240 strike
- Broke below $245 support, next level $238
- **Suggestion**: Wait for $238 to hold before catching knife
- **Alternative**: Put spread at $240/$235 if breakdown continues"
```

### Position Management
```
You: "Check my positions"

Claude Code: "2 open positions:

**AAPL**: +2.3% (Entry: $186.50, Current: $190.80)
→ Approaching first target at $192  
→ **Action**: Sell 1/2 position, trail stop to $189

**MSFT**: -0.8% (Entry: $442.00, Current: $438.50)  
→ Still above stop at $438.00
→ **Action**: Hold, watching for bounce off 20-day EMA

**Portfolio Heat**: 4.2% (within 6% limit)  
**Risk Warning**: Both positions are mega-cap tech - consider diversification"
```

## The Performance Architecture Advantage

### Traditional Approach:
```
User → UI → Database → Analysis Engine → Trading Algorithms → Broker → Results → UI → User
```

### Swing Sage High-Speed Approach:
```
User → Claude Code (parallel analysis) → Specific Trading Advice (60-90 seconds)
```

**Performance Benefits:**
- **70-80% faster responses** - Parallel execution vs sequential analysis
- **Smart memory integration** - Avoids redundant analysis when recent data exists
- **Flexible web searches** - Judgment-based searches vs forced multiple searches  
- **Structured data pipeline** - Pre-parsed analysis reduces processing overhead
- **Zero UI complexity** - Just natural language conversation  
- **Instant expertise** - Claude understands market context and nuance
- **Learning system** - Builds knowledge from successful trades with structured storage

## Event Memory System

Swing Sage uses an Event Memory System to store and retrieve trading insights, analysis, and execution records. The system automatically categorizes events by type and topic for intelligent retrieval.

### Event Types & Usage

**Event Types:**
- **analysis** - Trading analysis/recommendations from agents
- **proposal** - Trade ideas/suggestions for consideration  
- **insight** - Market observations/learnings and patterns
- **observation** - General notes/tracking and user actions

**Usage Patterns:**
```
User says "I bought 100 AAPL at $150" → observation (completed action)
Agent provides trade recommendation → proposal (trade suggestion)  
Agent shares technical analysis → analysis (analytical content)
Agent notes market pattern → insight (learning/observation)
```

**Memory Commands:**
- `"push this"` / `"save this"` / `"remember this"` → Store current analysis
- Topic-based retrieval: Events auto-categorized by symbols (AAPL, NVDA, etc.)
- Time-based filtering: Recent events vs historical analysis
- Confidence scoring: High-confidence insights prioritized

### Memory Workflow Example
```
You: "Analyze NVDA for swing trade"
Claude: [Provides comprehensive analysis]
You: "push this analysis"  
Claude: "✅ Stored analysis for topic 'NVDA' (Event ID: abc123)"

Later...
You: "What did we say about NVDA?"
Claude: [Retrieves stored NVDA analysis with context]
```

## Database Architecture

The system maintains a complete audit trail in PostgreSQL:

```sql
-- View complete analysis history
SELECT * FROM session_timeline WHERE session_id = 'your-session-id' ORDER BY event_time;

-- Check high-confidence trading memories
SELECT * FROM agent_memories WHERE memory_category = 'trading_insight' ORDER BY importance_score DESC;

-- Review market data coverage  
SELECT symbol, COUNT(*) as data_points FROM market_data GROUP BY symbol;
```

## Extending the Platform

### Adding New Data Sources:
```python
# Implement BaseMarketDataProvider
class YourProvider(BaseMarketDataProvider):
    async def get_market_data(self, symbol: str) -> MarketData:
        # Your data fetching logic
        return MarketData(...)
```

### Adding New Brokers:
```python
# Implement BrokerAdapter
class YourBroker(BrokerAdapter):
    def place_order(self, request: OrderRequest) -> Order:
        # Your order execution logic
        return Order(...)
```

### Custom Analysis Prompts:
```python
# Modify the system_prompt in claude_orchestrator.py
system_prompt = """You are Claude Code with specialized knowledge in [your strategy]..."""
```

## Success Metrics

- **Usability**: Non-trader can profitably trade within 1 hour
- **Performance**: >55% win rate on suggested setups  
- **Reliability**: <5% hallucination rate on price levels
- **Speed**: <90 seconds per complex analysis (70% improvement from 5 minutes)
- **Cost**: <$10/day in Claude Code API calls

## The Future

This is just the beginning. Imagine:

- **"Find me a covered call strategy for my AAPL position"** → Claude analyzes options chains and suggests specific strikes/expiries
- **"How did my Tesla trade from last week perform?"** → Claude retrieves the trade, analyzes the outcome, and updates its memory
- **"Market's looking shaky, should I hedge my tech exposure?"** → Claude suggests specific hedging strategies with VIX calls or inverse ETFs

**We're not building software. We're turning Claude Code itself into high-speed trading software through conversation.**

## Performance Optimization Summary

**🚀 2025 Performance Update:**
- **Response Time**: 5 minutes → 60-90 seconds (70-80% improvement)
- **Parallel Execution**: Price-analyst + risk-manager run simultaneously  
- **Smart Memory**: Avoids redundant analysis with intelligent caching
- **Flexible Searches**: Judgment-based web searches vs forced multiple searches
- **Structured Pipeline**: Pre-parsed analysis data eliminates regex processing overhead
- **Database Optimization**: Simple JSON field access vs complex trigger patterns

**Technical Improvements:**
- Enhanced `emit_event.py` with structured analysis extraction
- Simplified database triggers using structured payloads
- Updated agent configurations for optimal performance
- Parallel workflow implementation in CLAUDE.md

---

*Remember: Past performance doesn't guarantee future results. Always trade with money you can afford to lose. This platform is for educational and paper trading purposes.*