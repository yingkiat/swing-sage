#!/usr/bin/env python3
"""
Debug the MCP server error by running the Python script directly
"""

import sys
import os
import json
import traceback

# Add paths
project_root = os.path.dirname(os.path.dirname(__file__))
mcp_server_path = os.path.join(project_root, 'mcp-server', 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, mcp_server_path)

def debug_get_market_data():
    """Debug the exact Python code that the MCP server runs"""
    
    print("🔍 Debugging get_market_data function...")
    
    try:
        # Simple test first - just imports and basic setup
        print("1️⃣ Testing imports...")
        import asyncio
        from database.connection import db_manager
        from brokers.ibkr import IBKRBroker
        import threading
        import queue
        print("✅ All imports successful")
        
        print("2️⃣ Testing database initialization...")
        db_manager.initialize()
        print("✅ Database initialized")
        
        print("3️⃣ Testing IBKR threaded connection...")
        
        def run_ibkr_in_thread(result_queue, symbols):
            try:
                # Create a new event loop for this thread
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                broker = IBKRBroker(paper_trading=True, host='127.0.0.1', port=7497, client_id=1)
                broker.connect()
                
                thread_results = {}
                for symbol in symbols:
                    try:
                        print(f"🔍 Requesting comprehensive data for {symbol}...", file=sys.stderr)
                        
                        # Get basic quote
                        quote = broker.get_quote(symbol)
                        print(f"📊 Basic quote retrieved for {symbol}", file=sys.stderr)
                        
                        # Get additional market data
                        contract = broker._create_contract(symbol)
                        broker.ib.qualifyContracts(contract)
                        
                        # Request market data with all tick types
                        ticker = broker.ib.reqMktData(contract, 
                                                    genericTickList='100,101,104,106,165,221,225,233,236,258',
                                                    snapshot=False, 
                                                    regulatorySnapshot=False)
                        
                        # Wait longer for comprehensive data
                        broker.ib.sleep(3)
                        
                        # Collect all available tick data
                        comprehensive_data = {
                            'basic_quote': quote,
                            'all_ticks': {},
                            'market_data': {
                                'bid': ticker.bid,
                                'ask': ticker.ask,
                                'last': ticker.last,
                                'close': ticker.close,
                                'high': ticker.high,
                                'low': ticker.low,
                                'volume': ticker.volume,
                                'market_price': ticker.marketPrice(),
                                'avg_volume': getattr(ticker, 'avVolume', None),
                                'option_implied_vol': getattr(ticker, 'impliedVolatility', None),
                                'delta': getattr(ticker, 'delta', None),
                                'gamma': getattr(ticker, 'gamma', None),
                                'theta': getattr(ticker, 'theta', None),
                                'vega': getattr(ticker, 'vega', None),
                            }
                        }
                        
                        # Get historical data for technical analysis
                        try:
                            print(f"📈 Requesting historical data for {symbol}...", file=sys.stderr)
                            bars = broker.ib.reqHistoricalData(
                                contract, 
                                endDateTime='', 
                                durationStr='30 D',
                                barSizeSetting='1 day',
                                whatToShow='TRADES',
                                useRTH=True,
                                formatDate=1
                            )
                            
                            if bars:
                                comprehensive_data['historical_data'] = {
                                    'bar_count': len(bars),
                                    'last_5_bars': [
                                        {
                                            'date': str(bar.date),
                                            'open': bar.open,
                                            'high': bar.high,
                                            'low': bar.low,
                                            'close': bar.close,
                                            'volume': bar.volume
                                        } for bar in bars[-5:]  # Last 5 days
                                    ]
                                }
                            else:
                                comprehensive_data['historical_data'] = {'error': 'No historical data'}
                                
                        except Exception as hist_error:
                            print(f"❌ Historical data error: {hist_error}", file=sys.stderr)
                            comprehensive_data['historical_data'] = {'error': str(hist_error)}
                        
                        # Try to get fundamentals
                        try:
                            print(f"📋 Requesting fundamentals for {symbol}...", file=sys.stderr)
                            fundamentals = broker.ib.reqFundamentalData(contract, 'ReportSnapshot', [])
                            if fundamentals:
                                comprehensive_data['fundamentals'] = {'available': True, 'data': str(fundamentals)[:200]}
                            else:
                                comprehensive_data['fundamentals'] = {'available': False}
                        except Exception as fund_error:
                            comprehensive_data['fundamentals'] = {'error': str(fund_error)}
                        
                        thread_results[symbol] = comprehensive_data
                        print(f"✅ Comprehensive data collected for {symbol}", file=sys.stderr)
                        
                    except Exception as e:
                        print(f"❌ Error getting data for {symbol}: {e}", file=sys.stderr)
                        thread_results[symbol] = {'error': str(e)}
                
                broker.disconnect()
                result_queue.put(('success', thread_results))
                
            except Exception as e:
                result_queue.put(('error', str(e)))
        
        # Test IBKR connection
        symbols = ["AAPL"]
        result_queue = queue.Queue()
        thread = threading.Thread(target=run_ibkr_in_thread, args=(result_queue, symbols))
        thread.start()
        thread.join(timeout=15)
        
        if thread.is_alive():
            print("⏰ IBKR thread timeout")
            ibkr_success = False
            ibkr_results = {}
        else:
            try:
                status, ibkr_quotes = result_queue.get_nowait()
                if status == 'error':
                    print(f"❌ IBKR thread error: {ibkr_quotes}")
                    ibkr_success = False
                    ibkr_results = {}
                else:
                    print("✅ IBKR thread successful")
                    
                    # Process results
                    ibkr_results = {}
                    for symbol in symbols:
                        if symbol in ibkr_quotes and 'error' not in ibkr_quotes[symbol]:
                            comprehensive_data = ibkr_quotes[symbol]
                            
                            print(f"\n" + "="*60)
                            print(f"📊 COMPREHENSIVE IBKR DATA for {symbol}")
                            print("="*60)
                            
                            # 1. Basic Quote Data
                            basic_quote = comprehensive_data.get('basic_quote', {})
                            print(f"\n🔸 BASIC QUOTE:")
                            print(json.dumps(basic_quote, indent=2, default=str))
                            
                            # 2. Extended Market Data
                            market_data = comprehensive_data.get('market_data', {})
                            print(f"\n🔸 EXTENDED MARKET DATA:")
                            for key, value in market_data.items():
                                print(f"   {key}: {value}")
                            
                            # 3. Historical Data
                            historical = comprehensive_data.get('historical_data', {})
                            print(f"\n🔸 HISTORICAL DATA:")
                            if 'last_5_bars' in historical:
                                print(f"   Available bars: {historical.get('bar_count', 0)}")
                                print("   Last 5 trading days:")
                                for bar in historical['last_5_bars']:
                                    print(f"     {bar['date']}: O={bar['open']:.2f} H={bar['high']:.2f} L={bar['low']:.2f} C={bar['close']:.2f} V={bar['volume']}")
                            else:
                                print(f"   {historical}")
                            
                            # 4. Fundamentals
                            fundamentals = comprehensive_data.get('fundamentals', {})
                            print(f"\n🔸 FUNDAMENTALS:")
                            print(f"   {fundamentals}")
                            
                            # 5. Try to find best price source from all data
                            print(f"\n🎯 PRICE SOURCE ANALYSIS:")
                            price = None
                            price_source = "none"
                            
                            # Try market data first
                            if market_data.get('market_price') is not None and market_data['market_price'] == market_data['market_price']:
                                price = market_data['market_price']
                                price_source = "market_price"
                            elif market_data.get('last') is not None and market_data['last'] == market_data['last']:
                                price = market_data['last']
                                price_source = "last_price"
                            elif market_data.get('bid') is not None and market_data.get('ask') is not None:
                                price = (market_data['bid'] + market_data['ask']) / 2.0
                                price_source = "bid_ask_mid"
                            elif market_data.get('close') is not None:
                                price = market_data['close']
                                price_source = "previous_close"
                            # Try basic quote as fallback
                            elif basic_quote.get('price') is not None:
                                price = basic_quote['price']
                                price_source = "basic_quote_price"
                            elif basic_quote.get('last') is not None:
                                price = basic_quote['last']
                                price_source = "basic_quote_last"
                            # Try historical data as final fallback
                            elif historical.get('last_5_bars') and len(historical['last_5_bars']) > 0:
                                price = historical['last_5_bars'][-1]['close']
                                price_source = "historical_close"
                            
                            print(f"   SELECTED: {price_source} = {price}")
                            
                            if price is not None:
                                ibkr_results[symbol] = {
                                    'symbol': symbol,
                                    'current_price': float(price),
                                    'price_source': price_source,
                                    'data_source': 'ibkr_comprehensive',
                                    'comprehensive_data': comprehensive_data
                                }
                                print(f"✅ Successfully processed {symbol} with price ${price:.2f}")
                            else:
                                print(f"❌ No usable price data found for {symbol} in any source")
                        else:
                            error_msg = ibkr_quotes.get(symbol, {}).get('error', 'Unknown error')
                            print(f"❌ IBKR error for {symbol}: {error_msg}")
                    
                    ibkr_success = len(ibkr_results) > 0
                    
            except queue.Empty:
                print("❌ No results from IBKR thread")
                ibkr_success = False
                ibkr_results = {}
        
        print(f"4️⃣ IBKR Results: success={ibkr_success}, results={len(ibkr_results)}")
        
        # Create final response
        if ibkr_success:
            data_source = 'ibkr_live'
            results = ibkr_results
        else:
            print("5️⃣ No IBKR data available - would trigger web scraping fallback in MCP server")
            data_source = 'no_data_available'
            results = {}
        
        response = {
            'symbols_requested': len(symbols),
            'symbols_returned': len(results),
            'data_source': data_source,
            'status': 'success',
            'data': results
        }
        
        print("📄 Final response:")
        print(json.dumps(response, indent=2))
        return response
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = debug_get_market_data()
    if result and result.get('status') == 'success':
        print(f"\n✅ Debug PASSED - Data source: {result.get('data_source')}")
    else:
        print(f"\n❌ Debug FAILED")
    
    sys.exit(0 if result and result.get('status') == 'success' else 1)