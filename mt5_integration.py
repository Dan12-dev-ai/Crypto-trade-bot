"""
UOTA Elite v2 - MT5 Integration Module
Professional MetaTrader 5 bridge for Exness on Kali Linux
"""

# import os  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import os
import asyncio
import logging
import json

# Import mt5linux for Kali Linux compatibility (tunneling through VirtualBox Port Forwarding)
try:
    import mt5linux
    MT5_AVAILABLE = True
except ImportError:
    logging.error("mt5linux not available. Install with: pip install mt5linux")
    MT5_AVAILABLE = False

@dataclass
class MT5SymbolInfo:
    """MT5 symbol information"""
    symbol: str
    digits: int
    point: float
    tick_value: float
    tick_size: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    spread: int
    swap_long: float
    swap_short: float
    margin_required: float

@dataclass
class MT5Position:
    """MT5 position information"""
    ticket: int
    symbol: str
    type: int  # 0=buy, 1=sell
    volume: float
    price_open: float
    price_current: float
    swap: float
    profit: float
    time: datetime
    magic: int
    comment: str

@dataclass
class MT5Order:
    """MT5 order information"""
    ticket: int
    symbol: str
    type: int
    volume: float
    price_open: float
    price_current: float
    stop_loss: float
    take_profit: float
    time: datetime
    state: int
    magic: int
    comment: str

