"""
UOTA Elite v2 - Database and Persistence Layer
SQLite database for memory, logs, and persistent storage
"""

# import sqlite3  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
# import pandas  # Moved to function to avoid circular import as pd
# import aiosqlite  # Moved to function to avoid circular import
from pathlib import Path

from config # import config  # Moved to function to avoid circular import
try:
    from risk_manager import PositionRisk, RiskMetrics
except ImportError:
    # Define fallback classes if risk_manager import fails
    @dataclass
    class PositionRisk:
        symbol: str = ""
        side: str = ""
        size: float = 0.0
        entry_price: float = 0.0
        current_price: float = 0.0
        unrealized_pnl: float = 0.0
        leverage: float = 1.0
        
    @dataclass
    class RiskMetrics:
        current_balance: float = 0.0
        daily_pnl: float = 0.0
        total_pnl: float = 0.0
        daily_loss: float = 0.0
        max_drawdown: float = 0.0
        current_drawdown: float = 0.0
        open_positions: int = 0
        total_risk: float = 0.0
        leverage_used: float = 0.0
        volatility_score: float = 0.0
        risk_score: float = 0.0
        last_updated: datetime = None

try:
    from agents.supervisor import SupervisorAction
except ImportError:
    # Define fallback class
    @dataclass
    class SupervisorAction:
        decision: str = ""
        confidence: float = 0.0
        reasoning: str = ""
        parameters: Dict[str, Any] = None
        timestamp: datetime = None
        priority: int = 5

try:
    from agents.opportunity_spotter import TradingOpportunity
except ImportError:
    # Define fallback class
    @dataclass
    class TradingOpportunity:
        symbol: str = ""
        opportunity_type: str = ""
        confidence: float = 0.0
        expected_return: float = 0.0
        time_horizon: str = ""
        risk_level: str = ""
        catalyst: str = ""
        supporting_data: Dict[str, Any] = None
        timestamp: datetime = None
        urgency: float = 0.0

