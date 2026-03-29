"""
Crypto trade bot - Market Analyst Agent
Technical analysis + FinRL-style reinforcement learning signals
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import talib
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

from crewai import Agent, Task
from langchain.llms.base import LLM
from langchain.schema import HumanMessage, SystemMessage

@dataclass
class TechnicalSignal:
    """Technical analysis signal"""
    symbol: str
    timestamp: datetime
    price: float
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float  # 0-1
    indicators: Dict[str, float]
    timeframe: str
    confidence: float
    
@dataclass
class MLSignal:
    """Machine learning generated signal"""
    symbol: str
    timestamp: datetime
    prediction: float  # -1 to 1 (sell to buy)
    probability: float  # 0-1
    model_confidence: float
    features_used: List[str]
    expected_return: float
    volatility: float

class MarketAnalystAgent:
    """Market Analyst Agent - Technical analysis and ML signals"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.scaler = MinMaxScaler()
        self.model = None
        self.is_trained = False
        
        # Analysis parameters
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        self.lookback_periods = {
            'short': 20,
            'medium': 50,
            'long': 200
        }
        
        # Initialize ML model
        self._initialize_ml_model()
        
    def create_crewai_agent(self) -> Agent:
        """Create CrewAI agent instance"""
        return Agent(
            role='Market Analyst',
            goal='Generate precise trading signals using technical analysis and machine learning',
            backstory="""You are a quantitative analyst with expertise in both technical 
            analysis and machine learning. You've spent years developing trading algorithms 
            that combine classical technical indicators with modern deep learning approaches. 
            You can identify patterns in market data that others miss and provide highly 
            accurate trading signals with specific confidence levels.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
            system_template="""You are the Market Analyst Agent for Crypto trade bot.
            
            Your core responsibilities:
            1. Perform comprehensive technical analysis across multiple timeframes
            2. Generate ML-based predictions using historical patterns
            3. Combine signals to produce high-confidence trading recommendations
            4. Calculate expected returns and volatility for each signal
            5. Provide detailed reasoning for all signals
            
            Technical Indicators Used:
            - Moving Averages (EMA, SMA)
            - RSI, MACD, Stochastics
            - Bollinger Bands, ATR
            - Volume indicators
            - Pattern recognition
            
            ML Approach:
            - LSTM neural networks for time series prediction
            - Feature engineering from price and volume data
            - Ensemble methods for robustness
            - Real-time model updating
            
            Always provide specific confidence levels and expected returns."""
        )
        
    def _initialize_ml_model(self) -> None:
        """Initialize the machine learning model"""
        try:
            # Simple LSTM model for demonstration
            class TradingLSTM(nn.Module):
                def __init__(self, input_size=20, hidden_size=50, num_layers=2, output_size=1):
                    super(TradingLSTM, self).__init__()
                    self.hidden_size = hidden_size
                    self.num_layers = num_layers
                    self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
                    self.fc = nn.Linear(hidden_size, output_size)
                    self.dropout = nn.Dropout(0.2)
                    
                def forward(self, x):
                    h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                    c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
                    out, _ = self.lstm(x, (h0, c0))
                    out = self.dropout(out[:, -1, :])
                    out = self.fc(out)
                    return torch.tanh(out)  # Output between -1 and 1
                    
            self.model = TradingLSTM()
            self.logger.info("ML model initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing ML model: {e}")
            
    async def analyze_market(self, symbol: str, price_data: pd.DataFrame) -> List[TechnicalSignal]:
        """Perform comprehensive technical analysis"""
        try:
            signals = []
            
            for timeframe in self.timeframes:
                if timeframe in price_data.columns:
                    tf_data = price_data[timeframe]
                    signal = await self._analyze_timeframe(symbol, tf_data, timeframe)
                    if signal:
                        signals.append(signal)
                        
            # Combine signals across timeframes
            combined_signal = self._combine_technical_signals(signals)
            return [combined_signal] if combined_signal else []
            
        except Exception as e:
            self.logger.error(f"Error analyzing market for {symbol}: {e}")
            return []
            
    async def _analyze_timeframe(self, symbol: str, data: pd.DataFrame, timeframe: str) -> Optional[TechnicalSignal]:
        """Analyze specific timeframe"""
        try:
            if len(data) < 50:
                return None
                
            # Calculate technical indicators
            indicators = self._calculate_indicators(data)
            
            # Generate signal based on indicators
            signal_type, strength, confidence = self._generate_signal_from_indicators(indicators)
            
            current_price = data['close'].iloc[-1]
            
            return TechnicalSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                price=current_price,
                signal_type=signal_type,
                strength=strength,
                indicators=indicators,
                timeframe=timeframe,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing timeframe {timeframe} for {symbol}: {e}")
            return None
            
    def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive technical indicators"""
        try:
            close = data['close'].values.astype(float)
            high = data['high'].values.astype(float)
            low = data['low'].values.astype(float)
            volume = data['volume'].values.astype(float)
            
            indicators = {}
            
            # Trend indicators
            indicators['sma_20'] = talib.SMA(close, timeperiod=20)[-1]
            indicators['sma_50'] = talib.SMA(close, timeperiod=50)[-1]
            indicators['sma_200'] = talib.SMA(close, timeperiod=200)[-1]
            indicators['ema_12'] = talib.EMA(close, timeperiod=12)[-1]
            indicators['ema_26'] = talib.EMA(close, timeperiod=26)[-1]
            
            # Momentum indicators
            indicators['rsi'] = talib.RSI(close, timeperiod=14)[-1]
            macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = macd[-1]
            indicators['macd_signal'] = macd_signal[-1]
            indicators['macd_hist'] = macd_hist[-1]
            
            # Volatility indicators
            upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            indicators['bb_upper'] = upper[-1]
            indicators['bb_middle'] = middle[-1]
            indicators['bb_lower'] = lower[-1]
            indicators['atr'] = talib.ATR(high, low, close, timeperiod=14)[-1]
            
            # Volume indicators
            indicators['obv'] = talib.OBV(close, volume)[-1]
            indicators['adx'] = talib.ADX(high, low, close, timeperiod=14)[-1]
            
            # Price action
            indicators['stoch_k'], indicators['stoch_d'] = talib.STOCH(high, low, close)
            indicators['stoch_k'] = indicators['stoch_k'][-1]
            indicators['stoch_d'] = indicators['stoch_d'][-1]
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}

    def _generate_signal_from_indicators(self, indicators: Dict[str, float]) -> Tuple[str, float, float]:
        """Generate signal based on weighted indicator analysis"""
        try:
            score = 0
            count = 0
            
            # Trend Score
            if indicators.get('ema_12', 0) > indicators.get('ema_26', 0):
                score += 1
            else:
                score -= 1
            count += 1
            
            if indicators.get('sma_50', 0) > indicators.get('sma_200', 0):
                score += 1
            else:
                score -= 1
            count += 1
            
            # Momentum Score
            rsi = indicators.get('rsi', 50)
            if rsi > 70:  # Overbought
                score -= 1
            elif rsi < 30:  # Oversold
                score += 1
            elif rsi > 50:
                score += 0.5
            else:
                score -= 0.5
            count += 1
            
            # MACD Score
            if indicators.get('macd_hist', 0) > 0:
                score += 1
            else:
                score -= 1
            count += 1
            
            # Volatility Adjustment
            # (No direct score, but used for confidence)
            
            # ADX (Trend Strength)
            adx = indicators.get('adx', 0)
            strength_multiplier = 1.0
            if adx > 25:
                strength_multiplier = 1.5
            elif adx < 20:
                strength_multiplier = 0.5
                
            # Final calculation
            normalized_score = score / count
            
            if normalized_score > 0.3:
                signal_type = 'buy'
            elif normalized_score < -0.3:
                signal_type = 'sell'
            else:
                signal_type = 'hold'
                
            strength = abs(normalized_score) * strength_multiplier
            confidence = min(0.95, strength)
            
            return signal_type, min(1.0, strength), confidence
            
        except Exception as e:
            self.logger.error(f"Error generating signal from indicators: {e}")
            return 'hold', 0.0, 0.0
            
    def _combine_technical_signals(self, signals: List[TechnicalSignal]) -> Optional[TechnicalSignal]:
        """Combine signals across multiple timeframes"""
        try:
            if not signals:
                return None
                
            # Weight timeframes differently
            timeframe_weights = {
                '1m': 0.1, '5m': 0.15, '15m': 0.2,
                '1h': 0.25, '4h': 0.2, '1d': 0.1
            }
            
            buy_score = 0
            sell_score = 0
            total_weight = 0
            
            for signal in signals:
                weight = timeframe_weights.get(signal.timeframe, 0.1)
                total_weight += weight
                
                if signal.signal_type == 'buy':
                    buy_score += signal.strength * weight
                elif signal.signal_type == 'sell':
                    sell_score += signal.strength * weight
                    
            # Determine final signal
            if buy_score > sell_score:
                final_signal_type = 'buy'
                final_strength = buy_score / total_weight
            elif sell_score > buy_score:
                final_signal_type = 'sell'
                final_strength = sell_score / total_weight
            else:
                final_signal_type = 'hold'
                final_strength = 0.0
                
            # Use the most recent signal's price and indicators
            latest_signal = max(signals, key=lambda x: x.timestamp)
            
            return TechnicalSignal(
                symbol=latest_signal.symbol,
                timestamp=datetime.now(),
                price=latest_signal.price,
                signal_type=final_signal_type,
                strength=final_strength,
                indicators=latest_signal.indicators,
                timeframe='combined',
                confidence=min(final_strength * 1.2, 1.0)
            )
            
        except Exception as e:
            self.logger.error(f"Error combining technical signals: {e}")
            return None
            
    async def generate_ml_signal(self, symbol: str, price_data: pd.DataFrame) -> Optional[MLSignal]:
        """Generate machine learning based signal"""
        try:
            if len(price_data) < 100:
                return None
                
            # Prepare features
            features = self._prepare_ml_features(price_data)
            if features is None:
                return None
                
            # Make prediction
            with torch.no_grad():
                features_tensor = torch.FloatTensor(features).unsqueeze(0)
                prediction = self.model(features_tensor).item()
                
            # Calculate probability and confidence
            probability = abs(prediction)
            confidence = min(probability * 1.5, 1.0)
            
            # Calculate expected return and volatility
            returns = price_data['close'].pct_change().dropna()
            expected_return = returns.mean() * 252  # Annualized
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            return MLSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                prediction=prediction,
                probability=probability,
                model_confidence=confidence,
                features_used=list(features.keys()) if isinstance(features, dict) else [],
                expected_return=expected_return,
                volatility=volatility
            )
            
        except Exception as e:
            self.logger.error(f"Error generating ML signal for {symbol}: {e}")
            return None
            
    def _prepare_ml_features(self, data: pd.DataFrame) -> Optional[np.ndarray]:
        """Prepare features for ML model"""
        try:
            # Calculate technical features
            features = []
            
            # Price changes
            close = data['close']
            features.extend([
                close.pct_change(1).iloc[-1],  # 1-period return
                close.pct_change(5).iloc[-1],  # 5-period return
                close.pct_change(20).iloc[-1],  # 20-period return
            ])
            
            # Moving averages
            features.extend([
                close.rolling(10).mean().iloc[-1] / close.iloc[-1] - 1,
                close.rolling(20).mean().iloc[-1] / close.iloc[-1] - 1,
                close.rolling(50).mean().iloc[-1] / close.iloc[-1] - 1,
            ])
            
            # Volatility
            features.extend([
                close.pct_change().rolling(10).std().iloc[-1],
                close.pct_change().rolling(20).std().iloc[-1],
            ])
            
            # Volume features
            if 'volume' in data.columns:
                volume = data['volume']
                features.extend([
                    volume.rolling(10).mean().iloc[-1] / volume.iloc[-1] - 1,
                    volume.pct_change(1).iloc[-1],
                ])
            else:
                features.extend([0, 0])
                
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            features.append(rsi.iloc[-1] / 100)  # Normalize to 0-1
            
            # Fill NaN values
            features = np.array(features)
            features = np.nan_to_num(features, nan=0.0)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error preparing ML features: {e}")
            return None
            
    async def train_model(self, training_data: pd.DataFrame) -> None:
        """Train the ML model with historical data"""
        try:
            self.logger.info("Starting ML model training...")
            
            # Prepare training data
            X, y = self._prepare_training_data(training_data)
            
            if X is None or y is None:
                self.logger.error("Failed to prepare training data")
                return
                
            # Convert to tensors
            X_tensor = torch.FloatTensor(X)
            y_tensor = torch.FloatTensor(y).unsqueeze(1)
            
            # Training parameters
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            # Training loop
            epochs = 100
            batch_size = 32
            
            self.model.train()
            for epoch in range(epochs):
                total_loss = 0
                for i in range(0, len(X_tensor), batch_size):
                    batch_X = X_tensor[i:i+batch_size]
                    batch_y = y_tensor[i:i+batch_size]
                    
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                    
                if epoch % 10 == 0:
                    self.logger.info(f"Epoch {epoch}, Loss: {total_loss/len(X_tensor):.6f}")
                    
            self.is_trained = True
            self.logger.info("ML model training completed")
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            
    def _prepare_training_data(self, data: pd.DataFrame) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare training data for ML model"""
        try:
            if len(data) < 200:
                return None, None
                
            # Create sequences
            sequence_length = 20
            features_list = []
            targets = []
            
            for i in range(sequence_length, len(data)):
                # Extract features for sequence
                sequence_data = data.iloc[i-sequence_length:i]
                features = self._prepare_ml_features(sequence_data)
                
                if features is not None:
                    features_list.append(features)
                    
                    # Target: next period return
                    next_return = data['close'].iloc[i+1] / data['close'].iloc[i] - 1 if i+1 < len(data) else 0
                    # Normalize target to [-1, 1]
                    target = np.tanh(next_return * 10)  # Scale and bound
                    targets.append(target)
                    
            if not features_list:
                return None, None
                
            X = np.array(features_list)
            y = np.array(targets)
            
            return X, y
            
        except Exception as e:
            self.logger.error(f"Error preparing training data: {e}")
            return None, None
            
    def create_crewai_task(self) -> Task:
        """Create CrewAI task for market analysis"""
        return Task(
            description="""Perform comprehensive market analysis for the provided trading symbols.
            
            Your task:
            1. Analyze technical indicators across multiple timeframes
            2. Generate ML-based predictions for each symbol
            3. Combine signals to produce high-confidence recommendations
            4. Calculate expected returns and volatility
            5. Rank opportunities by risk-adjusted potential
            
            For each symbol provide:
            - Signal type (buy/sell/hold)
            - Confidence level (0-100%)
            - Expected return
            - Volatility estimate
            - Key supporting indicators
            - Risk assessment
            
            Focus on high-probability setups with favorable risk/reward ratios.""",
            expected_output="Detailed market analysis report with specific trading signals and confidence levels for each symbol.",
            agent=self.create_crewai_agent()
        )
