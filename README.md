# Swing Sage: Claude Code as a Trading Platform

> **The Paradigm Shift**: Claude Code becomes your personal trading advisor through conversation.

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

## How It Works

When you ask a trading question, Claude Code:

1. **Gathers market intelligence** - Fetches real-time data for key symbols
2. **Analyzes portfolio context** - Reviews your positions and available capital
3. **Retrieves trading memories** - Accesses insights from past successful analyses
4. **Performs comprehensive analysis** - Uses GPT-4 to synthesize everything
5. **Provides specific trades** - Entry/exit levels, position sizing, risk management
6. **Persists insights** - Stores high-confidence analysis for future learning

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

### Database Schema (`schema.sql`)
- **Agent Sessions**: Trading session tracking
- **Agent Deliberations**: Claude's reasoning and analysis
- **Agent Memories**: Long-term insights and patterns
- **Market Data**: Real-time price and technical data
- **Technical Indicators**: RSI, MACD, moving averages

## Example Conversations

### Morning Market Scan
```
You: "Good morning, scan for setups"

Claude Code: "Found 3 high-conviction setups:

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

### Real-Time Analysis  
```
You: "Why is TSLA dumping?"

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

## The Architecture Advantage

### Traditional Approach:
```
User → UI → Database → Analysis Engine → Trading Algorithms → Broker → Results → UI → User
```

### Claude Code Approach:
```
User → Claude Code (analyzes everything) → Specific Trading Advice
```

**Benefits:**
- **Zero UI complexity** - Just natural language conversation  
- **Instant expertise** - Claude understands market context and nuance
- **Dynamic analysis** - Every query spawns fresh, comprehensive analysis
- **Learning system** - Builds knowledge from successful trades
- **Complete audit trail** - Every decision logged to PostgreSQL

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
- **Speed**: <30 seconds per analysis query
- **Cost**: <$10/day in Claude Code API calls

## The Future

This is just the beginning. Imagine:

- **"Find me a covered call strategy for my AAPL position"** → Claude analyzes options chains and suggests specific strikes/expiries
- **"How did my Tesla trade from last week perform?"** → Claude retrieves the trade, analyzes the outcome, and updates its memory
- **"Market's looking shaky, should I hedge my tech exposure?"** → Claude suggests specific hedging strategies with VIX calls or inverse ETFs

**We're not building software. We're turning Claude Code itself into trading software through conversation.**

---

*Remember: Past performance doesn't guarantee future results. Always trade with money you can afford to lose. This platform is for educational and paper trading purposes.*