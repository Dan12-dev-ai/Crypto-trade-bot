"""
UOTA Elite v2 - Exchange Integration
Multi-exchange integration using CCXT Pro for real-time trading
"""

import asyncio
import logging
import json
import ccxt
import ccxt.pro as ccxtpro
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from config import config

class ExchangeStatus(Enum):
    """Exchange connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class ExchangeInfo:
    """Exchange information"""
    name: str
    status: ExchangeStatus
    last_ping: datetime
    latency_ms: float
    rate_limit_remaining: int
    supported_symbols: List[str]
    fees: Dict[str, float]
    balance: Dict[str, float]
    positions: Dict[str, Any]
    
@dataclass
class OrderBookEntry:
    """Order book entry"""
    price: float
    amount: float
    timestamp: datetime
    
@dataclass
class TickerData:
    """Ticker data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime

class ExchangeManager:
    """Multi-exchange manager using CCXT Pro"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Exchange connections
        self.exchanges: Dict[str, ccxtpro.Exchange] = {}
        self.exchange_info: Dict[str, ExchangeInfo] = {}
        
        # Real-time data streams
        self.tickers: Dict[str, TickerData] = {}
        self.orderbooks: Dict[str, Dict[str, List[OrderBookEntry]]] = {}
        self.trades: Dict[str, List[Dict]] = {}
        
        # Callbacks for real-time updates
        self.ticker_callbacks: List[Callable] = []
        self.orderbook_callbacks: List[Callable] = []
        self.trade_callbacks: List[Callable] = []
        
        # Monitoring
        self.is_monitoring = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Initialize exchanges
        self._initialize_exchanges()
        
    def _initialize_exchanges(self) -> None:
        """Initialize all configured exchanges"""
        try:
            for exchange_name in config.get_active_exchanges():
                self._add_exchange(exchange_name)
                
            self.logger.info(f"Initialized {len(self.exchanges)} exchanges")
            
        except Exception as e:
            self.logger.error(f"Error initializing exchanges: {e}")
            
    def _add_exchange(self, exchange_name: str) -> None:
        """Add an exchange to the manager"""
        try:
            exchange_config = config.exchanges[exchange_name]
            
            # Create CCXT Pro exchange instance
            exchange_class = getattr(ccxtpro, exchange_name)
            
            exchange_params = {
                'apiKey': exchange_config.api_key,
                'secret': exchange_config.api_secret,
                'sandbox': exchange_config.sandbox,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures for leverage trading
                }
            }
            
            if exchange_config.passphrase:
                exchange_params['passphrase'] = exchange_config.passphrase
                
            exchange = exchange_class(exchange_params)
            
            # Test connection
            if exchange.check_required_credentials():
                self.exchanges[exchange_name] = exchange
                
                # Initialize exchange info
                self.exchange_info[exchange_name] = ExchangeInfo(
                    name=exchange_name,
                    status=ExchangeStatus.DISCONNECTED,
                    last_ping=datetime.now(),
                    latency_ms=0.0,
                    rate_limit_remaining=exchange.rateLimit,
                    supported_symbols=[],
                    fees={},
                    balance={},
                    positions={}
                )
                
                self.logger.info(f"Added exchange: {exchange_name}")
            else:
                self.logger.error(f"Invalid credentials for {exchange_name}")
                
        except Exception as e:
            self.logger.error(f"Error adding exchange {exchange_name}: {e}")
            
    async def connect_all(self) -> None:
        """Connect to all exchanges"""
        try:
            for exchange_name, exchange in self.exchanges.items():
                await self._connect_exchange(exchange_name)
                
            # Start monitoring after all connections
            await self.start_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error connecting to exchanges: {e}")
            
    async def _connect_exchange(self, exchange_name: str) -> None:
        """Connect to a specific exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Test connection
            start_time = datetime.now()
            await exchange.load_markets()
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update exchange info
            info = self.exchange_info[exchange_name]
            info.status = ExchangeStatus.CONNECTED
            info.last_ping = datetime.now()
            info.latency_ms = latency
            info.supported_symbols = list(exchange.markets.keys())
            
            # Get fee structure
            try:
                fees = await exchange.fetch_trading_fees()
                info.fees = fees.get('trading', {})
            except:
                info.fees = {'taker': 0.001, 'maker': 0.001}
                
            # Get account balance
            try:
                balance = await exchange.fetch_balance()
                info.balance = balance.get('total', {})
            except:
                info.balance = {}
                
            # Get open positions
            try:
                positions = await exchange.fetch_positions()
                info.positions = {pos['symbol']: pos for pos in positions if pos.get('contracts', 0) != 0}
            except:
                info.positions = {}
                
            self.logger.info(f"Connected to {exchange_name} ({latency:.0f}ms)")
            
        except Exception as e:
            self.logger.error(f"Error connecting to {exchange_name}: {e}")
            if exchange_name in self.exchange_info:
                self.exchange_info[exchange_name].status = ExchangeStatus.ERROR
                
    async def start_monitoring(self) -> None:
        """Start real-time monitoring"""
        try:
            if self.is_monitoring:
                return
                
            self.is_monitoring = True
            
            # Start monitoring tasks for each exchange
            tasks = []
            for exchange_name in self.exchanges.keys():
                tasks.append(self._monitor_exchange(exchange_name))
                
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {e}")
            
    async def _monitor_exchange(self, exchange_name: str) -> None:
        """Monitor a specific exchange for real-time data"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Symbols to monitor (top 10 by volume)
            symbols_to_monitor = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
                'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT'
            ]
            
            # Filter symbols available on this exchange
            available_symbols = [
                symbol for symbol in symbols_to_monitor 
                if symbol in exchange.markets
            ]
            
            self.logger.info(f"Monitoring {len(available_symbols)} symbols on {exchange_name}")
            
            # Start real-time streams
            tasks = []
            
            # Watch tickers
            for symbol in available_symbols:
                tasks.append(self._watch_ticker(exchange, symbol))
                
            # Watch order books
            for symbol in available_symbols[:5]:  # Top 5 for order book
                tasks.append(self._watch_orderbook(exchange, symbol))
                
            # Watch trades
            for symbol in available_symbols[:3]:  # Top 3 for trades
                tasks.append(self._watch_trades(exchange, symbol))
                
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"Error monitoring {exchange_name}: {e}")
            
    async def _watch_ticker(self, exchange: ccxtpro.Exchange, symbol: str) -> None:
        """Watch ticker updates"""
        try:
            while self.is_monitoring:
                try:
                    ticker = await exchange.watch_ticker(symbol)
                    
                    ticker_data = TickerData(
                        symbol=symbol,
                        bid=ticker.get('bid', 0),
                        ask=ticker.get('ask', 0),
                        last=ticker.get('last', 0),
                        volume=ticker.get('baseVolume', 0),
                        change_24h=ticker.get('percentage', 0),
                        high_24h=ticker.get('high', 0),
                        low_24h=ticker.get('low', 0),
                        timestamp=datetime.now()
                    )
                    
                    self.tickers[f"{exchange.id}:{symbol}"] = ticker_data
                    
                    # Trigger callbacks
                    for callback in self.ticker_callbacks:
                        try:
                            await callback(ticker_data)
                        except:
                            pass
                            
                except Exception as e:
                    self.logger.error(f"Error watching ticker {symbol}: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error in ticker watcher for {symbol}: {e}")
            
    async def _watch_orderbook(self, exchange: ccxtpro.Exchange, symbol: str) -> None:
        """Watch order book updates"""
        try:
            while self.is_monitoring:
                try:
                    orderbook = await exchange.watch_order_book(symbol, 10)
                    
                    # Process bids
                    bids = [
                        OrderBookEntry(
                            price=float(bid[0]),
                            amount=float(bid[1]),
                            timestamp=datetime.now()
                        )
                        for bid in orderbook['bids']
                    ]
                    
                    # Process asks
                    asks = [
                        OrderBookEntry(
                            price=float(ask[0]),
                            amount=float(ask[1]),
                            timestamp=datetime.now()
                        )
                        for ask in orderbook['asks']
                    ]
                    
                    self.orderbooks[f"{exchange.id}:{symbol}"] = {
                        'bids': bids,
                        'asks': asks
                    }
                    
                    # Trigger callbacks
                    for callback in self.orderbook_callbacks:
                        try:
                            await callback(symbol, bids, asks)
                        except:
                            pass
                            
                except Exception as e:
                    self.logger.error(f"Error watching orderbook {symbol}: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error in orderbook watcher for {symbol}: {e}")
            
    async def _watch_trades(self, exchange: ccxtpro.Exchange, symbol: str) -> None:
        """Watch trade updates"""
        try:
            while self.is_monitoring:
                try:
                    trades = await exchange.watch_trades(symbol)
                    
                    trade_key = f"{exchange.id}:{symbol}"
                    if trade_key not in self.trades:
                        self.trades[trade_key] = []
                        
                    # Add new trades
                    for trade in trades:
                        trade_data = {
                            'id': trade['id'],
                            'price': trade['price'],
                            'amount': trade['amount'],
                            'side': trade['side'],
                            'timestamp': datetime.fromtimestamp(trade['timestamp'] / 1000)
                        }
                        self.trades[trade_key].append(trade_data)
                        
                    # Keep only recent trades
                    if len(self.trades[trade_key]) > 100:
                        self.trades[trade_key] = self.trades[trade_key][-100:]
                        
                    # Trigger callbacks
                    for callback in self.trade_callbacks:
                        try:
                            await callback(symbol, trades)
                        except:
                            pass
                            
                except Exception as e:
                    self.logger.error(f"Error watching trades {symbol}: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error in trade watcher for {symbol}: {e}")
            
    async def place_order(self,
                         exchange_name: str,
                         symbol: str,
                         side: str,
                         amount: float,
                         order_type: str = 'market',
                         price: Optional[float] = None,
                         params: Optional[Dict] = None) -> Optional[str]:
        """Place an order on a specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                self.logger.error(f"Exchange {exchange_name} not available")
                return None
                
            exchange = self.exchanges[exchange_name]
            
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount,
            }
            
            if price and order_type == 'limit':
                order_params['price'] = price
                
            if params:
                order_params.update(params)
                
            order = await exchange.create_order(**order_params)
            
            self.logger.info(f"Order placed on {exchange_name}: {order['id']}")
            return order['id']
            
        except Exception as e:
            self.logger.error(f"Error placing order on {exchange_name}: {e}")
            return None
            
    async def cancel_order(self, exchange_name: str, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            if exchange_name not in self.exchanges:
                return False
                
            exchange = self.exchanges[exchange_name]
            await exchange.cancel_order(order_id, symbol)
            
            self.logger.info(f"Order {order_id} cancelled on {exchange_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False
            
    async def get_balance(self, exchange_name: str) -> Dict[str, float]:
        """Get account balance"""
        try:
            if exchange_name not in self.exchanges:
                return {}
                
            exchange = self.exchanges[exchange_name]
            balance = await exchange.fetch_balance()
            
            # Update exchange info
            if exchange_name in self.exchange_info:
                self.exchange_info[exchange_name].balance = balance.get('total', {})
                
            return balance.get('total', {})
            
        except Exception as e:
            self.logger.error(f"Error getting balance from {exchange_name}: {e}")
            return {}
            
    async def get_positions(self, exchange_name: str) -> Dict[str, Any]:
        """Get open positions"""
        try:
            if exchange_name not in self.exchanges:
                return {}
                
            exchange = self.exchanges[exchange_name]
            positions = await exchange.fetch_positions()
            
            # Filter active positions
            active_positions = {
                pos['symbol']: pos for pos in positions 
                if pos.get('contracts', 0) != 0
            }
            
            # Update exchange info
            if exchange_name in self.exchange_info:
                self.exchange_info[exchange_name].positions = active_positions
                
            return active_positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions from {exchange_name}: {e}")
            return {}
            
    async def get_order_status(self, exchange_name: str, order_id: str, symbol: str) -> Optional[Dict]:
        """Get order status"""
        try:
            if exchange_name not in self.exchanges:
                return None
                
            exchange = self.exchanges[exchange_name]
            order = await exchange.fetch_order(order_id, symbol)
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return None
            
    def get_best_price(self, symbol: str, side: str) -> Optional[float]:
        """Get best price across all exchanges"""
        try:
            best_price = None
            
            for key, ticker in self.tickers.items():
                if symbol in key:
                    if side.lower() == 'buy' and ticker.ask > 0:
                        if best_price is None or ticker.ask < best_price:
                            best_price = ticker.ask
                    elif side.lower() == 'sell' and ticker.bid > 0:
                        if best_price is None or ticker.bid > best_price:
                            best_price = ticker.bid
                            
            return best_price
            
        except Exception as e:
            self.logger.error(f"Error getting best price for {symbol}: {e}")
            return None
            
    def get_spread(self, symbol: str) -> Optional[float]:
        """Get bid-ask spread for a symbol"""
        try:
            for key, ticker in self.tickers.items():
                if symbol in key and ticker.bid > 0 and ticker.ask > 0:
                    return ticker.ask - ticker.bid
                    
        except Exception as e:
            self.logger.error(f"Error getting spread for {symbol}: {e}")
            
        return None
        
    def add_ticker_callback(self, callback: Callable) -> None:
        """Add callback for ticker updates"""
        self.ticker_callbacks.append(callback)
        
    def add_orderbook_callback(self, callback: Callable) -> None:
        """Add callback for order book updates"""
        self.orderbook_callbacks.append(callback)
        
    def add_trade_callback(self, callback: Callable) -> None:
        """Add callback for trade updates"""
        self.trade_callbacks.append(callback)
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all exchanges"""
        try:
            health_status = {}
            
            for exchange_name, exchange in self.exchanges.items():
                try:
                    start_time = datetime.now()
                    
                    # Simple ping - fetch markets
                    await exchange.load_markets()
                    
                    latency = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Update exchange info
                    if exchange_name in self.exchange_info:
                        info = self.exchange_info[exchange_name]
                        info.last_ping = datetime.now()
                        info.latency_ms = latency
                        info.status = ExchangeStatus.CONNECTED
                        
                    health_status[exchange_name] = {
                        'status': 'connected',
                        'latency_ms': latency,
                        'last_ping': datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    if exchange_name in self.exchange_info:
                        self.exchange_info[exchange_name].status = ExchangeStatus.ERROR
                        
                    health_status[exchange_name] = {
                        'status': 'error',
                        'error': str(e),
                        'last_ping': self.exchange_info.get(exchange_name, ExchangeInfo('', ExchangeStatus.DISCONNECTED, datetime.now(), 0, 0, [], {}, {}, {})).last_ping.isoformat()
                    }
                    
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return {}
            
    async def close_all_connections(self) -> None:
        """Close all exchange connections"""
        try:
            self.is_monitoring = False
            
            for exchange_name, exchange in self.exchanges.items():
                try:
                    await exchange.close()
                    self.logger.info(f"Closed connection to {exchange_name}")
                except:
                    pass
                    
            self.exchanges.clear()
            self.tickers.clear()
            self.orderbooks.clear()
            self.trades.clear()
            
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")
            
    def get_summary(self) -> Dict[str, Any]:
        """Get exchange manager summary"""
        try:
            total_balance = {}
            total_positions = 0
            
            for exchange_name, info in self.exchange_info.items():
                # Aggregate balances
                for asset, amount in info.balance.items():
                    if amount > 0:
                        total_balance[asset] = total_balance.get(asset, 0) + amount
                        
                # Count positions
                total_positions += len(info.positions)
                
            return {
                'connected_exchanges': len([e for e in self.exchange_info.values() if e.status == ExchangeStatus.CONNECTED]),
                'total_exchanges': len(self.exchanges),
                'symbols_monitored': len(self.tickers),
                'total_balance_usd': total_balance.get('USDT', 0) + total_balance.get('USD', 0),
                'total_positions': total_positions,
                'exchange_status': {
                    name: info.status.value for name, info in self.exchange_info.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting summary: {e}")
            return {}

# Global exchange manager instance
exchange_manager = ExchangeManager()

if __name__ == "__main__":
    # Test exchange manager
    async def test_exchange_manager():
        manager = ExchangeManager()
        
        # Connect to exchanges
        await manager.connect_all()
        
        # Get summary
        summary = manager.get_summary()
        print("Exchange Manager Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
            
        # Health check
        health = await manager.health_check()
        print("\nExchange Health:")
        for exchange, status in health.items():
            print(f"  {exchange}: {status['status']}")
            
        # Close connections
        await manager.close_all_connections()
        
    asyncio.run(test_exchange_manager())
