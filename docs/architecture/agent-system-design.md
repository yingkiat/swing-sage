# Agent System Design - Swing Sage Trading Platform

## Core Concept: Claude Code as Trading Platform

Forget building traditional trading software. We're repurposing Claude Code - Anthropic's coding assistant - into a conversational trading advisor. Instead of Claude Code writing React components, it spawns trading agents that analyze markets and manage positions.

**The shift is simple but profound:**
- Traditional use: "Claude Code, build me a todo app"
- Our use: "Claude Code, find me today's best swing trade setups"

Everything happens within Claude Code's environment. The "UI" is the Claude Code chat. The "backend" is Claude Code spawning specialized agents via its SDK. The only external infrastructure is PostgreSQL for memory.

## Why Claude Code for Trading?

**Traditional Trading Platform:**
- Install TradingView, connect broker, configure scanners
- Learn complex UI, set up indicators, manage watchlists  
- Switch between apps for news, analysis, execution
- Months to become proficient

**Claude Code Trading Platform:**
- Open Claude Code, start talking
- "What's moving today?" → Instant analysis
- "Put $5k in NVDA at 885" → Position sizing calculated
- Zero learning curve - just conversation

**The Platform Advantages:**
1. **Dynamic agents** - Spawn exactly what you need per question
2. **Natural language** - No UI to learn, just chat
3. **Built-in intelligence** - Claude understands context and nuance
4. **No infrastructure** - Claude Code handles compute, you just need Postgres
5. **Instant iteration** - Modify agents on the fly through conversation

## How Claude Code Agents Work

**CRITICAL**: Use Claude Code's Task tool to spawn specialized agents, NOT traditional Python classes or LLM API calls.

When you ask a trading question, Claude Code:
1. Determines which specialist agents are needed
2. **Spawns those agents using the Task tool**
3. Each agent analyzes their specific domain using MCP tools
4. Results are synthesized into actionable advice
5. Context is persisted to PostgreSQL for memory

**Example implementation using Task tool with predefined subagents:**

```python
# This runs INSIDE Claude Code when you ask "Should I buy AAPL?"
def analyze_opportunity(ticker):
    # Use Task tool to spawn Price Action Specialist (uses .claude/agents/price-analyst.md)
    price_action = Task(
        subagent_type="price-analyst",
        description="Technical analysis",
        prompt=f"Analyze {ticker} for swing trading opportunities. Provide specific entry/exit levels and risk/reward analysis."
    )
    
    # Use Task tool to spawn Sentiment Scanner (uses .claude/agents/sentiment-scanner.md)
    sentiment = Task(
        subagent_type="sentiment-scanner",
        description="Sentiment analysis", 
        prompt=f"Analyze {ticker} news, social sentiment, and upcoming catalysts that could drive price movement."
    )
    
    # Use Task tool to spawn Risk Manager (uses .claude/agents/risk-manager.md)
    risk = Task(
        subagent_type="risk-manager",
        description="Risk assessment",
        prompt=f"Calculate position sizing for {ticker} trade with $10,000 portfolio. Include risk management plan."
    )
    
    # Synthesize results
    return create_trade_setup(price_action, sentiment, risk)
```

**Key Changes:**
- **Predefined Subagents**: Each subagent has detailed prompt in `.claude/agents/` directory
- **Simple Descriptions**: Task description is brief since subagent has full context
- **Focused Prompts**: Task prompt is specific query, subagent handles the methodology

**Key Points:**
- **Use Task tool**: Don't build Python classes, use Claude Code's native Task spawning
- **MCP Integration**: Agents access real data through MCP servers (market data, database, APIs)
- **Specialized Prompts**: Each agent has focused expertise through system prompts
- **Native Interface**: Everything happens through Claude Code conversation, not separate apps

## The Streamlined 3-Agent Architecture: Proposer → Counterer → Verdict

**Key Design Principle:** Think of trading decisions like a courtroom - you need someone to make the case (proposer), someone to challenge it (counterer), and someone to make the final judgment (verdict).

### 1. Price Analyst (The Proposer)
**Subagent Type:** `price-analyst`  
**Role:** Makes the strongest case for the directional trade (long OR short)
**Data sources:** MCP market data + Web searches (3 searches required)
**Enhanced capabilities:**
- **Technical Analysis:** Support/resistance, chart patterns, momentum indicators
- **Sentiment Analysis:** Recent news, social media buzz, analyst actions
- **Catalyst Identification:** Earnings, FDA approvals, corporate events

**Task prompt focus:**
- Combine technical setup with fundamental catalysts
- Make compelling case for direction (up/down) with specific levels
- Use 3 web searches for recent news and sentiment context
- Provide entry/exit recommendations with conviction scores

**Example spawn:**
```python
Task(
    subagent_type="price-analyst",
    description="Analyze NVDA setup",
    prompt="Analyze NVDA using MCP market data and web searches. Combine technical analysis with recent news/sentiment. Make the strongest case for directional trade with specific entry/exit levels and 2-10 day timeframe."
)
```

### 2. Risk Manager (The Counterer)
**Subagent Type:** `risk-manager`  
**Role:** Devil's advocate - identifies risks and challenges the proposer
**Data sources:** MCP market data + Portfolio data + Web searches (2 available)
**Task prompt focus:**
- Challenge the price analyst's thesis with contrary evidence
- Identify risk factors and potential issues
- Calculate position sizing constraints
- Play devil's advocate on what could go wrong

