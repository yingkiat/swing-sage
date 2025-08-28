#!/usr/bin/env python3
"""
Market data CLI script - EXACT COPY of the working logic from stdio-backup.js
This preserves all your proven threading, fallback, and error handling logic.
"""

import sys
import os
import asyncio
import json
import traceback
import threading
import queue
import argparse
from pathlib import Path

# Add paths exactly as in working backup
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'mcp-server'))

from src.database.connection import db_manager
from src.brokers.ibkr import IBKRBroker

async def get_market_data_main(symbols, include_technical):
    """
    EXACT COPY of the async function from your working stdio-backup.js
    """
    try:
        print(f"🔍 Fetching market data for: {symbols}", file=sys.stderr)
        
        # Log progress to file
        log_file = str(project_root / 'mcp-debug.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\nSTEP: Starting market data fetch for {symbols}\n")
        
        # Initialize database for fallback
        db_manager.initialize()
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("STEP: Database initialized successfully\n")
        
        # Try IBKR first, then fallback to database
        ibkr_results = {}
        ibkr_success = False
        
        try:
            print("🏦 Attempting IBKR connection...", file=sys.stderr)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("STEP: Starting IBKR connection attempt\n")
            
            # Run IBKR in a separate thread to avoid event loop conflicts
            def run_ibkr_in_thread(result_queue, symbols):
                try:
                    # Create a new event loop for this thread
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
                                f.write(f"SKIP: No valid price data for {symbol} (price={price})\n")
                            continue
                        
                        # Extract rich data from IBKR historical bars
                        historical_data = quote.get('historical_data', {})
                        if historical_data and 'latest_bar' in historical_data:
                            latest_bar = historical_data['latest_bar']
                            daily_high = latest_bar.get('high', price)
                            daily_low = latest_bar.get('low', price)
                            daily_volume = latest_bar.get('volume', 0)
                            daily_open = latest_bar.get('open', price)
                            
                            volume_info = f"Vol: {int(daily_volume):,}" if daily_volume else "Vol: N/A"
                            key_levels = f"Day High: ${daily_high:.2f}, Day Low: ${daily_low:.2f}, Open: ${daily_open:.2f}"
                            
                            # Calculate intraday metrics
                            daily_range = daily_high - daily_low
                            price_position = (price - daily_low) / daily_range if daily_range > 0 else 0.5
                            daily_change_pct = ((price - daily_open) / daily_open * 100) if daily_open > 0 else 0
                        else:
                            volume_info = str(quote.get("volume", "unknown")) + ' volume'
                            key_levels = f'Support: ${price-5:.2f}, Resistance: ${price+8:.2f}'
                            daily_range = 0
                            price_position = 0.5
                            daily_change_pct = 0
                        
                        result = {
                            'symbol': symbol,
                            'current_price': float(price),
                            'change_percent': round(daily_change_pct, 2),
                            'daily_range': round(daily_range, 2),
                            'price_position_in_range': round(price_position, 2),  # 0=at low, 1=at high
                            'setup_quality': data_quality,
                            'trend_direction': 'bullish' if daily_change_pct > 1 else 'bearish' if daily_change_pct < -1 else 'neutral',
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
                            # Calculate real technical indicators from historical data
                            bars_data = quote.get('comprehensive_data', {}).get('historical_data', {}).get('last_5_bars', [])
                            if not bars_data and 'historical_data' in quote:
                                # Fallback to basic historical data format
                                bars_data = [quote['historical_data']['latest_bar']] if 'latest_bar' in quote['historical_data'] else []
                            
                            if len(bars_data) >= 3:  # Need at least 3 bars for meaningful calculations
                                closes = [bar.get('close', price) for bar in bars_data]
                                highs = [bar.get('high', price) for bar in bars_data]  
                                lows = [bar.get('low', price) for bar in bars_data]
                                volumes = [bar.get('volume', 0) for bar in bars_data]
                                
                                # Simple 5-period moving average (approximates EMA for short term)
                                sma_5 = sum(closes) / len(closes)
                                
                                # Volume analysis
                                avg_volume = sum(volumes) / len(volumes) if volumes else 1
                                volume_ratio = (daily_volume / avg_volume) if avg_volume > 0 else 1.0
                                
                                # Price momentum (last close vs 5-period average)
                                momentum_score = (price - sma_5) / sma_5 if sma_5 > 0 else 0
                                
                                # Simple RSI approximation (price vs recent range)
                                recent_high = max(highs)
                                recent_low = min(lows)
                                range_position = (price - recent_low) / (recent_high - recent_low) if recent_high > recent_low else 0.5
                                rsi_approx = 30 + (range_position * 40)  # Scale to 30-70 range
                                
                                result['indicators'] = {
                                    'rsi_approx': round(rsi_approx, 1),
                                    'sma_5': round(sma_5, 2),
                                    'price_vs_sma5': round(momentum_score * 100, 1),  # % above/below SMA
                                    'volume_vs_avg': round(volume_ratio, 1),
                                    '5day_high': round(recent_high, 2),
                                    '5day_low': round(recent_low, 2),
                                    'range_position': round(range_position, 2)  # 0=at 5day low, 1=at 5day high
                                }
                            else:
                                # Fallback when insufficient historical data
                                result['indicators'] = {
                                    'note': 'Insufficient historical data for technical indicators',
                                    'daily_change_pct': round(daily_change_pct, 2),
                                    'price_in_daily_range': round(price_position, 2)
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
                f.write(f"ERROR: IBKR connection failed: {str(ibkr_error)}\n")
        
        # If IBKR succeeded, use those results, otherwise use database fallback
        if ibkr_success:
            results = ibkr_results
            data_source = 'ibkr_live'
            timestamp = 'live_ibkr'
        else:
            # Database fallback - EXACT same logic as working backup
            print("📋 Using database fallback...", file=sys.stderr)
            screening_data = await db_manager.get_latest_market_screening()
            data_source = 'database_fallback'
            timestamp = screening_data.get('timestamp', 'unknown')
            results = {}
            
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
                            f.write(f"SKIP: {symbol} not found in database\n")
                        continue
                
                except Exception as symbol_error:
                    print(f"❌ Error processing {symbol}: {symbol_error}", file=sys.stderr)
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"ERROR processing {symbol}: {str(symbol_error)}\n")
                    continue
        
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

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Get market data for symbols')
    parser.add_argument('--symbols', required=True, help='Comma-separated list of symbols')
    parser.add_argument('--technical', type=bool, default=True, help='Include technical indicators')
    
    args = parser.parse_args()
    symbols = [s.strip().upper() for s in args.symbols.split(',')]
    
    # Run the exact same async function from working backup
    asyncio.run(get_market_data_main(symbols, args.technical))

if __name__ == '__main__':
    main()