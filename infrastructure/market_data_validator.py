"""
UOTA Elite v2 - Market Data Validation Layer
Validates data quality before it reaches the trading logic
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import numpy  # Moved to function to avoid circular import as np
# import pandas  # Moved to function to avoid circular import as pd
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
# import aiofiles  # Moved to function to avoid circular import

class DataQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"

class ValidationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class DataValidationResult:
    """Result of market data validation"""
    is_valid: bool
    quality_score: float  # 0-100
    quality_level: DataQuality
    validation_messages: List[str]
    anomalies_detected: List[str]
    should_pause_trading: bool
    timestamp: datetime

@dataclass
class MarketDataAnomaly:
    """Market data anomaly information"""
    timestamp: datetime
    symbol: str
    anomaly_type: str
    description: str
    severity: ValidationLevel
    data_point: Optional[Dict[str, Any]]
    threshold: Optional[float]

class MarketDataValidator:
    """Validates market data quality and integrity"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_history = []
        self.anomaly_history = []
        self.is_monitoring = False
        
        # Validation thresholds (configurable)
        self.thresholds = {
            'max_spread_multiplier': 3.0,      # Max spread vs average spread
            'max_price_spike_percent': 0.5,    # 0.5% max price spike
            'min_volume_threshold': 0.1,       # Minimum volume vs average
            'max_gap_candles': 2,              # Max consecutive missing candles
            'max_price_deviation': 0.02,       # 2% max price deviation
            'min_data_points': 50,             # Minimum data points for analysis
            'max_timestamp_gap': 300,          # 5 minutes max timestamp gap
            'spread_consistency_threshold': 0.3 # 30% spread variation allowed
        }
        
        # Symbol-specific configurations
        self.symbol_configs = {
            'XAUUSD': {
                'typical_spread': 0.5,          # $0.5 typical spread
                'max_price_spike': 1.0,         # 1% max spike for gold
                'volume_threshold': 0.05        # Lower volume threshold for gold
            },
            'EURUSD': {
                'typical_spread': 0.0002,       # 0.2 pips typical spread
                'max_price_spike': 0.3,         # 0.3% max spike
                'volume_threshold': 0.1          # Standard volume threshold
            },
            'GBPUSD': {
                'typical_spread': 0.0003,       # 0.3 pips typical spread
                'max_price_spike': 0.4,         # 0.4% max spike
                'volume_threshold': 0.1
            },
            'USDJPY': {
                'typical_spread': 0.02,         # 0.02 pips typical spread
                'max_price_spike': 0.3,         # 0.3% max spike
                'volume_threshold': 0.1
            }
        }
        
        # Historical data for comparison
        self.historical_data = {}
        self.spread_history = {}
        self.volume_history = {}
        
    async def validate_market_data(self, symbol: str, market_data: List[Dict]) -> DataValidationResult:
        """Validate market data before it reaches trading logic"""
        try:
            self.logger.debug(f"🔍 Validating market data for {symbol}")
            
            validation_messages = []
            anomalies_detected = []
            quality_score = 100.0
            should_pause_trading = False
            
            # Basic data validation
            if not market_data or len(market_data) < self.thresholds['min_data_points']:
                validation_messages.append(f"Insufficient data points: {len(market_data) if market_data else 0}")
                quality_score -= 50.0
                should_pause_trading = True
            
            # Convert to DataFrame for analysis
            try:
                df = pd.DataFrame(market_data)
                df.set_index('time', inplace=True)
                df.sort_index(inplace=True)
            except Exception as e:
                validation_messages.append(f"Data format error: {e}")
                quality_score -= 40.0
                should_pause_trading = True
                return self._create_validation_result(
                    False, quality_score, validation_messages, anomalies_detected, should_pause_trading
                )
            
            # Validate data completeness
            completeness_score, completeness_issues = await self._validate_data_completeness(symbol, df)
            quality_score -= (100 - completeness_score)
            validation_messages.extend(completeness_issues)
            
            # Validate price consistency
            price_score, price_issues = await self._validate_price_consistency(symbol, df)
            quality_score -= (100 - price_score)
            validation_messages.extend(price_issues)
            
            # Validate spreads
            spread_score, spread_issues = await self._validate_spreads(symbol, df)
            quality_score -= (100 - spread_score)
            validation_messages.extend(spread_issues)
            
            # Validate volume
            volume_score, volume_issues = await self._validate_volume(symbol, df)
            quality_score -= (100 - volume_score)
            validation_messages.extend(volume_issues)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(symbol, df)
            anomalies_detected.extend(anomalies)
            
            # Check for critical issues
            critical_issues = [msg for msg in validation_messages if 'Critical' in msg]
            if critical_issues:
                should_pause_trading = True
            
            # Determine quality level
            quality_level = self._determine_quality_level(quality_score)
            
            # Create result
            result = DataValidationResult(
                is_valid=quality_score >= 50.0 and not should_pause_trading,
                quality_score=max(0, quality_score),
                quality_level=quality_level,
                validation_messages=validation_messages,
                anomalies_detected=anomalies,
                should_pause_trading=should_pause_trading,
                timestamp=datetime.now()
            )
            
            # Log validation result
            await self._log_validation_result(symbol, result)
            
            # Store for historical comparison
            await self._update_historical_data(symbol, df)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error validating market data for {symbol}: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.CRITICAL,
                validation_messages=[f"Validation error: {e}"],
                anomalies_detected=[],
                should_pause_trading=True,
                timestamp=datetime.now()
            )
    
    async def _validate_data_completeness(self, symbol: str, df: pd.DataFrame) -> Tuple[float, List[str]]:
        """Validate data completeness and consistency"""
        try:
            score = 100.0
            issues = []
            
            # Check for missing data
            missing_data = df.isnull().sum()
            if missing_data.any():
                for column, count in missing_data.items():
                    if count > 0:
                        issues.append(f"Missing {count} values in {column}")
                        score -= 10.0
            
            # Check for duplicate timestamps
            duplicate_times = df.index.duplicated().sum()
            if duplicate_times > 0:
                issues.append(f"Found {duplicate_times} duplicate timestamps")
                score -= 15.0
            
            # Check timestamp gaps
            if len(df) > 1:
                time_diffs = df.index.to_series().diff().dropna()
                max_gap = time_diffs.max().total_seconds()
                
                if max_gap > self.thresholds['max_timestamp_gap']:
                    issues.append(f"Large timestamp gap detected: {max_gap/60:.1f} minutes")
                    score -= 20.0
            
            # Check for forward/backward time jumps
            if len(df) > 2:
                time_diffs = df.index.to_series().diff().dropna()
                negative_gaps = (time_diffs < timedelta(0)).sum()
                if negative_gaps > 0:
                    issues.append(f"Found {negative_gaps} backward time jumps")
                    score -= 25.0
            
            return max(0, score), issues
            
        except Exception as e:
            self.logger.error(f"❌ Error validating data completeness: {e}")
            return 0.0, [f"Completeness validation error: {e}"]
    
    async def _validate_price_consistency(self, symbol: str, df: pd.DataFrame) -> Tuple[float, List[str]]:
        """Validate price data consistency"""
        try:
            score = 100.0
            issues = []
            
            # Check for negative or zero prices
            for price_col in ['open', 'high', 'low', 'close']:
                if price_col in df.columns:
                    invalid_prices = (df[price_col] <= 0).sum()
                    if invalid_prices > 0:
                        issues.append(f"Found {invalid_prices} invalid {price_col} prices (<= 0)")
                        score -= 30.0
            
            # Check high/low consistency
            if all(col in df.columns for col in ['high', 'low', 'open', 'close']):
                # High should be >= all other prices
                high_violations = (df['high'] < df[['open', 'close']].max(axis=1)).sum()
                if high_violations > 0:
                    issues.append(f"Found {high_violations} high price violations")
                    score -= 20.0
                
                # Low should be <= all other prices
                low_violations = (df['low'] > df[['open', 'close']].min(axis=1)).sum()
                if low_violations > 0:
                    issues.append(f"Found {low_violations} low price violations")
                    score -= 20.0
            
            # Check for price spikes
            if 'close' in df.columns:
                price_changes = df['close'].pct_change().abs()
                symbol_config = self.symbol_configs.get(symbol, {'max_price_spike': 0.3})
                max_spike = symbol_config['max_price_spike'] / 100  # Convert to decimal
                
                spike_threshold = max(max_spike, self.thresholds['max_price_spike_percent'])
                price_spikes = (price_changes > spike_threshold).sum()
                
                if price_spikes > 0:
                    issues.append(f"Found {price_spikes} price spikes > {spike_threshold*100:.1f}%")
                    score -= 15.0
            
            # Check for price jumps between consecutive candles
            if len(df) > 1:
                price_jumps = (df['close'].diff().abs() / df['close'].shift(1)).max()
                if price_jumps > self.thresholds['max_price_deviation']:
                    issues.append(f"Large price jump detected: {price_jumps*100:.2f}%")
                    score -= 25.0
            
            return max(0, score), issues
            
        except Exception as e:
            self.logger.error(f"❌ Error validating price consistency: {e}")
            return 0.0, [f"Price consistency validation error: {e}"]
    
    async def _validate_spreads(self, symbol: str, df: pd.DataFrame) -> Tuple[float, List[str]]:
        """Validate spread data"""
        try:
            score = 100.0
            issues = []
            
            # Check if spread data exists
            if 'spread' not in df.columns:
                issues.append("No spread data available")
                return 50.0, issues
            
            # Check for negative spreads
            negative_spreads = (df['spread'] < 0).sum()
            if negative_spreads > 0:
                issues.append(f"Found {negative_spreads} negative spreads")
                score -= 40.0
            
            # Check for unusually large spreads
            symbol_config = self.symbol_configs.get(symbol, {'typical_spread': 0.0002})
            typical_spread = symbol_config['typical_spread']
            
            avg_spread = df['spread'].mean()
            max_allowed_spread = typical_spread * self.thresholds['max_spread_multiplier']
            
            if avg_spread > max_allowed_spread:
                issues.append(f"High average spread: {avg_spread:.4f} (typical: {typical_spread:.4f})")
                score -= 25.0
            
            # Check spread consistency
            spread_std = df['spread'].std()
            spread_cv = spread_std / avg_spread if avg_spread > 0 else 0
            
            if spread_cv > self.thresholds['spread_consistency_threshold']:
                issues.append(f"Inconsistent spreads (CV: {spread_cv:.2f})")
                score -= 20.0
            
            # Check for spread spikes
            spread_spikes = (df['spread'] > max_allowed_spread * 2).sum()
            if spread_spikes > 0:
                issues.append(f"Found {spread_spikes} spread spikes")
                score -= 15.0
            
            return max(0, score), issues
            
        except Exception as e:
            self.logger.error(f"❌ Error validating spreads: {e}")
            return 0.0, [f"Spread validation error: {e}"]
    
    async def _validate_volume(self, symbol: str, df: pd.DataFrame) -> Tuple[float, List[str]]:
        """Validate volume data"""
        try:
            score = 100.0
            issues = []
            
            # Check if volume data exists
            if 'tick_volume' not in df.columns:
                issues.append("No volume data available")
                return 80.0, issues  # Less critical than price/spread
            
            # Check for negative volumes
            negative_volumes = (df['tick_volume'] < 0).sum()
            if negative_volumes > 0:
                issues.append(f"Found {negative_volumes} negative volumes")
                score -= 30.0
            
            # Check for zero volumes (might indicate data issues)
            zero_volumes = (df['tick_volume'] == 0).sum()
            zero_volume_ratio = zero_volumes / len(df)
            
            if zero_volume_ratio > 0.1:  # More than 10% zero volumes
                issues.append(f"High zero volume ratio: {zero_volume_ratio:.1%}")
                score -= 20.0
            
            # Check volume consistency
            avg_volume = df['tick_volume'].mean()
            symbol_config = self.symbol_configs.get(symbol, {'volume_threshold': 0.1})
            volume_threshold = symbol_config['volume_threshold']
            
            # Compare with historical average if available
            if symbol in self.volume_history and len(self.volume_history[symbol]) > 10:
                hist_avg = np.mean(self.volume_history[symbol][-10:])
                volume_ratio = avg_volume / hist_avg if hist_avg > 0 else 1.0
                
                if volume_ratio < volume_threshold:
                    issues.append(f"Low volume: {avg_volume:.1f} (historical avg: {hist_avg:.1f})")
                    score -= 15.0
            
            return max(0, score), issues
            
        except Exception as e:
            self.logger.error(f"❌ Error validating volume: {e}")
            return 0.0, [f"Volume validation error: {e}"]
    
    async def _detect_anomalies(self, symbol: str, df: pd.DataFrame) -> List[str]:
        """Detect specific market data anomalies"""
        try:
            anomalies = []
            
            # Detect sudden price movements
            if 'close' in df.columns and len(df) > 1:
                price_changes = df['close'].pct_change().abs()
                
                # Find extreme price movements
                extreme_threshold = price_changes.quantile(0.99)
                extreme_movements = price_changes[price_changes > extreme_threshold]
                
                for timestamp, change in extreme_movements.items():
                    anomalies.append(f"Extreme price movement: {change*100:.2f}% at {timestamp}")
            
            # Detect spread anomalies
            if 'spread' in df.columns:
                spread_threshold = df['spread'].quantile(0.95)
                wide_spreads = df[df['spread'] > spread_threshold]
                
                for timestamp, spread in wide_spreads.iterrows():
                    anomalies.append(f"Wide spread: {spread['spread']:.4f} at {timestamp}")
            
            # Detect volume anomalies
            if 'tick_volume' in df.columns:
                volume_threshold = df['tick_volume'].quantile(0.95)
                high_volumes = df[df['tick_volume'] > volume_threshold]
                
                for timestamp, volume in high_volumes.iterrows():
                    anomalies.append(f"High volume: {volume['tick_volume']:.0f} at {timestamp}")
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting anomalies: {e}")
            return [f"Anomaly detection error: {e}"]
    
    def _determine_quality_level(self, score: float) -> DataQuality:
        """Determine data quality level based on score"""
        if score >= 90:
            return DataQuality.EXCELLENT
        elif score >= 75:
            return DataQuality.GOOD
        elif score >= 60:
            return DataQuality.ACCEPTABLE
        elif score >= 40:
            return DataQuality.POOR
        else:
            return DataQuality.CRITICAL
    
    def _create_validation_result(self, is_valid: bool, score: float, 
                                messages: List[str], anomalies: List[str], 
                                should_pause: bool) -> DataValidationResult:
        """Create validation result"""
        return DataValidationResult(
            is_valid=is_valid,
            quality_score=max(0, score),
            quality_level=self._determine_quality_level(score),
            validation_messages=messages,
            anomalies_detected=anomalies,
            should_pause_trading=should_pause,
            timestamp=datetime.now()
        )
    
    async def _log_validation_result(self, symbol: str, result: DataValidationResult):
        """Log validation result"""
        try:
            # Add to history
            self.validation_history.append((symbol, result))
            
            # Keep only last 1000 validations
            if len(self.validation_history) > 1000:
                self.validation_history = self.validation_history[-1000:]
            
            # Log to file
            log_entry = {
                'timestamp': result.timestamp.isoformat(),
                'symbol': symbol,
                'is_valid': result.is_valid,
                'quality_score': result.quality_score,
                'quality_level': result.quality_level.value,
                'should_pause_trading': result.should_pause_trading,
                'validation_messages': result.validation_messages,
                'anomalies_detected': result.anomalies_detected
            }
            
            os.makedirs('logs/validation', exist_ok=True)
            log_file = f"logs/validation/data_validation_{datetime.now().strftime('%Y-%m-%d')}.json"
            
            # Read existing logs
            existing_logs = []
            if os.path.exists(log_file):
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    if content:
                        existing_logs = json.loads(content)
            
            # Add new log
            existing_logs.append(log_entry)
            
            # Keep only last 24 hours
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
            existing_logs = [log for log in existing_logs if log['timestamp'] > cutoff_time]
            
            # Save logs
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(existing_logs, indent=2))
            
            # Log to console
            if result.should_pause_trading:
                self.logger.critical(f"🚨 CRITICAL: Trading should pause for {symbol} - Data quality: {result.quality_level.value}")
            elif not result.is_valid:
                self.logger.warning(f"⚠️ Invalid data for {symbol} - Quality: {result.quality_level.value}")
            else:
                self.logger.debug(f"✅ Valid data for {symbol} - Quality: {result.quality_level.value} ({result.quality_score:.1f})")
                
        except Exception as e:
            self.logger.error(f"❌ Error logging validation result: {e}")
    
    async def _update_historical_data(self, symbol: str, df: pd.DataFrame):
        """Update historical data for comparison"""
        try:
            # Update spread history
            if 'spread' in df.columns:
                if symbol not in self.spread_history:
                    self.spread_history[symbol] = []
                
                avg_spread = df['spread'].mean()
                self.spread_history[symbol].append(avg_spread)
                
                # Keep only last 100 values
                if len(self.spread_history[symbol]) > 100:
                    self.spread_history[symbol] = self.spread_history[symbol][-100:]
            
            # Update volume history
            if 'tick_volume' in df.columns:
                if symbol not in self.volume_history:
                    self.volume_history[symbol] = []
                
                avg_volume = df['tick_volume'].mean()
                self.volume_history[symbol].append(avg_volume)
                
                # Keep only last 100 values
                if len(self.volume_history[symbol]) > 100:
                    self.volume_history[symbol] = self.volume_history[symbol][-100:]
            
            # Store recent data for anomaly detection
            if symbol not in self.historical_data:
                self.historical_data[symbol] = []
            
            self.historical_data[symbol].append(df.tail(10))  # Keep last 10 candles
            
            # Keep only last 50 entries
            if len(self.historical_data[symbol]) > 50:
                self.historical_data[symbol] = self.historical_data[symbol][-50:]
                
        except Exception as e:
            self.logger.error(f"❌ Error updating historical data: {e}")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary for dashboard"""
        try:
            if not self.validation_history:
                return {'status': 'no_data', 'message': 'No validation history available'}
            
            # Calculate statistics for last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_validations = [
                (symbol, result) for symbol, result in self.validation_history 
                if result.timestamp > one_hour_ago
            ]
            
            if not recent_validations:
                return {'status': 'no_recent_data', 'message': 'No recent validations'}
            
            # Calculate metrics
            total_validations = len(recent_validations)
            valid_count = sum(1 for _, result in recent_validations if result.is_valid)
            pause_count = sum(1 for _, result in recent_validations if result.should_pause_trading)
            
            avg_quality_score = sum(result.quality_score for _, result in recent_validations) / total_validations
            
            # Quality level distribution
            quality_levels = {}
            for _, result in recent_validations:
                level = result.quality_level.value
                quality_levels[level] = quality_levels.get(level, 0) + 1
            
            return {
                'status': 'active',
                'period_hours': 1,
                'total_validations': total_validations,
                'valid_count': valid_count,
                'pause_count': pause_count,
                'validity_rate': valid_count / total_validations,
                'average_quality_score': avg_quality_score,
                'quality_distribution': quality_levels,
                'symbols_validated': list(set(symbol for symbol, _ in recent_validations)),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting validation summary: {e}")
            return {'error': str(e)}

# Global market data validator instance
market_data_validator = MarketDataValidator()