**Example spawn:**
```python
Task(
    subagent_type="risk-manager",
    description="Risk assessment for NVDA trade",
    prompt="Challenge the NVDA bullish case. Identify risks, calculate position sizing for $50k account, and highlight what could invalidate the thesis. Play devil's advocate."
)
```

### 3. Trade Orchestrator (The Verdict)
**Subagent Type:** `trade-orchestrator`  
**Role:** Final judge - makes definitive decision with specific execution details
**Data sources:** Proposer + Counterer analysis + User preferences + Web searches (2 available)
**Task prompt focus:**
- **MUST provide specific execution details:**
  - Exact position size (shares/contracts, % of account)
  - Specific limit entry price (not ranges)
  - Options details: strike, expiration, current IV
  - Order type instructions
- Synthesize proposer/counterer debate into final BUY/SELL/HOLD decision
- Apply user preferences and constraints

**Example spawn:**
```python
Task(
    subagent_type="trade-orchestrator",
    description="Final NVDA trade decision",
    prompt="Based on price-analyst case and risk-manager concerns, make final NVDA trade decision. MUST include: exact position size, specific entry price, options details if applicable, stop loss, targets. User: $50k account, medium risk tolerance."
)
```

## The Claude Code Conversation Flow

### Morning Setup Session
```
You: "Good morning, scan for setups"

Claude Code: [Internally spawns all 5 agents across top 50 liquid names]
"Found 3 high-conviction setups:

1. NVDA - Coiled at 885 resistance
   - Entry: 885.50 break
   - Stop: 882.00  
   - Target: 892.00
   - Risk $350 to make $650
   
2. XOM - Bouncing off 50-day MA
   - Entry: 108.20-108.50 zone
   - Stop: 107.00
   - Target: 111.00
   - Risk $130 to make $270

Want me to set alerts for these levels?"
```

### Real-Time Analysis
```
You: "Why is TSLA dumping?"

Claude Code: [Spawns sentiment_scanner and price_analyst agents]
"TSLA down 4.2% on:
- Reuters: 'Tesla recalls 120k vehicles' (20 mins ago)
- Unusually high put volume at 240 strike
- Broke below 245 support, next level 238
- Suggestion: Wait for 238 to hold before catching knife"
```

### Position Management
```
You: "Check my open positions"

Claude Code: [Queries Postgres, spawns risk_manager agent]
"2 open positions:
- AAPL: +2.3%, approaching first target
  → Sell 1/2 at 188, trail stop to 185
  
- MSFT: -0.8%, still above stop
  → Hold, no exit signals yet

Portfolio heat: 4.2% (within 6% limit)
Correlation warning: Both are mega-cap tech"
```

## Project Structure

```
swing-sage/
├── CLAUDE.md                 # Trading behavior guidance (updated for 3-agent workflow)
├── .claude/agents/           # Streamlined agent prompt definitions
│   ├── price-analyst.md      # Technical + sentiment analysis (The Proposer)
│   ├── risk-manager.md       # Risk assessment + devil's advocate (The Counterer)
│   └── trade-orchestrator.md # Final execution details (The Verdict)
├── mcp-server/              # Market data and memory access
│   ├── trading-mcp-stdio.js # MCP protocol server
│   └── scripts/             # Python data fetching
│       └── get_market_data.py
├── docs/                    # Technical documentation
│   ├── architecture/        # System design docs
│   ├── technical/          # Troubleshooting guides
│   └── requirements/       # PRD specifications
└── schema.sql              # Database structure
```

## Performance Optimizations

**Web Search Strategy:**
- **Price-analyst**: 3 searches required for comprehensive news/sentiment coverage
- **Risk-manager**: 2 searches available for risk context when needed  
- **Trade-orchestrator**: 2 searches for critical missing information

**Workflow Efficiency:**
- **Simple queries**: Use price-analyst only (fast single-agent response)
- **Complex analysis**: Use full 3-agent workflow for comprehensive decisions
- **No data re-fetching**: Agents use provided MCP data, no Bash tools for data access

## Key Insights

- **Claude Code is the platform**, not just a tool to build platforms
- **Conversation replaces configuration** - no settings, just chat
- **Agents are ephemeral** - spawned per query, not persistent
- **Memory in Postgres** - only persistence layer needed
- **15-min delay is fine** - swing trading doesn't need real-time

## Success Metrics

- **Usability:** Non-trader can profitably trade within 1 hour
- **Performance:** >55% win rate on suggested setups
- **Reliability:** <5% hallucination rate on price levels
- **Speed:** <30 seconds per analysis query
- **Cost:** <$10/day in Claude Code API calls

## The Paradigm Shift

Traditional coding with Claude Code:
```
Human: "Build a dashboard showing stock prices"
Claude Code: [Writes React components]
```

Our approach:
```
Human: "What stocks should I buy today?"
Claude Code: [Becomes the dashboard, analyzes everything, gives specific trades]
```

We're not building software. We're turning Claude Code itself into trading software through conversation. The code Claude writes isn't the product - Claude's analysis IS the product.