#!/usr/bin/env python3
"""
UOTA Elite v2 - Hardened SMC Strategy
Institutional liquidity rules with hard-locked 1% risk management
"""

import numpy as np
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class SMCConfig:
    """SMC configuration with hard-locked rules"""
    risk_rule_percent: float = 1.0  # Hard-locked 1% risk
    min_confidence: float = 0.7  # Hard-locked 70% confidence
    max_spread_pips: float = 30.0  # Maximum spread for trade
    min_profit_ratio: float = 2.0  # Minimum profit to spread ratio
    max_daily_trades: int = 20  # Maximum trades per day
    lot_size_step: float = 0.01  # Lot size increment
    max_lot_size: float = 1.0  # Maximum lot size
    slippage_allowance: float = 5.0  # Pips slippage allowance

class HardenedSMCStrategy:
    """Hardened SMC strategy with institutional rules"""
    
    def __init__(self):
        self.config = SMCConfig()
        self.logger = self._setup_logging()
        
        # Trade tracking
        self.daily_trades = 0
        self.last_trade_date = None
        self.trade_history = []
        
        # SMC indicators (vectorized)
        self.price_buffer = np.zeros(200)  # 200 candles for analysis
        self.volume_buffer = np.zeros(200)
        self.time_buffer = np.zeros(200)
        
        # Institutional levels
        self.support_levels = []
        self.resistance_levels = []
        self.liquidity_zones = []
        
    def _setup_logging(self):
        """Setup logging"""
        import os
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/hft_smc_strategy.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def vectorized_market_analysis(self, prices: np.ndarray, volumes: np.ndarray) -> Dict:
        """Vectorized market analysis using NumPy"""
        try:
            if len(prices) < 50:
                return {'error': 'Insufficient data'}
            
            # Vectorized moving averages
            ma_5 = np.convolve(prices, np.ones(5)/5, mode='valid')
            ma_20 = np.convolve(prices, np.ones(20)/20, mode='valid')
            ma_50 = np.convolve(prices, np.ones(50)/50, mode='valid')
            
            # Vectorized volatility
            returns = np.diff(prices)
            volatility = np.std(returns[-20:])
            
            # Vectorized RSI calculation
            gains = np.where(returns > 0, returns, 0)
            losses = np.where(returns < 0, -returns, 0)
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
            
            rs = 100 - (100 / (1 + (avg_gain / avg_loss) if avg_loss > 0 else 1))
            rsi_values = []
            
            for i in range(13, len(returns)):
                if i >= 13:
                    # Simplified RSI calculation
                    rsi_values.append(rs)
                else:
                    # Use default RSI for early values
                    rsi_values.append(50)
            
            current_rsi = rsi_values[-1] if rsi_values else 50
            
            # Vectorized support/resistance
            highs = prices
            lows = prices
            
            # Find recent highs and lows
            recent_highs = self._find_swings(highs, window=10, is_high=True)
            recent_lows = self._find_swings(lows, window=10, is_high=False)
            
            # Fibonacci levels (simplified)
            current_price = prices[-1]
            fib_levels = self._calculate_fibonacci_levels(recent_highs, recent_lows, current_price)
            
            # Liquidity detection
            liquidity_sweep = self._detect_liquidity_sweep(prices, volumes, returns)
            
            # Order Block detection
            order_blocks = self._detect_order_blocks(prices, recent_highs, recent_lows)
            
            # Market structure
            market_structure = self._analyze_market_structure(ma_5, ma_20, ma_50)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'current_price': float(current_price),
                'ma_5': float(ma_5[-1]) if len(ma_5) > 0 else current_price,
                'ma_20': float(ma_20[-1]) if len(ma_20) > 0 else current_price,
                'ma_50': float(ma_50[-1]) if len(ma_50) > 0 else current_price,
                'volatility': float(volatility),
                'rsi': float(current_rsi),
                'recent_highs': recent_highs,
                'recent_lows': recent_lows,
                'fibonacci_levels': fib_levels,
                'liquidity_sweep': liquidity_sweep,
                'order_blocks': order_blocks,
                'market_structure': market_structure,
                'data_points': len(prices)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error in vectorized market analysis: {e}")
            return {'error': str(e)}
    
    def _find_swings(self, data: np.ndarray, window: int, is_high: bool) -> List[Dict]:
        """Find swing highs or lows using vectorized operations"""
        try:
            swings = []
            data_len = len(data)
            
            for i in range(window, data_len - window):
                window_data = data[i:i+window]
                
                if is_high:
                    # Find highest point
                    max_idx = np.argmax(window_data)
                    max_val = window_data[max_idx]
                    
                    # Check if it's a swing high
                    left_max = np.max(window_data[:max_idx]) if max_idx > 0 else max_val
                    right_max = np.max(window_data[max_idx+1:]) if max_idx < len(window_data) - 1 else max_val
                    
                    if max_val > left_max and max_val > right_max:
                        swings.append({
                            'index': i + max_idx,
                            'price': float(max_val),
                            'type': 'high'
                        })
                else:
                    # Find lowest point
                    min_idx = np.argmin(window_data)
                    min_val = window_data[min_idx]
                    
                    # Check if it's a swing low
                    left_min = np.min(window_data[:min_idx]) if min_idx > 0 else min_val
                    right_min = np.min(window_data[min_idx+1:]) if min_idx < len(window_data) - 1 else min_val
                    
                    if min_val < left_min and min_val < right_min:
                        swings.append({
                            'index': i + min_idx,
                            'price': float(min_val),
                            'type': 'low'
                        })
            
            return swings
            
        except Exception as e:
            self.logger.error(f"❌ Error finding swings: {e}")
            return []
    
    def _calculate_fibonacci_levels(self, highs: List[Dict], lows: List[Dict], current_price: float) -> List[Dict]:
        """Calculate Fibonacci retracement levels"""
        try:
            if not highs or not lows:
                return []
            
            # Find significant high and low
            recent_high = max(highs, key=lambda x: x['price'])
            recent_low = min(lows, key=lambda x: x['price'])
            
            diff = recent_high['price'] - recent_low['price']
            
            if diff <= 0:
                return []
            
            # Fibonacci ratios
            fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
            
            levels = []
            for ratio in fib_ratios:
                level_price = recent_low['price'] + (diff * ratio)
                levels.append({
                    'level': ratio,
                    'price': level_price,
                    'type': 'retracement'
                })
            
            return levels
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating Fibonacci levels: {e}")
            return []
    
    def _detect_liquidity_sweep(self, prices: np.ndarray, volumes: np.ndarray, returns: np.ndarray) -> Dict:
        """Detect liquidity sweeps using vectorized operations"""
        try:
            if len(returns) < 20:
                return {'detected': False, 'reason': 'Insufficient data'}
            
            # Calculate average volume
            avg_volume = np.mean(volumes[-20:])
            
            # Find volume spikes (potential liquidity grabs)
            volume_spikes = volumes > (avg_volume * 2)
            spike_indices = np.where(volume_spikes)[0]
            
            # Check for sharp price movements against volume spikes
            liquidity_sweeps = []
            
            for spike_idx in spike_indices:
                if spike_idx < len(returns) - 1:
                    # Check if price moved sharply after volume spike
                    price_move = abs(returns[spike_idx + 1])
                    
                    # Liquidity sweep criteria
                    if price_move > np.std(returns[-20:]) * 2:
                        liquidity_sweeps.append({
                            'index': spike_idx,
                            'price': float(prices[spike_idx]),
                            'volume': float(volumes[spike_idx]),
                            'move': float(price_move),
                            'strength': 'High' if price_move > np.std(returns[-20:]) * 3 else 'Medium'
                        })
            
            detected = len(liquidity_sweeps) > 0
            
            return {
                'detected': detected,
                'sweeps': liquidity_sweeps,
                'count': len(liquidity_sweeps),
                'avg_volume': float(avg_volume)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting liquidity sweep: {e}")
            return {'detected': False, 'error': str(e)}
    
    def _detect_order_blocks(self, prices: np.ndarray, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detect order blocks using institutional methodology"""
        try:
            order_blocks = []
            
            # Find consolidation zones
            for i in range(20, len(prices) - 20):
                window = prices[i-20:i+20]
                
                # Check for consolidation (low volatility)
                volatility = np.std(np.diff(window))
                
                if volatility < np.std(np.diff(prices)) * 0.5:  # Low volatility
                    # Find support/resistance in this window
                    window_high = np.max(window)
                    window_low = np.min(window)
                    
                    # Check if this is a valid order block
                    if self._is_valid_order_block(window, window_high, window_low, highs, lows):
                        order_blocks.append({
                            'start_index': i-20,
                            'end_index': i,
                            'high': float(window_high),
                            'low': float(window_low),
                            'strength': self._calculate_order_block_strength(window, window_high, window_low),
                            'type': 'consolidation'
                        })
            
            # Find breakout order blocks
            for high in highs[-5:]:  # Recent highs
                for low in lows[-5:]:  # Recent lows
                    # Check for order block at these levels
                    if abs(high['price'] - low['price']) < (high['price'] * 0.01):  # Within 1%
                        order_blocks.append({
                            'high_index': high['index'],
                            'low_index': low['index'],
                            'high': float(high['price']),
                            'low': float(low['price']),
                            'strength': min(high.get('strength', 0.5), low.get('strength', 0.5)),
                            'type': 'swing'
                        })
            
            return order_blocks
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting order blocks: {e}")
            return []
    
    def _is_valid_order_block(self, window: np.ndarray, high: float, low: float, highs: List[Dict], lows: List[Dict]) -> bool:
        """Validate if this is a genuine order block"""
        try:
            # Check if multiple touches occurred
            touches_at_high = np.sum(window >= high * 0.999) >= 2
            touches_at_low = np.sum(window <= low * 1.001) >= 2
            
            # Must have at least 2 touches
            if touches_at_high or touches_at_low:
                return True
            
            # Check for volume confirmation (if available)
            # This is simplified - in real implementation, would check volume profile
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error validating order block: {e}")
            return False
    
    def _calculate_order_block_strength(self, window: np.ndarray, high: float, low: float) -> float:
        """Calculate order block strength"""
        try:
            # Strength based on consolidation tightness
            range_size = high - low
            price_range = np.max(window) - np.min(window)
            
            # Stronger if consolidation is tighter
            if range_size > 0:
                strength = min(1.0, price_range / range_size)
            else:
                strength = 0.5
            
            return strength
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating order block strength: {e}")
            return 0.5
    
    def _analyze_market_structure(self, ma_5: np.ndarray, ma_20: np.ndarray, ma_50: np.ndarray) -> Dict:
        """Analyze market structure using moving averages"""
        try:
            current_price = float(ma_5[-1]) if len(ma_5) > 0 else 0
            
            structure = {
                'trend': 'RANGING',
                'strength': 'WEAK'
            }
            
            if len(ma_5) > 0 and len(ma_20) > 0 and len(ma_50) > 0:
                ma_5_val = float(ma_5[-1])
                ma_20_val = float(ma_20[-1])
                ma_50_val = float(ma_50[-1])
                
                # Determine trend
                if ma_5_val > ma_20_val > ma_50_val:
                    structure['trend'] = 'STRONG_UPTREND'
                    structure['strength'] = 'STRONG'
                elif ma_5_val < ma_20_val < ma_50_val:
                    structure['trend'] = 'STRONG_DOWNTREND'
                    structure['strength'] = 'STRONG'
                else:
                    # Check for alignment (uptrend but flattening)
                    if ma_5_val > ma_20_val and ma_5_val < ma_50_val:
                        structure['trend'] = 'UPTREND_CONSOLIDATION'
                        structure['strength'] = 'MEDIUM'
                    elif ma_5_val < ma_20_val and ma_5_val > ma_50_val:
                        structure['trend'] = 'DOWNTREND_CONSOLIDATION'
                        structure['strength'] = 'MEDIUM'
            
            structure['current_price'] = current_price
            structure['ma_5'] = ma_5_val
            structure['ma_20'] = ma_20_val
            structure['ma_50'] = ma_50_val
            
            return structure
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing market structure: {e}")
            return {'trend': 'UNKNOWN', 'strength': 'WEAK'}
    
    def check_trade_conditions(self, analysis: Dict, bid: float, ask: float) -> Dict:
        """Check if trade conditions are met with hard-locked rules"""
        try:
            current_price = analysis.get('current_price', 0)
            spread = ask - bid
            spread_pips = spread * 10000  # Convert to pips
            
            # Check 1: Spread must be acceptable
            if spread_pips > self.config.max_spread_pips:
                return {
                    'trade_allowed': False,
                    'reason': f'Spread too wide: {spread_pips:.1f} pips',
                    'spread_pips': spread_pips,
                    'max_allowed': self.config.max_spread_pips
                }
            
            # Check 2: Confidence must meet minimum
            confidence = analysis.get('confidence', 0)
            if confidence < self.config.min_confidence:
                return {
                    'trade_allowed': False,
                    'reason': f'Confidence too low: {confidence:.2f} < {self.config.min_confidence}',
                    'confidence': confidence,
                    'min_required': self.config.min_confidence
                }
            
            # Check 3: Must have order block
            order_blocks = analysis.get('order_blocks', [])
            if not order_blocks:
                return {
                    'trade_allowed': False,
                    'reason': 'No order blocks detected',
                    'order_blocks_count': 0
                }
            
            # Check 4: Daily trade limit
            current_date = datetime.now().date()
            if self.last_trade_date and current_date == self.last_trade_date:
                if self.daily_trades >= self.config.max_daily_trades:
                    return {
                        'trade_allowed': False,
                        'reason': f'Daily trade limit reached: {self.daily_trades}/{self.config.max_daily_trades}',
                        'daily_trades': self.daily_trades,
                        'max_allowed': self.config.max_daily_trades
                    }
            
            # Check 5: Risk management
            account_balance = 10000  # Example balance
            risk_amount = account_balance * (self.config.risk_rule_percent / 100)
            
            # Calculate position size based on risk
            atr = analysis.get('volatility', 0.001)  # Simplified ATR
            stop_distance = atr * 2  # 2x ATR for stop loss
            
            if stop_distance > 0:
                position_size = risk_amount / stop_distance
            else:
                position_size = self.config.lot_size_step
            
            # Apply lot size limits
            position_size = max(self.config.lot_size_step, min(position_size, self.config.max_lot_size))
            
            # Calculate potential loss
            potential_loss = position_size * stop_distance
            
            # Check if potential loss is within 1% risk
            if potential_loss > risk_amount:
                position_size = risk_amount / stop_distance
            
            return {
                'trade_allowed': True,
                'reason': 'All conditions met',
                'confidence': confidence,
                'spread_pips': spread_pips,
                'order_blocks_count': len(order_blocks),
                'position_size': position_size,
                'stop_distance': stop_distance,
                'potential_loss': potential_loss,
                'risk_percent': self.config.risk_rule_percent,
                'direction': self._determine_trade_direction(analysis)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error checking trade conditions: {e}")
            return {'trade_allowed': False, 'reason': f'Error: {e}'}
    
    def _determine_trade_direction(self, analysis: Dict) -> str:
        """Determine trade direction based on analysis"""
        try:
            structure = analysis.get('market_structure', {})
            trend = structure.get('trend', 'RANGING')
            
            if 'UPTREND' in trend:
                return 'BUY'
            elif 'DOWNTREND' in trend:
                return 'SELL'
            else:
                # Use other signals for ranging market
                liquidity_sweep = analysis.get('liquidity_sweep', {})
                
                if liquidity_sweep.get('detected') and liquidity_sweep.get('sweeps'):
                    last_sweep = liquidity_sweep['sweeps'][0]
                    
                    # If liquidity sweep detected, trade in direction of sweep
                    if last_sweep.get('move', 0) < 0:
                        return 'SELL'  # Sweep down, sell
                    else:
                        return 'BUY'   # Sweep up, buy
                
                return 'WAIT'  # No clear signal
                
        except Exception as e:
            self.logger.error(f"❌ Error determining trade direction: {e}")
            return 'WAIT'
    
    def execute_trade(self, trade_conditions: Dict) -> Dict:
        """Execute trade with hard-locked risk management"""
        try:
            if not trade_conditions.get('trade_allowed', False):
                return {
                    'success': False,
                    'reason': trade_conditions.get('reason', 'Trade not allowed')
                }
            
            # Calculate entry price with slippage allowance
            current_price = trade_conditions.get('current_price', 0)
            direction = trade_conditions.get('direction', 'BUY')
            
            if direction == 'BUY':
                entry_price = current_price + (self.config.slippage_allowance / 10000)
                stop_loss = current_price - trade_conditions.get('stop_distance', 0)
                take_profit = current_price + (trade_conditions.get('stop_distance', 0) * self.config.min_profit_ratio)
            else:
                entry_price = current_price - (self.config.slippage_allowance / 10000)
                stop_loss = current_price + trade_conditions.get('stop_distance', 0)
                take_profit = current_price - (trade_conditions.get('stop_distance', 0) * self.config.min_profit_ratio)
            
            # Execute trade (simplified - would connect to MT5)
            trade_result = {
                'success': True,
                'direction': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': trade_conditions.get('position_size', 0.01),
                'risk_amount': trade_conditions.get('potential_loss', 0),
                'timestamp': datetime.now().isoformat(),
                'confidence': trade_conditions.get('confidence', 0),
                'spread_pips': trade_conditions.get('spread_pips', 0)
            }
            
            # Update trade tracking
            self.daily_trades += 1
            self.last_trade_date = datetime.now().date()
            self.trade_history.append(trade_result)
            
            self.logger.info(f"📈 Trade executed: {direction} {trade_conditions.get('position_size', 0.01)} lots @ {entry_price}")
            
            return trade_result
            
        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'config': {
                    'risk_rule_percent': self.config.risk_rule_percent,
                    'min_confidence': self.config.min_confidence,
                    'max_spread_pips': self.config.max_spread_pips,
                    'max_daily_trades': self.config.max_daily_trades,
                    'lot_size_step': self.config.lot_size_step,
                    'max_lot_size': self.config.max_lot_size
                },
                'current_state': {
                    'daily_trades': self.daily_trades,
                    'last_trade_date': self.last_trade_date.isoformat() if self.last_trade_date else None,
                    'trade_history_count': len(self.trade_history),
                    'risk_rule_locked': True,
                    'smc_logic_locked': True
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting strategy status: {e}")
            return {'error': str(e)}

# Global hardened SMC strategy
hardened_smc_strategy = HardenedSMCStrategy()
