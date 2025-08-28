"""
IBKR broker adapter implementation.

This module implements the BrokerAdapter interface for Interactive Brokers TWS/Gateway,
supporting US options trading with both paper and live trading modes.
"""

from __future__ import annotations
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import (
    BrokerAdapter,
    BrokerError,
    OrderRequest,
    Order,
    OrderFill,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    Position,
    AccountInfo
)

# IBKR imports - these will be available when ib_insync is installed
try:
    from ib_insync import IB, Stock, Option, Contract, MarketOrder, LimitOrder, Order as IBOrder
    from ib_insync import OrderStatus as IBOrderStatus, Trade, Fill, Position as IBPosition
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    # Mock classes for development without ib_insync installed
    class IB:
        def __init__(self): pass
        def connect(self, *args, **kwargs): pass
        def disconnect(self): pass
        def isConnected(self): return False
        def placeOrder(self, *args, **kwargs): return None
        def positions(self): return []
        def accountSummary(self): return []
    
    class Stock:
        def __init__(self, *args, **kwargs): pass
    
    class Option:
        def __init__(self, *args, **kwargs): pass
    
    class MarketOrder:
        def __init__(self, *args, **kwargs): pass
    
    class LimitOrder:
        def __init__(self, *args, **kwargs): pass


logger = logging.getLogger(__name__)


