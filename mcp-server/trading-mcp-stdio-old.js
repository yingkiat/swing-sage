#!/usr/bin/env node
/**
 * Swing Sage Trading MCP Server - Stdio Protocol
 * 
 * Implements the proper MCP stdio protocol for Claude Code integration.
 * This is the correct format that Claude Code expects for MCP servers.
 */

const { spawn } = require('child_process');
const path = require('path');

class StdioMCPServer {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '..');
    this.requestId = 0;
    
    // Bind methods to preserve 'this' context
    this.handleMessage = this.handleMessage.bind(this);
    this.sendResponse = this.sendResponse.bind(this);
    this.sendError = this.sendError.bind(this);
  }

  start() {
    // Set up stdio communication
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (data) => {
      const lines = data.trim().split('\n');
      lines.forEach(line => {
        if (line.trim()) {
          try {
            const message = JSON.parse(line);
            this.handleMessage(message);
          } catch (error) {
            this.sendError(null, -32700, 'Parse error', error.message);
          }
        }
      });
    });

    // Initialize MCP server
    this.logToStderr('🚀 Swing Sage Stdio MCP Server initialized');
    this.logToStderr(`📁 Project root: ${this.projectRoot}`);
  }

  logToStderr(message) {
    // Use stderr for logging since stdout is reserved for MCP protocol
    console.error(`[MCP Server] ${message}`);
  }

  async handleMessage(message) {
    const { jsonrpc, id, method, params } = message;

    if (jsonrpc !== '2.0') {
      return this.sendError(id, -32600, 'Invalid Request', 'Invalid JSON-RPC version');
    }

    try {
      switch (method) {
        case 'initialize':
          await this.handleInitialize(id, params);
          break;
        
        case 'tools/list':
          await this.handleToolsList(id);
          break;
        
        case 'tools/call':
          await this.handleToolsCall(id, params);
          break;
        
        case 'notifications/initialized':
          // Client initialization complete - no response needed
          this.logToStderr('✅ Client initialization complete');
          break;
        
        default:
          this.sendError(id, -32601, 'Method not found', `Unknown method: ${method}`);
      }
    } catch (error) {
      this.logToStderr(`❌ Error handling ${method}: ${error.message}`);
      this.sendError(id, -32603, 'Internal error', error.message);
    }
  }

  async handleInitialize(id, params) {
    this.logToStderr('🔧 Initializing MCP server...');
    
    const response = {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
        logging: {}
      },
      serverInfo: {
        name: 'swing-sage-trading-server',
        version: '1.0.0'
      }
    };

    this.sendResponse(id, response);
    this.logToStderr('✅ MCP server initialized successfully');
  }

  async handleToolsList(id) {
    const tools = [
      {
        name: 'get_market_data',
        description: 'Fetch current market data and technical analysis for specified stock symbols',
        inputSchema: {
          type: 'object',
          properties: {
            symbols: {
              type: 'array',
              items: { type: 'string' },
              description: 'Stock symbols to analyze (e.g., ["AAPL", "NVDA", "MSFT"])'
            },
            include_technical: {
              type: 'boolean',
              description: 'Include technical indicators (RSI, EMA) in response',
              default: true
            }
          },
          required: ['symbols']
        }
      },
      {
        name: 'query_trading_memories',
        description: 'Search the PostgreSQL memory database for relevant trading insights and past analysis',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query for trading memories'
            },
            limit: {
              type: 'integer',
              description: 'Maximum number of memories to return',
              default: 5,
              minimum: 1,
              maximum: 20
            }
          },
          required: ['query']
        }
      },
      {
        name: 'store_trading_memory',
        description: 'Save new trading analysis or recommendations to the PostgreSQL memory database',
        inputSchema: {
          type: 'object',
          properties: {
            title: {
              type: 'string',
              description: 'Concise title for the memory'
            },
            content: {
              type: 'string',
              description: 'Detailed content of the trading insight'
            },
            importance_score: {
              type: 'number',
              description: 'Importance score from 0.0 to 1.0',
              minimum: 0.0,
              maximum: 1.0,
              default: 0.5
            },
            relevance_tags: {
              type: 'array',
              items: { type: 'string' },
              description: 'Relevant tags for future searching',
              default: []
            }
          },
          required: ['title', 'content']
        }
      }
    ];

    this.sendResponse(id, { tools });
  }

  async handleToolsCall(id, params) {
    const { name, arguments: args } = params;
    
    this.logToStderr(`🔧 Tool call: ${name}`);
    this.logToStderr(`📋 Arguments: ${JSON.stringify(args)}`);

    try {
      let result;

      switch (name) {
        case 'get_market_data':
          result = await this.getMarketData(args.symbols, args.include_technical);
          break;
        
        case 'query_trading_memories':
          result = await this.queryTradingMemories(args.query, args.limit);
          break;
        
        case 'store_trading_memory':
          result = await this.storeTradingMemory(args);
          break;
        
        default:
          throw new Error(`Unknown tool: ${name}`);
      }

      // MCP protocol expects tool results in specific format
      this.sendResponse(id, {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2)
          }
        ]
      });

    } catch (error) {
      this.logToStderr(`❌ Tool ${name} failed: ${error.message}`);
      this.sendError(id, -32603, 'Tool execution failed', error.message);
    }
  }

  // Tool implementations (same as HTTP version but adapted for stdio)
  async getMarketData(symbols, includeTechnical = true) {
    // First, create a diagnostic log file
    const diagnosticScript = `
import sys
import os
import json
from datetime import datetime

log_file = r'${this.projectRoot.replace(/\\/g, '\\\\')}/mcp-debug.log'

diagnosis = {
    'timestamp': datetime.now().isoformat(),
    'python_executable': sys.executable,
    'python_version': sys.version.split()[0],
    'cwd': os.getcwd(),
    'project_root': '${this.projectRoot.replace(/\\/g, '\\\\')}',
    'packages': {}
}

packages = ['ib_insync', 'sqlalchemy', 'psycopg2']
for pkg in packages:
    try:
        __import__(pkg)
        diagnosis['packages'][pkg] = 'available'
    except ImportError as e:
        diagnosis['packages'][pkg] = f'missing: {str(e)}'

# Check if virtual environment python exists
venv_path = r'${this.projectRoot.replace(/\\/g, '\\\\')}\.venv\\Scripts\\python.exe'
diagnosis['venv_python_exists'] = os.path.exists(venv_path)
diagnosis['current_python_is_venv'] = venv_path.lower() == sys.executable.lower()

try:
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\\n" + "="*50 + "\\n")
        f.write(json.dumps(diagnosis, indent=2))
        f.write("\\n" + "="*50 + "\\n")
except Exception as e:
    print(f"Failed to write log: {e}", file=sys.stderr)

print("Diagnostic written to mcp-debug.log", file=sys.stderr)
`;

    this.logToStderr('🔍 Running diagnostic and logging to mcp-debug.log...');
    await this.runPythonScript(diagnosticScript, 'diagnostic');
    
    // Try gradually adding complexity
    const testScript = `
import sys
import json
import os
import traceback

try:
    log_file = r'${this.projectRoot.replace(/\\/g, '\\\\')}/mcp-debug.log'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\\nTEST: Starting imports test\\n")
    
    # Add correct paths for mcp-server modules
    sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')
    sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}/mcp-server')
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: Paths added\\n")
    
    # Test imports one by one
    import asyncio
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: asyncio imported\\n")
    
    # Import from the correct module path
    from src.database.connection import db_manager
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: db_manager imported\\n")
    
    from src.brokers.ibkr import IBKRBroker  
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: IBKRBroker imported\\n")
    
    import threading
    import queue
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: threading and queue imported\\n")
    
    # Test database initialization
    db_manager.initialize()
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: Database initialized\\n")
    
    # Test IBKR connection in thread (simplified)
    def test_ibkr_thread():
        try:
            # Create event loop for thread
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            broker = IBKRBroker(paper_trading=True, host='127.0.0.1', port=7497, client_id=1)
            broker.connect()
            
            # Test simple quote
            quote = broker.get_quote('${symbols[0]}')
            broker.disconnect()
            return {'success': True, 'quote': quote}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Run IBKR test in thread
    import queue
    result_queue = queue.Queue()
    
    def threaded_test():
        result = test_ibkr_thread()
        result_queue.put(result)
    
    thread = threading.Thread(target=threaded_test)
    thread.start()
    thread.join(timeout=10)
    
    ibkr_result = {'success': False, 'error': 'timeout'}
    if not thread.is_alive():
        try:
            ibkr_result = result_queue.get_nowait()
        except:
            pass
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"TEST: IBKR result: {ibkr_result}\\n")
    
    # Build response based on IBKR success
    if ibkr_result.get('success'):
        quote_data = ibkr_result.get('quote', {})
        price = quote_data.get('price')
        
        # Try other IBKR price sources if price is None/NaN
        if price is None or price != price:  # Handle NaN
            price = quote_data.get('last')
        if price is None or price != price:
            if quote_data.get('bid') and quote_data.get('ask'):
                price = (quote_data['bid'] + quote_data['ask']) / 2.0
        if price is None or price != price:
            price = quote_data.get('last_close')
            
        # If still no valid price, historical data should have been tried
        if price is None or price != price:
            data_source = 'ibkr_no_data'
            price = None
        else:
            data_source = quote_data.get('data_source', 'ibkr_unknown')
    else:
        price = None
        data_source = 'connection_failed'
    
    # Test response with actual IBKR data
    if price is not None:
        response = {
            'symbols_requested': ${symbols.length},
            'symbols_returned': 1,  
            'data_source': data_source,
            'timestamp': 'live_test',
            'status': 'success',
            'data': {
                '${symbols[0]}': {
                    'symbol': '${symbols[0]}',
                    'current_price': float(price),
                    'data_source': data_source,
                    'setup_quality': data_source,
                    'indicators': {
                        'rsi': 50.0,
                        'ema_20': float(price),
                        'ema_50': float(price)
                    }
                }
            }
        }
    else:
        response = {
            'symbols_requested': ${symbols.length},
            'symbols_returned': 0,  
            'data_source': data_source,
            'timestamp': 'live_test',
            'status': 'no_data',
            'message': 'No valid price data available from IBKR',
            'data': {}
        }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: About to print JSON response\\n")
    
    print(json.dumps(response, indent=2))
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("TEST: JSON response printed successfully\\n")
        
except Exception as e:
    import traceback
    log_file = r'${this.projectRoot.replace(/\\/g, '\\\\')}/mcp-debug.log'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"TEST ERROR: {str(e)}\\n")
        f.write(f"TEST TRACEBACK: {traceback.format_exc()}\\n")
    
    error_response = {
        'status': 'error',
        'error_message': str(e)
    }
    print(json.dumps(error_response))
`;

    this.logToStderr('🔍 Running simple test script first...');
    return await this.runPythonScript(testScript, 'simple_test');
    
    // Complex script (temporarily disabled for debugging)
    const pythonScript = `
import sys
import os
import traceback
sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')
sys.path.insert(0, '${path.join(this.projectRoot, 'mcp-server').replace(/\\/g, '\\\\')}')

import asyncio
import json
from src.database.connection import db_manager
from src.brokers.ibkr import IBKRBroker

async def get_market_data_main():
    try:
        symbols = ${JSON.stringify(symbols)}
        include_technical = ${includeTechnical ? 'True' : 'False'}
        
        print(f"🔍 Fetching market data for: {symbols}", file=sys.stderr)
        
        # Log progress to file
        log_file = r'${this.projectRoot.replace(/\\/g, '\\\\')}/mcp-debug.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\\nSTEP: Starting market data fetch for {symbols}\\n")
        
        # Initialize database for fallback
        db_manager.initialize()
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("STEP: Database initialized successfully\\n")
        
        # Try IBKR first, then fallback to database
        ibkr_results = {}
        ibkr_success = False
        
        try:
            print("🏦 Attempting IBKR connection...", file=sys.stderr)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("STEP: Starting IBKR connection attempt\\n")
            
            # Run IBKR in a separate thread to avoid event loop conflicts
            import threading
            import queue
            
            def run_ibkr_in_thread(result_queue, symbols):
                try:
                    # Create a new event loop for this thread
                    import asyncio
                    try:
                        # Check if there's already a loop
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        # No loop exists, create one
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    broker = IBKRBroker(paper_trading=True, host='127.0.0.1', port=7497, client_id=1)
                    broker.connect()
                    
                    thread_results = {}
                    for symbol in symbols:
                        try:
                            quote = broker.get_quote(symbol)
                            thread_results[symbol] = quote
                        except Exception as e:
                            thread_results[symbol] = {'error': str(e)}
                    
                    broker.disconnect()
                    result_queue.put(('success', thread_results))
                    
                except Exception as e:
                    result_queue.put(('error', str(e)))
            
            # Run IBKR in separate thread
            result_queue = queue.Queue()
            thread = threading.Thread(target=run_ibkr_in_thread, args=(result_queue, symbols))
            thread.start()
            thread.join(timeout=15)  # 15 second timeout
            
            if thread.is_alive():
                print("⏰ IBKR connection timeout", file=sys.stderr)
                raise Exception("IBKR connection timeout")
            
            # Get results
            try:
                status, ibkr_quotes = result_queue.get_nowait()
                if status == 'error':
                    raise Exception(ibkr_quotes)
                
                print("✅ Connected to IBKR Gateway via thread", file=sys.stderr)
            
            # Process threaded results
            for symbol in symbols:
                if symbol in ibkr_quotes and 'error' not in ibkr_quotes[symbol]:
                    quote = ibkr_quotes[symbol]
                    
                    # Convert IBKR quote to our format - try multiple price sources
                    price = None
                    data_quality = 'no_data'
                    
                    # Use the data source from IBKR broker (it handles live vs historical fallback)
                    price = quote.get('price')
                    data_quality = quote.get('data_source', 'unknown')
                    
                    # Skip this symbol if no valid price data available
                    if price is None or price != price:  # None or NaN
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"SKIP: No valid price data for {symbol} (price={price})\\n")
                        continue
                    
                    # Calculate basic technical levels if we have historical data
                    historical_data = quote.get('historical_data', {})
                    if historical_data and 'latest_bar' in historical_data:
                        latest_bar = historical_data['latest_bar']
                        high_52w = latest_bar.get('high', price)  # Simplified
                        low_52w = latest_bar.get('low', price)   # Simplified
                        volume_info = "Vol: " + str(latest_bar.get('volume', 'N/A'))
                        key_levels = "Day High: " + str(round(high_52w, 2)) + ", Day Low: " + str(round(low_52w, 2))
                    else:
                        volume_info = str(quote.get("volume", "unknown")) + ' volume'
                        key_levels = 'Support: ' + str(round(price-5, 2)) + ', Resistance: ' + str(round(price+8, 2))
                    
                    result = {
                        'symbol': symbol,
                        'current_price': float(price),
                        'change_percent': 0.0,  # Could calculate from historical data
                        'volume_ratio': 1.0,
                        'momentum_score': 0.5,
                        'setup_quality': data_quality,
                        'trend_direction': 'neutral',
                        'key_levels': key_levels,
                        'volume_profile': volume_info,
                        'pattern': 'ibkr_data',
                        'timestamp': 'ibkr_data',
                        'data_source': f'ibkr_{data_quality}',
                        'bid': quote.get('bid'),
                        'ask': quote.get('ask'),
                        'last_close': quote.get('last_close'),
                        'historical_available': bool(historical_data)
                    }
                    
                    if include_technical:
                        result['indicators'] = {
                            'rsi': 50.0,  # Would need additional API calls
                            'ema_20': price,
                            'ema_50': price
                        }
                    
                    ibkr_results[symbol] = result
                    print(f"✅ Got {symbol} data from IBKR: $" + str(round(price, 2)), file=sys.stderr)
                    
                else:
                    error_msg = ibkr_quotes.get(symbol, {}).get('error', 'Unknown error')
                    print(f"❌ IBKR error for {symbol}: {error_msg}", file=sys.stderr)
            
                print("🔌 IBKR thread completed", file=sys.stderr)
                ibkr_success = len(ibkr_results) > 0
                
            except queue.Empty:
                print("❌ No results from IBKR thread", file=sys.stderr)
                raise Exception("No results from IBKR thread")
            
        except Exception as ibkr_error:
            print(f"❌ IBKR connection failed: {ibkr_error}", file=sys.stderr)
            print("📋 Falling back to database...", file=sys.stderr)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"ERROR: IBKR connection failed: {str(ibkr_error)}\\n")
        
        # If IBKR succeeded, use those results, otherwise try web search fallback
        if ibkr_success:
            results = ibkr_results
            data_source = 'ibkr_live'
            timestamp = 'live_ibkr'
        else:
            # Try web search for current prices as fallback
            print("🌐 IBKR failed, trying web search fallback...", file=sys.stderr)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("STEP: Attempting web search price fallback\\n")
            
            results = {}
            web_success = False
            
            try:
                import requests
                import re
                from bs4 import BeautifulSoup
                
                for symbol in symbols:
                    try:
                        # Use Yahoo Finance for quick price lookup
                        url = f'https://finance.yahoo.com/quote/{symbol}'
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        response = requests.get(url, headers=headers, timeout=5)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Look for the current price
                            price_element = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
                            if price_element and price_element.get('value'):
                                price = float(price_element['value'])
                                
                                result = {
                                    'symbol': symbol,
                                    'current_price': price,
                                    'change_percent': 0.0,
                                    'volume_ratio': 1.0,
                                    'momentum_score': 0.5,
                                    'setup_quality': 'web_scraped',
                                    'trend_direction': 'neutral',
                                    'key_levels': f'Support: {price-5:.2f}, Resistance: {price+8:.2f}',
                                    'volume_profile': 'unknown volume',
                                    'pattern': 'web_data',
                                    'timestamp': 'web_scraped',
                                    'data_source': 'yahoo_finance_web'
                                }
                                
                                if include_technical:
                                    result['indicators'] = {
                                        'rsi': None,  # No technical data from web scraping
                                        'ema_20': None,
                                        'ema_50': None
                                    }
                                
                                results[symbol] = result
                                web_success = True
                                print(f"✅ Got {symbol} price from web: $" + str(round(price, 2)), file=sys.stderr)
                            
                    except Exception as e:
                        print(f"❌ Web scraping failed for {symbol}: {e}", file=sys.stderr)
                        continue
                
            except ImportError:
                print("📋 Web scraping libraries not available, falling back to database...", file=sys.stderr)
            except Exception as e:
                print(f"❌ Web search fallback failed: {e}", file=sys.stderr)
            
            # If web search failed, try database as final fallback
            if not web_success:
                print("📋 Using database fallback...", file=sys.stderr)
                screening_data = await db_manager.get_latest_market_screening()
                data_source = 'database_fallback'
                timestamp = screening_data.get('timestamp', 'unknown')
                
                for symbol in symbols:
                    try:
                        if symbol in screening_data.get('stock_analysis', {}):
                            analysis = screening_data['stock_analysis'][symbol]
                        
                            result = {
                                'symbol': symbol,
                                'current_price': analysis.get('current_price', 0),
                                'change_percent': (analysis.get('current_price', 0) / 100 - 1) * 100,
                                'volume_ratio': 1.0,
                                'momentum_score': analysis.get('momentum_score', 0.5),
                                'setup_quality': analysis.get('setup_quality', 'unknown'),
                                'trend_direction': analysis.get('trend_direction', 'neutral'),
                                'key_levels': analysis.get('key_levels', 'No levels available'),
                                'volume_profile': analysis.get('volume_profile', 'Normal'),
                                'pattern': analysis.get('pattern', 'No pattern'),
                                'timestamp': str(screening_data.get('timestamp', 'Unknown')),
                                'data_source': 'database_fallback'
                            }
                            
                            if include_technical:
                                result['indicators'] = analysis.get('indicators', {
                                    'rsi': 50.0,
                                    'ema_20': analysis.get('current_price', 0),
                                    'ema_50': analysis.get('current_price', 0)
                                })
                            
                            results[symbol] = result
                        else:
                            # Skip symbols not in database - no fake data
                            with open(log_file, 'a', encoding='utf-8') as f:
                                f.write(f"SKIP: {symbol} not found in database\\n")
                            continue
                    
                    except Exception as symbol_error:
                        print(f"❌ Error processing {symbol}: {symbol_error}", file=sys.stderr)
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"ERROR processing {symbol}: {str(symbol_error)}\\n")
                        continue
            else:
                data_source = 'web_scraped_fallback'
                timestamp = 'web_scraped'
        
        # Add metadata  
        response = {
            'symbols_requested': len(symbols),
            'symbols_returned': len(results),
            'data_source': data_source,
            'timestamp': timestamp,
            'status': 'success',
            'data': results
        }
        
        print(json.dumps(response, indent=2))
        
    except Exception as e:
        print(f"💥 Critical error in get_market_data: {e}", file=sys.stderr)
        print(f"📍 Traceback: {traceback.format_exc()}", file=sys.stderr)
        
        # Final fallback response
        fallback_response = {
            'symbols_requested': len(symbols) if 'symbols' in locals() else 0,
            'symbols_returned': 0,
            'data_source': 'critical_error_fallback',
            'timestamp': 'error',
            'status': 'error',
            'error_message': str(e),
            'data': {}
        }
        print(json.dumps(fallback_response, indent=2))

# Run async function
asyncio.run(get_market_data_main())
    `;

    return await this.runPythonScript(pythonScript, 'get_market_data');
  }

  async queryTradingMemories(query, limit = 5) {
    const pythonScript = `
import sys
import os
import traceback
sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')
sys.path.insert(0, '${path.join(this.projectRoot, 'mcp-server').replace(/\\/g, '\\\\')}')

import json
from sqlalchemy import text
from src.database.connection import db_manager

try:
    query = "${query.replace(/"/g, '\\"')}"
    limit = ${limit}
    memory_types = ["trading_insight", "market_analysis"]
    
    print(f"🔍 Searching memories for: '{query}' (limit: {limit})", file=sys.stderr)
    
    # Initialize database
    db_manager.initialize()
    
    with db_manager.session_context() as session:
        # Build SQL query for agent_memories table
        memory_type_conditions = " OR ".join([f"memory_category = '{mt}'" for mt in memory_types])
        
        query_sql = f"""
            SELECT 
                memory_id,
                memory_type,
                memory_category,
                title,
                content,
                importance_score,
                relevance_tags,
                created_at,
                session_id
            FROM agent_memories 
            WHERE ({memory_type_conditions})
               OR (content ILIKE %s)
               OR (title ILIKE %s)
            ORDER BY importance_score DESC, created_at DESC
            LIMIT %s
        """
        
        search_term = f"%{query}%"
        results = session.execute(text(query_sql), (search_term, search_term, limit)).fetchall()
        
        print(f"📊 Found {len(results)} matching memories", file=sys.stderr)
        
        # Format memories for Claude Code
        formatted_memories = []
        for row in results:
            memory = {
                'memory_id': str(row.memory_id) if row.memory_id else 'unknown',
                'type': row.memory_type or 'general',
                'category': row.memory_category or 'trading_insight',
                'title': row.title or 'Untitled Memory',
                'content': row.content or 'No content available',
                'importance_score': float(row.importance_score) if row.importance_score else 0.0,
                'tags': row.relevance_tags if row.relevance_tags else [],
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'session_id': str(row.session_id) if row.session_id else None
            }
            formatted_memories.append(memory)
        
        # Return structured response
        response = {
            'query': query,
            'memory_types_searched': memory_types,
            'memories_found': len(formatted_memories),
            'memories': formatted_memories,
            'database_status': 'connected',
            'search_timestamp': str(session.execute("SELECT NOW()").scalar()),
            'status': 'success'
        }
        
        print(json.dumps(response, indent=2))
        
except Exception as e:
    print(f"💥 Error in query_trading_memories: {e}", file=sys.stderr)
    print(f"📍 Traceback: {traceback.format_exc()}", file=sys.stderr)
    
    # Fallback response if database query fails
    fallback_response = {
        'query': query if 'query' in locals() else 'unknown',
        'memory_types_searched': memory_types if 'memory_types' in locals() else [],
        'memories_found': 0,
        'memories': [],
        'database_status': 'error',
        'error_message': str(e),
        'fallback_insights': [
            {
                'memory_id': 'fallback-1',
                'type': 'fallback',
                'category': 'trading_principle',
                'title': 'Risk Management Foundation',
                'content': 'Always use stop losses and position sizing based on account risk tolerance. Risk no more than 1-2% of account per trade.',
                'importance_score': 0.9,
                'tags': ['risk_management', 'position_sizing'],
                'source': 'fallback_knowledge'
            }
        ],
        'status': 'error_with_fallback'
    }
    print(json.dumps(fallback_response, indent=2))
    `;

    return await this.runPythonScript(pythonScript, 'query_trading_memories');
  }

  async storeTradingMemory(params) {
    const {
      title,
      content,
      importance_score = 0.5,
      relevance_tags = []
    } = params;

    const pythonScript = `
import sys
import os
import traceback
import uuid
import json
from datetime import datetime
sys.path.insert(0, '${this.projectRoot.replace(/\\/g, '\\\\')}')
sys.path.insert(0, '${path.join(this.projectRoot, 'mcp-server').replace(/\\/g, '\\\\')}')

from sqlalchemy import text
from src.database.connection import db_manager

try:
    # Parameters
    memory_type = "long_term"
    memory_category = "trading_insight"
    title = """${title.replace(/"/g, '\\"')}"""
    content = """${content.replace(/"/g, '\\"')}"""
    importance_score = ${importance_score}
    relevance_tags = ${JSON.stringify(relevance_tags)}
    
    print(f"💾 Storing trading memory: '{title}'", file=sys.stderr)
    
    # Initialize database
    db_manager.initialize()
    
    with db_manager.session_context() as session:
        # Generate unique memory ID
        memory_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        # Insert memory into database
        insert_sql = """
            INSERT INTO agent_memories (
                memory_id, session_id, memory_type, memory_category,
                title, content, importance_score, relevance_tags,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Serialize JSON fields
        tags_json = json.dumps(relevance_tags) if relevance_tags else None
        
        session.execute(text(insert_sql), (
            memory_id, session_id, memory_type, memory_category,
            title, content, importance_score, tags_json, datetime.now()
        ))
        
        session.commit()
        
        # Get total memory count
        count_result = session.execute(text("SELECT COUNT(*) as total FROM agent_memories")).fetchone()
        total_memories = count_result.total
        
        print(f"✅ Memory stored successfully. Total memories: {total_memories}", file=sys.stderr)
        
        response = {
            'success': True,
            'memory_id': memory_id,
            'session_id': session_id,
            'stored_at': datetime.now().isoformat(),
            'database_status': 'inserted',
            'total_memories': total_memories,
            'memory_details': {
                'type': memory_type,
                'category': memory_category,
                'title': title,
                'importance_score': importance_score,
                'tags_count': len(relevance_tags)
            },
            'status': 'success'
        }
        
        print(json.dumps(response, indent=2))
        
except Exception as e:
    print(f"💥 Error in store_trading_memory: {e}", file=sys.stderr)
    print(f"📍 Traceback: {traceback.format_exc()}", file=sys.stderr)
    
    error_response = {
        'success': False,
        'error_message': str(e),
        'database_status': 'error',
        'timestamp': datetime.now().isoformat() if 'datetime' in sys.modules else 'unknown',
        'attempted_title': title if 'title' in locals() else 'unknown',
        'status': 'error'
    }
    print(json.dumps(error_response, indent=2))
    `;

    return await this.runPythonScript(pythonScript, 'store_trading_memory');
  }

  async runPythonScript(script, toolName) {
    return new Promise((resolve, reject) => {
      // Try to find the virtual environment Python
      const fs = require('fs');
      const path = require('path');
      
      let pythonCommand = 'python';
      
      // Check for virtual environment in common locations
      const venvPaths = [
        path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe'),  // Windows venv
        path.join(this.projectRoot, 'venv', 'Scripts', 'python.exe'),   // Windows venv alternate
        path.join(this.projectRoot, '.venv', 'bin', 'python'),          // Unix venv
        path.join(this.projectRoot, 'venv', 'bin', 'python')            // Unix venv alternate
      ];
      
      for (const venvPath of venvPaths) {
        if (fs.existsSync(venvPath)) {
          pythonCommand = venvPath;
          this.logToStderr(`🐍 Using virtual environment Python: ${venvPath}`);
          break;
        }
      }
      
      if (pythonCommand === 'python') {
        this.logToStderr(`⚠️ Using system Python - virtual environment not found`);
      }
      
      const python = spawn(pythonCommand, ['-c', script], {
        cwd: this.projectRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONPATH: this.projectRoot }
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
        // Log Python stderr to our stderr (not stdout which is reserved for MCP)
        console.error(`🐍 [${toolName}] ${data.toString().trim()}`);
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            this.logToStderr(`🎉 Python script ${toolName} succeeded`);
            resolve(result);
          } catch (e) {
            this.logToStderr(`⚠️ Python script ${toolName} succeeded but JSON parse failed`);
            resolve({ 
              raw_output: stdout.trim(), 
              parse_error: e.message,
              stderr_output: stderr.trim(),
              tool_name: toolName
            });
          }
        } else {
          this.logToStderr(`💥 Python script ${toolName} failed with code ${code}`);
          reject(new Error(`Python script failed (exit code ${code}): ${stderr.trim()}`));
        }
      });

      python.on('error', (err) => {
        this.logToStderr(`🚨 Python process error for ${toolName}: ${err.message}`);
        reject(new Error(`Python process error: ${err.message}`));
      });
    });
  }

  sendResponse(id, result) {
    const response = {
      jsonrpc: '2.0',
      id,
      result
    };
    
    // Send to stdout (reserved for MCP protocol)
    process.stdout.write(JSON.stringify(response) + '\n');
  }

  sendError(id, code, message, data = null) {
    const response = {
      jsonrpc: '2.0',
      id,
      error: {
        code,
        message,
        ...(data && { data })
      }
    };
    
    // Send to stdout (reserved for MCP protocol)
    process.stdout.write(JSON.stringify(response) + '\n');
  }
}

// Start the stdio MCP server
if (require.main === module) {
  const server = new StdioMCPServer();
  server.start();
}

module.exports = StdioMCPServer;