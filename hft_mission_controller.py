#!/usr/bin/env python3
"""
UOTA Elite v2 - HFT Mission Controller
Fastest and most stable trading agent for low-spec VPS
"""

import asyncio
import logging
import json
import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class HFTMissionController:
    """HFT Mission Controller for zero-budget deployment"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.is_running = False
        self.mission_start = None
        
        # Import optimized components
        from hft_optimizer import hft_optimizer
        from hft_telegram_c2 import hft_telegram_c2
        from hardened_smc_strategy import hardened_smc_strategy
        from keep_alive import keep_alive_monitor
        
        self.optimizer = hft_optimizer
        self.telegram_c2 = hft_telegram_c2
        self.smc_strategy = hardened_smc_strategy
        self.keep_alive = keep_alive_monitor
        
        # Performance tracking
        self.loop_times = []
        self.last_optimization = time.time()
        
    def _setup_logging(self):
        """Setup logging"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/hft_mission.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def ultra_fast_market_analysis(self, symbol: str = 'XAUUSD') -> Dict:
        """Ultra-fast market analysis using vectorized operations"""
        try:
            start_time = time.time()
            
            # Get price data (simplified - would use MT5 in real implementation)
            import numpy as np
            
            # Generate realistic price data for testing
            np.random.seed(42)  # For reproducible results
            base_price = 2000.0
            price_changes = np.random.normal(0, 0.5, 100)  # Random walk with volatility
            
            prices = base_price + np.cumsum(price_changes)
            volumes = np.random.exponential(1.0, 100)  # Random volumes
            
            # Use vectorized SMC analysis
            analysis = self.smc_strategy.vectorized_market_analysis(prices, volumes)
            
            analysis_time = time.time() - start_time
            analysis['analysis_time_ms'] = analysis_time * 1000
            analysis['symbol'] = symbol
            
            self.logger.debug(f"🧠 Ultra-fast analysis completed in {analysis_time*1000:.2f}ms")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in ultra-fast analysis: {e}")
            return {}
    
    async def check_trade_opportunity(self, analysis: Dict, bid: float, ask: float) -> Dict:
        """Check trade opportunity with institutional rules"""
        try:
            start_time = time.time()
            
            # Check trade conditions
            trade_conditions = self.smc_strategy.check_trade_conditions(analysis, bid, ask)
            
            # Additional optimization: Skip analysis if spread is too wide
            if trade_conditions.get('spread_pips', 0) > self.smc_strategy.config.max_spread_pips:
                return {
                    'opportunity': False,
                    'reason': f'Spread too wide: {trade_conditions.get("spread_pips", 0):.1f} pips',
                    'analysis_time_ms': (time.time() - start_time) * 1000
                }
            
            # Check if we have a high-confidence setup
            if trade_conditions.get('confidence', 0) >= 0.8:
                trade_conditions['opportunity'] = 'HIGH'
            elif trade_conditions.get('confidence', 0) >= 0.7:
                trade_conditions['opportunity'] = 'MEDIUM'
            else:
                trade_conditions['opportunity'] = 'LOW'
            
            trade_conditions['opportunity_score'] = trade_conditions.get('confidence', 0) * 100
            trade_conditions['analysis_time_ms'] = (time.time() - start_time) * 1000
            
            self.logger.debug(f"🎯 Trade opportunity check: {trade_conditions['opportunity']} ({trade_conditions['opportunity_score']:.1f})")
            
            return trade_conditions
            
        except Exception as e:
            self.logger.error(f"❌ Error checking trade opportunity: {e}")
            return {'opportunity': False, 'error': str(e)}
    
    async def execute_optimized_trade(self, trade_conditions: Dict) -> Dict:
        """Execute trade with maximum optimization"""
        try:
            start_time = time.time()
            
            if not trade_conditions.get('trade_allowed', False):
                return {
                    'success': False,
                    'reason': trade_conditions.get('reason', 'Trade not allowed'),
                    'execution_time_ms': (time.time() - start_time) * 1000
                }
            
            # Execute trade using hardened SMC strategy
            trade_result = self.smc_strategy.execute_trade(trade_conditions)
            trade_result['execution_time_ms'] = (time.time() - start_time) * 1000
            
            # Send notification
            await self.telegram_c2.send_message(f"""
📈 **HFT TRADE EXECUTED**
═══════════════════════════════════
Direction: {trade_result.get('direction', 'UNKNOWN')}
Size: {trade_result.get('position_size', 0):.2f} lots
Entry: {trade_result.get('entry_price', 0):.5f}
Stop Loss: {trade_result.get('stop_loss', 0):.5f}
Take Profit: {trade_result.get('take_profit', 0):.5f}
Risk: {trade_result.get('risk_percent', 0):.1f}%
Confidence: {trade_result.get('confidence', 0):.1f}
Spread: {trade_result.get('spread_pips', 0):.1f} pips
Execution: {trade_result.get('execution_time_ms', 0):.2f}ms
Time: {datetime.now().strftime('%H:%M:%S')}
""")
            
            self.loop_times.append(trade_result.get('execution_time_ms', 0))
            
            # Keep loop time history manageable
            if len(self.loop_times) > 100:
                self.loop_times = self.loop_times[-50:]
            
            self.logger.info(f"⚡ Trade executed: {trade_result.get('direction')} {trade_result.get('position_size', 0):.2f} lots in {trade_result.get('execution_time_ms', 0):.2f}ms")
            
            return trade_result
            
        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {e}")
            return {'success': False, 'error': str(e)}
    
    async def optimize_system_performance(self):
        """Optimize system for maximum performance"""
        try:
            # Run optimization every 5 minutes
            if time.time() - self.last_optimization < 300:
                return
            
            self.last_optimization = time.time()
            
            # Optimize memory
            self.optimizer.optimize_memory_usage()
            
            # Get performance metrics
            metrics = self.optimizer.get_performance_metrics()
            
            # Log performance summary
            if int(time.time()) % 900 == 0:  # Every 15 minutes
                self.logger.info(f"📊 Performance: CPU {metrics.get('cpu_usage_percent', 0):.1f}%, Memory {metrics.get('memory_usage_mb', 0):.1f}MB")
            
            # Force garbage collection
            import gc
            collected = gc.collect()
            
            self.logger.debug(f"🧹 System optimized: {collected} objects collected")
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing system: {e}")
    
    async def run_hft_mission_loop(self):
        """Main HFT mission loop"""
        try:
            self.logger.info("🚀 Starting HFT Mission Controller...")
            self.is_running = True
            self.mission_start = datetime.now()
            
            loop_count = 0
            
            while self.is_running:
                try:
                    loop_start = time.time()
                    
                    # Ultra-fast market analysis
                    analysis = await self.ultra_fast_market_analysis()
                    
                    if 'error' not in analysis:
                        # Simulate bid/ask (would get from MT5)
                        current_price = analysis.get('current_price', 2000.0)
                        spread = 0.5  # 50 pips spread
                        bid = current_price - (spread / 20000)
                        ask = current_price + (spread / 20000)
                        
                        # Check trade opportunity
                        trade_conditions = await self.check_trade_opportunity(analysis, bid, ask)
                        
                        # Execute trade if opportunity is good
                        if trade_conditions.get('opportunity') in ['HIGH', 'MEDIUM']:
                            trade_result = await self.execute_optimized_trade(trade_conditions)
                            
                            # Log trade
                            self.logger.info(f"📈 Trade #{loop_count + 1}: {trade_result.get('direction')} {trade_result.get('position_size', 0):.2f} lots @ {trade_result.get('entry_price', 0):.5f}")
                        
                            # Send performance optimization
                            await self.telegram_c2.send_message(f"📈 **HFT TRADE #{loop_count + 1} EXECUTED**\\nDirection: {trade_result.get('direction')}\\nSize: {trade_result.get('position_size', 0):.2f} lots\\nEntry: {trade_result.get('entry_price', 0):.5f}\\nConfidence: {trade_result.get('confidence', 0):.1f}%\\nExecution: {trade_result.get('execution_time_ms', 0):.2f}ms")
                    
                    # Optimize system performance
                    await self.optimize_system_performance()
                    
                    # Calculate loop time
                    loop_time = time.time() - loop_start
                    
                    # Log slow loops
                    if loop_time > 1.0:  # If loop takes more than 1 second
                        self.logger.warning(f"⚠️ Slow loop detected: {loop_time:.2f}s")
                    
                    loop_count += 1
                    
                    # Adaptive delay based on performance
                    if loop_time < 0.1:
                        await asyncio.sleep(0.01)  # 10ms for ultra-fast
                    elif loop_time < 0.5:
                        await asyncio.sleep(0.05)  # 50ms for fast
                    else:
                        await asyncio.sleep(0.1)   # 100ms for normal
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 HFT Mission stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in HFT mission loop: {e}")
                    await asyncio.sleep(0.1)
            
            self.is_running = False
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in HFT mission loop: {e}")
    
    def get_mission_status(self) -> Dict:
        """Get comprehensive mission status"""
        try:
            uptime = datetime.now() - self.mission_start if self.mission_start else timedelta(0)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'is_running': self.is_running,
                'uptime': str(uptime),
                'mission_start': self.mission_start.isoformat() if self.mission_start else None,
                'loop_performance': {
                    'avg_loop_time_ms': sum(self.loop_times) / len(self.loop_times) if self.loop_times else 0,
                    'max_loop_time_ms': max(self.loop_times) if self.loop_times else 0,
                    'min_loop_time_ms': min(self.loop_times) if self.loop_times else 0,
                    'total_loops': len(self.loop_times)
                },
                'strategy_status': self.smc_strategy.get_strategy_status(),
                'system_performance': self.optimizer.get_performance_metrics()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting mission status: {e}")
            return {'error': str(e)}
    
    async def start_mission(self):
        """Start the HFT mission"""
        try:
            self.logger.info("🚀 Starting HFT Mission...")
            
            # Start keep-alive monitor
            self.keep_alive.run_keep_alive_monitor()
            
            # Start HFT mission loop
            await self.run_hft_mission_loop()
            
        except Exception as e:
            self.logger.error(f"❌ Error starting mission: {e}")
    
    def stop_mission(self):
        """Stop the HFT mission"""
        try:
            self.is_running = False
            self.keep_alive.stop()
            self.logger.info("🛑 HFT Mission stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping mission: {e}")

# Global HFT mission controller
hft_mission_controller = HFTMissionController()

async def main():
    """Main entry point"""
    print("🚀 Starting HFT Mission Controller...")
    
    controller = hft_mission_controller
    
    try:
        await controller.start_mission()
    except KeyboardInterrupt:
        print("\n🛑 HFT Mission stopped by user")
        controller.stop_mission()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        controller.stop_mission()

if __name__ == "__main__":
    asyncio.run(main())
