# MCP Integration Guide for Swing Sage Trading Platform

**Updated**: August 26, 2025  
**Status**: Implementation guide for July 2025 Claude Code MCP capabilities

This guide shows how to integrate Swing Sage with Claude Code using MCP (Model Context Protocol) to create a native trading platform experience.

## Overview

MCP enables Claude Code to connect directly to our existing:
- PostgreSQL database (trading memories and analysis)
- Market data providers (Yahoo Finance, IBKR)
- Broker integrations (Interactive Brokers)
- Custom trading logic and risk management

## Prerequisites

### Install Claude Code CLI
```bash
# Install globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Verify Existing Swing Sage Components
```bash
# Test database connection
python setup_database.py

# Test market data provider
python -c "
import asyncio
from market_data.providers.yfinance_provider import YFinanceProvider
provider = YFinanceProvider()
data = asyncio.run(provider.get_market_data('AAPL'))
print(f'AAPL: ${float(data.current_price):.2f}' if data else 'Market data failed')
"
```

## MCP Server Implementation

### 1. Create Trading MCP Server

Create `trading-mcp-server.js` in the project root:

```javascript
#!/usr/bin/env node
/**
 * Swing Sage Trading MCP Server
 * Integrates existing Python trading system with Claude Code
 */

const { spawn } = require('child_process');
const path = require('path');

class TradingMCPServer {
  constructor() {
    this.projectRoot = __dirname;
  }

  async handleRequest(method, params) {
    try {
      switch (method) {
        case 'get_market_data':
          return await this.getMarketData(params.symbols);
        
        case 'query_trading_memories':
          return await this.queryTradingMemories(params.query, params.limit);
        
        case 'analyze_technical_indicators':
          return await this.analyzeTechnicalIndicators(params.symbol);
        
        case 'get_portfolio_analysis':
          return await this.getPortfolioAnalysis();
        
        case 'search_news_sentiment':
          return await this.searchNewsSentiment(params.symbols);
        
        case 'calculate_position_sizing':
          return await this.calculatePositionSizing(params);
        
        default:
          throw new Error(`Unknown method: ${method}`);
      }
    } catch (error) {
      return {
        error: true,
        message: error.message,
        method: method
      };
    }
  }

  async getMarketData(symbols) {
    const pythonScript = `
import asyncio
import json
from market_data.providers.yfinance_provider import YFinanceProvider

async def get_data():
    provider = YFinanceProvider()
    symbols = ${JSON.stringify(symbols)}
    results = {}
    
    for symbol in symbols:
        try:
            data = await provider.get_market_data(symbol)
            if data:
                results[symbol] = {
                    'current_price': float(data.current_price),
                    'change_percent': float(data.change_percent),
                    'volume': data.volume,
                    'volume_ratio': data.volume_ratio,
                    'timestamp': data.timestamp.isoformat()
                }
            else:
                results[symbol] = {'error': 'No data available'}
        except Exception as e:
            results[symbol] = {'error': str(e)}
    
    return results

result = asyncio.run(get_data())
print(json.dumps(result))
    `;

    return await this.runPythonScript(pythonScript);
  }

  async queryTradingMemories(query, limit = 5) {
    const pythonScript = `
import json
from core.postgres_manager import db_manager

# Initialize database
db_manager.initialize()

# Search memories
memories = db_manager.get_memories(
    memory_type='long_term',
    memory_category='trading_insight',
    limit=${limit}
)

# Format for Claude Code
formatted_memories = []
for memory in memories:
    formatted_memories.append({
        'title': memory['title'],
        'content': memory['content'],
        'importance_score': float(memory['importance_score']) if memory['importance_score'] else 0,
        'tags': memory['relevance_tags'] or [],
        'created_at': memory['created_at'].isoformat() if memory['created_at'] else None
    })

print(json.dumps({
    'query': '${query}',
    'memories_found': len(formatted_memories),
    'memories': formatted_memories
}))
    `;

    return await this.runPythonScript(pythonScript);
  }

