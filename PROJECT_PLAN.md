# Swing-Sage Project Plan
*Conversational Trading Platform via Claude Code*

## Executive Summary

**Vision:** Transform Claude Code into a conversational trading advisor that spawns specialized agents to analyze markets and manage positions through natural language interaction.

**Core Value Proposition:** Replace complex trading platforms with simple conversation - "What should I buy today?" gets you specific trade setups with entries, stops, and targets.

## MVP Definition (Version 1.0)

### Must-Have Features
1. **Morning Scan Workflow**
   - User: "Scan for setups"
   - Returns: 3-5 ranked trade opportunities with specific levels
   - Each setup includes: entry, stop, target, position size

2. **Individual Stock Analysis**
   - User: "Analyze AAPL" 
   - Returns: Price action, sentiment, options flow synthesis
   - Actionable recommendation: buy/sell/wait with levels

3. **Position Management**
   - User: "Check my positions"
   - Returns: Current P&L, exit recommendations, risk assessment
   - Updates stops/targets based on price action

4. **Basic Memory**
   - Remembers your open positions
   - Tracks setup performance over time
   - Learns from wins/losses

### Nice-to-Have (Future Versions)
- Real-time alerts for setup triggers
- Sector rotation analysis  
- Options strategies beyond basic put/call flow
- Integration with broker for execution
- Performance analytics dashboard

## Technical Architecture

### Core Components
```
Claude Code (Orchestrator)
├── Agent Manager - Spawns/coordinates specialist agents
├── Data Layer - IBKR API + web scraping
├── Memory Layer - PostgreSQL for persistence
└── Synthesis Engine - Combines agent outputs
```

### The Five Specialist Agents
1. **Price Action Specialist** - Technical analysis, levels, momentum
2. **Sentiment Scanner** - News, social media, catalysts
3. **Options Flow Reader** - Unusual activity, smart money positioning
4. **Relative Strength Ranker** - Sector/market comparison
5. **Risk Manager** - Position sizing, portfolio heat, correlations

### Data Sources
- **IBKR API** - 15-min delayed bars, options chains, fundamentals
- **Web Scraping** - News headlines, Reddit sentiment, earnings dates
- **PostgreSQL** - Trade setups, position history, agent conversations

## User Stories & Workflows

### Story 1: Morning Market Preparation
**As a swing trader, I want to quickly identify the best setups for the day**

**Workflow:**
1. User opens Claude Code, types: "Good morning, scan for setups"
2. Claude Code spawns all 5 agents across 50 liquid stocks
3. Agents analyze their domains in parallel
4. Results synthesized into ranked opportunities
5. User gets 3-5 specific trade setups with levels

**Success Criteria:**
- Complete scan in <60 seconds
- Each setup has entry/stop/target prices
- Win rate >55% on suggested setups

### Story 2: Individual Stock Deep Dive  
**As a trader, I want to understand why a stock is moving and whether to trade it**

**Workflow:**
1. User: "Why is NVDA up 3%?"
2. Price Action agent analyzes chart patterns
3. Sentiment agent scrapes recent news
4. Options agent checks unusual volume
5. Synthesis provides context and trade recommendation

**Success Criteria:**
- Response in <30 seconds
- Identifies key catalyst if available
- Provides specific actionable levels

### Story 3: Position Management
**As an active trader, I want to know when to exit my current positions**

**Workflow:**
1. User: "Check my open positions"
2. System queries PostgreSQL for current trades
3. Risk Manager analyzes each position vs current market
4. Updates stop losses and profit targets
5. Flags overconcentration or correlation risks

**Success Criteria:**
- Shows real-time P&L for each position
- Updates stops based on price action
- Warns of portfolio risk violations

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal:** Basic Claude Code environment with single agent

**Tasks:**
- [ ] Set up PostgreSQL database with core schema
- [ ] Create IBKR API connection wrapper
- [ ] Build Price Action Specialist agent
- [ ] Test end-to-end: query → agent → response
- [ ] Implement basic conversation memory

