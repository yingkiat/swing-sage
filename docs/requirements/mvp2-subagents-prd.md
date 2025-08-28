# Swing Sage MVP2 - Custom Trading Subagents PRD

**Version:** 1.0  
**Date:** August 27, 2025  
**Status:** Draft  
**Prerequisite:** MVP1 MCP Server must be completed  
**Author:** Claude Code Development Team

---

## Executive Summary

### Vision
Create specialized AI trading agents within Claude Code that collaborate to provide sophisticated trading analysis through natural @ mention conversations.

### Mission Statement  
Transform Claude Code into a multi-agent trading desk where specialized AI agents (@price-analyst, @risk-manager) work together using shared MCP tools to provide institutional-quality trading recommendations.

### Success Metrics
- **Multi-Agent Conversations**: Natural @mention collaboration between specialized agents
- **Specialized Expertise**: Each agent demonstrates deep domain knowledge in their area
- **Tool Integration**: Agents seamlessly use MVP1 MCP tools for data access
- **User Experience**: Feels like chatting with a team of expert traders

---

## Product Overview

### What We're Building
**2 Specialized Trading Subagents** that use MVP1 MCP tools:

1. **@price-analyst** - Technical analysis and market data specialist
2. **@risk-manager** - Position sizing and risk assessment specialist

### Core User Journey
```
User: "I'm considering NVDA at $885. What do you think?"

@price-analyst: [Uses get_market_data('NVDA')] [Uses query_trading_memories('NVDA technical')] 
"NVDA is breaking resistance at $885 with 2.1x volume. RSI at 64 shows momentum without being overbought. Historical patterns suggest targets at $895-900. This matches our May 15th analysis of similar setups."

@risk-manager: [Uses query_trading_memories('NVDA position sizing')] [Uses get_market_data('NVDA')] 
"With NVDA at $885 entry, I recommend $880 stop loss ($5 risk per share). For a $50K account with 2% risk, position size should be 200 shares ($177K notional). However, this represents high concentration - consider reducing to 100 shares for better portfolio balance."

User: "What if we wait for a pullback?"

@price-analyst: "Key support is at $875-$878. If we get a pullback to that zone with volume drying up, it would offer a better risk/reward setup with $873 stop loss."

@risk-manager: "Pullback entry at $875 improves our risk/reward from 1.8:1 to 2.5:1. Would allow 250 shares with same $1000 risk budget. I'd wait for the pullback."
```

### Why Custom Subagents
- **Specialized Expertise**: Each agent has focused domain knowledge and reasoning patterns
- **Natural Collaboration**: @mention workflow feels like consulting with expert team
- **Persistent Context**: Agents remember their analysis within conversations
- **Tool Leverage**: Agents use MVP1 infrastructure (get_market_data, query/store_trading_memories)
- **Scalable**: Easy to add new specialists (@sentiment-scanner, @options-strategist, etc.)

---

## Technical Requirements

### Architecture Overview
```
User ↔ Claude Code Interface
    ↓
@price-analyst ←→ @risk-manager (Agent Collaboration)
    ↓
MVP1 MCP Tools (get_market_data, query_trading_memories, store_trading_memory)
    ↓
PostgreSQL + Market Data Infrastructure
```

### Subagent Specifications

#### 1. @price-analyst Subagent
**Purpose**: Technical analysis and price action specialist

**Core Expertise**:
- Technical indicator interpretation (RSI, MACD, EMA, volume)
- Chart pattern recognition (breakouts, support/resistance, trends)  
- Price level identification (entry, target, stop loss recommendations)
- Historical pattern matching using trading memories
- Market momentum and trend analysis

**Tool Usage Patterns**:
- **get_market_data**: Always requests current price, volume, technical indicators
- **query_trading_memories**: Searches for similar setups, price patterns, technical analysis
- **store_trading_memory**: Saves technical analysis and price level insights

**Personality & Communication Style**:
- Analytical and data-driven
- Focuses on charts, patterns, and technical evidence
- Provides specific price levels and technical reasoning
- References historical precedents from memory database
- Acknowledges uncertainty and multiple scenarios

