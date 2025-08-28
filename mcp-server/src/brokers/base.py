"""
Abstract base classes and data models for broker integration.

This module defines the core interfaces and data structures that all
broker implementations must follow.
"""

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    """Time in force enumeration."""
    DAY = "DAY"         # Good for day
    IOC = "IOC"         # Immediate or cancel
    GTC = "GTC"         # Good till cancelled
    FOK = "FOK"         # Fill or kill


class OrderStatus(str, Enum):
    """Order status enumeration."""
    NEW = "NEW"                 # Order submitted, not yet acknowledged
    PENDING = "PENDING"         # Order acknowledged by exchange
    PARTIAL = "PARTIAL"         # Partially filled
    FILLED = "FILLED"           # Completely filled
    REJECTED = "REJECTED"       # Order rejected
    CANCELLED = "CANCELLED"     # Order cancelled
    EXPIRED = "EXPIRED"         # Order expired


@dataclass
class OrderRequest:
    """
    Request to place an order.
    
    This is the unified interface that all broker adapters accept.
    """
    client_order_id: str                        # Unique ID for idempotency
    symbol: str                                 # Symbol (e.g., "AAPL", "AAPL240315C00180000")
    qty: int                                    # Quantity
    side: OrderSide                             # BUY or SELL
    order_type: OrderType                       # Order type
    limit_price: Optional[float] = None         # Required for LIMIT orders
    stop_price: Optional[float] = None          # Required for STOP orders
    tif: TimeInForce = TimeInForce.DAY         # Time in force
    metadata: Optional[Dict[str, Any]] = None   # Additional metadata
    
    def __post_init__(self):
        """Validate order request parameters."""
        if self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT) and self.limit_price is None:
            raise ValueError(f"{self.order_type} orders require limit_price")
        
        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT) and self.stop_price is None:
            raise ValueError(f"{self.order_type} orders require stop_price")
        
        if self.qty <= 0:
            raise ValueError("Quantity must be positive")


@dataclass
class OrderFill:
    """Represents a single fill of an order."""
    price: float                                # Fill price
    qty: int                                    # Fill quantity
    timestamp: float                            # Unix timestamp of fill
    fill_id: Optional[str] = None              # Broker's fill ID


@dataclass
class Order:
    """
    Represents an order in the system.
    
    This is the unified order representation returned by all broker adapters.
    """
    broker_order_id: str                        # Broker's internal order ID
    request: OrderRequest                       # Original order request
    status: OrderStatus                         # Current order status
    filled_qty: int = 0                        # Total filled quantity
    avg_fill_price: Optional[float] = None     # Average fill price
    fills: List[OrderFill] = field(default_factory=list)  # Individual fills
    created_at: float = field(default_factory=time.time)  # Order creation time
    updated_at: float = field(default_factory=time.time)  # Last update time
    reject_reason: Optional[str] = None        # Reason for rejection
    raw_response: Optional[Dict[str, Any]] = None  # Raw broker response
    
    @property
    def remaining_qty(self) -> int:
        """Calculate remaining quantity to be filled."""
        return self.request.qty - self.filled_qty
    
    @property
    def is_terminal(self) -> bool:
        """Check if order is in a terminal state."""
        return self.status in (OrderStatus.FILLED, OrderStatus.REJECTED, 
                              OrderStatus.CANCELLED, OrderStatus.EXPIRED)
    
    def add_fill(self, fill: OrderFill) -> None:
        """Add a fill to the order and update status."""
        self.fills.append(fill)
        self.filled_qty += fill.qty
        self.updated_at = time.time()
        
        # Update average fill price
        total_value = sum(f.price * f.qty for f in self.fills)
        self.avg_fill_price = total_value / self.filled_qty
        
        # Update status based on fill
        if self.filled_qty >= self.request.qty:
            self.status = OrderStatus.FILLED
        elif self.filled_qty > 0:
            self.status = OrderStatus.PARTIAL


@dataclass
class Position:
    """Represents a position in an account."""
    symbol: str                                 # Symbol
    qty: int                                   # Position quantity (negative for short)
    avg_cost: float                            # Average cost basis
    market_value: float                        # Current market value
    unrealized_pnl: float                      # Unrealized P&L
    metadata: Optional[Dict[str, Any]] = None  # Additional position data


@dataclass
class AccountInfo:
    """Represents account information."""
    account_id: str                            # Account identifier
    cash_balance: float                        # Available cash
    buying_power: float                        # Available buying power
    total_equity: float                        # Total account equity
    day_trades_remaining: Optional[int] = None # Day trades remaining (if applicable)
    metadata: Optional[Dict[str, Any]] = None  # Additional account data


class BrokerError(Exception):
    """Base exception for broker-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 raw_error: Optional[Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.raw_error = raw_error


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.
    
    All broker implementations must inherit from this class and implement
    the required methods. This ensures a consistent interface across
    different brokers.
    """
    
    @abstractmethod
    def place_order(self, request: OrderRequest) -> Order:
        """
        Place a new order.
        
        Must be idempotent on client_order_id - calling with the same
        client_order_id should return the same order.
        
        Args:
            request: Order request details
            
        Returns:
            Order object with broker order ID and status
            
        Raises:
            BrokerError: If order placement fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get current account positions.
        
        Returns:
            List of current positions
            
        Raises:
            BrokerError: If position lookup fails
        """
        pass
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """
        Get account information and balances.
        
        Returns:
            Current account information
            
        Raises:
            BrokerError: If account lookup fails
        """
        pass
    
    @abstractmethod
    def connect(self) -> None:
        """
        Establish connection to the broker.
        
        Raises:
            BrokerError: If connection fails
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close connection to the broker.
        
        Raises:
            BrokerError: If disconnection fails
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        pass