**Deliverable:** Can ask "Analyze AAPL" and get price action analysis

### Phase 2: Multi-Agent System (Week 2-3)
**Goal:** All 5 specialists working in coordination

**Tasks:**
- [ ] Build remaining 4 specialist agents
- [ ] Create agent orchestration logic
- [ ] Implement parallel agent execution
- [ ] Build synthesis engine for combining outputs
- [ ] Add position tracking to database

**Deliverable:** Complete "scan for setups" workflow

### Phase 3: Conversation Interface (Week 4)
**Goal:** Natural language intent parsing and context

**Tasks:**
- [ ] Build intent recognition for common queries
- [ ] Implement conversation context management
- [ ] Add position management workflows
- [ ] Create alert system for setup triggers
- [ ] Refine agent prompts based on testing

**Deliverable:** Fully conversational trading advisor

### Phase 4: Learning & Optimization (Week 5-6)
**Goal:** Performance tracking and continuous improvement

**Tasks:**
- [ ] Implement trade outcome tracking
- [ ] Build performance analytics
- [ ] Create agent prompt optimization based on results
- [ ] Add risk management guardrails
- [ ] Performance testing and reliability improvements

**Deliverable:** Production-ready trading advisor

## Success Metrics

### User Experience
- **Learning Curve:** Non-trader profitable within 1 hour
- **Response Time:** <30 seconds for analysis queries
- **Usability:** 90% of common queries understood correctly

### Trading Performance  
- **Win Rate:** >55% on suggested setups
- **Risk Management:** Portfolio heat stays within defined limits
- **Reliability:** <5% hallucination rate on price levels

### Technical Performance
- **Uptime:** 99% availability during market hours
- **Cost:** <$10/day in Claude Code API calls
- **Data Quality:** Real-time sync with IBKR, <1min data lag

## Risk Assessment

### High Risk Items
1. **Claude Code API Reliability** - Platform dependency
   - *Mitigation:* Build fallback for critical functions
2. **IBKR Data Quality** - 15-min delay may miss fast moves  
   - *Mitigation:* Focus on swing trades, not scalping
3. **Agent Hallucination** - Wrong price levels could cause losses
   - *Mitigation:* Validation layers, confidence scoring

### Medium Risk Items  
1. **Market Regime Changes** - Agents trained on current market
   - *Mitigation:* Regular prompt updates, performance monitoring
2. **Cost Escalation** - Heavy API usage
   - *Mitigation:* Caching, request optimization
3. **Regulatory Compliance** - Trading advice implications
   - *Mitigation:* Clear disclaimers, educational framing

### Low Risk Items
1. **PostgreSQL Performance** - Standard database scaling
2. **Web Scraping Reliability** - Multiple source fallbacks
3. **User Interface** - Claude Code handles conversation naturally

## Decision Framework

### Technical Decisions
- **Python over JavaScript** - Better AI/ML ecosystem
- **PostgreSQL over MongoDB** - ACID compliance for financial data  
- **IBKR over other brokers** - Best API for retail access
- **15-min delay over real-time** - Cost vs. swing trading needs

### Product Decisions  
- **Conversation over GUI** - Leverages Claude Code strengths
- **Synthesis over raw data** - User wants decisions, not data
- **Swing focus over day trading** - Matches data frequency
- **Education over execution** - Regulatory simplicity

## Next Actions

### Immediate (This Week)
1. Review and approve this plan
2. Set up development environment
3. Create PostgreSQL database with schema
4. Build IBKR connection wrapper
5. Start with Price Action Specialist agent

### Dependencies & Blockers
- IBKR API credentials and approval
- PostgreSQL instance setup
- Claude Code environment configuration
- Market data subscription costs

### Resource Requirements
- Development time: 40-50 hours over 6 weeks
- Claude Code API costs: ~$200-400/month estimated
- IBKR market data: $1-4/month per exchange
- PostgreSQL hosting: $20-50/month

---

**Next Step:** Review this plan and confirm MVP scope before beginning Phase 1 implementation.