  async analyzeTechnicalIndicators(symbol) {
    const pythonScript = `
import asyncio
import json
import numpy as np
from market_data.providers.yfinance_provider import YFinanceProvider

async def analyze_technical():
    provider = YFinanceProvider()
    
    # Get historical data for technical analysis
    historical = await provider.get_historical_data('${symbol}', period='3mo', interval='1d')
    
    if not historical:
        return {'error': 'No historical data available'}
    
    closes = np.array(historical['close'])
    volumes = np.array(historical['volume'])
    
    # Calculate basic indicators
    def calculate_rsi(prices, period=14):
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.convolve(gains, np.ones(period)/period, mode='valid')
        avg_losses = np.convolve(losses, np.ones(period)/period, mode='valid')
        
        rs = avg_gains / (avg_losses + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi[-1] if len(rsi) > 0 else 50
    
    def calculate_ema(prices, period):
        ema = []
        multiplier = 2 / (period + 1)
        ema.append(prices[0])
        
        for price in prices[1:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        return ema[-1]
    
    # Calculate indicators
    current_price = closes[-1]
    rsi = calculate_rsi(closes)
    ema_20 = calculate_ema(closes, 20)
    ema_50 = calculate_ema(closes, 50)
    
    # Volume analysis
    avg_volume = np.mean(volumes[-10:])
    current_volume = volumes[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
    
    # Support/resistance (simplified)
    recent_highs = np.max(closes[-20:])
    recent_lows = np.min(closes[-20:])
    
    return {
        'symbol': '${symbol}',
        'current_price': float(current_price),
        'technical_indicators': {
            'rsi': float(rsi),
            'ema_20': float(ema_20),
            'ema_50': float(ema_50),
            'volume_ratio': float(volume_ratio),
            'resistance': float(recent_highs),
            'support': float(recent_lows)
        },
        'analysis': {
            'trend': 'bullish' if current_price > ema_20 > ema_50 else 'bearish' if current_price < ema_20 < ema_50 else 'neutral',
            'momentum': 'strong' if rsi > 70 else 'weak' if rsi < 30 else 'neutral',
            'volume_profile': 'above_average' if volume_ratio > 1.5 else 'below_average' if volume_ratio < 0.8 else 'normal'
        }
    }

result = asyncio.run(analyze_technical())
print(json.dumps(result))
    `;

    return await this.runPythonScript(pythonScript);
  }

  async getPortfolioAnalysis() {
    const pythonScript = `
import json
from core.claude_orchestrator import claude_trading_platform

# Get portfolio context (this would integrate with real broker in production)
portfolio = {
    'total_equity': 100000,
    'available_cash': 25000,
    'current_positions': [],
    'risk_metrics': {
        'portfolio_beta': 1.1,
        'total_risk_exposure': '3.2%',
        'diversification_score': 0.7
    },
    'recent_performance': {
        'daily_pnl': 150.50,
        'weekly_pnl': -230.25,
        'monthly_pnl': 1250.75
    }
}

print(json.dumps(portfolio))
    `;

    return await this.runPythonScript(pythonScript);
  }

  async calculatePositionSizing(params) {
    const { symbol, entry_price, stop_loss, account_size, risk_percent } = params;
    
    const pythonScript = `
import json

# Position sizing calculation
symbol = '${symbol}'
entry_price = ${entry_price}
stop_loss = ${stop_loss}
account_size = ${account_size}
risk_percent = ${risk_percent || 2}

# Calculate risk per share
risk_per_share = abs(entry_price - stop_loss)
total_risk_amount = account_size * (risk_percent / 100)
position_size = int(total_risk_amount / risk_per_share) if risk_per_share > 0 else 0
total_position_value = position_size * entry_price

result = {
    'symbol': symbol,
    'entry_price': entry_price,
    'stop_loss': stop_loss,
    'risk_per_share': round(risk_per_share, 2),
    'position_size': position_size,
    'total_position_value': round(total_position_value, 2),
    'total_risk_amount': round(total_risk_amount, 2),
    'risk_reward_ratio': round((entry_price - stop_loss) / risk_per_share, 2) if risk_per_share > 0 else 0
}

print(json.dumps(result))
    `;

    return await this.runPythonScript(pythonScript);
  }

