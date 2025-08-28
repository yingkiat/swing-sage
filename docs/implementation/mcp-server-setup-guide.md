# MCP Server Setup Guide - Stdio Protocol

**Updated**: August 27, 2025  
**Protocol**: Stdio (Standard Input/Output) - Correct format for Claude Code  
**Status**: Production Ready

## Overview

This guide shows how to register and use the Swing Sage Trading MCP Server with Claude Code using the **stdio protocol** - the proper way that Claude Code expects MCP servers to work.

## Prerequisites

**Claude CLI Installation**:
```bash
# Install Claude CLI globally
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

## Important: Stdio vs HTTP Protocol

**✅ Stdio Protocol (What We Use)**:
- Claude Code runs MCP server as a subprocess
- Communication via stdin/stdout using JSON-RPC
- No need to keep servers running manually
- Claude Code manages the process lifecycle automatically

**❌ HTTP Protocol (What Doesn't Work)**:
- Requires running HTTP server on port (like 3001)
- Claude Code can't connect to HTTP URLs by default
- Complex setup with manual process management

## One-Time Setup

### Step 1: Register MCP Server

**Single Command Registration**:
```bash
claude mcp add trading-server -- node C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js
```

**What This Does**:
- Registers `trading-server` with Claude Code
- Points to the stdio MCP server file
- Claude Code will run this server automatically when needed

### Step 2: Verify Registration

```bash
claude mcp list
```

**Expected Output**:
```
trading-server: node C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js - ✓ Connected
```

## Usage

### Start Claude Code Session

```bash
claude
```

Claude Code automatically:
1. Starts your MCP server process
2. Establishes stdio communication
3. Makes your 3 tools available

### Test Your Tools

**Verify Tools Available**:
```
"What tools do you have available?"
```

**Expected Response**: Claude Code should list:
- `get_market_data` - Fetch market data and technical analysis
- `query_trading_memories` - Search trading insights database
- `store_trading_memory` - Save new trading recommendations

### Test Individual Tools

**Test Market Data**:
```
"Get market data for AAPL and NVDA"
```

**Test Memory Search**:
```
"Search for NVDA trading insights"
```

**Test Memory Storage**:
```
"Store this insight: NVDA momentum breakouts work best with volume confirmation"
```

### Test Complete Trading Cycle

```
"What's a good swing trade setup today?"
```

**Expected Flow**:
1. Claude Code calls `get_market_data` for current market data
2. Claude Code calls `query_trading_memories` for relevant insights
3. Claude Code synthesizes recommendation
4. Claude Code calls `store_trading_memory` to save analysis

## Configuration File

Claude Code creates a configuration automatically. If you want to see it, check `.claude.json`:

```json
{
  "mcpServers": {
    "trading-server": {
      "type": "stdio",
      "command": "node",
      "args": [
        "C:\\Users\\shing\\Work\\swing-sage\\mcp-server\\trading-mcp-stdio.js"
      ]
    }
  }
}
```

## Troubleshooting

### Registration Issues

**Problem**: `claude mcp add` command fails

**Solutions**:
```bash
# Ensure Claude CLI is installed
npm install -g @anthropic-ai/claude-code

# Check file path exists
ls C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js

# Try absolute path registration
claude mcp add trading-server -- node "C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js"
```

### Connection Issues

**Problem**: `claude mcp list` shows `✗ Failed to connect`

**Solutions**:
```bash
# Test MCP server manually
node C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js

# Should start and wait for stdin input (Ctrl+C to exit)

# Re-register if needed
claude mcp remove trading-server
claude mcp add trading-server -- node C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js
```

### Database Issues

**Problem**: Tools work but return database errors

**Solutions**:
```bash
# Test database connection
python -c "
import sys
sys.path.append('C:/Users/shing/Work/swing-sage')
from mcp_server.src.database.connection import db_manager
db_manager.initialize()
print('Database connection OK')
"

# Ensure PostgreSQL is running
# Check .env file has correct DATABASE_URL
```

### Python Path Issues

**Problem**: MCP server can't import Python modules

**Solutions**:
```bash
# Ensure you're in correct directory structure
cd C:\Users\shing\Work\swing-sage

# Test Python imports manually
python -c "
import sys
sys.path.insert(0, '.')
from mcp_server.src.database.connection import db_manager
print('Python imports OK')
"
```

## Development Tips

### Testing MCP Server Directly

```bash
# Navigate to project directory
cd C:\Users\shing\Work\swing-sage

# Run MCP server directly (for debugging)
node mcp-server/trading-mcp-stdio.js

# Send test JSON-RPC message
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node mcp-server/trading-mcp-stdio.js
```

### Viewing MCP Server Logs

The stdio server logs to stderr, so you'll see logs when Claude Code runs it. To see detailed logs:

1. Run Claude Code with debug mode (if available)
2. Check stderr output when tools are called
3. MCP server logs include: `🚀 Initialized`, `🔧 Tool call: get_market_data`, etc.

### Updating MCP Server

When you modify `trading-mcp-stdio.js`:

```bash
# No need to restart anything
# Claude Code will use the updated file automatically on next tool call

# Optional: Test changes manually
claude mcp list  # Should still show ✓ Connected
```

## Key Advantages of Stdio Approach

✅ **Automatic Process Management**: Claude Code handles starting/stopping  
✅ **No Port Conflicts**: No need to manage HTTP ports  
✅ **Simpler Debugging**: All communication is logged  
✅ **Better Error Handling**: JSON-RPC protocol with proper error codes  
✅ **Process Isolation**: Each Claude Code session gets its own MCP process  

## What's Different from HTTP Approach

| Aspect | HTTP Approach ❌ | Stdio Approach ✅ |
|--------|------------------|-------------------|
| **Setup** | Start server manually, register URL | Register once, Claude Code manages |
| **Process** | Keep HTTP server running | Claude Code starts/stops automatically |
| **Communication** | HTTP requests/responses | JSON-RPC via stdin/stdout |
| **Debugging** | Check server logs + HTTP status | All logs visible in stderr |
| **Reliability** | Server can crash/disconnect | Process restarted automatically |

## Next Steps

Once your MCP server is working with Claude Code:

1. **Test Complete Trading Workflows**: Try complex multi-step trading conversations
2. **Implement MVP2**: Add custom trading subagents (@price-analyst, @risk-manager)  
3. **Add Real Market Data**: Upgrade from fallback data to live market feeds
4. **Enhance Memory System**: Add more sophisticated trading insight storage

---

## Quick Reference

```bash
# One-time setup
claude mcp add trading-server -- node C:\Users\shing\Work\swing-sage\mcp-server\trading-mcp-stdio.js

# Daily usage
claude                           # Start Claude Code with MCP tools
"What tools do you have?"        # Verify tools loaded
"Get market data for AAPL"       # Test trading functionality

# Management
claude mcp list                  # Check server status
claude mcp remove trading-server # Remove if needed
```

**Status**: ✅ Ready for Production Trading Conversations  
**Next**: Test complete trading workflow with Claude Code