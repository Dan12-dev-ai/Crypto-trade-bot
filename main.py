"""
DEDANBOT - Main Entry Point
Ultimate Opportunistic Trading Agent - Autonomous Trading System
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import our modules with error handling
try:
    from config import config
    from risk_manager import risk_manager
    from agents.supervisor import SupervisorAgent
    from opportunity_scanner import opportunity_scanner
    from exchange_integration import exchange_manager
    from telegram_alerts import telegram_alerts
    from database import database, SystemLog
    from dashboard import Dashboard
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure all required packages are installed: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dedanbot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DEDANBOT:
    """Main DEDANBOT trading system"""
    
    def __init__(self):
        self.supervisor: Optional[SupervisorAgent] = None
        self.is_running = False
        self.tasks = []
        
        # Ensure log directory exists
        Path('logs').mkdir(exist_ok=True)
        
    async def initialize(self, starting_balance: float) -> None:
        """Initialize the trading system"""
        try:
            logger.info("🤖 Initializing DEDANBOT...")
            
            # Validate configuration
            config_errors = config.validate_config()
            if config_errors:
                logger.error("Configuration errors found:")
                for error in config_errors:
                    logger.error(f"  - {error}")
                raise ValueError("Invalid configuration")
                
            # Initialize database
            logger.info("📊 Initializing database...")
            await database.save_log(SystemLog(
                level="INFO",
                component="main",
                message="System initialization started"
            ))
            
            # Initialize exchange manager
            logger.info("🌐 Connecting to exchanges...")
            await exchange_manager.connect_all()
            
            # Initialize supervisor
            logger.info("🧠 Initializing supervisor agent...")
            from langchain_community.llms import Ollama
            
            llm = Ollama(
                model=config.agents.llm_model,
                base_url=config.agents.ollama_base_url
            )
            
            self.supervisor = SupervisorAgent(llm)
            await self.supervisor.initialize(starting_balance)
            
            # Initialize Telegram alerts
            logger.info("📱 Starting Telegram bot...")
            await telegram_alerts.start()
            
            # Start opportunity scanner
            logger.info("🔍 Starting opportunity scanner...")
            scanner_task = asyncio.create_task(opportunity_scanner.start_scanning())
            self.tasks.append(scanner_task)
            
            # Send startup notification
            await telegram_alerts.send_system_alert(
                "System Startup",
                "DEDANBOT has been initialized and is ready to trade",
                "medium"
            )
            
            logger.info("✅ DEDANBOT initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing system: {e}")
            await database.save_log(SystemLog(
                level="ERROR",
                component="main",
                message=f"Initialization failed: {str(e)}",
                data={"error": str(e)}
            ))
            raise
            
    async def start_trading(self) -> None:
        """Start the main trading loop"""
        try:
            if not self.supervisor:
                raise ValueError("Supervisor not initialized")
                
            self.is_running = True
            logger.info("🚀 Starting autonomous trading...")
            
            await database.save_log(SystemLog(
                level="INFO",
                component="main",
                message="Autonomous trading started"
            ))
            
            # Start supervisor supervision loop
            supervisor_task = asyncio.create_task(self.supervisor.run_supervision_loop())
            self.tasks.append(supervisor_task)
            
            # Start monitoring tasks
            monitor_task = asyncio.create_task(self._monitor_system())
            self.tasks.append(monitor_task)
            
            # Start daily tasks
            daily_task = asyncio.create_task(self._daily_tasks())
            self.tasks.append(daily_task)
            
            logger.info("🎯 Trading system is now fully operational")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Error starting trading: {e}")
            await database.save_log(SystemLog(
                level="ERROR",
                component="main",
                message=f"Trading start failed: {str(e)}",
                data={"error": str(e)}
            ))
            
    async def _monitor_system(self) -> None:
        """Monitor system health and performance"""
        try:
            while self.is_running:
                try:
                    # Monitor exchange connections
                    health_status = await exchange_manager.health_check()
                    
                    for exchange, status in health_status.items():
                        if status['status'] == 'error':
                            await telegram_alerts.send_system_alert(
                                "Exchange Connection Error",
                                f"Lost connection to {exchange}: {status.get('error', 'Unknown error')}",
                                "high"
                            )
                            
                    # Monitor risk metrics
                    risk_summary = risk_manager.get_risk_summary()
                    
                    # Check for risk alerts
                    if risk_summary['daily_loss_pct'] >= 0.8:  # 80% of daily limit
                        await telegram_alerts.send_risk_alert(
                            "Daily Loss Limit",
                            f"Daily loss approaching limit: {risk_summary['daily_loss_pct']:.1%}",
                            risk_summary['daily_loss_pct'],
                            config.trading.max_daily_loss
                        )
                        
                    if risk_summary['current_drawdown'] >= 0.15:  # 15% drawdown
                        await telegram_alerts.send_risk_alert(
                            "High Drawdown",
                            f"Current drawdown: {risk_summary['current_drawdown']:.1%}",
                            risk_summary['current_drawdown'],
                            config.trading.max_drawdown
                        )
                        
                    # Log system status
                    await database.save_log(SystemLog(
                        level="INFO",
                        component="monitor",
                        message="System health check completed",
                        data={
                            "exchanges": health_status,
                            "risk_metrics": risk_summary,
                            "active_positions": risk_summary['open_positions']
                        }
                    ))
                    
                    # Wait before next check
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in system monitoring: {e}")
                    await asyncio.sleep(30)  # Brief pause on error
                    
        except Exception as e:
            logger.error(f"Critical error in system monitoring: {e}")
            
    async def _daily_tasks(self) -> None:
        """Perform daily maintenance tasks"""
        try:
            while self.is_running:
                try:
                    # Wait until midnight
                    now = datetime.now()
                    next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    if next_midnight <= now:
                        next_midnight += timedelta(days=1)
                        
                    sleep_seconds = (next_midnight - now).total_seconds()
                    await asyncio.sleep(sleep_seconds)
                    
                    # Daily reset
                    logger.info("🔄 Performing daily reset...")
                    
                    # Reset risk manager daily metrics
                    await risk_manager.reset_daily()
                    
                    # Send daily summary
                    await telegram_alerts.send_daily_summary()
                    
                    # Clean up old data
                    await database.cleanup_old_data(days_to_keep=90)
                    
                    # Backup database
                    backup_path = f"data/backup/dedanbot_backup_{datetime.now().strftime('%Y%m%d')}.db"
                    await database.backup_database(backup_path)
                    
                    # Log daily reset
                    await database.save_log(SystemLog(
                        level="INFO",
                        component="daily_tasks",
                        message="Daily reset completed",
                        data={"backup_path": backup_path}
                    ))
                    
                    logger.info("✅ Daily reset completed")
                    
                except Exception as e:
                    logger.error(f"Error in daily tasks: {e}")
                    await asyncio.sleep(3600)  # Try again in an hour
                    
        except Exception as e:
            logger.error(f"Critical error in daily tasks: {e}")
            
    async def stop(self) -> None:
        """Stop the trading system gracefully"""
        try:
            logger.info("🛑 Shutting down DEDANBOT...")
            
            self.is_running = False
            
            # Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
                    
            # Wait for tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Emergency stop all positions if needed
            if risk_manager.get_risk_summary()['open_positions'] > 0:
                logger.warning("Emergency closing all positions...")
                # This would trigger emergency close through supervisor
                
            # Stop components
            opportunity_scanner.stop_scanning()
            await telegram_alerts.stop()
            await exchange_manager.close_all_connections()
            
            # Send shutdown notification
            try:
                await telegram_alerts.send_system_alert(
                    "System Shutdown",
                    "DEDANBOT has been shut down",
                    "medium"
                )
            except:
                pass  # Telegram might already be stopped
                
            # Log shutdown
            await database.save_log(SystemLog(
                level="INFO",
                component="main",
                message="System shutdown completed"
            ))
            
            logger.info("✅ DEDANBOT shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def run_dashboard():
    """Run the Streamlit dashboard"""
    try:
        # Import and run dashboard
        import subprocess
        import webbrowser
        
        # Start Streamlit dashboard
        dashboard_process = subprocess.Popen([
            "streamlit", "run", "dashboard.py",
            "--server.port", str(config.dashboard.port),
            "--server.address", config.dashboard.host,
            "--server.headless", "true"
        ])
        
        # Open browser (optional)
        if config.dashboard.host == "localhost":
            webbrowser.open(f"http://localhost:{config.dashboard.port}")
            
        logger.info(f"📊 Dashboard started at http://{config.dashboard.host}:{config.dashboard.port}")
        
        return dashboard_process
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        return None

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DEDANBOT - Autonomous Trading Agent")
    parser.add_argument("--balance", type=float, default=config.trading.starting_balance,
                       help="Starting balance for trading")
    parser.add_argument("--leverage", type=float, default=config.trading.max_leverage,
                       help="Maximum leverage")
    parser.add_argument("--goal", type=str, default=config.trading.goal_command,
                       help="Trading goal command")
    parser.add_argument("--dashboard", action="store_true",
                       help="Run dashboard alongside trading")
    parser.add_argument("--paper", action="store_true",
                       help="Run in paper trading mode")
    parser.add_argument("--backtest", action="store_true",
                       help="Run backtesting mode")
    
    args = parser.parse_args()
    
    # Update configuration with command line arguments
    config.trading.starting_balance = args.balance
    config.trading.max_leverage = args.leverage
    config.trading.goal_command = args.goal
    
    if args.paper:
        logger.info("📝 Running in paper trading mode")
        # Set all exchanges to testnet/sandbox
        for exchange_config in config.exchanges.values():
            exchange_config.sandbox = True
            exchange_config.testnet = True
            
    # Create and initialize system
    dedanbot = DEDANBOT()
    dedanbot.setup_signal_handlers()
    
    dashboard_process = None
    
    try:
        # Initialize system
        await dedanbot.initialize(args.balance)
        
        # Start dashboard if requested
        if args.dashboard:
            dashboard_process = await run_dashboard()
            
        # Start trading
        if not args.backtest:
            await dedanbot.start_trading()
        else:
            logger.info("📈 Backtesting mode - running analysis...")
            # Implement backtesting logic here
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await database.save_log(SystemLog(
            level="CRITICAL",
            component="main",
            message=f"Fatal error: {str(e)}",
            data={"error": str(e)}
        ))
    finally:
        # Cleanup
        await uota.stop()
        
        if dashboard_process:
            dashboard_process.terminate()
            dashboard_process.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 UOTA Elite v2 shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