**Sample System Prompt**:
```
You are @price-analyst, a technical analysis expert specializing in swing trading setups. 

CORE EXPERTISE:
- Technical indicator interpretation (RSI, MACD, EMA, volume analysis)
- Support/resistance level identification  
- Chart pattern recognition (breakouts, pullbacks, trend continuations)
- Price action analysis and momentum assessment
- Risk/reward calculations based on technical levels

TOOL USAGE:
- Always get current market data before analysis
- Search trading memories for similar technical setups
- Store your analysis insights for future reference
- Focus on actionable price levels (entry, stop, target)

COMMUNICATION STYLE:
- Lead with current technical picture
- Reference specific price levels and indicators  
- Acknowledge multiple scenarios and probabilities
- Use historical context from trading memories
- Collaborate respectfully with @risk-manager

EXAMPLE RESPONSE PATTERN:
"[Current technical analysis] Based on [specific indicators], I see [pattern/setup]. Key levels are [entry/stop/target]. This resembles [historical context from memories]. [Risk/reward assessment]."
```

#### 2. @risk-manager Subagent  
**Purpose**: Position sizing, risk assessment, and portfolio management specialist

**Core Expertise**:
- Position sizing calculations (% risk, dollar risk, share quantity)
- Risk/reward ratio analysis and optimization
- Portfolio concentration and correlation assessment
- Stop loss placement and trade management
- Account risk management and drawdown prevention

**Tool Usage Patterns**:
- **get_market_data**: Focuses on volatility, correlation data, portfolio context
- **query_trading_memories**: Searches for risk management lessons, position sizing examples
- **store_trading_memory**: Saves risk management insights and position sizing rules

**Personality & Communication Style**:
- Conservative and risk-focused
- Quantitative approach with specific calculations
- Always considers portfolio impact and concentration risk
- Challenges aggressive positions constructively
- Emphasizes capital preservation

**Sample System Prompt**:
```
You are @risk-manager, a risk management and position sizing specialist.

CORE EXPERTISE:
- Position sizing based on account risk tolerance (typically 1-2% per trade)
- Risk/reward ratio calculation and optimization
- Stop loss placement and trade management strategies
- Portfolio risk assessment (concentration, correlation, overall exposure)
- Capital preservation and drawdown management

TOOL USAGE:
- Get market data to assess volatility and risk metrics
- Search memories for similar risk scenarios and lessons learned
- Store risk management insights and position sizing rules
- Focus on portfolio impact and risk optimization

COMMUNICATION STYLE:
- Lead with risk assessment and position sizing calculations
- Provide specific share quantities and dollar risk amounts
- Consider portfolio context and concentration limits
- Challenge risky positions constructively
- Emphasize capital preservation alongside profit potential

EXAMPLE RESPONSE PATTERN:
"For [entry price] with [stop loss], risk per share is $[X]. With [account size] and [risk %], I recommend [share quantity]. However, [portfolio considerations]. Consider [risk optimization suggestions]."
```

### Agent Collaboration Framework

#### Natural @Mention Workflow
- Users can address specific agents: `@price-analyst what's AAPL setup?`
- Agents can reference each other: `I agree with @risk-manager's position sizing`
- Multi-agent discussions: Both agents contribute to complex decisions
- Context sharing: Agents see previous responses in conversation

#### Decision Making Process
```
1. User asks trading question
2. @price-analyst provides technical analysis (uses MCP tools)
3. @risk-manager provides risk assessment (uses MCP tools)  
4. Agents collaborate on final recommendation
5. Both agents store insights via store_trading_memory
```

#### Conflict Resolution
- Agents acknowledge disagreements professionally
- Present multiple scenarios when views differ
- Defer to user preference when agents disagree
- Learn from outcomes through memory storage

---

## Implementation Requirements

### Claude Code Subagent Creation

#### Agent Creation Commands
```bash
# Create price analyst subagent
claude agents create price-analyst \
  --description "Technical analysis and price action specialist for swing trading" \
  --tools "get_market_data,query_trading_memories,store_trading_memory" \
  --prompt-file "./agents/price-analyst-prompt.md"

# Create risk manager subagent  
claude agents create risk-manager \
  --description "Position sizing and risk assessment specialist" \
  --tools "get_market_data,query_trading_memories,store_trading_memory" \
  --prompt-file "./agents/risk-manager-prompt.md"
```

#### Agent Configuration Files
**Required Files**:
- `agents/price-analyst-prompt.md` - Complete system prompt and expertise definition
- `agents/risk-manager-prompt.md` - Risk management focused system prompt
- `agents/agent-config.yaml` - Configuration for tool permissions and collaboration rules

**Directory Structure**:
```
swing-sage/
├── agents/
│   ├── price-analyst-prompt.md
│   ├── risk-manager-prompt.md  
│   └── agent-config.yaml
├── mcp-server/
│   └── trading-mcp-server.js (from MVP1)
```

