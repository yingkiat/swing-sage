@echo off
echo Starting Swing Sage MCP Server...
cd /d "%~dp0mcp-server"
node trading-mcp-stdio.js
pause