class MT5Integration:
    """Professional MT5 integration for UOTA Elite v2"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.account_info = {}
        self.symbols_info = {}
        self.positions = {}
        self.orders = {}
        
        # Load Exness credentials from environment
        self.login = os.getenv('EXNESS_LOGIN', '')
        self.password = os.getenv('EXNESS_PASSWORD', '')
        self.server = os.getenv('EXNESS_SERVER', '')
        self.wine_path = os.getenv('EXNESS_PATH_WINE', '/usr/bin/wine')
        self.mt5_path = os.getenv('EXNESS_PATH_MT5', '')
        
        # Elite trading pairs (SMC focus)
        self.elite_symbols = [
            'XAUUSD',    # Gold (primary focus)
            'EURUSD',    # Euro/Dollar
            'GBPUSD',    # Pound/Dollar
            'USDJPY',    # Dollar/Yen
            'AUDUSD',    # Aussie/Dollar
            'USDCAD',    # Dollar/Loonie
            'NZDUSD',    # Kiwi/Dollar
            'USDCHF'     # Dollar/Franc
        ]
        
    async def initialize(self) -> bool:
        """Initialize MT5 connection with Exness via mt5linux bridge"""
        try:
            if not MT5_AVAILABLE:
                self.logger.error("❌ mt5linux not available")
                return False
                
            if not all([self.login, self.password, self.server]):
                self.logger.error("❌ Missing Exness credentials in .env")
                return False
            
            # Initialize MT5 with bridge connection
            self.logger.info(f"🔗 Connecting to MT5 Bridge at 127.0.0.1:8001...")
            
            # Attempt connection with 5s retry logic (Auto-Reconnect)
            while True:
                try:
                    # Create mt5linux instance with specified host and port
                    self.mt5 = mt5linux.MetaTrader5(host='127.0.0.1', port=8001)
                    
                    if self.mt5.initialize():
                        # Login to Exness
                        login_result = self.mt5.login(
                            login=int(self.login),
                            password=self.password,
                            server=self.server
                        )
                        
                        if login_result:
                            self.is_connected = True
                            self.logger.info(f"✅ [BRIDGE ACTIVE]: Kali is now commanding the Windows MT5.")
                            
                            # Get account info
                            self.account_info = self.mt5.account_info()._asdict()
                            self.logger.info(f"💰 Account: {self.account_info.get('login')} | Equity: ${self.account_info.get('equity', 0):.2f}")
                            
                            # Load elite symbols
                            await self._load_elite_symbols()
                            
                            return True
                        else:
                            error_code = self.mt5.last_error()
                            self.logger.error(f"❌ Login failed: {error_code}. Retrying in 5s...")
                            self.mt5.shutdown()
                    else:
                        error_code = self.mt5.last_error()
                        self.logger.error(f"❌ MT5 Bridge initialization failed: {error_code}. Retrying in 5s...")
                        
                except Exception as e:
                    self.logger.error(f"❌ Connection error: {e}. Retrying in 5s...")
                
                await asyncio.sleep(5)  # Auto-Reconnect retry every 5 seconds
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in MT5 initialization: {e}")
            return False
    
    async def _load_elite_symbols(self):
        """Load information for elite trading symbols"""
        try:
            for symbol in self.elite_symbols:
                try:
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info:
                        self.symbols_info[symbol] = MT5SymbolInfo(
                            symbol=symbol,
                            digits=symbol_info.digits,
                            point=symbol_info.point,
                            tick_value=symbol_info.tick_value,
                            tick_size=symbol_info.tick_size,
                            contract_size=symbol_info.contract_size,
                            volume_min=symbol_info.volume_min,
                            volume_max=symbol_info.volume_max,
                            volume_step=symbol_info.volume_step,
                            spread=symbol_info.spread,
                            swap_long=symbol_info.swap_long,
                            swap_short=symbol_info.swap_short,
                            margin_required=symbol_info.margin_required
                        )
                        self.logger.debug(f"✅ Loaded symbol: {symbol}")
                    else:
                        self.logger.warning(f"⚠️ Symbol not available: {symbol}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error loading symbol {symbol}: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error loading elite symbols: {e}")
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance with professional formatting"""
        try:
            if not self.is_connected:
                await self.initialize()
            
            if self.is_connected and self.account_info:
                balance = self.account_info.get('balance', 0)
                equity = self.account_info.get('equity', 0)
                margin = self.account_info.get('margin', 0)
                free_margin = self.account_info.get('margin_free', 0)
                profit = self.account_info.get('profit', 0)
                
                result = {
                    'total_balance': equity,
                    'balance': balance,
                    'equity': equity,
                    'margin': margin,
                    'free_margin': free_margin,
                    'profit': profit,
                    'leverage': self.account_info.get('leverage', 100),
                    'currency': self.account_info.get('currency', 'USD'),
                    'exchange_count': 1 if self.is_connected else 0,
                    'last_updated': datetime.now().isoformat()
                }
                
                self.logger.info(f"💰 Exness Account - Balance: ${balance:.2f} | Equity: ${equity:.2f} | Profit: ${profit:.2f}")
                return result
            else:
                # Return fallback for demo mode
                return {
                    'total_balance': 1000.0,
                    'balance': 1000.0,
                    'equity': 1000.0,
                    'margin': 0.0,
                    'free_margin': 1000.0,
                    'profit': 0.0,
                    'leverage': 500,
                    'currency': 'USD',
                    'exchange_count': 0,
                    'last_updated': datetime.now().isoformat(),
                    'demo_mode': True
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting account balance: {e}")
            return {
                'total_balance': 1000.0,
                'balance': 1000.0,
                'equity': 1000.0,
                'margin': 0.0,
                'free_margin': 1000.0,
                'profit': 0.0,
                'leverage': 500,
                'currency': 'USD',
                'exchange_count': 0,
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def get_symbol_info(self, symbol: str) -> Optional[MT5SymbolInfo]:
        """Get symbol information"""
        try:
            if symbol in self.symbols_info:
                return self.symbols_info[symbol]
            else:
                # Try to load symbol on demand
                symbol_info = self.mt5.symbol_info(symbol)
                if symbol_info:
                    mt5_symbol = MT5SymbolInfo(
                        symbol=symbol,
                        digits=symbol_info.digits,
                        point=symbol_info.point,
                        tick_value=symbol_info.tick_value,
                        tick_size=symbol_info.tick_size,
                        contract_size=symbol_info.contract_size,
                        volume_min=symbol_info.volume_min,
                        volume_max=symbol_info.volume_max,
                        volume_step=symbol_info.volume_step,
                        spread=symbol_info.spread,
                        swap_long=symbol_info.swap_long,
                        swap_short=symbol_info.swap_short,
                        margin_required=symbol_info.margin_required
                    )
                    self.symbols_info[symbol] = mt5_symbol
                    return mt5_symbol
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error getting symbol info for {symbol}: {e}")
            return None
    
    async def get_positions(self) -> List[MT5Position]:
        """Get open positions"""
        try:
            if not self.is_connected:
                return []
            
            positions = self.mt5.positions_get()
            if positions:
                return [
                    MT5Position(
                        ticket=pos.ticket,
                        symbol=pos.symbol,
                        type=pos.type,
                        volume=pos.volume,
                        price_open=pos.price_open,
                        price_current=pos.price_current,
                        swap=pos.swap,
                        profit=pos.profit,
                        time=datetime.fromtimestamp(pos.time),
                        magic=pos.magic,
                        comment=pos.comment
                    )
                    for pos in positions
                ]
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Error getting positions: {e}")
            return []
    
    async def place_order(self, 
                        symbol: str, 
                        order_type: int,  # 0=buy, 1=sell
                        volume: float,
                        price: float = 0.0,
                        stop_loss: float = 0.0,
                        take_profit: float = 0.0,
                        comment: str = "UOTA Elite v2") -> Optional[int]:
        """Place order with professional validation"""
        try:
            if not self.is_connected:
                return None
            
            # Get symbol info
            symbol_info = await self.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"❌ Symbol not available: {symbol}")
                return None
            
            # Validate volume
            if volume < symbol_info.volume_min or volume > symbol_info.volume_max:
                self.logger.error(f"❌ Invalid volume {volume} for {symbol}")
                return None
            
            # Round volume to step
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
            
            # Prepare request
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,  # 20 point deviation
                "magic": 123456,  # UOTA Elite magic number
                "comment": comment,
                "type_time": self.mt5.ORDER_TIME_GTC,  # Good till cancelled
                "type_filling": self.mt5.ORDER_FILLING_IOC,  # Immediate or cancel
            }
            
            # Send order
            result = self.mt5.order_send(request)
            
            if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ Order placed: {symbol} {volume} lots @ {result.price}")
                return result.order
            else:
                self.logger.error(f"❌ Order failed: {result.retcode} - {result.comment}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error placing order: {e}")
            return None
    
    async def close_position(self, ticket: int) -> bool:
        """Close position"""
        try:
            if not self.is_connected:
                return False
            
            # Get position
            position = self.mt5.positions_get(ticket=ticket)
            if not position:
                return False
            
            position = position[0]
            
            # Prepare close request
            request = {
                "action": self.mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": self.mt5.ORDER_TYPE_SELL if position.type == self.mt5.POSITION_TYPE_BUY else self.mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": self.mt5.symbol_info_tick(position.symbol).ask if position.type == self.mt5.POSITION_TYPE_BUY else self.mt5.symbol_info_tick(position.symbol).bid,
                "deviation": 20,
                "magic": 123456,
                "comment": "UOTA Elite v2 Close",
                "type_time": self.mt5.ORDER_TIME_GTC,
                "type_filling": self.mt5.ORDER_FILLING_IOC,
            }
            
            # Close position
            result = self.mt5.order_send(request)
            
            if result.retcode == self.mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ Position closed: {ticket}")
                return True
            else:
                self.logger.error(f"❌ Close failed: {result.retcode} - {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error closing position: {e}")
            return False
    
    async def get_market_data(self, symbol: str, timeframe: int = None, count: int = 100) -> List[Dict]:
        """Get market data for analysis"""
        try:
            if not self.is_connected:
                return []
            
            # Default to M1 if timeframe not specified
            if timeframe is None:
                timeframe = self.mt5.TIMEFRAME_M1
                
            rates = self.mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is None:
                self.logger.error(f"❌ Cannot get rates for {symbol}")
                return []
            
            return [
                {
                    'time': datetime.fromtimestamp(rate[0]),
                    'open': rate[1],
                    'high': rate[2],
                    'low': rate[3],
                    'close': rate[4],
                    'tick_volume': rate[5],
                    'spread': rate[6],
                    'real_volume': rate[7]
                }
                for rate in rates
            ]
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market data for {symbol}: {e}")
            return []
    
    async def shutdown(self):
        """Shutdown MT5 connection"""
        try:
            if self.is_connected and hasattr(self, 'mt5'):
                self.mt5.shutdown()
                self.is_connected = False
                self.logger.info("🔌 MT5 connection closed")
                
        except Exception as e:
            self.logger.error(f"❌ Error shutting down MT5: {e}")

# Global MT5 integration instance
mt5_integration = MT5Integration()
