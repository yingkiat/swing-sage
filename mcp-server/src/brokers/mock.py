"""
Mock broker adapter for testing and development.

This module provides a mock implementation of the BrokerAdapter interface
for testing without requiring a real broker connection.
"""

from __future__ import annotations
import time
import random
from typing import Dict, List, Optional, Any

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


class MockBroker(BrokerAdapter):
    """
    Mock broker adapter for testing.
    
    Simulates order execution with configurable behavior for testing
    different scenarios including fills, rejections, and partial fills.
    """
    
    def __init__(self, 
                 simulate_latency: bool = True,
                 rejection_rate: float = 0.0,
                 partial_fill_rate: float = 0.0,
                 initial_cash: float = 100000.0):
        """
        Initialize mock broker.
        
        Args:
            simulate_latency: Add random delays to simulate network latency
            rejection_rate: Fraction of orders to reject (0.0 to 1.0)
            partial_fill_rate: Fraction of orders to partially fill (0.0 to 1.0)
            initial_cash: Starting cash balance
        """
        self.simulate_latency = simulate_latency
        self.rejection_rate = rejection_rate
        self.partial_fill_rate = partial_fill_rate
        
        # Mock account state
        self.cash_balance = initial_cash
        self.positions: Dict[str, Position] = {}
        self.orders: Dict[str, Order] = {}  # broker_order_id -> Order
        self.client_order_map: Dict[str, str] = {}  # client_order_id -> broker_order_id
        
        # Connection state
        self._connected = False
        self._order_counter = 1000
        
        # Market data simulation (simplified)
        self._market_prices = {
            'AAPL': 180.0,
            'MSFT': 380.0,
            'GOOGL': 140.0,
            'AMZN': 160.0,
            'AMD': 140.0,
            # Add some options symbols for testing
            'AAPL240315C00180000': 5.0,
            'MSFT240315C00380000': 8.0,
        }
    
    def connect(self) -> None:
        """Simulate connection to broker."""
        if self.simulate_latency:
            time.sleep(random.uniform(0.1, 0.3))
        
        self._connected = True
    
    def disconnect(self) -> None:
        """Simulate disconnection from broker."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
    
    def place_order(self, request: OrderRequest) -> Order:
        """
        Simulate order placement with configurable behavior.
        """
        if not self.is_connected():
            raise BrokerError("Mock broker not connected")
        
        # Check for idempotency
        if request.client_order_id in self.client_order_map:
            broker_order_id = self.client_order_map[request.client_order_id]
            return self.orders[broker_order_id]
        
        # Simulate network latency
        if self.simulate_latency:
            time.sleep(random.uniform(0.01, 0.05))
        
        # Generate broker order ID
        broker_order_id = f"MOCK_{self._order_counter}"
        self._order_counter += 1
        
        # Simulate order rejection
        if random.random() < self.rejection_rate:
            order = Order(
                broker_order_id=broker_order_id,
                request=request,
                status=OrderStatus.REJECTED,
                reject_reason="Mock rejection for testing"
            )
        else:
            order = Order(
                broker_order_id=broker_order_id,
                request=request,
                status=OrderStatus.NEW
            )
            
            # Simulate immediate or delayed fill
            self._simulate_fill(order)
        
        # Store order
        self.orders[broker_order_id] = order
        self.client_order_map[request.client_order_id] = broker_order_id
        
        return order
    
    def get_order(self, broker_order_id: str) -> Order:
        """Retrieve order by broker order ID."""
        if not self.is_connected():
            raise BrokerError("Mock broker not connected")
        
        if broker_order_id not in self.orders:
            raise BrokerError(f"Order not found: {broker_order_id}")
        
        order = self.orders[broker_order_id]
        
        # Simulate potential status updates
        if order.status == OrderStatus.NEW and random.random() < 0.1:
            self._simulate_fill(order)
        
        return order
    
    def cancel_order(self, broker_order_id: str) -> Order:
        """Cancel an order."""
        if not self.is_connected():
            raise BrokerError("Mock broker not connected")
        
        if broker_order_id not in self.orders:
            raise BrokerError(f"Order not found: {broker_order_id}")
        
        order = self.orders[broker_order_id]
        
        if order.is_terminal:
            raise BrokerError(f"Cannot cancel order in terminal state: {order.status}")
        
        order.status = OrderStatus.CANCELLED
        order.updated_at = time.time()
        
        return order
    
    def get_positions(self) -> List[Position]:
        """Get current positions."""
        if not self.is_connected():
            raise BrokerError("Mock broker not connected")
        
        return list(self.positions.values())
    
    def get_account_info(self) -> AccountInfo:
        """Get account information."""
        if not self.is_connected():
            raise BrokerError("Mock broker not connected")
        
        # Calculate total equity
        position_value = sum(pos.market_value for pos in self.positions.values())
        total_equity = self.cash_balance + position_value
        
        return AccountInfo(
            account_id="MOCK_ACCOUNT_123",
            cash_balance=self.cash_balance,
            buying_power=self.cash_balance * 2,  # Assume 2:1 margin
            total_equity=total_equity,
            day_trades_remaining=3,
            metadata={"mock": True}
        )
    
    def _simulate_fill(self, order: Order) -> None:
        """Simulate order fill with random behavior."""
        symbol = order.request.symbol
        
        # Get market price (with some random variation)
        base_price = self._market_prices.get(symbol, 100.0)
        market_price = base_price * (1 + random.uniform(-0.02, 0.02))  # ±2% variation
        
        # Determine fill price based on order type
        if order.request.order_type == OrderType.MARKET:
            fill_price = market_price
        elif order.request.order_type == OrderType.LIMIT:
            # Check if limit price is marketable
            if order.request.side == OrderSide.BUY:
                if order.request.limit_price >= market_price:
                    fill_price = min(order.request.limit_price, market_price)
                else:
                    # Order not marketable, leave as NEW
                    return
            else:  # SELL
                if order.request.limit_price <= market_price:
                    fill_price = max(order.request.limit_price, market_price)
                else:
                    # Order not marketable, leave as NEW
                    return
        else:
            fill_price = market_price
        
        # Determine fill quantity
        if random.random() < self.partial_fill_rate:
            # Partial fill
            fill_qty = random.randint(1, order.request.qty - 1)
        else:
            # Full fill
            fill_qty = order.request.qty - order.filled_qty
        
        # Create fill
        fill = OrderFill(
            price=fill_price,
            qty=fill_qty,
            timestamp=time.time()
        )
        
        # Update order
        order.add_fill(fill)
        
        # Update positions and cash
        self._update_position(order.request.symbol, order.request.side, fill_qty, fill_price)
        
        # Update cash balance
        if order.request.side == OrderSide.BUY:
            self.cash_balance -= fill_qty * fill_price
        else:
            self.cash_balance += fill_qty * fill_price
    
    def _update_position(self, symbol: str, side: OrderSide, qty: int, price: float) -> None:
        """Update position based on fill."""
        if symbol not in self.positions:
            # New position
            if side == OrderSide.BUY:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    qty=qty,
                    avg_cost=price,
                    market_value=qty * price,
                    unrealized_pnl=0.0
                )
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    qty=-qty,
                    avg_cost=price,
                    market_value=qty * price,
                    unrealized_pnl=0.0
                )
        else:
            # Update existing position
            pos = self.positions[symbol]
            
            if side == OrderSide.BUY:
                new_qty = pos.qty + qty
                if pos.qty == 0:
                    new_avg_cost = price
                else:
                    total_cost = (pos.qty * pos.avg_cost) + (qty * price)
                    new_avg_cost = total_cost / new_qty if new_qty != 0 else 0
                pos.qty = new_qty
                pos.avg_cost = new_avg_cost
            else:
                pos.qty -= qty
            
            # Update market value (simplified)
            current_price = self._market_prices.get(symbol, price)
            pos.market_value = abs(pos.qty) * current_price
            pos.unrealized_pnl = (current_price - pos.avg_cost) * pos.qty
            
            # Remove position if quantity is zero
            if pos.qty == 0:
                del self.positions[symbol]
    
    def set_market_price(self, symbol: str, price: float) -> None:
        """Set market price for testing purposes."""
        self._market_prices[symbol] = price
    
    def force_fill_order(self, broker_order_id: str, fill_price: Optional[float] = None) -> None:
        """Force fill an order for testing purposes."""
        if broker_order_id not in self.orders:
            raise BrokerError(f"Order not found: {broker_order_id}")
        
        order = self.orders[broker_order_id]
        
        if order.is_terminal:
            return
        
        # Use provided price or market price
        if fill_price is None:
            fill_price = self._market_prices.get(order.request.symbol, 100.0)
        
        remaining_qty = order.remaining_qty
        fill = OrderFill(
            price=fill_price,
            qty=remaining_qty,
            timestamp=time.time()
        )
        
        order.add_fill(fill)
        self._update_position(order.request.symbol, order.request.side, remaining_qty, fill_price)
        
        # Update cash balance
        if order.request.side == OrderSide.BUY:
            self.cash_balance -= remaining_qty * fill_price
        else:
            self.cash_balance += remaining_qty * fill_price