# Troubleshooting Guide - Swing Sage Technical Issues

## PostgreSQL Configuration & Issues

### User's PostgreSQL Setup
- **Host**: 127.0.0.1 (use instead of localhost to force IPv4)
- **Port**: 5432
- **Database**: options_bot
- **User**: postgres
- **Password**: [user will provide in .env file]

### Critical Issue: Database Manager Initialization
**Problem**: The `db_manager` global instance initializes at import time, before `.env` file is loaded, causing it to use default credentials instead of environment variables.

**Solution**: Always re-initialize `db_manager.database_url` after loading environment:
```python
# After load_dotenv()
db_manager.database_url = os.getenv('DATABASE_URL', db_manager.database_url)
db_manager.initialize()
```

### PostgreSQL Connection Issues
- Use `127.0.0.1` instead of `localhost` to avoid IPv6 connection issues
- Password with special characters (`$`, `@`, `#`) must be URL-encoded in DATABASE_URL
- Test connection with: `psql -h 127.0.0.1 -U postgres -d options_bot`

### JSONB Serialization Issues
**Problem**: PostgreSQL JSONB columns require JSON strings, not Python dictionaries.

**Solution**: Always use `json.dumps()` before inserting into JSONB columns:
```python
# Wrong
'metadata': {'key': 'value'}

# Correct  
'metadata': json.dumps({'key': 'value'})
```

### LLM Response Parsing Issues
**Problem**: OpenAI models often wrap JSON responses in markdown code blocks (```json ... ```).

**Solution**: Use the utility function in `options_bot/utils/llm.py`:
```python
from options_bot.utils.llm import parse_llm_json_response
data = parse_llm_json_response(llm_response_content)
```

## MCP Server & IBKR Integration Issues

### CRITICAL: Import Path Configuration  
**Problem**: The MCP server Node.js process can't find Python modules due to incorrect sys.path setup.

**Root Cause**: When adding paths to sys.path in JavaScript template strings, the module structure must match exactly:
```javascript
// WRONG - causes "No module named 'src'" error
sys.path.insert(0, '${projectRoot}/mcp-server/src')

// CORRECT - allows "from src.module import" to work
sys.path.insert(0, '${projectRoot}/mcp-server')
```

**Solution**: In MCP server JavaScript, always add the parent directory of the module hierarchy to sys.path.

### Virtual Environment Detection Issues
**Problem**: Node.js subprocess spawns system Python instead of virtual environment Python, causing "ib_insync not available" errors.

**Solution**: MCP server now auto-detects and uses virtual environment Python:
```javascript
const venvPaths = [
  path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe'),  // Windows
  path.join(this.projectRoot, '.venv', 'bin', 'python')          // Unix
];
```

### IBKR Connection Architecture
**Working Solution**: 
- ✅ **Threading approach** - Runs IBKR in separate thread to avoid asyncio event loop conflicts
- ✅ **Event loop creation** - Creates new asyncio event loop per thread for ib_insync compatibility  
- ✅ **Timeout handling** - 15-second timeout with graceful fallback to database/mock data
- ✅ **NaN handling** - Paper trading returns NaN prices, falls back to reasonable defaults

### Debugging MCP Server Issues
**Key Technique**: Add diagnostic logging to separate log file since MCP stderr/stdout is consumed by Claude Code:
```javascript
const diagnosticScript = `
log_file = r'${projectRoot}/mcp-debug.log'
with open(log_file, 'a') as f:
    f.write("Step completed successfully\\n")
`;
```

### CRITICAL: JavaScript Template Literal Conflicts
**Problem**: Python f-strings with `${}` syntax inside JavaScript template literals cause "Missing } in template expression" errors.

**Examples of BROKEN code:**
```javascript
// WRONG - causes SyntaxError
const script = `
print(f"Price: ${price:.2f}")  # JavaScript sees ${price:.2f} as template literal
print(f"Level: ${level-5:.2f}, Resistance: ${level+8:.2f}")  # Multiple conflicts
`;
```

**Solutions:**
```javascript
// CORRECT - Use string concatenation
const script = `
print(f"Price: $" + str(round(price, 2)))
print("Level: " + str(round(level-5, 2)) + ", Resistance: " + str(round(level+8, 2)))
`;

// CORRECT - Escape the dollar sign
const script = `
print(f"Price: \\${price:.2f}")
`;

// CORRECT - Use different quote styles
const script = `
print("Price: " + f"${price:.2f}")
`;
```

**Rule**: NEVER use `${variable}` Python f-string syntax inside JavaScript template literals. Always use string concatenation or escaping.

## Common Development Issues & Solutions

### Rich JSON Display Error
**Problem**: `JSON()` component expects string, not dict.
**Error**: `the JSON object must be str, bytes or bytearray, not dict`
**Solution**: Use `json.dumps()` with `default=str` for datetime handling:
```python
console.print(JSON(json.dumps(data, indent=2, default=str)))
```

### Context Manager vs Generator Error  
**Problem**: Using `db_manager.get_session()` as context manager fails.
**Error**: `'generator' object does not support the context manager protocol`
**Solution**: Use `db_manager.session_context()` instead:
```python
# Wrong
with db_manager.get_session() as session:

# Correct  
with db_manager.session_context() as session:
```

## Database Schema Reference

```sql
-- Core tables that Claude Code writes to
CREATE TABLE trade_setups (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10),
    created_by_agent VARCHAR(50),
    conversation_context TEXT,
    entry_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    target_price DECIMAL(10,2),
    confidence INTEGER,
    setup_json JSONB,  -- Full agent analysis
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE agent_conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    user_query TEXT,
    agents_spawned TEXT[],
    response TEXT,
    market_snapshot JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE position_history (
    id SERIAL PRIMARY KEY,
    setup_id INTEGER REFERENCES trade_setups(id),
    entry_executed TIMESTAMP,
    exit_executed TIMESTAMP,
    pnl DECIMAL(10,2),
    agent_notes JSONB
);
```