# Swing Sage Documentation

Welcome to the comprehensive documentation for Swing Sage - the world's first Claude Code native trading platform.

## Revolutionary Architecture (Updated August 2025)

**Swing Sage successfully integrates with Claude Code using the July 2025 native capabilities:**

- **Streamlined 3-Agent System** for specialized trading analysis (price-analyst, risk-manager, trade-orchestrator)
- **MCP Server Integration** connecting Claude Code to real market data and PostgreSQL memories  
- **Multi-Agent Orchestration** through Claude Code's native conversation interface
- **Real-Time Trading Intelligence** through Claude Code tools and subagent collaboration

## What We Built

Swing Sage transforms Claude Code into a **sophisticated trading advisor** that:

1. **Uses natural language as the primary interface** - No complex UIs to learn
2. **Leverages LLMs (GPT-4/Claude) for market analysis** - Sophisticated reasoning about market data
3. **Maintains conversation memory in PostgreSQL** - Learns from past analyses
4. **Integrates real market data and broker APIs** - Yahoo Finance + Interactive Brokers
5. **Provides specific trading recommendations** - Not just analysis, but actionable trades

## Documentation Structure

### [Architecture](./architecture/)
- [**System Overview**](./architecture/system-overview.md) - High-level architecture and data flow
- [**Database Schema**](./architecture/database-schema.md) - PostgreSQL tables and relationships  
- [**API Integrations**](./architecture/api-integrations.md) - Market data and broker connections

### [Technical Details](./technical/)
- [**Claude Code Integration Reality**](./technical/claude-code-integration.md) - What's possible vs what we built
- [**LLM Prompting**](./technical/llm-prompting.md) - How we prompt GPT-4 for trading analysis
- [**Deployment Guide**](./technical/deployment.md) - Production setup and scaling

### [Development](./development/)
- [**Setup Guide**](./development/setup-guide.md) - Development environment setup
- [**Testing Guide**](./development/testing-guide.md) - How to test all components
- [**Extending Platform**](./development/extending-platform.md) - Adding new features and data sources

### [Trading Features](./trading/)
- [**Conversation Examples**](./trading/conversation-examples.md) - Real examples of trading conversations
- [**Risk Management**](./trading/risk-management.md) - Built-in risk controls and position sizing
- [**Memory System**](./trading/memory-system.md) - How the platform learns from successful trades

## Quick Start

1. **Read the [System Overview](./architecture/system-overview.md)** to understand the architecture
2. **Follow the [Setup Guide](./development/setup-guide.md)** to get the platform running
3. **Try the [Conversation Examples](./trading/conversation-examples.md)** to see it in action
4. **Review [Claude Code Integration Reality](./technical/claude-code-integration.md)** to understand current limitations

## Key Concepts

### Conversation-Driven Interface
Instead of complex UIs with charts and buttons, you interact through natural language:
```
User: "Find me a good swing trade setup for today"
System: [Analyzes 6 stocks, checks portfolio, reviews memories] 
        "NVDA breaking $885 resistance with volume - entry at $885.50..."
```

### LLM-Powered Analysis 
The system uses GPT-4 to synthesize:
- Real-time market data from Yahoo Finance
- Technical indicators (RSI, MACD, moving averages)
- Portfolio context and available capital
- Historical insights from past successful trades

### PostgreSQL Memory System
Every analysis, decision, and outcome is stored in PostgreSQL, creating a learning system that improves over time.

## Current Implementation Status

1. **✅ Claude Code Native Integration** - Uses July 2025 MCP server + subagents
2. **✅ Custom Trading Subagents** - price-analyst, risk-manager specialized agents
3. **✅ Conversational Interface** - Natural language through Claude Code chat
4. **🔄 MVP Phase** - `get_market_data` and `query_trading_memories` tools implemented

## Future Vision

The ultimate goal remains creating a conversation-driven trading platform that feels as natural as chatting with an expert trader. While we can't literally "turn Claude Code into a trading platform," we can build something that captures that vision through sophisticated LLM integration.

---

**Next**: Start with the [System Overview](./architecture/system-overview.md) to understand how everything fits together.