@dataclass
class TradeRecord:
    """Trade record for database storage"""
    id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    pnl: float = 0.0
    commission: float = 0.0
    leverage: float = 1.0
    strategy: str = ""
    timestamp: datetime = None
    duration: Optional[timedelta] = None
    exchange: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemLog:
    """System log record"""
    id: Optional[int] = None
    timestamp: datetime = None
    level: str = "INFO"
    component: str = ""
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DatabaseManager:
    """Database manager for persistent storage"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or config.database.db_path
        self.connection = None
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        amount REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        pnl REAL DEFAULT 0.0,
                        commission REAL DEFAULT 0.0,
                        leverage REAL DEFAULT 1.0,
                        strategy TEXT,
                        timestamp DATETIME NOT NULL,
                        duration TEXT,
                        exchange TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Positions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL UNIQUE,
                        side TEXT NOT NULL,
                        size REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        unrealized_pnl REAL DEFAULT 0.0,
                        leverage REAL DEFAULT 1.0,
                        stop_loss REAL,
                        take_profit REAL,
                        trailing_stop REAL,
                        timestamp DATETIME NOT NULL,
                        exchange TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Risk metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS risk_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        current_balance REAL NOT NULL,
                        daily_pnl REAL DEFAULT 0.0,
                        total_pnl REAL DEFAULT 0.0,
                        daily_loss REAL DEFAULT 0.0,
                        max_drawdown REAL DEFAULT 0.0,
                        current_drawdown REAL DEFAULT 0.0,
                        open_positions INTEGER DEFAULT 0,
                        total_risk REAL DEFAULT 0.0,
                        leverage_used REAL DEFAULT 0.0,
                        volatility_score REAL DEFAULT 0.0,
                        risk_score REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Opportunities table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS opportunities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        opportunity_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        expected_return REAL NOT NULL,
                        time_horizon TEXT,
                        risk_level TEXT,
                        catalyst TEXT,
                        supporting_data TEXT,
                        urgency REAL DEFAULT 0.0,
                        timestamp DATETIME NOT NULL,
                        executed BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Supervisor actions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS supervisor_actions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        reasoning TEXT,
                        parameters TEXT,
                        priority INTEGER DEFAULT 5,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        level TEXT NOT NULL,
                        component TEXT NOT NULL,
                        message TEXT NOT NULL,
                        data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL UNIQUE,
                        total_trades INTEGER DEFAULT 0,
                        winning_trades INTEGER DEFAULT 0,
                        losing_trades INTEGER DEFAULT 0,
                        total_pnl REAL DEFAULT 0.0,
                        max_drawdown REAL DEFAULT 0.0,
                        sharpe_ratio REAL DEFAULT 0.0,
                        profit_factor REAL DEFAULT 0.0,
                        avg_trade REAL DEFAULT 0.0,
                        win_rate REAL DEFAULT 0.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)")
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
            
    # Trade operations
    async def save_trade(self, trade: TradeRecord) -> int:
        """Save a trade record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO trades (symbol, side, amount, entry_price, exit_price, pnl, 
                                      commission, leverage, strategy, timestamp, duration, exchange)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.symbol, trade.side, trade.amount, trade.entry_price,
                    trade.exit_price, trade.pnl, trade.commission, trade.leverage,
                    trade.strategy, trade.timestamp, str(trade.duration) if trade.duration else None,
                    trade.exchange
                ))
                
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Error saving trade: {e}")
            return 0
            
    async def get_trades(self, 
                        symbol: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[TradeRecord]:
        """Get trades with optional filters"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM trades WHERE 1=1"
                params = []
                
                if symbol:
                    query += " AND symbol = ?"
                    params.append(symbol)
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                    
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                trades = []
                for row in rows:
                    trade = TradeRecord(
                        id=row[0],
                        symbol=row[1],
                        side=row[2],
                        amount=row[3],
                        entry_price=row[4],
                        exit_price=row[5],
                        pnl=row[6],
                        commission=row[7],
                        leverage=row[8],
                        strategy=row[9],
                        timestamp=datetime.fromisoformat(row[10]),
                        duration=timedelta(seconds=float(row[11])) if row[11] else None,
                        exchange=row[12]
                    )
                    trades.append(trade)
                    
                return trades
                
        except Exception as e:
            self.logger.error(f"Error getting trades: {e}")
            return []
            
    # Position operations
    async def save_position(self, position: PositionRisk) -> None:
        """Save or update position"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO positions 
                    (symbol, side, size, entry_price, current_price, unrealized_pnl, 
                     leverage, stop_loss, take_profit, trailing_stop, timestamp, exchange)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.symbol, position.side, position.size, position.entry_price,
                    position.current_price, position.unrealized_pnl, position.leverage,
                    position.stop_loss, position.take_profit, position.trailing_stop,
                    position.entry_time, ""  # Exchange info
                ))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving position: {e}")
            
    async def get_positions(self) -> List[PositionRisk]:
        """Get all positions"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT * FROM positions")
                rows = await cursor.fetchall()
                
                positions = []
                for row in rows:
                    position = PositionRisk(
                        symbol=row[1],
                        side=row[2],
                        size=row[3],
                        entry_price=row[4],
                        current_price=row[5],
                        unrealized_pnl=row[6],
                        leverage=row[7],
                        stop_loss=row[8],
                        take_profit=row[9],
                        trailing_stop=row[10],
                        entry_time=datetime.fromisoformat(row[11])
                    )
                    positions.append(position)
                    
                return positions
                
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
            
    async def delete_position(self, symbol: str) -> None:
        """Delete a position"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error deleting position: {e}")
            
    # Risk metrics operations
    async def save_risk_metrics(self, metrics: RiskMetrics) -> None:
        """Save risk metrics snapshot"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO risk_metrics 
                    (timestamp, current_balance, daily_pnl, total_pnl, daily_loss,
                     max_drawdown, current_drawdown, open_positions, total_risk,
                     leverage_used, volatility_score, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.last_updated, metrics.current_balance, metrics.daily_pnl,
                    metrics.total_pnl, metrics.daily_loss, metrics.max_drawdown,
                    metrics.current_drawdown, metrics.open_positions, metrics.total_risk,
                    metrics.leverage_used, metrics.volatility_score, metrics.risk_score
                ))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving risk metrics: {e}")
            
    async def get_risk_metrics(self, 
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[RiskMetrics]:
        """Get risk metrics history"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM risk_metrics WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                    
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                metrics_list = []
                for row in rows:
                    metrics = RiskMetrics(
                        current_balance=row[2],
                        daily_pnl=row[3],
                        total_pnl=row[4],
                        daily_loss=row[5],
                        max_drawdown=row[6],
                        current_drawdown=row[7],
                        open_positions=row[8],
                        total_risk=row[9],
                        leverage_used=row[10],
                        volatility_score=row[11],
                        risk_score=row[12],
                        last_updated=datetime.fromisoformat(row[1])
                    )
                    metrics_list.append(metrics)
                    
                return metrics_list
                
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return []
            
    # Opportunity operations
    async def save_opportunity(self, opportunity: TradingOpportunity) -> int:
        """Save trading opportunity"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO opportunities 
                    (symbol, opportunity_type, confidence, expected_return, time_horizon,
                     risk_level, catalyst, supporting_data, urgency, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity.symbol, opportunity.opportunity_type, opportunity.confidence,
                    opportunity.expected_return, opportunity.time_horizon, opportunity.risk_level,
                    opportunity.catalyst, json.dumps(opportunity.supporting_data),
                    opportunity.urgency, opportunity.timestamp
                ))
                
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Error saving opportunity: {e}")
            return 0
            
    async def get_opportunities(self, 
                               executed_only: bool = False,
                               limit: int = 50) -> List[TradingOpportunity]:
        """Get opportunities"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM opportunities WHERE 1=1"
                params = []
                
                if executed_only:
                    query += " AND executed = TRUE"
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                opportunities = []
                for row in rows:
                    opportunity = TradingOpportunity(
                        symbol=row[1],
                        opportunity_type=row[2],
                        confidence=row[3],
                        expected_return=row[4],
                        time_horizon=row[5],
                        risk_level=row[6],
                        catalyst=row[7],
                        supporting_data=json.loads(row[8]) if row[8] else {},
                        timestamp=datetime.fromisoformat(row[9]),
                        urgency=row[10]
                    )
                    opportunities.append(opportunity)
                    
                return opportunities
                
        except Exception as e:
            self.logger.error(f"Error getting opportunities: {e}")
            return []
            
    # Supervisor action operations
    async def save_supervisor_action(self, action: SupervisorAction) -> int:
        """Save supervisor action"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO supervisor_actions 
                    (decision, confidence, reasoning, parameters, priority, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    action.decision.value, action.confidence, action.reasoning,
                    json.dumps(action.parameters), action.priority, action.timestamp
                ))
                
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Error saving supervisor action: {e}")
            return 0
            
    # System log operations
    async def save_log(self, log: SystemLog) -> int:
        """Save system log"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO system_logs 
                    (timestamp, level, component, message, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    log.timestamp, log.level, log.component, log.message,
                    json.dumps(log.data) if log.data else None
                ))
                
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Error saving log: {e}")
            return 0
            
    async def get_logs(self, 
                      level: Optional[str] = None,
                      component: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      limit: int = 100) -> List[SystemLog]:
        """Get system logs"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM system_logs WHERE 1=1"
                params = []
                
                if level:
                    query += " AND level = ?"
                    params.append(level)
                    
                if component:
                    query += " AND component = ?"
                    params.append(component)
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                logs = []
                for row in rows:
                    log = SystemLog(
                        id=row[0],
                        timestamp=datetime.fromisoformat(row[1]),
                        level=row[2],
                        component=row[3],
                        message=row[4],
                        data=json.loads(row[5]) if row[5] else None
                    )
                    logs.append(log)
                    
                return logs
                
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return []
            
    # Performance metrics operations
    async def save_daily_performance(self, 
                                   date: datetime,
                                   metrics: Dict[str, float]) -> None:
        """Save daily performance metrics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO performance_metrics 
                    (date, total_trades, winning_trades, losing_trades, total_pnl,
                     max_drawdown, sharpe_ratio, profit_factor, avg_trade, win_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date.date(),
                    metrics.get('total_trades', 0),
                    metrics.get('winning_trades', 0),
                    metrics.get('losing_trades', 0),
                    metrics.get('total_pnl', 0.0),
                    metrics.get('max_drawdown', 0.0),
                    metrics.get('sharpe_ratio', 0.0),
                    metrics.get('profit_factor', 0.0),
                    metrics.get('avg_trade', 0.0),
                    metrics.get('win_rate', 0.0)
                ))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving daily performance: {e}")
            
    async def get_performance_metrics(self, 
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get performance metrics as DataFrame"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "SELECT * FROM performance_metrics WHERE 1=1"
                params = []
                
                if start_date:
                    query += " AND date >= ?"
                    params.append(start_date.date())
                    
                if end_date:
                    query += " AND date <= ?"
                    params.append(end_date.date())
                    
                query += " ORDER BY date"
                
                df = pd.read_sql_query(query, db, params=params)
                df['date'] = pd.to_datetime(df['date'])
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return pd.DataFrame()
            
    # Settings operations
    async def save_setting(self, key: str, value: str) -> None:
        """Save a setting"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO settings (key, value)
                    VALUES (?, ?)
                """, (key, value))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving setting: {e}")
            
    async def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT value FROM settings WHERE key = ?", (key,)
                )
                row = await cursor.fetchone()
                return row[0] if row else default
                
        except Exception as e:
            self.logger.error(f"Error getting setting: {e}")
            return default
            
    # Database maintenance
    async def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            # import shutil  # Moved to function to avoid circular import
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up database: {e}")
            return False
            
    async def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Clean old logs
                await db.execute(
                    "DELETE FROM system_logs WHERE timestamp < ?", (cutoff_date,)
                )
                
                # Clean old risk metrics
                await db.execute(
                    "DELETE FROM risk_metrics WHERE timestamp < ?", (cutoff_date,)
                )
                
                # Clean old opportunities
                await db.execute(
                    "DELETE FROM opportunities WHERE timestamp < ? AND executed = FALSE", 
                    (cutoff_date,)
                )
                
                await db.commit()
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # Count records in each table
                tables = ['trades', 'positions', 'risk_metrics', 'opportunities', 
                         'supervisor_actions', 'system_logs', 'performance_metrics']
                
                for table in tables:
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                    count = await cursor.fetchone()
                    stats[f"{table}_count"] = count[0]
                    
                # Database size
                db_size = Path(self.db_path).stat().st_size
                stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}

# Global database manager instance
database = DatabaseManager()

if __name__ == "__main__":
    # Test database
    async def test_database():
        db = DatabaseManager("test_trading_bot.db")
        
        # Test saving a trade
        trade = TradeRecord(
            symbol="BTC/USDT",
            side="buy",
            amount=0.1,
            entry_price=45000.0,
            exit_price=46000.0,
            pnl=100.0,
            commission=1.0,
            leverage=10.0,
            strategy="test"
        )
        
        trade_id = await db.save_trade(trade)
        print(f"Trade saved with ID: {trade_id}")
        
        # Test getting trades
        trades = await db.get_trades()
        print(f"Retrieved {len(trades)} trades")
        
        # Test database stats
        stats = await db.get_database_stats()
        print(f"Database stats: {stats}")
        
    asyncio.run(test_database())
