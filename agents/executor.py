"""
Crypto trade bot - Executor Agent
Places orders with correct leverage, manages SL/TP/trailing stops
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import ccxt
import numpy as np

from crewai import Agent, Task
from langchain.llms.base import LLM
from langchain.schema import HumanMessage, SystemMessage

from config import config
from risk_manager import risk_manager

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Order statuses"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    """Order data structure"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    trailing_amount: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    exchange: str = ""
    client_order_id: str = ""
    
@dataclass
class Position:
    """Position data structure"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    exchange: str = ""

class ExecutorAgent:
    """Executor Agent - Handles order execution and position management"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # Exchange connections
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.active_orders: Dict[str, Order] = {}
        self.positions: Dict[str, Position] = {}
        
        # Execution parameters
        self.max_slippage = 0.001  # 0.1%
        self.order_timeout = 30  # seconds
        self.retry_attempts = 3
        self.retry_delay = 1  # second
        
        # Initialize exchanges
        self._initialize_exchanges()
        
    def create_crewai_agent(self) -> Agent:
        """Create CrewAI agent instance"""
        return Agent(
            role='Trade Executor',
            goal='Execute trades with precision and manage positions with optimal risk control',
            backstory="""You are an expert trade executor with years of experience in 
            high-frequency trading and position management. You execute orders with surgical 
            precision, always getting the best possible fills while maintaining strict 
            risk controls. You specialize in managing complex order types including 
            trailing stops and multi-leg strategies. Your execution discipline is legendary 
            - you never chase prices and always respect risk parameters.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
            system_template="""You are the Trade Executor Agent for Crypto trade bot.
            
            Your core responsibilities:
            1. Execute trades at optimal prices with minimal slippage
            2. Manage stop losses, take profits, and trailing stops
            3. Monitor positions and adjust risk parameters
            4. Handle order failures and retries gracefully
            5. Maintain precise position records and P&L tracking
            
            Execution Rules:
            - Always respect risk manager position sizing
            - Use limit orders when possible to reduce slippage
            - Set stop losses immediately on position entry
            - Monitor positions continuously for adjustment opportunities
            - Cancel and replace orders when market conditions change
            
            Risk Management:
            - Never exceed maximum leverage
            - Always use stop losses on every position
            - Scale into/out of positions when appropriate
            - Monitor margin requirements continuously
            - Emergency close positions when risk limits breached
            
            Execute with precision and maintain discipline at all times."""
        )
        
    def _initialize_exchanges(self) -> None:
        """Initialize exchange connections"""
        try:
            for exchange_name in config.get_active_exchanges():
                exchange_config = config.exchanges[exchange_name]
                
                # Create exchange instance
                exchange_class = getattr(ccxt, exchange_name)
                
                exchange_params = {
                    'apiKey': exchange_config.api_key,
                    'secret': exchange_config.api_secret,
                    'sandbox': exchange_config.sandbox,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',  # Use futures for leverage
                    }
                }
                
                # Add passphrase for exchanges that require it
                if exchange_config.passphrase:
                    exchange_params['passphrase'] = exchange_config.passphrase
                    
                exchange = exchange_class(exchange_params)
                
                # Test connection
                if exchange.check_required_credentials():
                    self.exchanges[exchange_name] = exchange
                    self.logger.info(f"Connected to {exchange_name}")
                else:
                    self.logger.error(f"Failed to connect to {exchange_name} - invalid credentials")
                    
        except Exception as e:
            self.logger.error(f"Error initializing exchanges: {e}")
            
    async def execute_trade(self,
                          symbol: str,
                          side: str,
                          amount: float,
                          order_type: str = "market",
                          price: Optional[float] = None,
                          stop_loss: Optional[float] = None,
                          take_profit: Optional[float] = None,
                          leverage: Optional[float] = None) -> Optional[str]:
        """Execute a complete trade with risk management"""
        try:
            # Validate trade with risk manager
            current_price = price or await self._get_current_price(symbol)
            if not current_price:
                return None
                
            # Set default stop loss if not provided
            if not stop_loss:
                atr = await self._get_atr(symbol)
                if side.lower() == 'buy':
                    stop_loss = current_price - (atr * config.trading.stop_loss_atr_multiplier)
                else:
                    stop_loss = current_price + (atr * config.trading.stop_loss_atr_multiplier)
                    
            # Validate with risk manager
            is_valid, reason = risk_manager.validate_trade(
                symbol, side, amount, current_price, stop_loss, leverage or config.trading.max_leverage
            )
            
            if not is_valid:
                self.logger.warning(f"Trade rejected by risk manager: {reason}")
                return None
                
            # Select best exchange for this symbol
            exchange_name = await self._select_best_exchange(symbol)
            if not exchange_name:
                self.logger.error(f"No exchange available for {symbol}")
                return None
                
            exchange = self.exchanges[exchange_name]
            
            # Set leverage if specified
            if leverage:
                try:
                    await exchange.set_leverage(leverage, symbol)
                    self.logger.info(f"Set leverage to {leverage}x for {symbol}")
                except Exception as e:
                    self.logger.warning(f"Failed to set leverage: {e}")
                    
            # Execute main order
            order_id = await self._place_order(
                exchange, symbol, side, amount, order_type, price
            )
            
            if not order_id:
                return None
                
            # Wait for order fill
            order = await self._wait_for_order_fill(exchange, order_id)
            if not order or order.status != OrderStatus.FILLED:
                self.logger.error(f"Order {order_id} failed to fill")
                return None
                
            # Set stop loss and take profit
            await self._set_bracket_orders(
                exchange, symbol, side, order.filled_amount, 
                order.filled_price, stop_loss, take_profit
            )
            
            # Update position tracking
            await self._update_position_tracking(symbol, side, order.filled_amount, order.filled_price)
            
            # Update risk manager
            await risk_manager.update_position(
                symbol, side, order.filled_amount, order.filled_price,
                order.filled_price, stop_loss, take_profit
            )
            
            self.logger.info(f"Trade executed: {side} {amount:.4f} {symbol} at {order.filled_price:.4f}")
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return None
            
    async def _place_order(self,
                         exchange: ccxt.Exchange,
                         symbol: str,
                         side: str,
                         amount: float,
                         order_type: str,
                         price: Optional[float] = None,
                         stop_price: Optional[float] = None) -> Optional[str]:
        """Place an order on the exchange"""
        try:
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount,
            }
            
            if price and order_type == 'limit':
                order_params['price'] = price
                
            if stop_price:
                order_params['params'] = {'stopPrice': stop_price}
                
            # Add client order ID for tracking
            client_order_id = f"UOTA_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{np.random.randint(1000, 9999)}"
            order_params['clientOrderId'] = client_order_id
            
            # Place order with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    # Filter out None values and unpack
                    filtered_params = {k: v for k, v in order_params.items() if v is not None}
                    order = await exchange.create_order(**filtered_params)
                    
                    # Store order in tracking
                    tracked_order = Order(
                        id=order['id'],
                        symbol=symbol,
                        side=OrderSide(side),
                        order_type=OrderType(order_type),
                        amount=amount,
                        price=price,
                        stop_price=stop_price,
                        exchange=exchange.id,
                        client_order_id=client_order_id
                    )
                    
                    self.active_orders[order['id']] = tracked_order
                    return order['id']
                    
                except Exception as e:
                    self.logger.warning(f"Order attempt {attempt + 1} failed: {e}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay)
                    else:
                        raise
                        
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None
            
    async def _wait_for_order_fill(self,
                                 exchange: ccxt.Exchange,
                                 order_id: str,
                                 timeout: int = 30) -> Optional[Order]:
        """Wait for order to be filled"""
        try:
            start_time = datetime.now()
            
            while (datetime.now() - start_time).seconds < timeout:
                try:
                    order_data = await exchange.fetch_order(order_id)
                    
                    # Update order status
                    if order_id in self.active_orders:
                        order = self.active_orders[order_id]
                        
                        if order_data['status'] == 'closed':
                            order.status = OrderStatus.FILLED
                            order.filled_amount = order_data['filled']
                            order.filled_price = order_data.get('average', order_data.get('price'))
                            order.commission = order_data.get('fee', {}).get('cost', 0)
                            
                            self.logger.info(f"Order {order_id} filled at {order.filled_price}")
                            return order
                            
                        elif order_data['status'] == 'canceled':
                            order.status = OrderStatus.CANCELLED
                            return order
                            
                        elif order_data['status'] == 'open':
                            order.status = OrderStatus.OPEN
                            
                except Exception as e:
                    self.logger.error(f"Error checking order status: {e}")
                    
                await asyncio.sleep(1)
                
            # Timeout reached
            if order_id in self.active_orders:
                self.active_orders[order_id].status = OrderStatus.CANCELLED
                
            # Try to cancel the order
            try:
                await exchange.cancel_order(order_id)
                self.logger.warning(f"Order {order_id} timed out and was cancelled")
            except:
                pass
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for order fill: {e}")
            return None
            
    async def _set_bracket_orders(self,
                                exchange: ccxt.Exchange,
                                symbol: str,
                                side: str,
                                amount: float,
                                entry_price: float,
                                stop_loss: Optional[float],
                                take_profit: Optional[float]) -> None:
        """Set stop loss and take profit orders"""
        try:
            # Set stop loss
            if stop_loss:
                stop_side = 'sell' if side == 'buy' else 'buy'
                
                stop_order = await self._place_order(
                    exchange, symbol, stop_side, amount, 'stop_loss', None, stop_loss
                )
                
                if stop_order:
                    self.logger.info(f"Stop loss set at {stop_loss} for {symbol}")
                    
            # Set take profit
            if take_profit:
                profit_side = 'sell' if side == 'buy' else 'buy'
                
                profit_order = await self._place_order(
                    exchange, symbol, profit_side, amount, 'limit', take_profit
                )
                
                if profit_order:
                    self.logger.info(f"Take profit set at {take_profit} for {symbol}")
                    
        except Exception as e:
            self.logger.error(f"Error setting bracket orders: {e}")
            
    async def close_position(self,
                           symbol: str,
                           reason: str = "Manual close",
                           market_order: bool = True) -> Optional[float]:
        """Close a position"""
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position found for {symbol}")
                return None
                
            position = self.positions[symbol]
            
            # Determine order side
            close_side = 'sell' if position.side == 'long' else 'buy'
            
            # Get current price
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return None
                
            # Close position
            order_id = await self._place_order(
                self.exchanges[position.exchange],
                symbol, close_side, position.size,
                'market' if market_order else 'limit',
                current_price if not market_order else None
            )
            
            if not order_id:
                return None
                
            # Wait for fill
            order = await self._wait_for_order_fill(
                self.exchanges[position.exchange], order_id
            )
            
            if order and order.status == OrderStatus.FILLED:
                # Calculate realized P&L
                if position.side == 'long':
                    realized_pnl = position.size * (order.filled_price - position.entry_price)
                else:
                    realized_pnl = position.size * (position.entry_price - order.filled_price)
                    
                realized_pnl -= order.commission
                
                # Update risk manager
                await risk_manager.close_position(symbol, order.filled_price, order.commission)
                
                # Remove from tracking
                del self.positions[symbol]
                
                self.logger.info(f"Position {symbol} closed: P&L ${realized_pnl:.2f}")
                return realized_pnl
                
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
            return None
            
    async def update_trailing_stop(self,
                                 symbol: str,
                                 new_price: float,
                                 trail_amount: float) -> bool:
        """Update trailing stop for a position"""
        try:
            if symbol not in self.positions:
                return False
                
            position = self.positions[symbol]
            
            # Calculate new stop level
            if position.side == 'long':
                new_stop = new_price - trail_amount
                if new_stop > (position.trailing_stop or 0):
                    position.trailing_stop = new_stop
                    
                    # Cancel old stop order and create new one
                    await self._update_stop_order(symbol, new_stop)
                    self.logger.info(f"Trailing stop updated to {new_stop} for {symbol}")
                    return True
            else:
                new_stop = new_price + trail_amount
                if new_stop < (position.trailing_stop or float('inf')):
                    position.trailing_stop = new_stop
                    
                    await self._update_stop_order(symbol, new_stop)
                    self.logger.info(f"Trailing stop updated to {new_stop} for {symbol}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {symbol}: {e}")
            
        return False
        
    async def _update_stop_order(self, symbol: str, new_stop_price: float) -> None:
        """Update stop loss order"""
        try:
            # This is a simplified implementation
            # In practice, you'd need to cancel the existing stop order and create a new one
            position = self.positions[symbol]
            exchange = self.exchanges[position.exchange]
            
            # Cancel existing stop orders (implementation depends on exchange)
            # Create new stop order at new_stop_price
            stop_side = 'sell' if position.side == 'long' else 'buy'
            
            await self._place_order(
                exchange, symbol, stop_side, position.size, 'stop_loss', None, new_stop_price
            )
            
        except Exception as e:
            self.logger.error(f"Error updating stop order: {e}")
            
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        try:
            # Try exchanges in order of preference
            for exchange_name, exchange in self.exchanges.items():
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    return ticker['last'] or ticker['bid'] or ticker['ask']
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            
        return None
        
    async def _get_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            # Get OHLCV data
            exchange = list(self.exchanges.values())[0]  # Use first available exchange
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=period + 1)
            
            if len(ohlcv) < period:
                return 0.01  # Default 1% if insufficient data
                
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Calculate True Range
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR
            atr = df['tr'].rolling(window=period).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            return atr / current_price  # Return as percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR for {symbol}: {e}")
            return 0.01  # Default 1%
            
    async def _select_best_exchange(self, symbol: str) -> Optional[str]:
        """Select best exchange for trading a symbol"""
        try:
            # Simple selection - could be enhanced with liquidity, fees, etc.
            for exchange_name, exchange in self.exchanges.items():
                try:
                    markets = await exchange.load_markets()
                    if symbol in markets:
                        return exchange_name
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error selecting exchange for {symbol}: {e}")
            
        return None
        
    async def _update_position_tracking(self,
                                       symbol: str,
                                       side: str,
                                       amount: float,
                                       price: float) -> None:
        """Update position tracking"""
        try:
            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]
                
                # This is simplified - would need to handle partial fills, averaging, etc.
                position.size += amount if side == position.side else -amount
                
                if abs(position.size) < 0.0001:  # Position closed
                    del self.positions[symbol]
            else:
                # New position
                self.positions[symbol] = Position(
                    symbol=symbol,
                    side=side,
                    size=amount,
                    entry_price=price,
                    current_price=price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    leverage=config.trading.max_leverage,
                    exchange=list(self.exchanges.keys())[0]  # Use first exchange
                )
                
        except Exception as e:
            self.logger.error(f"Error updating position tracking: {e}")
            
    async def monitor_positions(self) -> None:
        """Monitor and update all open positions"""
        try:
            for symbol, position in list(self.positions.items()):
                # Get current price
                current_price = await self._get_current_price(symbol)
                if not current_price:
                    continue
                    
                position.current_price = current_price
                
                # Calculate unrealized P&L
                if position.side == 'long':
                    position.unrealized_pnl = position.size * (current_price - position.entry_price)
                else:
                    position.unrealized_pnl = position.size * (position.entry_price - current_price)
                    
                # Update trailing stops if needed
                if position.trailing_stop:
                    await self.update_trailing_stop(
                        symbol, current_price, 
                        abs(current_price - position.trailing_stop)
                    )
                    
                # Update risk manager
                await risk_manager.update_position(
                    symbol, position.side, position.size, current_price
                )
                
        except Exception as e:
            self.logger.error(f"Error monitoring positions: {e}")
            
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        try:
            return {
                'active_orders': len(self.active_orders),
                'open_positions': len(self.positions),
                'connected_exchanges': list(self.exchanges.keys()),
                'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
                'total_realized_pnl': sum(pos.realized_pnl for pos in self.positions.values()),
                'positions': {
                    symbol: {
                        'side': pos.side,
                        'size': pos.size,
                        'entry_price': pos.entry_price,
                        'current_price': pos.current_price,
                        'unrealized_pnl': pos.unrealized_pnl,
                        'leverage': pos.leverage
                    }
                    for symbol, pos in self.positions.items()
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating execution summary: {e}")
            return {}
            
    def create_crewai_task(self) -> Task:
        """Create CrewAI task for trade execution"""
        return Task(
            description="""Execute the approved trading plan with precision and optimal risk management.
            
            Trading Plan:
            - Symbol: {symbol}
            - Side: {side}
            - Position Size: {position_size}
            - Entry Price: {entry_price}
            - Stop Loss: {stop_loss}
            - Take Profit: {take_profit}
            - Leverage: {leverage}
            
            Your task:
            1. Select the best exchange for execution
            2. Set appropriate leverage
            3. Execute the main order with minimal slippage
            4. Immediately set stop loss and take profit orders
            5. Monitor position and adjust stops as needed
            6. Track all execution details and costs
            
            Execution Requirements:
            - Use limit orders when possible to reduce slippage
            - Set stop losses immediately on position entry
            - Monitor for trailing stop opportunities
            - Track all commissions and fees
            - Handle any execution errors gracefully
            
            Provide detailed execution report including:
            - Exchange used and execution price
            - Slippage and commission costs
            - Order IDs and confirmation status
            - Position details and risk parameters""",
            expected_output="Complete trade execution with all risk management orders in place and detailed execution report.",
            agent=self.create_crewai_agent()
        )