### Integration Requirements

#### MVP1 Dependency
- **Prerequisite**: MVP1 MCP server must be running and registered with Claude Code
- **Tool Access**: Both agents must have access to all 3 MCP tools
- **Data Consistency**: Agents share same PostgreSQL memory database
- **Performance**: MCP tools must handle concurrent agent requests

#### Conversation Context
- **Shared Memory**: Both agents can see entire conversation history
- **Context Persistence**: Agent analysis persists across multiple exchanges
- **Tool Results Sharing**: When one agent calls get_market_data, results available to other agent
- **Memory Coordination**: Agents don't duplicate memory storage unnecessarily

---

## Non-Functional Requirements

### Performance
- **Agent Response Time**: < 8 seconds for complete analysis (including MCP tool calls)
- **Multi-Agent Conversations**: < 15 seconds for full @price-analyst + @risk-manager collaboration
- **Tool Call Efficiency**: Minimize redundant MCP tool calls between agents
- **Concurrent Usage**: Support multiple users with agent conversations simultaneously

### User Experience
- **Natural Language**: Agents respond conversationally, not like APIs
- **Personality Consistency**: Each agent maintains consistent expertise and communication style
- **Collaboration Quality**: Agents reference each other's analysis appropriately
- **Error Handling**: Graceful degradation when MCP tools unavailable

### Reliability
- **Agent Availability**: 99% uptime for agent interactions
- **Tool Integration**: Robust handling of MCP tool failures
- **Context Preservation**: Agent conversations survive tool failures
- **Learning Continuity**: Memory storage doesn't block agent responses

---

## Success Metrics & KPIs

### User Experience Metrics
- **💬 Natural Conversations**: Users address agents by @mention naturally
- **🤝 Agent Collaboration**: Agents reference each other's analysis appropriately
- **🎯 Specialized Value**: Each agent provides unique insights in their domain
- **⚡ Response Quality**: Agents provide actionable, specific trading recommendations

### Technical Metrics
- **🔧 Agent Success Rate**: 95%+ successful agent interactions
- **📊 Tool Integration**: 98%+ successful MCP tool calls from agents
- **🕐 Performance**: Mean response time meets requirements
- **💾 Memory Quality**: Relevant insights stored and retrieved effectively

### Business Metrics
- **📈 User Engagement**: Users return for multiple trading conversations
- **🎯 Recommendation Quality**: Specific, actionable trade setups provided
- **🧠 Learning Evidence**: Agents reference historical insights appropriately
- **🔄 Workflow Adoption**: Users naturally use @mention workflow

---

## Implementation Plan

### Phase 1: Agent Prompts & Configuration (Week 1)
**Goal**: Create specialized agent prompts and configuration files

**Tasks**:
1. **Write detailed system prompts** for @price-analyst and @risk-manager
2. **Create agent configuration files** with tool permissions and collaboration rules
3. **Test prompts individually** using Claude Code playground or API
4. **Refine agent personalities** and communication styles
5. **Validate tool usage patterns** in prompts

**Deliverables**:
- `agents/price-analyst-prompt.md` - Complete system prompt
- `agents/risk-manager-prompt.md` - Complete system prompt  
- `agents/agent-config.yaml` - Configuration file
- Prompt testing results and refinements

**Success Criteria**:
- Agents demonstrate distinct personalities and expertise
- Tool usage patterns align with requirements
- Prompts produce consistent, high-quality responses
- Agent collaboration framework is clear

### Phase 2: Subagent Creation & Testing (Week 2)
**Goal**: Create actual subagents in Claude Code and test basic functionality

**Tasks**:
1. **Create subagents using Claude CLI** with prompt files
2. **Test individual agent functionality** with simple queries
3. **Verify MCP tool integration** - agents successfully call get_market_data, etc.
4. **Test agent @mention workflow** - addressing specific agents
5. **Debug integration issues** and refine configurations

**Deliverables**:
- Working @price-analyst and @risk-manager subagents registered in Claude Code
- Test cases demonstrating individual agent capabilities
- Integration testing results with MVP1 MCP tools
- Bug fixes and configuration improvements

**Success Criteria**:
- Both agents respond appropriately to @mentions
- Agents successfully use all 3 MCP tools
- Individual agent expertise is clearly demonstrated
- No critical integration issues blocking functionality

### Phase 3: Multi-Agent Collaboration (Week 3)
**Goal**: Enable natural collaboration between agents in trading conversations

