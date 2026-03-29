"""
DEDANBOT - Strategy Manager
Handles automatic strategy switching based on market conditions (ADX, ATR)
"""

import pandas as pd
import pandas_ta as ta
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple

class TradingStrategy(Enum):
    TREND = "TrendStrategy"
    RANGE = "RangeStrategy"
    SCALPING = "ScalpingStrategy"
    WAIT = "WaitStrategy"

class StrategyManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Thresholds for strategy switching
        self.adx_trend_threshold = 25
        self.adx_range_threshold = 20
        
        # Volatility thresholds (Relative ATR: ATR / Close * 100)
        self.volatility_low_threshold = 0.5  # Below 0.5% relative volatility is considered low
        self.volatility_extreme_threshold = 2.5  # Above 2.5% relative volatility is considered extreme
        
    def analyze_market_conditions(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze market data using pandas_ta to determine the optimal trading strategy.
        
        Args:
            data: DataFrame with 'high', 'low', 'close', 'volume' columns.
            
        Returns:
            Dict containing the recommended strategy, reasoning, and technical metrics.
        """
        try:
            # Validate data requirements
            if data is None or data.empty or len(data) < 20:
                return {
                    "strategy": TradingStrategy.WAIT,
                    "reason": "Insufficient data for analysis (minimum 20 periods required)",
                    "metrics": {}
                }

            # Ensure column names are lowercase for pandas_ta consistency
            data.columns = [col.lower() for col in data.columns]

            # 1. Calculate Trend Strength (ADX)
            # ADX > 25 indicates a strong trend, < 20 indicates a weak trend/ranging market
            adx_df = ta.adx(data['high'], data['low'], data['close'], length=14)
            if adx_df is None or adx_df.empty:
                raise ValueError("Failed to calculate ADX")
                
            current_adx = adx_df['ADX_14'].iloc[-1]

            # 2. Calculate Volatility (ATR)
            atr_df = ta.atr(data['high'], data['low'], data['close'], length=14)
            if atr_df is None or atr_df.empty:
                raise ValueError("Failed to calculate ATR")
                
            current_atr = atr_df.iloc[-1]
            
            # 3. Calculate Relative Volatility (ATR as % of Price)
            current_price = data['close'].iloc[-1]
            rel_volatility = (current_atr / current_price) * 100

            # --- Strategy Switching Logic ---
            strategy = TradingStrategy.WAIT
            reason = ""

            # Rule 1: Extremely High Volatility -> ScalpingStrategy
            if rel_volatility > self.volatility_extreme_threshold:
                strategy = TradingStrategy.SCALPING
                reason = f"Extremely high volatility detected (Rel Vol: {rel_volatility:.2f}%). Switching to ScalpingStrategy for quick entries/exits."
            
            # Rule 2: Strong Trend -> TrendStrategy
            elif current_adx > self.adx_trend_threshold:
                strategy = TradingStrategy.TREND
                reason = f"Strong trend confirmed (ADX: {current_adx:.2f}). Switching to TrendStrategy to follow market momentum."
                
            # Rule 3: Low Trend and Low Volatility -> RangeStrategy
            elif current_adx < self.adx_range_threshold and rel_volatility < self.volatility_low_threshold:
                strategy = TradingStrategy.RANGE
                reason = f"Range-bound market with low volatility (ADX: {current_adx:.2f}, Rel Vol: {rel_volatility:.2f}%). Switching to RangeStrategy for mean reversion."
            
            # Default: Wait or Neutral
            else:
                strategy = TradingStrategy.WAIT
                reason = f"Market in transition or neutral state (ADX: {current_adx:.2f}, Rel Vol: {rel_volatility:.2f}%). Waiting for clearer signals."

            self.logger.info(f"Strategy Manager Recommendation: {strategy.value} | Reason: {reason}")

            return {
                "strategy": strategy,
                "strategy_name": strategy.value,
                "reason": reason,
                "metrics": {
                    "adx": round(current_adx, 2),
                    "atr": round(current_atr, 4),
                    "rel_volatility_pct": round(rel_volatility, 2),
                    "price": round(current_price, 4)
                }
            }

        except Exception as e:
            self.logger.error(f"Error in strategy manager analysis: {e}")
            return {
                "strategy": TradingStrategy.WAIT,
                "reason": f"Analysis error: {str(e)}",
                "metrics": {}
            }

# Global instance for easy access
strategy_manager = StrategyManager()
