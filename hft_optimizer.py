#!/usr/bin/env python3
"""
UOTA Elite v2 - High-Frequency Trading (HFT) Optimizer
Lightning speed optimization for zero-budget 24/7 cloud deployment
"""

import asyncio
import numpy as np
import pandas as pd
import logging
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil

@dataclass
class HFTConfig:
    """HFT configuration"""
    max_candles: int = 100  # Reduced from 1000 for memory efficiency
    cpu_threshold: float = 80.0  # CPU usage threshold
    memory_threshold_mb: float = 100.0  # Memory threshold
    max_workers: int = 4  # Async worker pool size
    order_timeout: float = 0.1  # 100ms order timeout
    heartbeat_interval: float = 30.0  # 30 seconds
    log_level: str = "CRITICAL"  # Only critical events

class HFTOptimizer:
    """High-Frequency Trading Optimizer"""
    
    def __init__(self):
        self.config = HFTConfig()
        self.logger = self._setup_logging()
        self.is_running = False
        
        # Performance tracking
        self.execution_times = []
        self.memory_usage = []
        self.cpu_usage = []
        
        # Async components
        self.mt5_semaphore = asyncio.Semaphore(self.config.max_workers)
        self.telegram_semaphore = asyncio.Semaphore(2)
        
        # NumPy optimized arrays
        self.price_buffer = np.zeros(self.config.max_candles)
        self.volume_buffer = np.zeros(self.config.max_candles)
        self.time_buffer = np.zeros(self.config.max_candles)
        
    def _setup_logging(self):
        """Setup optimized logging"""
        os.makedirs('logs', exist_ok=True)
        
        # Only log critical events to save disk space
        logging.basicConfig(
            level=logging.CRITICAL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/hft_optimizer.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def async_mt5_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Asynchronous MT5 operation with semaphore control"""
        async with self.mt5_semaphore:
            try:
                start_time = time.time()
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    operation_func(*args, **kwargs),
                    timeout=self.config.order_timeout
                )
                
                execution_time = time.time() - start_time
                self.execution_times.append(execution_time)
                
                # Keep execution time history manageable
                if len(self.execution_times) > 1000:
                    self.execution_times = self.execution_times[-500:]
                
                self.logger.debug(f"⚡ {operation_name} completed in {execution_time*1000:.2f}ms")
                return result
                
            except asyncio.TimeoutError:
                self.logger.critical(f"⏰ {operation_name} timeout after {self.config.order_timeout}s")
                raise
            except Exception as e:
                self.logger.critical(f"❌ {operation_name} failed: {e}")
                raise
    
    def vectorized_smc_analysis(self, price_data: np.ndarray, volume_data: np.ndarray) -> Dict:
        """Vectorized SMC analysis using NumPy"""
        try:
            start_time = time.time()
            
            # Vectorized calculations using NumPy
            prices = price_data[-self.config.max_candles:]
            volumes = volume_data[-self.config.max_candles:]
            
            # Calculate moving averages (vectorized)
            ma_short = np.convolve(prices, np.ones(5)/5, mode='valid')[-1]
            ma_long = np.convolve(prices, np.ones(20)/20, mode='valid')[-1]
            
            # Calculate volatility (vectorized)
            returns = np.diff(prices)
            volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0
            
            # Detect Order Blocks (vectorized)
            highs = prices
            lows = prices
            
            # Find swing highs and lows
            swing_highs = np.where(prices[1:-1] > prices[:-2])[0] + 1
            swing_lows = np.where(prices[1:-1] < prices[:-2])[0] + 1
            
            # Order Block detection (simplified but vectorized)
            order_blocks = []
            if len(swing_highs) > 0 and len(swing_lows) > 0:
                # Last swing high and low
                last_swing_high = swing_highs[-1] if len(swing_highs) > 0 else len(prices) - 1
                last_swing_low = swing_lows[-1] if len(swing_lows) > 0 else 0
                
                # Order Block zones
                if last_swing_high > 0:
                    order_blocks.append({
                        'type': 'sell_side',
                        'price': prices[last_swing_high],
                        'strength': abs(prices[last_swing_high] - prices[-1])
                    })
                
                if last_swing_low > 0:
                    order_blocks.append({
                        'type': 'buy_side',
                        'price': prices[last_swing_low],
                        'strength': abs(prices[-1] - prices[last_swing_low])
                    })
            
            # Liquidity Sweep detection (vectorized)
            liquidity_sweep = False
            if len(returns) > 10:
                recent_returns = returns[-10:]
                # Check for sharp price movement against trend
                if len(recent_returns) > 5:
                    trend = np.mean(recent_returns[-5:])
                    current_move = recent_returns[-1]
                    
                    # Liquidity sweep if current move is opposite to trend
                    if (trend > 0 and current_move < -trend * 2) or \
                       (trend < 0 and current_move > -trend * 2):
                        liquidity_sweep = True
            
            # Calculate confidence score (vectorized)
            confidence_factors = []
            
            # Trend alignment
            if ma_short > ma_long:
                confidence_factors.append(0.8)  # Uptrend
            elif ma_short < ma_long:
                confidence_factors.append(0.8)  # Downtrend
            else:
                confidence_factors.append(0.3)  # Ranging
            
            # Volatility factor
            if volatility > 0:
                vol_factor = min(1.0, 0.5 / volatility)
                confidence_factors.append(vol_factor)
            else:
                confidence_factors.append(0.5)
            
            # Volume factor
            avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
            current_volume = volumes[-1] if len(volumes) > 0 else 0
            
            if current_volume > avg_volume * 1.5:
                confidence_factors.append(0.9)
            elif current_volume > avg_volume:
                confidence_factors.append(0.7)
            else:
                confidence_factors.append(0.4)
            
            # Final confidence score
            confidence = np.mean(confidence_factors)
            
            analysis_time = time.time() - start_time
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'symbol': 'XAUUSD',
                'current_price': float(prices[-1]) if len(prices) > 0 else 0,
                'ma_short': float(ma_short),
                'ma_long': float(ma_long),
                'volatility': float(volatility),
                'liquidity_sweep': liquidity_sweep,
                'order_blocks': order_blocks,
                'confidence': float(confidence),
                'analysis_time_ms': analysis_time * 1000,
                'data_points': len(prices)
            }
            
            self.logger.debug(f"🧠 SMC analysis completed in {analysis_time*1000:.2f}ms")
            
            return result
            
        except Exception as e:
            self.logger.critical(f"❌ Vectorized SMC analysis failed: {e}")
            return {}
    
    def optimize_memory_usage(self):
        """Optimize memory usage below 100MB"""
        try:
            # Get current memory usage
            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024
            
            if current_memory > self.config.memory_threshold_mb:
                self.logger.warning(f"🧹 Memory usage high: {current_memory:.1f}MB - Optimizing...")
                
                # Force garbage collection
                import gc
                collected = gc.collect()
                
                # Clear buffers
                self.price_buffer = np.zeros(self.config.max_candles)
                self.volume_buffer = np.zeros(self.config.max_candles)
                self.time_buffer = np.zeros(self.config.max_candles)
                
                # Clear execution history
                if len(self.execution_times) > 100:
                    self.execution_times = self.execution_times[-50:]
                
                new_memory = process.memory_info().rss / 1024 / 1024
                
                self.logger.info(f"🧹 Memory optimized: {current_memory:.1f}MB -> {new_memory:.1f}MB ({collected} objects)")
                
                return new_memory < self.config.memory_threshold_mb
            
            return True
            
        except Exception as e:
            self.logger.critical(f"❌ Memory optimization failed: {e}")
            return False
    
    def check_spread_and_fees(self, symbol: str, bid: float, ask: float) -> Dict:
        """Check spread and fees to ensure profitability"""
        try:
            spread = ask - bid
            spread_pips = spread * 10000  # Convert to pips for XAUUSD
            
            # Calculate if spread is acceptable (less than 30 pips for XAUUSD)
            spread_acceptable = spread_pips < 30
            
            # Calculate minimum profit needed to cover spread
            min_profit = spread * 2  # Need to make at least 2x spread
            
            result = {
                'symbol': symbol,
                'bid': bid,
                'ask': ask,
                'spread': spread,
                'spread_pips': spread_pips,
                'spread_acceptable': spread_acceptable,
                'min_profit_pips': min_profit * 10000,
                'trade_recommended': spread_acceptable,
                'timestamp': datetime.now().isoformat()
            }
            
            if not spread_acceptable:
                self.logger.warning(f"💸 Spread too wide: {spread_pips:.1f} pips - Trade not recommended")
            else:
                self.logger.info(f"✅ Spread acceptable: {spread_pips:.1f} pips")
            
            return result
            
        except Exception as e:
            self.logger.critical(f"❌ Spread check failed: {e}")
            return {}
    
    async def async_telegram_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Asynchronous Telegram operation with semaphore control"""
        async with self.telegram_semaphore:
            try:
                start_time = time.time()
                
                result = await operation_func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                self.logger.debug(f"📱 {operation_name} completed in {execution_time*1000:.2f}ms")
                
                return result
                
            except Exception as e:
                self.logger.critical(f"❌ Telegram {operation_name} failed: {e}")
                raise
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        try:
            process = psutil.Process()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
                'cpu_usage_percent': psutil.cpu_percent(interval=0.1),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'active_threads': threading.active_count(),
                'execution_times': {
                    'count': len(self.execution_times),
                    'avg_ms': np.mean(self.execution_times) * 1000 if self.execution_times else 0,
                    'max_ms': np.max(self.execution_times) * 1000 if self.execution_times else 0,
                    'min_ms': np.min(self.execution_times) * 1000 if self.execution_times else 0
                },
                'buffer_sizes': {
                    'price_buffer': len(self.price_buffer),
                    'volume_buffer': len(self.volume_buffer),
                    'time_buffer': len(self.time_buffer)
                }
            }
            
            # Check thresholds
            metrics['memory_ok'] = metrics['memory_usage_mb'] < self.config.memory_threshold_mb
            metrics['cpu_ok'] = metrics['cpu_usage_percent'] < self.config.cpu_threshold
            
            return metrics
            
        except Exception as e:
            self.logger.critical(f"❌ Error getting performance metrics: {e}")
            return {}
    
    async def run_hft_optimization(self):
        """Run HFT optimization loop"""
        try:
            self.logger.info("⚡ Starting HFT optimization...")
            self.is_running = True
            
            while self.is_running:
                try:
                    start_time = time.time()
                    
                    # Optimize memory if needed
                    self.optimize_memory_usage()
                    
                    # Get performance metrics
                    metrics = self.get_performance_metrics()
                    
                    # Log critical events only
                    if not metrics['memory_ok']:
                        self.logger.critical(f"🚨 Memory usage high: {metrics['memory_usage_mb']:.1f}MB")
                    
                    if not metrics['cpu_ok']:
                        self.logger.critical(f"🚨 CPU usage high: {metrics['cpu_usage_percent']:.1f}%")
                    
                    # Log performance summary every 5 minutes
                    if int(time.time()) % 300 == 0:
                        self.logger.critical(f"📊 Performance: CPU {metrics['cpu_usage_percent']:.1f}%, Memory {metrics['memory_usage_mb']:.1f}MB")
                    
                    # Async sleep with minimal CPU usage
                    await asyncio.sleep(1.0)
                    
                    # Monitor execution time
                    loop_time = time.time() - start_time
                    if loop_time > 1.1:  # If loop takes more than 1.1 seconds
                        self.logger.critical(f"⚠️ Loop slow: {loop_time:.2f}s")
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 HFT optimization stopped by user")
                    break
                except Exception as e:
                    self.logger.critical(f"❌ Error in HFT optimization loop: {e}")
                    await asyncio.sleep(1.0)
            
            self.is_running = False
            
        except Exception as e:
            self.logger.critical(f"❌ Fatal error in HFT optimization: {e}")
    
    def stop(self):
        """Stop HFT optimizer"""
        self.is_running = False
        self.logger.info("🛑 HFT optimizer stopped")

# Global HFT optimizer instance
hft_optimizer = HFTOptimizer()

async def main():
    """Main entry point"""
    print("⚡ Starting HFT Optimizer...")
    
    optimizer = hft_optimizer
    
    try:
        await optimizer.run_hft_optimization()
    except KeyboardInterrupt:
        print("\n🛑 HFT Optimizer stopped by user")
        optimizer.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        optimizer.stop()

if __name__ == "__main__":
    asyncio.run(main())
