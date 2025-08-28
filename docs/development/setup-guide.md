# Development Setup Guide

This guide will help you set up Swing Sage for development, testing, and experimentation.

## Prerequisites

### Required Software
- **Python 3.9+** - The platform is built in Python
- **PostgreSQL 12+** - Required for data storage and memory system
- **Git** - For version control and updates

### Optional Software  
- **Interactive Brokers TWS/Gateway** - For real broker integration (paper trading)
- **Docker** - For containerized PostgreSQL (alternative to local install)

## Quick Start (5 Minutes)

### 1. Clone Repository
```bash
git clone <repository-url>
cd swing-sage
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt

# Or using virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Database
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your PostgreSQL credentials
DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/swing_sage
```

### 4. Initialize Database
```bash
python setup_database.py
```

### 5. Test Basic Functionality
```python
python -c "
from core.claude_orchestrator import claude_trading_platform
from core.postgres_manager import db_manager

# Test database connection
print('Database connection:', db_manager.test_connection())

# Test session creation
session_id = claude_trading_platform.start_session('test-session')
print('Session created:', session_id)
print('Setup complete!')
"
```

## Detailed Setup

### Python Environment Setup

#### Option 1: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv swing-sage-env

# Activate environment
# On Linux/Mac:
source swing-sage-env/bin/activate
# On Windows:
swing-sage-env\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Option 2: Conda Environment
```bash
# Create conda environment
conda create -n swing-sage python=3.11
conda activate swing-sage

# Install dependencies
pip install -r requirements.txt
```

### PostgreSQL Setup

#### Option 1: Local PostgreSQL Installation

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set for 'postgres' user
4. PostgreSQL runs on port 5432 by default

**macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb swing_sage
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb swing_sage
```

#### Option 2: Docker PostgreSQL
```bash
# Run PostgreSQL in Docker
docker run --name swing-sage-postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=swing_sage \
  -p 5432:5432 \
  -d postgres:15

# Verify it's running
docker ps
```

### Environment Configuration

Create and configure your `.env` file:

```bash
# Copy the template
cp .env.example .env
```

Edit `.env` with your specific settings:
```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@127.0.0.1:5432/swing_sage

# LLM API Keys (optional for testing)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Broker Configuration (optional)
IBKR_TWS_PORT=7497
IBKR_GATEWAY_PORT=4001
```

**Important Notes:**
- Replace `your_password` with your actual PostgreSQL password
- The database name `swing_sage` must match what you created
- LLM API keys are optional - system will work with mock responses for testing
- IBKR configuration is only needed for real broker integration

### Database Initialization

Run the setup script:
```bash
python setup_database.py
```

**Expected Output:**
```
🎯 Swing Sage - Claude Code Trading Platform

🔌 Connecting to PostgreSQL server at 127.0.0.1:5432
📊 Database 'swing_sage' already exists
📋 Applying schema from schema.sql
✅ Schema applied successfully
🗄️ Database Connection Test

PostgreSQL Version: PostgreSQL 15.2
Sessions: 0
Deliberations: 0

✅ Connection successful!

🎉 Database setup completed successfully!
```

### Verify Installation

Test all major components:

```python
# Create test file: test_installation.py
from core.claude_orchestrator import claude_trading_platform
from core.postgres_manager import db_manager
from market_data.providers.yfinance_provider import YFinanceProvider
import asyncio

async def test_installation():
    print("🧪 Testing Swing Sage Installation")
    print("-" * 40)
    
    # Test 1: Database Connection
    print("1. Database Connection:", "✅" if db_manager.test_connection() else "❌")
    
    # Test 2: Session Creation
    try:
        session_id = claude_trading_platform.start_session('installation-test')
        print(f"2. Session Creation: ✅ ({session_id[:8]}...)")
    except Exception as e:
        print(f"2. Session Creation: ❌ ({e})")
    
    # Test 3: Market Data Provider
    try:
        provider = YFinanceProvider()
        data = await provider.get_market_data('AAPL')
        print(f"3. Market Data: ✅ (AAPL: ${float(data.current_price):.2f})" if data else "3. Market Data: ❌")
    except Exception as e:
        print(f"3. Market Data: ❌ ({e})")
    
    # Test 4: LLM Integration (basic)
    try:
        from core.llm_utils import LLMClient
        client = LLMClient()
        print("4. LLM Client: ✅")
    except Exception as e:
        print(f"4. LLM Client: ❌ ({e})")
    
    print("-" * 40)
    print("🎉 Installation test complete!")

# Run the test
asyncio.run(test_installation())
```

Run the test:
```bash
python test_installation.py
```

## Development Workflow

### Daily Development Setup
```bash
# 1. Activate environment
source venv/bin/activate  # or conda activate swing-sage

# 2. Pull latest changes
git pull origin main

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Update database schema if needed
python setup_database.py

