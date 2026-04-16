"""
Crypto trade bot - Anti-Hallucination Grounding System
Multi-source verification and reality checking for AI decisions
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import hashlib  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
# import aiohttp  # Moved to function to avoid circular import
# import numpy  # Moved to function to avoid circular import as np
from collections import defaultdict

class VerificationLevel(Enum):
    """Verification confidence levels"""
    HIGH = "high"      # 3+ sources agree
    MEDIUM = "medium"  # 2 sources agree
    LOW = "low"        # 1 source or conflicting
    FAILED = "failed"  # No reliable data

@dataclass
class PriceData:
    """Price data from a source"""
    exchange: str
    symbol: str
    price: float
    timestamp: datetime
    volume: float
    spread: float
    confidence: float
    source_hash: str

@dataclass
class VerificationResult:
    """Result of multi-source verification"""
    symbol: str
    verified_price: float
    confidence_level: VerificationLevel
    sources_used: List[str]
    price_variance: float
    timestamp: datetime
    anomaly_detected: bool
    recommendation: str

@dataclass
class AIDecision:
    """AI decision to be verified"""
    decision_type: str  # 'buy', 'sell', 'hold', 'adjust_position'
    symbol: str
    confidence: float
    reasoning: str
    expected_outcome: str
    risk_score: float
    timestamp: datetime

@dataclass
class GroundedDecision:
    """Grounded and verified AI decision"""
    original_decision: AIDecision
    verification_result: VerificationResult
    final_decision: str
    adjusted_confidence: float
    grounding_factors: List[str]
    warnings: List[str]

class AntiHallucinationGrounding:
    """Advanced anti-hallucination and reality checking system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.price_sources: Dict[str, Dict] = {}
        self.verification_history: List[VerificationResult] = []
        self.decision_history: List[GroundedDecision] = []
        
        # Configuration
        self.min_sources = 2
        self.price_variance_threshold = 0.001  # 0.1%
        self.confidence_threshold = 0.7
        self.verification_timeout = 5.0  # seconds
        
        # Exchange endpoints for verification
        self.exchange_endpoints = {
            'binance': 'https://api.binance.com/api/v3/ticker/price',
            'bybit': 'https://api.bybit.com/v5/market/tickers',
            'okx': 'https://www.okx.com/api/v5/market/ticker',
            'coinbase': 'https://api.pro.coinbase.com/products'
        }
        
        # Data consistency tracking
        self.consistency_tracker = defaultdict(list)
        self.anomaly_detector = AnomalyDetector()
        
    async def initialize(self):
        """Initialize the grounding system"""
        try:
            await self.setup_price_sources()
            self.logger.info("Anti-hallucination grounding system initialized")
        except Exception as e:
            self.logger.error(f"Error initializing grounding system: {e}")
            
    async def setup_price_sources(self):
        """Setup multiple price sources for verification"""
        for exchange_name, endpoint in self.exchange_endpoints.items():
            self.price_sources[exchange_name] = {
                'endpoint': endpoint,
                'last_update': datetime.now(),
                'success_rate': 1.0,
                'avg_latency': 0.0,
                'active': True
            }
            
    async def verify_price_data(self, symbol: str) -> VerificationResult:
        """Verify price data across multiple exchanges"""
        try:
            self.logger.info(f"Verifying price data for {symbol}")
            
            # Collect price data from multiple sources
            price_data_points = await self.collect_price_data(symbol)
            
            if len(price_data_points) < self.min_sources:
                return VerificationResult(
                    symbol=symbol,
                    verified_price=0.0,
                    confidence_level=VerificationLevel.FAILED,
                    sources_used=[],
                    price_variance=0.0,
                    timestamp=datetime.now(),
                    anomaly_detected=True,
                    recommendation="INSUFFICIENT_DATA"
                )
                
            # Analyze price consistency
            prices = [point.price for point in price_data_points]
            verified_price = np.median(prices)
            price_variance = np.std(prices) / verified_price
            
            # Detect anomalies
            anomaly_detected = self.anomaly_detector.detect_price_anomaly(prices)
            
            # Determine confidence level
            confidence_level = self.calculate_confidence_level(price_data_points, price_variance)
            
            # Generate recommendation
            recommendation = self.generate_verification_recommendation(
                confidence_level, price_variance, anomaly_detected, len(price_data_points)
            )
            
            result = VerificationResult(
                symbol=symbol,
                verified_price=verified_price,
                confidence_level=confidence_level,
                sources_used=[point.exchange for point in price_data_points],
                price_variance=price_variance,
                timestamp=datetime.now(),
                anomaly_detected=anomaly_detected,
                recommendation=recommendation
            )
            
            self.verification_history.append(result)
            await self.update_source_reliability(price_data_points)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error verifying price data for {symbol}: {e}")
            return VerificationResult(
                symbol=symbol,
                verified_price=0.0,
                confidence_level=VerificationLevel.FAILED,
                sources_used=[],
                price_variance=0.0,
                timestamp=datetime.now(),
                anomaly_detected=True,
                recommendation=f"VERIFICATION_ERROR: {str(e)}"
            )
            
    async def collect_price_data(self, symbol: str) -> List[PriceData]:
        """Collect price data from multiple exchanges"""
        price_data_points = []
        tasks = []
        
        for exchange_name, config in self.price_sources.items():
            if config['active']:
                task = self.fetch_exchange_price(exchange_name, symbol)
                tasks.append(task)
                
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, PriceData):
                price_data_points.append(result)
            elif isinstance(result, Exception):
                self.logger.warning(f"Failed to fetch price: {result}")
                
        return price_data_points
        
    async def fetch_exchange_price(self, exchange: str, symbol: str) -> PriceData:
        """Fetch price from a specific exchange"""
        try:
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                # Adjust symbol format for different exchanges
                formatted_symbol = self.format_symbol_for_exchange(symbol, exchange)
                
                if exchange == 'binance':
                    url = f"{self.exchange_endpoints[exchange]}?symbol={formatted_symbol}"
                    async with session.get(url, timeout=self.verification_timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            price = float(data['price'])
                            return self.create_price_data_point(exchange, symbol, price, start_time)
                            
                elif exchange == 'bybit':
                    url = f"{self.exchange_endpoints[exchange]}?category=linear&symbol={formatted_symbol}"
                    async with session.get(url, timeout=self.verification_timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            for ticker in data.get('result', {}).get('list', []):
                                if ticker['symbol'] == formatted_symbol:
                                    price = float(ticker['lastPrice'])
                                    return self.create_price_data_point(exchange, symbol, price, start_time)
                                    
                elif exchange == 'okx':
                    url = f"{self.exchange_endpoints[exchange]}?instId={formatted_symbol}"
                    async with session.get(url, timeout=self.verification_timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            for ticker in data.get('data', []):
                                if ticker['instId'] == formatted_symbol:
                                    price = float(ticker['last'])
                                    return self.create_price_data_point(exchange, symbol, price, start_time)
                                    
            raise Exception(f"No data found for {symbol} on {exchange}")
            
        except Exception as e:
            self.logger.error(f"Error fetching price from {exchange}: {e}")
            # Update source reliability
            self.price_sources[exchange]['success_rate'] *= 0.9
            raise
            
    def format_symbol_for_exchange(self, symbol: str, exchange: str) -> str:
        """Format symbol for specific exchange"""
        if exchange == 'binance':
            return symbol.replace('/', '')
        elif exchange == 'bybit':
            return symbol.replace('/', '')
        elif exchange == 'okx':
            return symbol.replace('/', '-')
        else:
            return symbol
            
    def create_price_data_point(self, exchange: str, symbol: str, price: float, start_time: datetime) -> PriceData:
        """Create price data point with metadata"""
        timestamp = datetime.now()
        latency = (timestamp - start_time).total_seconds()
        
        # Calculate confidence based on latency and source reliability
        source_config = self.price_sources[exchange]
        reliability = source_config['success_rate']
        latency_score = max(0, 1 - latency / 1.0)  # 1 second latency threshold
        confidence = (reliability + latency_score) / 2
        
        # Generate source hash for tracking
        source_hash = hashlib.md5(f"{exchange}{symbol}{timestamp}".encode()).hexdigest()[:8]
        
        return PriceData(
            exchange=exchange,
            symbol=symbol,
            price=price,
            timestamp=timestamp,
            volume=0.0,  # Would need additional API call
            spread=0.0,  # Would need additional API call
            confidence=confidence,
            source_hash=source_hash
        )
        
    def calculate_confidence_level(self, price_data_points: List[PriceData], variance: float) -> VerificationLevel:
        """Calculate verification confidence level"""
        num_sources = len(price_data_points)
        
        if num_sources >= 3 and variance < self.price_variance_threshold:
            return VerificationLevel.HIGH
        elif num_sources >= 2 and variance < self.price_variance_threshold * 2:
            return VerificationLevel.MEDIUM
        elif num_sources >= 1:
            return VerificationLevel.LOW
        else:
            return VerificationLevel.FAILED
            
    def generate_verification_recommendation(self, confidence: VerificationLevel, variance: float, 
                                          anomaly: bool, num_sources: int) -> str:
        """Generate verification recommendation"""
        if confidence == VerificationLevel.HIGH:
            return "PROCEED_WITH_HIGH_CONFIDENCE"
        elif confidence == VerificationLevel.MEDIUM:
            return "PROCEED_WITH_CAUTION"
        elif anomaly:
            return "WAIT_FOR_STABILITY"
        elif variance > self.price_variance_threshold * 2:
            return "VERIFY_MANUALLY"
        else:
            return "INSUFFICIENT_DATA"
            
    async def ground_ai_decision(self, decision: AIDecision) -> GroundedDecision:
        """Ground AI decision with reality verification"""
        try:
            self.logger.info(f"Grounding AI decision: {decision.decision_type} for {decision.symbol}")
            
            # Verify price data
            verification = await self.verify_price_data(decision.symbol)
            
            # Cross-check decision logic
            grounding_factors = []
            warnings = []
            adjusted_confidence = decision.confidence
            
            # Check if verification supports the decision
            if verification.confidence_level == VerificationLevel.FAILED:
                warnings.append("Price verification failed - decision may be based on hallucinated data")
                adjusted_confidence *= 0.3
                
            elif verification.anomaly_detected:
                warnings.append("Price anomaly detected - market conditions unusual")
                adjusted_confidence *= 0.7
                
            elif verification.price_variance > self.price_variance_threshold:
                warnings.append(f"High price variance ({verification.price_variance:.3%}) - data inconsistency")
                adjusted_confidence *= 0.8
                
            # Check decision consistency with historical patterns
            consistency_score = self.check_decision_consistency(decision)
            if consistency_score < 0.5:
                warnings.append("Decision inconsistent with historical patterns")
                adjusted_confidence *= 0.6
            else:
                grounding_factors.append(f"Consistent with {consistency_score:.1%} of historical decisions")
                
            # Final decision based on grounded confidence
            if adjusted_confidence >= self.confidence_threshold and verification.confidence_level != VerificationLevel.FAILED:
                final_decision = decision.decision_type
                grounding_factors.append("Verification passed confidence threshold")
            else:
                final_decision = "HOLD"
                grounding_factors.append("Decision grounded due to insufficient verification")
                
            grounded_decision = GroundedDecision(
                original_decision=decision,
                verification_result=verification,
                final_decision=final_decision,
                adjusted_confidence=adjusted_confidence,
                grounding_factors=grounding_factors,
                warnings=warnings
            )
            
            self.decision_history.append(grounded_decision)
            
            self.logger.info(f"Decision grounded: {decision.decision_type} -> {final_decision} (confidence: {adjusted_confidence:.2f})")
            
            return grounded_decision
            
        except Exception as e:
            self.logger.error(f"Error grounding AI decision: {e}")
            return GroundedDecision(
                original_decision=decision,
                verification_result=VerificationResult(
                    symbol=decision.symbol,
                    verified_price=0.0,
                    confidence_level=VerificationLevel.FAILED,
                    sources_used=[],
                    price_variance=0.0,
                    timestamp=datetime.now(),
                    anomaly_detected=True,
                    recommendation="GROUNDING_ERROR"
                ),
                final_decision="HOLD",
                adjusted_confidence=0.0,
                grounding_factors=[],
                warnings=[f"Grounding failed: {str(e)}"]
            )
            
    def check_decision_consistency(self, decision: AIDecision) -> float:
        """Check decision consistency with historical patterns"""
        try:
            # Find similar historical decisions
            similar_decisions = [
                d for d in self.decision_history 
                if d.original_decision.symbol == decision.symbol and 
                d.original_decision.decision_type == decision.decision_type
            ]
            
            if not similar_decisions:
                return 0.5  # No historical data
                
            # Calculate consistency based on successful outcomes
            successful_decisions = [
                d for d in similar_decisions 
                if d.adjusted_confidence > self.confidence_threshold
            ]
            
            consistency = len(successful_decisions) / len(similar_decisions)
            return consistency
            
        except Exception as e:
            self.logger.error(f"Error checking decision consistency: {e}")
            return 0.5
            
    async def update_source_reliability(self, price_data_points: List[PriceData]):
        """Update source reliability metrics"""
        for point in price_data_points:
            exchange = point.exchange
            if exchange in self.price_sources:
                config = self.price_sources[exchange]
                
                # Update success rate
                config['success_rate'] = min(1.0, config['success_rate'] * 1.01)  # Gradual improvement
                
                # Update latency (simplified)
                config['avg_latency'] = (config['avg_latency'] + 0.1) / 2  # Moving average
                
    async def get_grounding_report(self) -> Dict[str, Any]:
        """Generate comprehensive grounding report"""
        try:
            recent_verifications = [
                v for v in self.verification_history 
                if v.timestamp > datetime.now() - timedelta(hours=1)
            ]
            
            recent_decisions = [
                d for d in self.decision_history 
                if d.original_decision.timestamp > datetime.now() - timedelta(hours=1)
            ]
            
            verification_success_rate = len([v for v in recent_verifications if v.confidence_level != VerificationLevel.FAILED]) / len(recent_verifications) if recent_verifications else 0
            
            grounding_effectiveness = len([d for d in recent_decisions if d.adjusted_confidence > 0.5]) / len(recent_decisions) if recent_decisions else 0
            
            return {
                'timestamp': datetime.now(),
                'active_sources': len([s for s in self.price_sources.values() if s['active']]),
                'verification_success_rate': verification_success_rate,
                'grounding_effectiveness': grounding_effectiveness,
                'recent_verifications': len(recent_verifications),
                'recent_decisions': len(recent_decisions),
                'average_confidence': np.mean([d.adjusted_confidence for d in recent_decisions]) if recent_decisions else 0,
                'warnings_issued': sum(len(d.warnings) for d in recent_decisions)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating grounding report: {e}")
            return {}

class AnomalyDetector:
    """Simple anomaly detection for price data"""
    
    def __init__(self):
        self.price_history = defaultdict(list)
        
    def detect_price_anomaly(self, prices: List[float]) -> bool:
        """Detect if prices contain anomalies"""
        if len(prices) < 3:
            return False
            
        # Calculate z-scores
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if std_price == 0:
            return False
            
        z_scores = [(price - mean_price) / std_price for price in prices]
        
        # Check for outliers (z-score > 2)
        outliers = [z for z in z_scores if abs(z) > 2]
        
        return len(outliers) > 0

# Global instance
anti_hallucination = AntiHallucinationGrounding()