**Tasks**:
1. **Test multi-agent conversations** with both agents contributing
2. **Refine agent interaction patterns** and collaboration quality
3. **Optimize conversation flow** and reduce redundancy
4. **Test complex trading scenarios** requiring both agents
5. **Performance optimization** and response time improvements

**Deliverables**:
- Smooth multi-agent trading conversations
- Optimized collaboration patterns between agents
- Performance benchmarks for multi-agent scenarios
- User experience improvements based on testing
- Complete integration with MVP1 MCP infrastructure

**Success Criteria**:
- Natural conversations with both agents contributing unique value
- Agents reference each other's analysis appropriately
- Performance meets requirements for multi-agent scenarios
- Users can have complete trading conversations from question to recommendation

---

## Risk Assessment & Mitigation

### High Risk Items

#### 1. Claude Code Subagent Feature Availability
**Risk**: Custom subagents may not be available or work as expected  
**Impact**: Cannot implement multi-agent framework, falls back to single Claude Code instance  
**Mitigation**: 
- Verify subagent feature availability before implementation
- Test with simple subagents first before trading specialization
- Fallback plan: Implement prompt-switching within single Claude Code instance
- Document exact Claude Code version requirements

#### 2. Agent Prompt Engineering Complexity
**Risk**: Agents may not maintain consistent personalities or collaboration quality  
**Impact**: Poor user experience, agents provide conflicting or low-quality advice  
**Mitigation**:
- Extensive prompt testing and refinement process
- Clear role definitions and communication guidelines
- Example conversations and response patterns in prompts
- Iterative improvement based on real usage

#### 3. MCP Tool Performance Under Agent Load
**Risk**: Multiple agents calling MCP tools simultaneously may cause performance issues  
**Impact**: Slow responses, timeouts, poor user experience  
**Mitigation**:
- Performance testing with concurrent agent requests
- Optimize MCP server for multiple simultaneous tool calls
- Implement tool call caching to reduce redundant requests
- Monitor and optimize database query performance

### Medium Risk Items

#### 4. Agent Context Management
**Risk**: Agents may lose context or provide inconsistent analysis across conversation  
**Impact**: Disjointed conversations, agents contradict themselves or each other  
**Mitigation**:
- Test conversation persistence and context handling
- Implement context summarization if needed
- Clear guidelines for agents referencing previous analysis
- Monitor conversation quality over extended interactions

#### 5. User Adoption of @Mention Workflow
**Risk**: Users may not naturally adopt @mention pattern for agent interaction  
**Impact**: Reduced value proposition, agents not utilized effectively  
**Mitigation**:
- Clear onboarding and examples showing @mention usage
- Agents proactively suggest collaboration ("Let me ask @risk-manager...")
- Natural fallback when users don't use @mentions
- Documentation and tutorials demonstrating workflows

---

## Future Enhancements (Post-MVP2)

### Phase 4: Additional Specialist Agents
- **@sentiment-scanner** - News and social sentiment analysis specialist
- **@options-strategist** - Options trading and strategy specialist  
- **@portfolio-manager** - Multi-position portfolio optimization specialist
- **@macro-analyst** - Economic and market regime analysis specialist

### Phase 5: Advanced Agent Capabilities
- **Real-time market alerts** - Agents proactively notify about setup triggers
- **Backtesting integration** - Agents reference historical performance of similar setups
- **Cross-timeframe analysis** - Agents analyze multiple timeframes (5min, 1hr, daily)
- **Sector rotation insights** - Agents identify relative strength opportunities

### Phase 6: Production Trading Integration
- **Live order placement** - Integration with MVP1 place_order tool (when available)
- **Position monitoring** - Agents track and manage active positions
- **Performance attribution** - Agents learn from actual trading outcomes
- **Risk monitoring** - Real-time portfolio risk assessment and alerts

---

## Conclusion

MVP2 transforms Claude Code into a sophisticated multi-agent trading desk where specialized AI experts collaborate to provide institutional-quality analysis. By building on MVP1's MCP infrastructure, we create a natural conversation experience that feels like consulting with a team of expert traders.

The @mention workflow and specialized agent personalities create a unique user experience that demonstrates the power of Claude Code's custom subagent capabilities for domain-specific applications.

**Success enables**: Advanced multi-agent trading workflows, natural language portfolio management, and the foundation for a complete AI trading desk experience.

---

**Document Status**: ✅ Ready for Implementation (Requires MVP1 Completion)  
**Review Date**: August 27, 2025  
**Approved By**: Development Team