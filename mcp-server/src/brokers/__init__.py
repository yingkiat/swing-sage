"""
Broker abstraction layer for options trading bot.

This package provides a unified interface for interacting with different
brokers, starting with Interactive Brokers (IBKR) integration for US options trading.
"""

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

__all__ = [
    'BrokerAdapter',
    'BrokerError',
    'OrderRequest',
    'Order',
    'OrderFill',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'TimeInForce',
    'Position',
    'AccountInfo'
]