  async runPythonScript(script) {
    return new Promise((resolve, reject) => {
      const python = spawn('python', ['-c', script], {
        cwd: this.projectRoot,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            resolve(result);
          } catch (e) {
            resolve({ raw_output: stdout.trim(), parse_error: e.message });
          }
        } else {
          reject(new Error(`Python script failed: ${stderr}`));
        }
      });
    });
  }
}

// MCP Server Protocol Implementation
const server = new TradingMCPServer();

const tools = [
  {
    name: "get_market_data",
    description: "Fetch real-time market data for specified symbols",
    inputSchema: {
      type: "object",
      properties: {
        symbols: {
          type: "array",
          items: { type: "string" },
          description: "Stock symbols to fetch data for (e.g., ['AAPL', 'NVDA'])"
        }
      },
      required: ["symbols"]
    }
  },
  {
    name: "query_trading_memories",
    description: "Search PostgreSQL database for relevant trading insights and memories",
    inputSchema: {
      type: "object", 
      properties: {
        query: {
          type: "string",
          description: "Search query for trading memories"
        },
        limit: {
          type: "integer",
          description: "Maximum number of memories to return",
          default: 5
        }
      },
      required: ["query"]
    }
  },
  {
    name: "analyze_technical_indicators",
    description: "Calculate technical indicators (RSI, EMA, support/resistance) for a symbol",
    inputSchema: {
      type: "object",
      properties: {
        symbol: {
          type: "string",
          description: "Stock symbol to analyze"
        }
      },
      required: ["symbol"]
    }
  },
  {
    name: "get_portfolio_analysis", 
    description: "Get current portfolio status, positions, and risk metrics",
    inputSchema: {
      type: "object",
      properties: {}
    }
  },
  {
    name: "calculate_position_sizing",
    description: "Calculate optimal position size based on risk management rules",
    inputSchema: {
      type: "object",
      properties: {
        symbol: { type: "string", description: "Stock symbol" },
        entry_price: { type: "number", description: "Planned entry price" },
        stop_loss: { type: "number", description: "Stop loss price" },
        account_size: { type: "number", description: "Total account value" },
        risk_percent: { type: "number", description: "Risk percentage (default 2%)", default: 2 }
      },
      required: ["symbol", "entry_price", "stop_loss", "account_size"]
    }
  }
];

// Simple HTTP server for MCP protocol
const http = require('http');

const server_instance = http.createServer(async (req, res) => {
  if (req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    
    req.on('end', async () => {
      try {
        const request = JSON.parse(body);
        
        if (request.method === 'tools/list') {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ tools }));
          return;
        }
        
        if (request.method === 'tools/call') {
          const { name, arguments: args } = request.params;
          const result = await server.handleRequest(name, args);
          
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            content: [{ 
              type: "text", 
              text: JSON.stringify(result, null, 2) 
            }] 
          }));
          return;
        }
        
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: "Unknown method" }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

const PORT = process.env.MCP_PORT || 3001;
server_instance.listen(PORT, () => {
  console.log(`Trading MCP Server running on port ${PORT}`);
  console.log(`Available tools: ${tools.map(t => t.name).join(', ')}`);
});
```

### 2. Make Server Executable

```bash
# Make the server executable
chmod +x trading-mcp-server.js

# Test the server
node trading-mcp-server.js
# Should output: Trading MCP Server running on port 3001
```

### 3. Register with Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add ./trading-mcp-server.js

# Verify installation
claude mcp list
```

## Testing MCP Integration

### Basic Function Tests

```bash
# Start Claude Code
claude

# Test market data
"Get market data for AAPL and NVDA"

# Test trading memories
"Search for NVDA trading insights from our database"  

# Test technical analysis
"Analyze technical indicators for MSFT"

# Test position sizing
"Calculate position size for AAPL trade: entry $187.50, stop $185.00, account size $50000"
```