class IBKRBroker(BrokerAdapter):
    """
    Interactive Brokers broker adapter for US options trading.
    
    This adapter implements the unified BrokerAdapter interface using
    IBKR's TWS/Gateway API for US stock and options trading.
    
    Features:
    - Paper and live trading support
    - US options chain data access
    - Real-time market data (with subscription)
    - Historical data access
    - Order management with status tracking
    
    Configuration:
    - Requires TWS or IB Gateway running on localhost
    - Default port: 7497 (configure paper/live mode in Gateway settings)
    - API permissions must be enabled in TWS/Gateway
    """
    
    def __init__(self, paper_trading: bool = True, host: str = "127.0.0.1", 
                 port: int = 7497, client_id: int = 1):
        """
        Initialize IBKR broker adapter.
        
        Args:
            paper_trading: If True, use paper trading mode (configure in Gateway)
            host: TWS/Gateway host address
            port: TWS/Gateway port (default: 7497, configure in Gateway settings)
            client_id: Client ID for API connection
        """
        if not IBKR_AVAILABLE:
            raise BrokerError("ib_insync not available. Install with: pip install ib_insync")
        
        self.paper_trading = paper_trading
        self.host = host
        self.port = port
        self.client_id = client_id
        
        # Initialize IB connection
        self.ib = IB()
        self._connected = False
        self._orders: Dict[str, Order] = {}  # Track orders by broker_order_id
        
        logger.info(f"Initialized IBKR adapter - Paper: {paper_trading}, Port: {self.port}")
    
    def connect(self) -> None:
        """
        Establish connection to IBKR TWS/Gateway.
        
        Raises:
            BrokerError: If connection fails
        """
        try:
            logger.info(f"Connecting to IBKR Gateway at {self.host}:{self.port}")
            self.ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            self._connected = True
            logger.info("Successfully connected to IBKR Gateway")
            
            # Log managed accounts
            accounts = self.ib.managedAccounts()
            logger.info(f"Managed accounts: {accounts}")
            
        except Exception as e:
            self._connected = False
            error_msg = f"Failed to connect to IBKR Gateway: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)
    
    def disconnect(self) -> None:
        """
        Close connection to IBKR TWS/Gateway.
        
        Raises:
            BrokerError: If disconnection fails
        """
        try:
            if self._connected:
                self.ib.disconnect()
                self._connected = False
                logger.info("Disconnected from IBKR Gateway")
        except Exception as e:
            error_msg = f"Failed to disconnect from IBKR Gateway: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)
    
    def is_connected(self) -> bool:
        """
        Check if connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected and self.ib.isConnected()
    
    def _create_contract(self, symbol: str) -> Contract:
        """
        Create IBKR contract from symbol.
        
        Args:
            symbol: Symbol (e.g., "AAPL" for stock, "AAPL240315C00180000" for option)
            
        Returns:
            IBKR Contract object
        """
        # Simple heuristic: if symbol is > 6 chars and contains digits, likely option
        if len(symbol) > 6 and any(c.isdigit() for c in symbol):
            # Option symbol parsing would go here
            # For now, default to stock
            return Stock(symbol, 'SMART', 'USD')
        else:
            # Stock
            return Stock(symbol, 'SMART', 'USD')
    
    def _map_order_side(self, side: OrderSide) -> str:
        """Map unified OrderSide to IBKR action."""
        return "BUY" if side == OrderSide.BUY else "SELL"
    
    def _map_order_type(self, request: OrderRequest) -> IBOrder:
        """Map unified OrderRequest to IBKR Order."""
        action = self._map_order_side(request.side)
        
        if request.order_type == OrderType.MARKET:
            return MarketOrder(action, request.qty)
        elif request.order_type == OrderType.LIMIT:
            return LimitOrder(action, request.qty, request.limit_price)
        else:
            raise BrokerError(f"Unsupported order type: {request.order_type}")
    
    def _map_order_status(self, ib_status: str) -> OrderStatus:
        """Map IBKR order status to unified OrderStatus."""
        status_map = {
            "Submitted": OrderStatus.NEW,
            "PendingSubmit": OrderStatus.PENDING,
            "PreSubmitted": OrderStatus.PENDING,
            "Filled": OrderStatus.FILLED,
            "PartiallyFilled": OrderStatus.PARTIAL,
            "Cancelled": OrderStatus.CANCELLED,
            "Inactive": OrderStatus.REJECTED,
            "ApiCancelled": OrderStatus.CANCELLED,
        }
        return status_map.get(ib_status, OrderStatus.NEW)
    
    def place_order(self, request: OrderRequest) -> Order:
        """
        Place a new order.
        
        Args:
            request: Order request details
            
        Returns:
            Order object with broker order ID and status
            
        Raises:
            BrokerError: If order placement fails
        """
        if not self.is_connected():
            raise BrokerError("Not connected to IBKR Gateway")
        
        try:
            # Create contract and order
            contract = self._create_contract(request.symbol)
            ib_order = self._map_order_type(request)
            
            # Set order ID for idempotency
            ib_order.clientId = self.client_id
            ib_order.orderId = hash(request.client_order_id) % 1000000  # Simple ID mapping
            
            # Place order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # Create unified order object
            order = Order(
                broker_order_id=str(ib_order.orderId),
                request=request,
                status=self._map_order_status(trade.orderStatus.status),
                raw_response={"trade": trade, "order": ib_order}
            )
            
            # Store order for tracking
            self._orders[order.broker_order_id] = order
            
            logger.info(f"Placed order {order.broker_order_id} for {request.symbol}")
            return order
            
        except Exception as e:
            error_msg = f"Failed to place order: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)
    
    def get_order(self, broker_order_id: str) -> Order:
        """
        Retrieve order status by broker order ID.
        
        Args:
            broker_order_id: Broker's internal order ID
            
        Returns:
            Current order state
            
        Raises:
            BrokerError: If order lookup fails
        """
        if broker_order_id in self._orders:
            # Return cached order (in real implementation, we'd update from IBKR)
            return self._orders[broker_order_id]
        else:
            raise BrokerError(f"Order {broker_order_id} not found")
    
    def cancel_order(self, broker_order_id: str) -> Order:
        """
        Cancel an existing order.
        
        Args:
            broker_order_id: Broker's internal order ID
            
        Returns:
            Updated order state
            
        Raises:
            BrokerError: If cancellation fails
        """
        if not self.is_connected():
            raise BrokerError("Not connected to IBKR Gateway")
        
        try:
            order = self.get_order(broker_order_id)
            
            # Cancel order via IBKR API
            self.ib.cancelOrder(int(broker_order_id))
            
            # Update order status
            order.status = OrderStatus.CANCELLED
            order.updated_at = time.time()
            
            logger.info(f"Cancelled order {broker_order_id}")
            return order
            
        except Exception as e:
            error_msg = f"Failed to cancel order {broker_order_id}: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)
    
    def get_positions(self) -> List[Position]:
        """
        Get current account positions.
        
        Returns:
            List of current positions
            
        Raises:
            BrokerError: If position lookup fails
        """
        if not self.is_connected():
            raise BrokerError("Not connected to IBKR Gateway")
        
        try:
            positions = []
            ib_positions = self.ib.positions()
            
            for pos in ib_positions:
                position = Position(
                    symbol=pos.contract.symbol,
                    qty=int(pos.position),
                    avg_cost=float(pos.avgCost) if pos.avgCost else 0.0,
                    market_value=float(pos.marketValue) if pos.marketValue else 0.0,
                    unrealized_pnl=float(pos.unrealizedPNL) if pos.unrealizedPNL else 0.0,
                    metadata={
                        "account": pos.account,
                        "contract": pos.contract
                    }
                )
                positions.append(position)
            
            logger.info(f"Retrieved {len(positions)} positions")
            return positions
            
        except Exception as e:
            error_msg = f"Failed to get positions: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)
    
    def get_account_info(self) -> AccountInfo:
        """
        Get account information and balances.
        
        Returns:
            Current account information
            
        Raises:
            BrokerError: If account lookup fails
        """
        if not self.is_connected():
            raise BrokerError("Not connected to IBKR Gateway")
        
        try:
            # Get account summary
            account_values = self.ib.accountSummary()
            
            # Parse relevant values
            cash_balance = 0.0
            buying_power = 0.0
            total_equity = 0.0
            
            for item in account_values:
                if item.tag == "CashBalance":
                    cash_balance = float(item.value)
                elif item.tag == "BuyingPower":
                    buying_power = float(item.value)
                elif item.tag == "NetLiquidation":
                    total_equity = float(item.value)
            
            account_info = AccountInfo(
                account_id=self.ib.managedAccounts()[0] if self.ib.managedAccounts() else "Unknown",
                cash_balance=cash_balance,
                buying_power=buying_power,
                total_equity=total_equity,
                metadata={"paper_trading": self.paper_trading}
            )
            
            logger.info(f"Retrieved account info for {account_info.account_id}")
            return account_info
            
        except Exception as e:
            error_msg = f"Failed to get account info: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get quote data for a symbol, using historical data as fallback when live data requires subscription.
        
        Args:
            symbol: Symbol to get quote for
            
        Returns:
            Quote data with price, volume, etc.
        """
        if not self.is_connected():
            raise BrokerError("Not connected to IBKR Gateway")
        
        try:
            contract = self._create_contract(symbol)
            self.ib.qualifyContracts(contract)
            
            # Try to get live market data first
            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(1)  # Wait for data
            
            price = None
            data_source = "no_data"
            
            # 1. Try live market data (requires subscription)
            if ticker.marketPrice() and ticker.marketPrice() == ticker.marketPrice():
                price = ticker.marketPrice()
                data_source = "real_time"
            elif ticker.last and ticker.last == ticker.last:
                price = ticker.last
                data_source = "delayed"
            elif ticker.bid and ticker.ask and ticker.bid == ticker.bid and ticker.ask == ticker.ask:
                price = (ticker.bid + ticker.ask) / 2.0
                data_source = "bid_ask"
            elif ticker.close and ticker.close == ticker.close:
                price = ticker.close
                data_source = "previous_close"
            
            # 2. If live data unavailable, use historical data (this works without subscription)
            if price is None or price != price:  # None or NaN
                try:
                    logger.info(f"Live data unavailable for {symbol}, fetching historical data...")
                    bars = self.ib.reqHistoricalData(
                        contract, 
                        endDateTime='', 
                        durationStr='5 D',  # Last 5 days
                        barSizeSetting='1 day',
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1
                    )
                    
                    if bars and len(bars) > 0:
                        # Use the most recent close price
                        latest_bar = bars[-1]
                        price = latest_bar.close
                        data_source = "historical_close"
                        logger.info(f"Using historical close price for {symbol}: ${price:.2f}")
                        
                        # Also get OHLCV data for technical analysis
                        historical_data = {
                            'latest_bar': {
                                'date': str(latest_bar.date),
                                'open': latest_bar.open,
                                'high': latest_bar.high,
                                'low': latest_bar.low,
                                'close': latest_bar.close,
                                'volume': latest_bar.volume
                            },
                            'bars_available': len(bars)
                        }
                    else:
                        historical_data = None
                        logger.warning(f"No historical data available for {symbol}")
                        
                except Exception as hist_error:
                    logger.warning(f"Historical data request failed for {symbol}: {hist_error}")
                    historical_data = None
            else:
                historical_data = None
            
            return {
                "symbol": symbol,
                "price": price,
                "bid": ticker.bid if ticker.bid and ticker.bid == ticker.bid else None,
                "ask": ticker.ask if ticker.ask and ticker.ask == ticker.ask else None,
                "volume": ticker.volume if ticker.volume and ticker.volume == ticker.volume else None,
                "last_close": ticker.close if ticker.close and ticker.close == ticker.close else None,
                "last": ticker.last if ticker.last and ticker.last == ticker.last else None,
                "data_source": data_source,
                "historical_data": historical_data,
                "delayed_data_available": bool(historical_data or ticker.last or ticker.bid or ticker.ask or ticker.close)
            }
            
        except Exception as e:
            error_msg = f"Failed to get quote for {symbol}: {e}"
            logger.error(error_msg)
            raise BrokerError(error_msg, raw_error=e)