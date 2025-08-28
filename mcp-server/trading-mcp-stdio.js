#!/usr/bin/env node
/**
 * Swing Sage Trading MCP Server - Modular Stdio Protocol
 * 
 * Hybrid approach: Clean JavaScript MCP handling + proven Python logic in CLI scripts.
 * This preserves the working IBKR integration while making the code maintainable.
 */

const { spawn } = require('child_process');
const path = require('path');

class ModularStdioMCPServer {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '..');
    this.scriptsDir = path.join(__dirname, 'scripts');
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
    this.logToStderr('🚀 Swing Sage Modular MCP Server initialized');
    this.logToStderr(`📁 Project root: ${this.projectRoot}`);
    this.logToStderr(`📁 Scripts dir: ${this.scriptsDir}`);
  }

  logToStderr(message) {
    // Use stderr for logging since stdout is reserved for MCP protocol
    console.error(`[Modular MCP] ${message}`);
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
    this.logToStderr('🔧 Initializing modular MCP server...');
    
    const response = {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
        logging: {}
      },
      serverInfo: {
        name: 'swing-sage-trading-server-modular',
        version: '1.0.0'
      }
    };

    this.sendResponse(id, response);
    this.logToStderr('✅ Modular MCP server initialized successfully');
  }

  async handleToolsList(id) {
    const tools = [
      {
        name: 'get_market_data',
        description: 'Fetch current market data and technical analysis for specified stock symbols (Modular Version)',
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
        description: 'Search the PostgreSQL memory database for relevant trading insights and past analysis (Legacy)',
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
        description: 'Save new trading analysis or recommendations to the PostgreSQL memory database (Legacy)',
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
          result = await this.getMarketDataModular(args.symbols, args.include_technical);
          break;
        
        case 'query_trading_memories':
          result = await this.queryTradingMemoriesLegacy(args.query, args.limit);
          break;
        
        case 'store_trading_memory':
          result = await this.storeTradingMemoryLegacy(args);
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

  /**
   * NEW MODULAR APPROACH: Call clean Python CLI script instead of generating code
   */
  async getMarketDataModular(symbols, includeTechnical = true) {
    try {
      this.logToStderr('🔄 Using modular approach with Python CLI script');
      
      const scriptPath = path.join(this.scriptsDir, 'get_market_data.py');
      const symbolsArg = symbols.join(',');
      
      const args = [
        scriptPath,
        '--symbols', symbolsArg,
        '--technical', includeTechnical.toString()
      ];
      
      this.logToStderr(`📞 Calling: python ${scriptPath} --symbols ${symbolsArg} --technical ${includeTechnical}`);
      
      const result = await this.runPythonCLI(args, 'get_market_data_modular');
      
      this.logToStderr('✅ Modular market data fetch completed');
      return result;
      
    } catch (error) {
      this.logToStderr(`❌ Modular market data failed: ${error.message}`);
      
      // Fallback response
      return {
        symbols_requested: symbols.length,
        symbols_returned: 0,
        data_source: 'modular_script_error',
        timestamp: new Date().toISOString(),
        status: 'error',
        error_message: error.message,
        data: {}
      };
    }
  }


  /**
   * LEGACY APPROACHES: Keep for memory tools until we migrate them
   */
  async queryTradingMemoriesLegacy(query, limit = 5) {
    this.logToStderr('⚠️ Using legacy approach for memory queries (TODO: migrate to CLI script)');
    
    // For now, use the proven generated script approach from backup
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
    
    # Fallback response
    fallback_response = {
        'query': query if 'query' in locals() else 'unknown',
        'memory_types_searched': memory_types if 'memory_types' in locals() else [],
        'memories_found': 0,
        'memories': [],
        'database_status': 'error',
        'error_message': str(e),
        'status': 'error_with_fallback'
    }
    print(json.dumps(fallback_response, indent=2))
    `;

    return await this.runPythonScript(pythonScript, 'query_trading_memories_legacy');
  }

  async storeTradingMemoryLegacy(params) {
    this.logToStderr('⚠️ Using legacy approach for memory storage (TODO: migrate to CLI script)');
    
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

    return await this.runPythonScript(pythonScript, 'store_trading_memory_legacy');
  }

  /**
   * NEW: Run Python CLI scripts instead of generating code
   */
  async runPythonCLI(scriptArgs, toolName) {
    return new Promise((resolve, reject) => {
      // Find virtual environment Python (same logic as backup)
      const fs = require('fs');
      const path = require('path');
      
      let pythonCommand = 'python';
      
      const venvPaths = [
        path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe'),  // Windows
        path.join(this.projectRoot, 'venv', 'Scripts', 'python.exe'),   
        path.join(this.projectRoot, '.venv', 'bin', 'python'),          // Unix
        path.join(this.projectRoot, 'venv', 'bin', 'python')            
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
      
      const python = spawn(pythonCommand, scriptArgs, {
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
        // Log Python stderr to our stderr
        console.error(`🐍 [${toolName}] ${data.toString().trim()}`);
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            this.logToStderr(`🎉 Python CLI script ${toolName} succeeded`);
            resolve(result);
          } catch (e) {
            this.logToStderr(`⚠️ Python CLI script ${toolName} succeeded but JSON parse failed`);
            resolve({ 
              raw_output: stdout.trim(), 
              parse_error: e.message,
              stderr_output: stderr.trim(),
              tool_name: toolName
            });
          }
        } else {
          this.logToStderr(`💥 Python CLI script ${toolName} failed with code ${code}`);
          reject(new Error(`Python CLI script failed (exit code ${code}): ${stderr.trim()}`));
        }
      });

      python.on('error', (err) => {
        this.logToStderr(`🚨 Python process error for ${toolName}: ${err.message}`);
        reject(new Error(`Python process error: ${err.message}`));
      });
    });
  }

  /**
   * LEGACY: Keep for memory tools until migrated
   */
  async runPythonScript(script, toolName) {
    return new Promise((resolve, reject) => {
      const fs = require('fs');
      const path = require('path');
      
      let pythonCommand = 'python';
      
      const venvPaths = [
        path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe'),
        path.join(this.projectRoot, 'venv', 'Scripts', 'python.exe'),
        path.join(this.projectRoot, '.venv', 'bin', 'python'),
        path.join(this.projectRoot, 'venv', 'bin', 'python')
      ];
      
      for (const venvPath of venvPaths) {
        if (fs.existsSync(venvPath)) {
          pythonCommand = venvPath;
          break;
        }
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
        console.error(`🐍 [${toolName}] ${data.toString().trim()}`);
      });

      python.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            resolve(result);
          } catch (e) {
            resolve({ 
              raw_output: stdout.trim(), 
              parse_error: e.message,
              stderr_output: stderr.trim(),
              tool_name: toolName
            });
          }
        } else {
          reject(new Error(`Python script failed (exit code ${code}): ${stderr.trim()}`));
        }
      });

      python.on('error', (err) => {
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
    
    process.stdout.write(JSON.stringify(response) + '\n');
  }
}

// Start the modular stdio MCP server
if (require.main === module) {
  const server = new ModularStdioMCPServer();
  server.start();
}

module.exports = ModularStdioMCPServer;