### Expected Responses

**Market Data Request:**
```
User: "Get market data for AAPL"

Claude Code: [Calls get_market_data tool]
Current market data for AAPL:
- Price: $187.65 (+0.8%)
- Volume: 1.3x average
- Technical trend: Bullish (above EMA20)
```

**Trading Memory Search:**
```
User: "Search for NVDA breakout strategies"

Claude Code: [Calls query_trading_memories tool]
Found 3 relevant trading memories:
1. "NVDA momentum breakouts work best with volume confirmation" (Score: 0.90)
2. "NVDA resistance at $885 level historically strong" (Score: 0.75)
3. "Best NVDA entries occur on RSI 45-65 range" (Score: 0.68)
```

## Advanced Configuration

### Environment Variables

Create `.env.mcp` for server configuration:
```bash
MCP_PORT=3001
PYTHON_PATH=/path/to/your/python
PROJECT_ROOT=/path/to/swing-sage
POSTGRES_URL=postgresql://postgres:password@127.0.0.1:5432/swing_sage
```

### Performance Optimization

```javascript
// Add caching to reduce database calls
class CacheManager {
  constructor() {
    this.cache = new Map();
    this.cacheTTL = 60000; // 1 minute
  }
  
  get(key) {
    const item = this.cache.get(key);
    if (item && Date.now() - item.timestamp < this.cacheTTL) {
      return item.data;
    }
    return null;
  }
  
  set(key, data) {
    this.cache.set(key, { data, timestamp: Date.now() });
  }
}
```

### Error Handling

```javascript
// Enhanced error handling
async handleRequest(method, params) {
  const startTime = Date.now();
  
  try {
    const result = await this.processRequest(method, params);
    
    console.log(`[${method}] Success in ${Date.now() - startTime}ms`);
    return result;
    
  } catch (error) {
    console.error(`[${method}] Error: ${error.message}`);
    
    return {
      error: true,
      message: `Trading analysis temporarily unavailable: ${error.message}`,
      method: method,
      timestamp: new Date().toISOString(),
      fallback_suggestion: this.getFallbackSuggestion(method)
    };
  }
}
```

## Troubleshooting

### Common Issues

**Server Won't Start:**
```bash
# Check Node.js version
node --version  # Should be 16+ 

# Check port conflicts  
lsof -i :3001

# Test Python integration
python -c "from core.postgres_manager import db_manager; print('OK')"
```

**Database Connection Errors:**
```bash
# Verify PostgreSQL is running
pg_ctl status

# Test database connection
python setup_database.py

# Check .env configuration
cat .env
```

**Claude Code Can't Find Tools:**
```bash
# Re-register MCP server
claude mcp remove trading-mcp-server
claude mcp add ./trading-mcp-server.js

# Check Claude Code logs
claude --debug
```

### Performance Monitoring

Add logging to track performance:
```javascript
// Monitor tool usage
const toolStats = {};

async function logToolUsage(tool, duration, success) {
  if (!toolStats[tool]) {
    toolStats[tool] = { calls: 0, avgDuration: 0, errors: 0 };
  }
  
  toolStats[tool].calls++;
  toolStats[tool].avgDuration = 
    (toolStats[tool].avgDuration + duration) / 2;
    
  if (!success) toolStats[tool].errors++;
  
  // Log every 10 calls
  if (toolStats[tool].calls % 10 === 0) {
    console.log(`[${tool}] Stats:`, toolStats[tool]);
  }
}
```

## Next Steps

1. **Test MCP Server** - Verify all tools work correctly
2. **Create Subagents** - Follow [Subagent Architecture Guide](./subagent-architecture.md)  
3. **Integration Testing** - Test complete trading workflows
4. **Production Deployment** - Scale for live trading

---

**Status**: MCP server provides foundation for native Claude Code integration. Next step is creating specialized subagents that use these tools for sophisticated trading analysis.