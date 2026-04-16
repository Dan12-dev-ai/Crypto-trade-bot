"""
UOTA Elite v2 - SMC Logic Gate
Smart Money Concepts validation for elite trading
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class SMCDecision(Enum):
    """SMC decision types"""
    BUY_STRONG = "buy_strong"
    BUY_WEAK = "buy_weak"
    SELL_STRONG = "sell_strong"
    SELL_WEAK = "sell_weak"
    NO_SETUP = "no_setup"

@dataclass
class SMCAnalysis:
    """Complete SMC analysis result"""
    decision: SMCDecision
    confidence: float  # 0-1
    order_block_signal: float
    liquidity_sweep_signal: float
    market_structure_signal: float
    rsi_signal: float
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    reasoning: str
    timestamp: datetime

class SMCLogicGate:
    """Elite SMC Logic Gate - Only allows high-confidence setups"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Elite symbols for SMC analysis
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
        
        # SMC thresholds (elite standards)
        self.order_block_threshold = 0.75  # 75% minimum
        self.liquidity_sweep_threshold = 0.70  # 70% minimum
        self.market_structure_threshold = 0.65  # 65% minimum
        self.rsi_threshold = 0.60  # 60% minimum
        
        # Risk management (1% absolute rule)
        self.max_risk_per_trade = 0.01  # 1% non-negotiable
        
        # Performance tracking
        self.skill_score = 100.0  # Start at 100%
        self.setup_count = 0
        self.valid_setup_count = 0
        
    async def analyze_smc_setup(self, 
                              symbol: str, 
                              market_data: List[Dict],
                              account_balance: float = 1000.0) -> Optional[SMCAnalysis]:
        """Complete SMC analysis with logic gate validation"""
        try:
            # Validate symbol
            if symbol not in self.elite_symbols:
                self.logger.warning(f"⚠️ Non-elite symbol: {symbol}")
                return None
            
            # Minimum data requirement
            if len(market_data) < 50:
                self.logger.warning(f"⚠️ Insufficient data for {symbol}: {len(market_data)} candles")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(market_data)
            df.set_index('time', inplace=True)
            df.sort_index(inplace=True)
            
            # Perform SMC analysis
            order_block_signal = await self._analyze_order_blocks(df)
            liquidity_sweep_signal = await self._analyze_liquidity_sweeps(df)
            market_structure_signal = await self._analyze_market_structure(df)
            rsi_signal = await self._analyze_rsi(df)
            
            # Logic Gate validation
            setup_valid = await self._validate_smc_logic_gate(
                order_block_signal,
                liquidity_sweep_signal,
                market_structure_signal,
                rsi_signal
            )
            
            if not setup_valid:
                self.logger.debug(f"🔒 Logic Gate blocked setup for {symbol}")
                return None
            
            # Calculate combined confidence
            combined_confidence = (
                order_block_signal * 0.35 +      # Order blocks weighted highest
                liquidity_sweep_signal * 0.30 +  # Liquidity sweeps
                market_structure_signal * 0.20 +  # Market structure
                rsi_signal * 0.15                 # RSI confirmation
            )
            
            # Determine trade direction and levels
            decision, entry, stop_loss, take_profit = await self._determine_trade_setup(
                df, order_block_signal, liquidity_sweep_signal
            )
            
            if decision == SMCDecision.NO_SETUP:
                return None
            
            # Calculate lot size based on 1% risk rule
            lot_size = await self._calculate_lot_size(
                entry, stop_loss, account_balance, symbol
            )
            
            # Generate reasoning
            reasoning = await self._generate_reasoning(
                order_block_signal, liquidity_sweep_signal,
                market_structure_signal, rsi_signal, decision
            )
            
            analysis = SMCAnalysis(
                decision=decision,
                confidence=combined_confidence,
                order_block_signal=order_block_signal,
                liquidity_sweep_signal=liquidity_sweep_signal,
                market_structure_signal=market_structure_signal,
                rsi_signal=rsi_signal,
                entry_price=entry,
                stop_loss=stop_loss,
                take_profit=take_profit,
                lot_size=lot_size,
                reasoning=reasoning,
                timestamp=datetime.now()
            )
            
            # Update skill score
            self.setup_count += 1
            if combined_confidence >= 0.80:  # 80%+ confidence = valid setup
                self.valid_setup_count += 1
                self.skill_score = (self.valid_setup_count / self.setup_count) * 100
            
            self.logger.info(f"🎯 SMC Setup Found: {symbol} | Confidence: {combined_confidence:.1%} | {decision.value}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error in SMC analysis for {symbol}: {e}")
            return None
    
    async def _validate_smc_logic_gate(self,
                                     order_block: float,
                                     liquidity_sweep: float,
                                     market_structure: float,
                                     rsi: float) -> bool:
        """Logic Gate validation - only allow elite setups"""
        try:
            # All signals must meet minimum thresholds
            if order_block < self.order_block_threshold:
                self.logger.debug(f"🔒 Order block too weak: {order_block:.1%} < {self.order_block_threshold:.1%}")
                return False
            
            if liquidity_sweep < self.liquidity_sweep_threshold:
                self.logger.debug(f"🔒 Liquidity sweep too weak: {liquidity_sweep:.1%} < {self.liquidity_sweep_threshold:.1%}")
                return False
            
            if market_structure < self.market_structure_threshold:
                self.logger.debug(f"🔒 Market structure too weak: {market_structure:.1%} < {self.market_structure_threshold:.1%}")
                return False
            
            if rsi < self.rsi_threshold:
                self.logger.debug(f"🔒 RSI too weak: {rsi:.1%} < {self.rsi_threshold:.1%}")
                return False
            
            # Additional validation: signals must be aligned
            signal_alignment = abs(order_block - liquidity_sweep) < 0.3  # Within 30%
            if not signal_alignment:
                self.logger.debug(f"🔒 Signals not aligned: OB={order_block:.1%}, LS={liquidity_sweep:.1%}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in logic gate validation: {e}")
            return False
    
    async def _analyze_order_blocks(self, df: pd.DataFrame) -> float:
        """Analyze Order Block patterns"""
        try:
            # Order Block characteristics
            high = df['high']
            low = df['low']
            close = df['close']
            volume = df.get('tick_volume', pd.Series([1]*len(df)))
            
            # Find strong momentum moves (last 10 candles)
            recent_df = df.tail(10)
            
            # Calculate momentum strength
            price_change = (recent_df['close'].iloc[-1] - recent_df['close'].iloc[0]) / recent_df['close'].iloc[0]
            momentum_score = min(abs(price_change) / 0.005, 1.0)  # 0.5% move = full score
            
            # Volume confirmation
            avg_volume = volume.tail(10).mean()
            current_volume = volume.tail(1).iloc[0]
            volume_score = min(current_volume / (avg_volume * 1.5), 1.0)  # 1.5x avg = full score
            
            # Consolidation pattern (price compression)
            price_range = (high.tail(5).max() - low.tail(5).min()) / close.tail(5).iloc[0]
            consolidation_score = 1.0 - min(price_range / 0.01, 1.0)  # 1% range = no consolidation
            
            # Order Block confidence
            order_block_confidence = (
                momentum_score * 0.4 +
                volume_score * 0.3 +
                consolidation_score * 0.3
            )
            
            return min(order_block_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing order blocks: {e}")
            return 0.0
    
    async def _analyze_liquidity_sweeps(self, df: pd.DataFrame) -> float:
        """Analyze Liquidity Sweep patterns"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            # Find recent extremes
            recent_high = high.tail(20).max()
            recent_low = low.tail(20).min()
            current_price = close.tail(1).iloc[0]
            
            # Check for sweep above recent high
            if current_price > recent_high * 0.999:  # Within 0.1% of high
                # Look for reversal pattern
                sweep_score = 0.8
            # Check for sweep below recent low
            elif current_price < recent_low * 1.001:  # Within 0.1% of low
                # Look for reversal pattern
                sweep_score = 0.8
            else:
                sweep_score = 0.0
            
            # Volume confirmation (low volume on sweep = manipulation)
            avg_volume = df.get('tick_volume', pd.Series([1]*len(df))).tail(20).mean()
            current_volume = df.get('tick_volume', pd.Series([1]*len(df))).tail(1).iloc[0]
            volume_manipulation = 1.0 - min(current_volume / (avg_volume * 0.7), 1.0)  # Low vol = manipulation
            
            # Price rejection (wick analysis)
            if len(df) >= 3:
                last_candle = df.tail(1).iloc[0]
                prev_candle = df.tail(2).iloc[0]
                
                # Check for long wick (rejection)
                if last_candle['high'] - last_candle['close'] > (last_candle['close'] - last_candle['low']) * 2:
                    rejection_score = 0.8
                elif last_candle['close'] - last_candle['low'] > (last_candle['high'] - last_candle['close']) * 2:
                    rejection_score = 0.8
                else:
                    rejection_score = 0.0
            else:
                rejection_score = 0.0
            
            # Liquidity Sweep confidence
            liquidity_sweep_confidence = (
                sweep_score * 0.5 +
                volume_manipulation * 0.3 +
                rejection_score * 0.2
            )
            
            return min(liquidity_sweep_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing liquidity sweeps: {e}")
            return 0.0
    
    async def _analyze_market_structure(self, df: pd.DataFrame) -> float:
        """Analyze Market Structure"""
        try:
            close = df['close']
            
            # Calculate moving averages
            ma_20 = close.rolling(20).mean()
            ma_50 = close.rolling(50).mean()
            
            # Trend strength
            if len(ma_20) >= 2 and len(ma_50) >= 2:
                trend_20 = (ma_20.iloc[-1] - ma_20.iloc[-2]) / ma_20.iloc[-2]
                trend_50 = (ma_50.iloc[-1] - ma_50.iloc[-2]) / ma_50.iloc[-2]
                
                trend_alignment = 1.0 if (trend_20 * trend_50) > 0 else 0.0
                trend_strength = min((abs(trend_20) + abs(trend_50)) / 0.002, 1.0)  # 0.2% = full score
            else:
                trend_alignment = 0.0
                trend_strength = 0.0
            
            # Price position relative to MAs
            current_price = close.tail(1).iloc[0]
            if len(ma_20) >= 1 and len(ma_50) >= 1:
                ma_20_current = ma_20.iloc[-1]
                ma_50_current = ma_50.iloc[-1]
                
                # Price above both MAs = bullish structure
                if current_price > ma_20_current and current_price > ma_50_current:
                    structure_score = 0.8
                # Price below both MAs = bearish structure
                elif current_price < ma_20_current and current_price < ma_50_current:
                    structure_score = 0.8
                # Price between MAs = neutral
                else:
                    structure_score = 0.4
            else:
                structure_score = 0.0
            
            # Volatility normalization
            returns = close.pct_change().dropna()
            volatility = returns.tail(20).std()
            optimal_volatility = 1.0 - abs(volatility - 0.02) / 0.02  # 2% vol = optimal
            vol_score = max(optimal_volatility, 0)
            
            # Market Structure confidence
            market_structure_confidence = (
                trend_alignment * 0.4 +
                trend_strength * 0.3 +
                structure_score * 0.2 +
                vol_score * 0.1
            )
            
            return min(market_structure_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing market structure: {e}")
            return 0.0
    
    async def _analyze_rsi(self, df: pd.DataFrame) -> float:
        """Analyze RSI for confirmation"""
        try:
            close = df['close']
            
            # Calculate RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            if len(rsi) >= 1:
                current_rsi = rsi.iloc[-1]
                
                # RSI in optimal range (30-70)
                if 30 <= current_rsi <= 70:
                    rsi_score = 0.8
                # RSI approaching extremes (20-30 or 70-80)
                elif 20 <= current_rsi <= 30 or 70 <= current_rsi <= 80:
                    rsi_score = 0.6
                # RSI in danger zones (<20 or >80)
                else:
                    rsi_score = 0.2
                
                # RSI momentum (divergence check)
                if len(rsi) >= 3:
                    rsi_trend = rsi.tail(3).diff().mean()
                    price_trend = close.tail(3).pct_change().mean()
                    
                    # Bullish divergence (price down, RSI up)
                    if price_trend < 0 and rsi_trend > 0:
                        divergence_bonus = 0.2
                    # Bearish divergence (price up, RSI down)
                    elif price_trend > 0 and rsi_trend < 0:
                        divergence_bonus = 0.2
                    else:
                        divergence_bonus = 0.0
                    
                    rsi_score = min(rsi_score + divergence_bonus, 1.0)
                
                return rsi_score
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"❌ Error analyzing RSI: {e}")
            return 0.0
    
    async def _determine_trade_setup(self,
                                    df: pd.DataFrame,
                                    order_block_signal: float,
                                    liquidity_sweep_signal: float) -> Tuple[SMCDecision, float, float, float]:
        """Determine trade direction and levels"""
        try:
            current_price = df['close'].tail(1).iloc[0]
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            
            # Determine direction based on SMC signals
            if order_block_signal > 0.8 and liquidity_sweep_signal > 0.7:
                # Strong bullish setup
                decision = SMCDecision.BUY_STRONG
                entry = current_price * 0.999  # Slight discount
                stop_loss = recent_low * 0.998  # Below recent low
                take_profit = current_price * 1.015  # 1.5% target
                
            elif order_block_signal > 0.6 and liquidity_sweep_signal > 0.5:
                # Weak bullish setup
                decision = SMCDecision.BUY_WEAK
                entry = current_price * 0.9995
                stop_loss = recent_low * 0.999
                take_profit = current_price * 1.01  # 1% target
                
            elif order_block_signal < 0.2 and liquidity_sweep_signal < 0.3:
                # Strong bearish setup
                decision = SMCDecision.SELL_STRONG
                entry = current_price * 1.001  # Slight premium
                stop_loss = recent_high * 1.002  # Above recent high
                take_profit = current_price * 0.985  # 1.5% target
                
            elif order_block_signal < 0.4 and liquidity_sweep_signal < 0.5:
                # Weak bearish setup
                decision = SMCDecision.SELL_WEAK
                entry = current_price * 1.0005
                stop_loss = recent_high * 1.001
                take_profit = current_price * 0.99  # 1% target
                
            else:
                decision = SMCDecision.NO_SETUP
                entry = stop_loss = take_profit = current_price
            
            return decision, entry, stop_loss, take_profit
            
        except Exception as e:
            self.logger.error(f"❌ Error determining trade setup: {e}")
            return SMCDecision.NO_SETUP, 0, 0, 0
    
    async def _calculate_lot_size(self,
                                entry_price: float,
                                stop_loss: float,
                                account_balance: float,
                                symbol: str) -> float:
        """Calculate lot size based on 1% risk rule"""
        try:
            # Calculate risk amount (1% of account)
            risk_amount = account_balance * self.max_risk_per_trade
            
            # Calculate stop distance in pips
            stop_distance = abs(entry_price - stop_loss)
            
            # Calculate lot size (simplified for forex)
            # For XAUUSD: 1 lot = $100 per point
            # For forex pairs: 1 lot = $10 per point
            if symbol == 'XAUUSD':
                pip_value = 100.0  # $100 per point
            else:
                pip_value = 10.0   # $10 per point
            
            # Calculate lot size
            lot_size = risk_amount / (stop_distance * pip_value)
            
            # Round to standard lot sizes
            standard_lots = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0]
            
            # Find closest standard lot
            closest_lot = min(standard_lots, key=lambda x: abs(x - lot_size))
            
            # Ensure minimum lot size
            if closest_lot < 0.01:
                closest_lot = 0.01
            
            # Ensure maximum lot size (risk management)
            if closest_lot > 5.0:
                closest_lot = 5.0
            
            self.logger.debug(f"💰 Lot size calculation: {account_balance:.2f} balance -> {closest_lot:.2f} lots")
            
            return closest_lot
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating lot size: {e}")
            return 0.01  # Minimum lot size
    
    async def _generate_reasoning(self,
                                order_block: float,
                                liquidity_sweep: float,
                                market_structure: float,
                                rsi: float,
                                decision: SMCDecision) -> str:
        """Generate reasoning for the setup"""
        try:
            reasoning_parts = []
            
            # Order Block reasoning
            if order_block >= 0.8:
                reasoning_parts.append("Strong Order Block detected")
            elif order_block >= 0.6:
                reasoning_parts.append("Moderate Order Block")
            else:
                reasoning_parts.append("Weak Order Block")
            
            # Liquidity Sweep reasoning
            if liquidity_sweep >= 0.7:
                reasoning_parts.append("Clear Liquidity Sweep")
            elif liquidity_sweep >= 0.5:
                reasoning_parts.append("Potential Liquidity Sweep")
            else:
                reasoning_parts.append("No Liquidity Sweep")
            
            # Market Structure reasoning
            if market_structure >= 0.7:
                reasoning_parts.append("Aligned Market Structure")
            elif market_structure >= 0.5:
                reasoning_parts.append("Neutral Market Structure")
            else:
                reasoning_parts.append("Conflicted Market Structure")
            
            # RSI reasoning
            if rsi >= 0.7:
                reasoning_parts.append("Strong RSI confirmation")
            elif rsi >= 0.5:
                reasoning_parts.append("Moderate RSI confirmation")
            else:
                reasoning_parts.append("Weak RSI confirmation")
            
            # Direction reasoning
            if decision in [SMCDecision.BUY_STRONG, SMCDecision.BUY_WEAK]:
                reasoning_parts.append("Bullish bias")
            elif decision in [SMCDecision.SELL_STRONG, SMCDecision.SELL_WEAK]:
                reasoning_parts.append("Bearish bias")
            
            return " | ".join(reasoning_parts)
            
        except Exception as e:
            self.logger.error(f"❌ Error generating reasoning: {e}")
            return "Error generating reasoning"
    
    def get_skill_score(self) -> float:
        """Get current skill score"""
        return self.skill_score
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'skill_score': self.skill_score,
            'total_setups_analyzed': self.setup_count,
            'valid_setups_found': self.valid_setup_count,
            'setup_quality_ratio': self.valid_setup_count / max(self.setup_count, 1),
            'last_updated': datetime.now().isoformat()
        }

# Global SMC Logic Gate instance
smc_logic_gate = SMCLogicGate()
