"""
Crypto trade bot - Self-Correction Layer
Automated learning from trading mistakes and performance optimization
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import numpy  # Moved to function to avoid circular import as np
# import pandas  # Moved to function to avoid circular import as pd
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
# import pickle  # Moved to function to avoid circular import
from pathlib import Path

@dataclass
class TradeMistake:
    """Record of a trading mistake for learning"""
    timestamp: datetime
    symbol: str
    mistake_type: str  # 'bad_entry', 'bad_exit', 'risk_violation', 'timing_error'
    pnl: float
    decision_factors: Dict[str, float]
    market_conditions: Dict[str, str]
    should_have_actioned: str
    confidence_before: float
    confidence_after: float
    lesson_learned: str

@dataclass
class OptimizationSuggestion:
    """AI-generated optimization suggestion"""
    component: str  # 'risk_params', 'entry_criteria', 'exit_strategy', 'timing'
    current_value: Any
    suggested_value: Any
    expected_improvement: float
    confidence: float
    reasoning: str
    implementation_priority: str  # 'high', 'medium', 'low'

class SelfCorrectionLayer:
    """Advanced self-learning and optimization system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mistakes: List[TradeMistake] = []
        self.suggestions: List[OptimizationSuggestion] = []
        self.performance_history: List[Dict] = []
        
        # ML models for pattern recognition
        self.mistake_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Learning parameters
        self.learning_rate = 0.01
        self.min_mistakes_for_learning = 10
        self.optimization_threshold = 0.05  # 5% improvement threshold
        
        # Storage paths
        self.mistakes_file = Path("data/mistakes.json")
        self.model_file = Path("data/self_correction_model.pkl")
        self.suggestions_file = Path("data/suggestions.json")
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize the self-correction system"""
        try:
            await self.load_historical_data()
            await self.train_models()
            self.logger.info("Self-correction layer initialized")
        except Exception as e:
            self.logger.error(f"Error initializing self-correction: {e}")
            
    async def analyze_trade_mistake(self, trade_data: Dict) -> Optional[TradeMistake]:
        """Analyze a completed trade for potential mistakes"""
        try:
            pnl = trade_data.get('pnl', 0)
            symbol = trade_data.get('symbol', '')
            
            # Only analyze losing trades or trades with poor risk/reward
            if pnl >= 0 and trade_data.get('risk_reward_ratio', 0) > 2.0:
                return None
                
            mistake_type = self._classify_mistake_type(trade_data)
            
            # Extract decision factors
            decision_factors = {
                'rsi_at_entry': trade_data.get('rsi', 50),
                'volume_spike': trade_data.get('volume_ratio', 1.0),
                'volatility': trade_data.get('volatility', 0.02),
                'sentiment_score': trade_data.get('sentiment', 0.0),
                'time_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday()
            }
            
            # Market conditions
            market_conditions = {
                'trend': trade_data.get('trend', 'sideways'),
                'volatility_regime': trade_data.get('volatility_regime', 'normal'),
                'session': trade_data.get('session', 'neutral')
            }
            
            # Determine what should have been done
            should_have_actioned = self._determine_optimal_action(trade_data, mistake_type)
            
            # Generate lesson learned
            lesson_learned = self._generate_lesson(trade_data, mistake_type)
            
            mistake = TradeMistake(
                timestamp=datetime.now(),
                symbol=symbol,
                mistake_type=mistake_type,
                pnl=pnl,
                decision_factors=decision_factors,
                market_conditions=market_conditions,
                should_have_actioned=should_have_actioned,
                confidence_before=trade_data.get('confidence', 0.5),
                confidence_after=max(0.1, trade_data.get('confidence', 0.5) - 0.2),
                lesson_learned=lesson_learned
            )
            
            self.mistakes.append(mistake)
            await self.save_mistakes()
            
            # Trigger retraining if enough mistakes collected
            if len(self.mistakes) >= self.min_mistakes_for_learning:
                await self.train_models()
                await self.generate_optimization_suggestions()
                
            return mistake
            
        except Exception as e:
            self.logger.error(f"Error analyzing trade mistake: {e}")
            return None
            
    def _classify_mistake_type(self, trade_data: Dict) -> str:
        """Classify the type of mistake made"""
        pnl = trade_data.get('pnl', 0)
        entry_price = trade_data.get('entry_price', 0)
        exit_price = trade_data.get('exit_price', 0)
        max_profit = trade_data.get('max_profit', 0)
        max_loss = trade_data.get('max_loss', 0)
        
        # Bad entry - went negative immediately
        if max_loss > abs(pnl) * 2:
            return 'bad_entry'
            
        # Bad exit - had good profit but ended with loss
        elif max_profit > abs(pnl) * 3 and pnl < 0:
            return 'bad_exit'
            
        # Risk violation - position too large or stop too wide
        elif trade_data.get('risk_percent', 0) > 0.02:
            return 'risk_violation'
            
        # Timing error - right direction but wrong timing
        else:
            return 'timing_error'
            
    def _determine_optimal_action(self, trade_data: Dict, mistake_type: str) -> str:
        """Determine what should have been done differently"""
        if mistake_type == 'bad_entry':
            return 'WAIT_FOR_BETTER_SETUP'
        elif mistake_type == 'bad_exit':
            return 'TAKE_PROFIT_EARLIER'
        elif mistake_type == 'risk_violation':
            return 'REDUCE_POSITION_SIZE'
        else:
            return 'IMPROVE_TIMING'
            
    def _generate_lesson(self, trade_data: Dict, mistake_type: str) -> str:
        """Generate a lesson learned from the mistake"""
        lessons = {
            'bad_entry': f"Entry was premature. RSI was {trade_data.get('rsi', 50):.1f} and volume ratio was {trade_data.get('volume_ratio', 1.0):.1f}. Wait for stronger confirmation.",
            'bad_exit': f"Exit was too late. Max profit was {trade_data.get('max_profit', 0):.2f} but final P&L was {trade_data.get('pnl', 0):.2f}. Implement tighter profit taking.",
            'risk_violation': f"Risk was {trade_data.get('risk_percent', 0):.2%} - exceeds 1% limit. Always respect position sizing rules.",
            'timing_error': f"Direction was correct but timing was off. Consider waiting for pullback or breakout confirmation."
        }
        return lessons.get(mistake_type, "Review trade execution criteria.")
        
    async def train_models(self):
        """Train ML models on collected mistakes"""
        try:
            if len(self.mistakes) < self.min_mistakes_for_learning:
                return
                
            # Prepare training data
            X = []
            y = []
            
            for mistake in self.mistakes:
                features = [
                    mistake.decision_factors.get('rsi_at_entry', 50),
                    mistake.decision_factors.get('volume_spike', 1.0),
                    mistake.decision_factors.get('volatility', 0.02),
                    mistake.decision_factors.get('sentiment_score', 0.0),
                    mistake.decision_factors.get('time_of_day', 12),
                    mistake.decision_factors.get('day_of_week', 3)
                ]
                X.append(features)
                y.append(mistake.mistake_type)
                
            # Train classifier
            X_scaled = self.scaler.fit_transform(X)
            self.mistake_classifier.fit(X_scaled, y)
            self.is_trained = True
            
            # Save model
            with open(self.model_file, 'wb') as f:
                pickle.dump({
                    'classifier': self.mistake_classifier,
                    'scaler': self.scaler
                }, f)
                
            self.logger.info(f"Self-correction model trained on {len(self.mistakes)} mistakes")
            
        except Exception as e:
            self.logger.error(f"Error training models: {e}")
            
    async def generate_optimization_suggestions(self):
        """Generate optimization suggestions based on learned patterns"""
        try:
            if not self.is_trained:
                return
                
            # Analyze mistake patterns
            mistake_patterns = self._analyze_mistake_patterns()
            
            # Generate suggestions for each pattern
            for pattern, frequency in mistake_patterns.items():
                if frequency > 0.3:  # 30% or more of mistakes
                    suggestion = self._create_suggestion_for_pattern(pattern, frequency)
                    if suggestion:
                        self.suggestions.append(suggestion)
                        
            # Sort by priority
            self.suggestions.sort(key=lambda x: x.confidence * x.expected_improvement, reverse=True)
            
            # Save suggestions
            await self.save_suggestions()
            
            self.logger.info(f"Generated {len(self.suggestions)} optimization suggestions")
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            
    def _analyze_mistake_patterns(self) -> Dict[str, float]:
        """Analyze patterns in mistakes"""
        patterns = {}
        total_mistakes = len(self.mistakes)
        
        # Count by mistake type
        for mistake in self.mistakes:
            patterns[mistake.mistake_type] = patterns.get(mistake.mistake_type, 0) + 1
            
        # Convert to percentages
        for key in patterns:
            patterns[key] = patterns[key] / total_mistakes
            
        return patterns
        
    def _create_suggestion_for_pattern(self, pattern: str, frequency: float) -> Optional[OptimizationSuggestion]:
        """Create optimization suggestion for a mistake pattern"""
        suggestions = {
            'bad_entry': OptimizationSuggestion(
                component='entry_criteria',
                current_value='RSI > 30',
                suggested_value='RSI > 40 AND Volume > 1.5x average',
                expected_improvement=0.15,
                confidence=frequency,
                reasoning=f"Bad entries account for {frequency:.1%} of mistakes. Stricter entry criteria needed.",
                implementation_priority='high'
            ),
            'bad_exit': OptimizationSuggestion(
                component='exit_strategy',
                current_value='Fixed TP at 2R',
                suggested_value='Trailing stop after 1R with partial exits',
                expected_improvement=0.20,
                confidence=frequency,
                reasoning=f"Poor exits account for {frequency:.1%} of mistakes. Better profit taking needed.",
                implementation_priority='high'
            ),
            'risk_violation': OptimizationSuggestion(
                component='risk_params',
                current_value='1% max risk',
                suggested_value='0.5% max risk with dynamic sizing',
                expected_improvement=0.10,
                confidence=frequency,
                reasoning=f"Risk violations in {frequency:.1%} of cases. More conservative sizing needed.",
                implementation_priority='medium'
            ),
            'timing_error': OptimizationSuggestion(
                component='timing',
                current_value='Immediate execution',
                suggested_value='Wait for confirmation candle',
                expected_improvement=0.12,
                confidence=frequency,
                reasoning=f"Timing errors in {frequency:.1%} of cases. Better entry timing needed.",
                implementation_priority='medium'
            )
        }
        
        return suggestions.get(pattern)
        
    async def predict_mistake_probability(self, trade_setup: Dict) -> float:
        """Predict probability of mistake for a given trade setup"""
        try:
            if not self.is_trained:
                return 0.0
                
            features = [
                trade_setup.get('rsi', 50),
                trade_setup.get('volume_ratio', 1.0),
                trade_setup.get('volatility', 0.02),
                trade_setup.get('sentiment', 0.0),
                datetime.now().hour,
                datetime.now().weekday()
            ]
            
            X_scaled = self.scaler.transform([features])
            probabilities = self.mistake_classifier.predict_proba(X_scaled)
            
            # Return maximum probability of any mistake type
            return np.max(probabilities)
            
        except Exception as e:
            self.logger.error(f"Error predicting mistake probability: {e}")
            return 0.5  # Default to medium risk
            
    async def get_top_suggestions(self, limit: int = 5) -> List[OptimizationSuggestion]:
        """Get top optimization suggestions"""
        return self.suggestions[:limit]
        
    async def save_mistakes(self):
        """Save mistakes to file"""
        try:
            mistakes_data = [asdict(mistake) for mistake in self.mistakes]
            with open(self.mistakes_file, 'w') as f:
                json.dump(mistakes_data, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving mistakes: {e}")
            
    async def save_suggestions(self):
        """Save suggestions to file"""
        try:
            suggestions_data = [asdict(suggestion) for suggestion in self.suggestions]
            with open(self.suggestions_file, 'w') as f:
                json.dump(suggestions_data, f, default=str, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving suggestions: {e}")
            
    async def load_historical_data(self):
        """Load historical mistakes and suggestions"""
        try:
            # Load mistakes
            if self.mistakes_file.exists():
                with open(self.mistakes_file, 'r') as f:
                    mistakes_data = json.load(f)
                    self.mistakes = [
                        TradeMistake(**mistake) for mistake in mistakes_data
                    ]
                    
            # Load suggestions
            if self.suggestions_file.exists():
                with open(self.suggestions_file, 'r') as f:
                    suggestions_data = json.load(f)
                    self.suggestions = [
                        OptimizationSuggestion(**suggestion) for suggestion in suggestions_data
                    ]
                    
            # Load model
            if self.model_file.exists():
                with open(self.model_file, 'rb') as f:
                    model_data = pickle.load(f)
                    self.mistake_classifier = model_data['classifier']
                    self.scaler = model_data['scaler']
                    self.is_trained = True
                    
            self.logger.info(f"Loaded {len(self.mistakes)} historical mistakes and {len(self.suggestions)} suggestions")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {e}")

# Global instance
self_correction_layer = SelfCorrectionLayer()