# 5. Start developing!
```

### Running the Platform

#### Basic Market Analysis
```python
# Create: daily_analysis.py
import asyncio
from core.claude_orchestrator import claude_trading_platform

async def daily_scan():
    session_id = claude_trading_platform.start_session("daily-scan")
    
    analysis = await claude_trading_platform.analyze_market_opportunity(
        "What are the best swing trade opportunities today?"
    )
    
    print("📊 Daily Market Analysis")
    print("=" * 50)
    print(analysis["analysis"].get("market_outlook", "Analysis in progress..."))
    print()
    
    primary = analysis["analysis"].get("primary_recommendation", {})
    if primary:
        print(f"🎯 Top Setup: {primary.get('symbol', 'Unknown')}")
        print(f"   Entry: {primary.get('entry_zone', 'TBD')}")
        print(f"   Target: {primary.get('target', 'TBD')}")
        print(f"   Stop: {primary.get('stop_loss', 'TBD')}")

asyncio.run(daily_scan())
```

Run it:
```bash
python daily_analysis.py
```

#### Interactive Session
```python
# Create: interactive_trading.py
import asyncio
from core.claude_orchestrator import claude_trading_platform

async def interactive_session():
    session_id = claude_trading_platform.start_session("interactive")
    print(f"📱 Trading Session Started: {session_id[:8]}...")
    print("Ask me anything about the markets!\n")
    
    while True:
        query = input("You: ")
        if query.lower() in ['exit', 'quit', 'bye']:
            break
            
        analysis = await claude_trading_platform.analyze_market_opportunity(query)
        
        print("\n🤖 Swing Sage:")
        print(analysis["analysis"].get("market_outlook", "Let me analyze that..."))
        
        primary = analysis["analysis"].get("primary_recommendation")
        if primary:
            print(f"\n💡 Recommendation: {primary}")
        
        print("\n" + "-"*50 + "\n")

asyncio.run(interactive_session())
```

### Development Tools

#### Database Inspection
```bash
# Connect to database
psql -h 127.0.0.1 -U postgres -d swing_sage

# Useful queries
\dt                                    -- List all tables
SELECT * FROM session_summary;         -- View session summaries
SELECT * FROM agent_memories LIMIT 5;  -- Check memories
```

#### Log Analysis
```python
# View recent session activity
from core.postgres_manager import db_manager

# Get recent sessions
sessions = db_manager.get_session_summary()
for session in sessions[:3]:
    print(f"Session: {session['session_name']}")
    print(f"  Created: {session['created_at']}")
    print(f"  Deliberations: {session['total_deliberations']}")
    print(f"  Confidence: {session['avg_confidence']:.2f}")
    print()
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```
Error: FATAL: password authentication failed for user "postgres"
```

**Solutions:**
1. Check password in `.env` file
2. Verify PostgreSQL is running: `pg_ctl status`
3. Test connection manually: `psql -h 127.0.0.1 -U postgres -d swing_sage`

#### Import Errors
```
ModuleNotFoundError: No module named 'core'
```

**Solutions:**
1. Ensure you're in the project root directory
2. Activate virtual environment
3. Install dependencies: `pip install -r requirements.txt`

#### Market Data Errors
```
Failed to get market data for AAPL: HTTP Error 429
```

**Solutions:**
1. Yahoo Finance has rate limits - wait a few minutes
2. Check internet connection
3. Try different symbol

#### LLM API Errors
```
Error: No API key configured
```

**Solutions:**
1. Add API keys to `.env` file
2. System works without API keys using mock responses
3. For real LLM analysis, get keys from OpenAI or Anthropic

### Development Tips

#### Code Organization
```
swing-sage/
├── core/           # Core orchestration and LLM
├── market_data/    # Data providers and models  
├── brokers/        # Broker integrations
├── agents/         # Future: specialized analysis agents
└── docs/           # Documentation
```

#### Testing Components
```python
# Test market data
from market_data.providers.yfinance_provider import YFinanceProvider
provider = YFinanceProvider()
data = await provider.get_market_data('MSFT')
print(data)

# Test database operations  
from core.postgres_manager import db_manager
memories = db_manager.get_memories(memory_type='long_term', limit=3)
print(memories)
```

#### Database Schema Updates
```bash
# After modifying schema.sql
python setup_database.py  # Re-creates all tables

# Or for production, use migrations
# (Future: Alembic integration)
```

## Next Steps

Once you have everything working:

1. **Read [Conversation Examples](../trading/conversation-examples.md)** - See the platform in action
2. **Review [System Overview](../architecture/system-overview.md)** - Understand the architecture  
3. **Check [Extending Platform](./extending-platform.md)** - Add new features
4. **Try [Testing Guide](./testing-guide.md)** - Run comprehensive tests

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the logs in your terminal
3. Test individual components to isolate the problem
4. Check that all dependencies are properly installed

The platform is designed to work with minimal configuration - most issues are related to database setup or missing dependencies.

---

**Next**: Try the [Testing Guide](./testing-guide.md) to validate your installation.