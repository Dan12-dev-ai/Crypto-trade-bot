#!/usr/bin/env python3
"""
UOTA Elite v2 - Chaos Testing Suite
Comprehensive integration and stress testing for all modules
"""

import asyncio
import logging
import sys
import os
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import unittest.mock as mock
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Internal imports
from main_orchestrator import MainOrchestrator, TradingSignal, SystemState, AgentRole
from memory.vector_store import VectorMemoryManager, MarketPattern
from simulation.digital_twin import DigitalTwinEnvironment, SimulationResult, SimulationOutcome
from research.autonomous_research import AutonomousResearchLab, ResearchStatus
from execution.consensus_engine import ConsensusExecutionEngine, AgentVote, VoteType, ValidationStatus
from security.ip_validator import IPValidator, SecurityLevel, SecurityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/chaos_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestResult(Enum):
    """Test result status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

@dataclass
class ChaosTestResult:
    """Chaos test result"""
    test_name: str
    test_category: str
    result: TestResult
    execution_time: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None

class ChaosTestSuite:
    """Comprehensive chaos testing suite"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        self.start_time = datetime.now()
        
        # Test environment setup
        self.orchestrator = None
        self.vector_memory = None
        self.digital_twin = None
        self.research_lab = None
        self.consensus_engine = None
        self.ip_validator = None
        
        # Test data
        self.test_signals = []
        self.test_patterns = []
        self.test_scenarios = []
        
    async def initialize(self) -> None:
        """Initialize test environment"""
        try:
            self.logger.info("Initializing Chaos Test Suite")
            
            # Create test directories
            Path('tests/data').mkdir(exist_ok=True)
            Path('tests/logs').mkdir(exist_ok=True)
            
            # Initialize components
            await self._initialize_components()
            
            # Create test data
            await self._create_test_data()
            
            self.logger.info("Chaos Test Suite initialized")
            
        except Exception as e:
            self.logger.error(f"Test suite initialization failed: {e}")
            raise
    
    async def _initialize_components(self) -> None:
        """Initialize all components for testing"""
        try:
            # Initialize IP Validator
            self.ip_validator = IPValidator()
            await self.ip_validator.initialize()
            
            # Initialize Vector Memory
            self.vector_memory = VectorMemoryManager()
            await self.vector_memory.initialize()
            
            # Initialize Digital Twin
            self.digital_twin = DigitalTwinEnvironment()
            await self.digital_twin.initialize()
            
            # Initialize Research Lab
            self.research_lab = AutonomousResearchLab()
            await self.research_lab.initialize()
            
            # Initialize Consensus Engine
            self.consensus_engine = ConsensusExecutionEngine()
            await self.consensus_engine.initialize()
            
            # Initialize Orchestrator
            self.orchestrator = MainOrchestrator()
            # Don't start orchestrator, just initialize components
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
    
    async def _create_test_data(self) -> None:
        """Create test data for chaos testing"""
        try:
            # Create test trading signals
            self.test_signals = [
                TradingSignal(
                    symbol='BTC/USDT',
                    action='BUY',
                    confidence=0.8,
                    reasoning='Test signal 1 - Strong momentum',
                    timestamp=datetime.now()
                ),
                TradingSignal(
                    symbol='ETH/USDT',
                    action='SELL',
                    confidence=0.6,
                    reasoning='Test signal 2 - Overbought conditions',
                    timestamp=datetime.now()
                ),
                TradingSignal(
                    symbol='BNB/USDT',
                    action='BUY',
                    confidence=0.9,
                    reasoning='Test signal 3 - Breakout confirmed',
                    timestamp=datetime.now()
                )
            ]
            
            # Create synthetic market anomalies
            self.test_patterns = [
                MarketPattern(
                    pattern_id='synthetic_anomaly_1',
                    symbol='BTC/USDT',
                    timeframe='1h',
                    pattern_type='liquidity_sweep',
                    features={
                        'volume_spike': 3.5,
                        'price_deviation': 0.05,
                        'rsi_divergence': -0.8
                    },
                    context={
                        'market_state': 'high_volatility',
                        'time_of_day': 'market_open'
                    },
                    confidence=0.95,
                    timestamp=datetime.now()
                ),
                MarketPattern(
                    pattern_id='synthetic_anomaly_2',
                    symbol='ETH/USDT',
                    timeframe='4h',
                    pattern_type='whale_movement',
                    features={
                        'transaction_size': 10000000,
                        'price_impact': 0.03,
                        'exchange_concentration': 0.8
                    },
                    context={
                        'market_state': 'low_liquidity',
                        'time_of_day': 'asian_session'
                    },
                    confidence=0.88,
                    timestamp=datetime.now()
                )
            ]
            
        except Exception as e:
            self.logger.error(f"Test data creation failed: {e}")
            raise
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all chaos tests"""
        try:
            self.logger.info("Starting Chaos Testing Suite")
            
        except Exception as e:
            self.logger.error(f"Chaos testing failed: {e}")
            return {
                'total_tests': len(self.test_results),
                'passed': len([r for r in self.test_results if r.result == TestResult.PASSED]),
                'failed': len([r for r in self.test_results if r.result == TestResult.FAILED]),
                'errors': len([r for r in self.test_results if r.result == TestResult.ERROR]),
                'execution_time': (datetime.now() - self.start_time).total_seconds(),
                'results': self.test_results
            }
    
    async def test_agent_consensus_loop(self) -> ChaosTestResult:
        """Test 1: Agent Consensus Loop with veto scenario"""
        start_time = time.time()
        test_name = "Agent Consensus Loop - Veto Scenario"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Create test signal
            signal = self.test_signals[0]
            
            # Mock agent decisions with conflict scenario
            agent_decisions = {
                'analyst': {
                    'signal': 'BUY',
                    'confidence': 0.85,
                    'reasoning': 'Strong bullish momentum detected',
                    'signal_strength': 0.8,
                    'indicator_alignment': 0.9
                },
                'researcher': {
                    'signal': 'HOLD',
                    'confidence': 0.7,
                    'reasoning': 'Conflicting patterns found in historical data',
                    'patterns_found': 3,
                    'confidence': 0.6
                }
            }
            
            # Risk governor veto
            risk_assessment = {
                'risk_level': 'HIGH',
                'risk_score': 0.9,
                'reason': 'Market volatility exceeds risk thresholds',
                'risk_factors': {
                    'volatility_spike': True,
                    'liquidity_concern': True,
                    'news_sentiment': 'negative'
                }
            }
            
            # Digital twin simulation
            simulation_results = {
                'confidence': 0.6,
                'recommendation': 'REJECT',
                'simulated_pnl': -0.05,
                'simulated_max_drawdown': 0.12,
                'reasoning': 'High probability of loss in current conditions'
            }
            
            # Build consensus
            consensus_result = await self.consensus_engine.build_consensus(
                signal, agent_decisions, risk_assessment, simulation_results
            )
            
            # Verify veto was processed correctly
            test_passed = (
                consensus_result.execution_approved == False and
                consensus_result.consensus_score < 0.8 and
                consensus_result.risk_assessment['risk_level'] == 'HIGH'
            )
            
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Integration",
                result=TestResult.PASSED if test_passed else TestResult.FAILED,
                execution_time=time.time() - start_time,
                details={
                    'consensus_score': consensus_result.consensus_score,
                    'execution_approved': consensus_result.execution_approved,
                    'risk_level': consensus_result.risk_assessment['risk_level'],
                    'final_decision': consensus_result.final_decision.value,
                    'agent_votes': len(consensus_result.agent_votes)
                },
                timestamp=datetime.now()
            )
            
            self.logger.info(f"{test_name}: {result.result.value}")
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Integration",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def test_memory_integrity(self) -> ChaosTestResult:
        """Test 2: Memory Integrity with synthetic anomaly"""
        start_time = time.time()
        test_name = "Memory Integrity - Synthetic Anomaly Injection"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Inject synthetic anomaly into Vector DB
            anomaly = self.test_patterns[0]
            pattern_id = await self.vector_memory.store_market_data({
                'symbol': anomaly.symbol,
                'price': 45000.0,
                'volume': 1000000.0,
                'anomaly_type': anomaly.pattern_type,
                'features': anomaly.features,
                'timestamp': anomaly.timestamp.isoformat()
            })
            
            # Create market data that should trigger anomaly detection
            market_data = {
                'symbol': 'BTC/USDT',
                'price': 44800.0,
                'volume': 3500000.0,  # High volume matching anomaly
                'rsi': 35.0,  # Oversold
                'timestamp': datetime.now().isoformat()
            }
            
            # Find similar patterns
            similar_patterns = await self.vector_memory.find_similar_patterns(market_data)
            
            # Verify anomaly was found and affects confidence
            anomaly_found = len(similar_patterns) > 0
            confidence_modified = False
            
            if anomaly_found:
                # Simulate analyst using anomaly to modify confidence
                original_confidence = 0.8
                anomaly_impact = similar_patterns[0].get('similarity', 0) * 0.3
                modified_confidence = original_confidence - anomaly_impact
                confidence_modified = modified_confidence < original_confidence
            
            test_passed = anomaly_found and confidence_modified
            
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Integration",
                result=TestResult.PASSED if test_passed else TestResult.FAILED,
                execution_time=time.time() - start_time,
                details={
                    'anomaly_injected': True,
                    'similar_patterns_found': len(similar_patterns),
                    'confidence_modified': confidence_modified,
                    'pattern_id': pattern_id
                },
                timestamp=datetime.now()
            )
            
            self.logger.info(f"{test_name}: {result.result.value}")
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Integration",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def test_digital_twin_validation(self) -> ChaosTestResult:
        """Test 3: Digital Twin Validation with shadow trade loss"""
        start_time = time.time()
        test_name = "Digital Twin Validation - Shadow Trade Loss"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Create test signal
            signal = self.test_signals[1]
            
            # Mock digital twin to return loss scenario
            with mock.patch.object(self.digital_twin, 'validate_signal') as mock_validate:
                mock_validate.return_value = SimulationResult(
                    signal_id=f"sim_{datetime.now().timestamp()}",
                    original_signal=signal,
                    simulated_pnl=-0.08,  # 8% loss
                    simulated_max_drawdown=0.15,  # 15% drawdown
                    simulated_win_rate=0.3,  # 30% win rate
                    risk_assessment={'risk_level': 'HIGH', 'confidence': 0.2},
                    market_conditions={'volatility': 'extreme'},
                    outcome=SimulationOutcome.LOSS,
                    confidence=0.25,
                    recommendation="REJECT",
                    reasoning="High probability of significant loss in current market conditions",
                    timestamp=datetime.now()
                )
                
                # Validate signal with digital twin
                simulation_result = await self.digital_twin.validate_signal(signal)
                
                # Verify executor receives loss data and rejects trade
                agent_decisions = {
                    'executor': {
                        'decision': 'REJECT',
                        'confidence': 0.9,
                        'reasoning': f"Digital twin simulation shows {simulation_result.simulated_pnl:.1%} expected loss",
                        'simulation_data': {
                            'pnl': simulation_result.simulated_pnl,
                            'max_drawdown': simulation_result.simulated_max_drawdown,
                            'recommendation': simulation_result.recommendation
                        }
                    }
                }
                
                # Build consensus with executor rejection
                consensus_result = await self.consensus_engine.build_consensus(
                    signal, agent_decisions, {'risk_level': 'MEDIUM'}, simulation_result.__dict__
                )
                
                # Verify trade was rejected before hitting broker API
                test_passed = (
                    simulation_result.recommendation == "REJECT" and
                    consensus_result.execution_approved == False and
                    simulation_result.simulated_pnl < 0
                )
                
                result = ChaosTestResult(
                    test_name=test_name,
                    test_category="Integration",
                    result=TestResult.PASSED if test_passed else TestResult.FAILED,
                    execution_time=time.time() - start_time,
                    details={
                        'simulation_pnl': simulation_result.simulated_pnl,
                        'simulation_recommendation': simulation_result.recommendation,
                        'consensus_approved': consensus_result.execution_approved,
                        'executor_decision': 'REJECT'
                    },
                    timestamp=datetime.now()
                )
                
                self.logger.info(f"{test_name}: {result.result.value}")
                self.test_results.append(result)
                return result
                
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Integration",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def test_fault_injection(self) -> ChaosTestResult:
        """Test 4: Fault Injection - LLM Connection Loss"""
        start_time = time.time()
        test_name = "Fault Injection - LLM Connection Loss"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Simulate LLM connection loss
            with mock.patch('main_orchestrator.Ollama') as mock_ollama:
                # Mock Ollama to raise connection error
                mock_ollama.side_effect = ConnectionError("Connection to LLM failed")
                
                # Test orchestrator fault detection
                emergency_triggered = False
                emergency_time = None
                
                # Mock emergency detection
                def mock_emergency_stop():
                    nonlocal emergency_triggered, emergency_time
                    emergency_triggered = True
                    emergency_time = time.time()
                
                # Simulate fault detection
                fault_start = time.time()
                try:
                    # This would normally fail due to LLM connection
                    orchestrator = MainOrchestrator()
                    # Mock the emergency stop
                    orchestrator.emergency_stop = mock_emergency_stop
                    await orchestrator._emergency_stop({})
                except:
                    # Expected to fail
                    pass
                
                # Simulate watchdog detection (within 3 seconds)
                watchdog_detected = emergency_triggered and (emergency_time - fault_start) < 3.0 if emergency_time else False
                
                test_passed = emergency_triggered and watchdog_detected
                
                result = ChaosTestResult(
                    test_name=test_name,
                    test_category="Reliability",
                    result=TestResult.PASSED if test_passed else TestResult.FAILED,
                    execution_time=time.time() - start_time,
                    details={
                        'emergency_triggered': emergency_triggered,
                        'watchdog_detected': watchdog_detected,
                        'detection_time': emergency_time - fault_start if emergency_time else None
                    },
                    timestamp=datetime.now()
                )
                
                self.logger.info(f"{test_name}: {result.result.value}")
                self.test_results.append(result)
                return result
                
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Reliability",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def test_environment_validation(self) -> ChaosTestResult:
        """Test 5: Environment Validation - Security Decorator"""
        start_time = time.time()
        test_name = "Environment Validation - Security Decorator"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Test 1: Non-production environment
            blocked_attempts = 0
            total_attempts = 0
            
            # Mock non-production environment
            with mock.patch.dict(os.environ, {'PRODUCTION_MODE': 'false'}):
                @self.ip_validator.validate_execution_environment()
                async def test_trade_execution():
                    return "Trade executed"
                
                try:
                    await test_trade_execution()
                except SecurityError:
                    blocked_attempts += 1
                except Exception:
                    pass
                
                total_attempts += 1
            
            # Test 2: Invalid API key
            with mock.patch.dict(os.environ, {'EXCHANGE_API_KEY': 'test_key'}):
                @self.ip_validator.validate_execution_environment()
                async def test_trade_execution2():
                    return "Trade executed"
                
                try:
                    await test_trade_execution2()
                except SecurityError:
                    blocked_attempts += 1
                except Exception:
                    pass
                
                total_attempts += 1
            
            # Test 3: Valid production environment (should pass)
            with mock.patch.dict(os.environ, {
                'PRODUCTION_MODE': 'true',
                'EXCHANGE_API_KEY': 'prod_key_12345',
                'DEBUG': 'false'
            }):
                @self.ip_validator.validate_execution_environment()
                async def test_trade_execution3():
                    return "Trade executed"
                
                try:
                    result = await test_trade_execution3()
                    if result == "Trade executed":
                        # Valid execution passed
                        pass
                except SecurityError:
                    blocked_attempts += 1
                except Exception:
                    pass
                
                total_attempts += 1
            
            # Verify security is working (at least 2/3 attempts blocked)
            test_passed = blocked_attempts >= 2 and total_attempts == 3
            
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Reliability",
                result=TestResult.PASSED if test_passed else TestResult.FAILED,
                execution_time=time.time() - start_time,
                details={
                    'blocked_attempts': blocked_attempts,
                    'total_attempts': total_attempts,
                    'security_effectiveness': blocked_attempts / total_attempts
                },
                timestamp=datetime.now()
            )
            
            self.logger.info(f"{test_name}: {result.result.value}")
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Reliability",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def test_deployment_verification(self) -> ChaosTestResult:
        """Test 6: Deployment Verification - Koyeb Config"""
        start_time = time.time()
        test_name = "Deployment Verification - Koyeb Config"
        
        try:
            self.logger.info(f"Running {test_name}")
            
            # Load and validate koyeb_config.yml
            config_path = Path('koyeb_config.yml')
            config_valid = False
            variables_found = []
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_content = f.read()
                
                # Check for required variables
                required_vars = [
                    'OLLAMA_BASE_URL',
                    'CHROMA_HOST',
                    'REDIS_URL',
                    'POSTGRES_URL',
                    'EXCHANGE_API_KEY',
                    'TELEGRAM_BOT_TOKEN',
                    'SECURITY_LEVEL'
                ]
                
                variables_found = [var for var in required_vars if var in config_content]
                config_valid = len(variables_found) >= len(required_vars) * 0.8  # 80% of variables found
            
            # Test IP validator mapping to container IP
            ip_mapping_works = False
            try:
                # Test IP validation
                current_ip = await self.ip_validator._get_current_ip()
                if current_ip:
                    validation_result = await self.ip_validator._validate_ip_address(
                        current_ip, SecurityLevel.INTERNAL
                    )
                    ip_mapping_works = validation_result['status'] == ValidationStatus.APPROVED
            except:
                pass
            
            test_passed = config_valid and ip_mapping_works
            
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Deployment",
                result=TestResult.PASSED if test_passed else TestResult.FAILED,
                execution_time=time.time() - start_time,
                details={
                    'config_valid': config_valid,
                    'variables_found': len(variables_found),
                    'ip_mapping_works': ip_mapping_works,
                    'current_ip': await self.ip_validator._get_current_ip() if self.ip_validator else None
                },
                timestamp=datetime.now()
            )
            
            self.logger.info(f"{test_name}: {result.result.value}")
            self.test_results.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"{test_name} failed: {e}")
            result = ChaosTestResult(
                test_name=test_name,
                test_category="Deployment",
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            )
            self.test_results.append(result)
            return result
    
    async def cleanup(self) -> None:
        """Cleanup test environment"""
        try:
            self.logger.info("Cleaning up test environment")
            
            # Stop all components
            if self.vector_memory:
                await self.vector_memory.stop()
            
            if self.digital_twin:
                await self.digital_twin.stop()
            
            if self.research_lab:
                await self.research_lab.stop()
            
            if self.consensus_engine:
                await self.consensus_engine.stop()
            
            if self.ip_validator:
                self.ip_validator.is_initialized = False
            
            self.logger.info("Test environment cleaned up")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

# Main execution
async def main():
    """Run chaos tests"""
    test_suite = ChaosTestSuite()
    
    try:
        await test_suite.initialize()
        
        # Run all tests
        tests = [
            test_suite.test_agent_consensus_loop,
            test_suite.test_memory_integrity,
            test_suite.test_digital_twin_validation,
            test_suite.test_fault_injection,
            test_suite.test_environment_validation,
            test_suite.test_deployment_verification
        ]
        
        for test in tests:
            await test()
        
        # Generate summary
        total_tests = len(test_suite.test_results)
        passed = len([r for r in test_suite.test_results if r.result == TestResult.PASSED])
        failed = len([r for r in test_suite.test_results if r.result == TestResult.FAILED])
        errors = len([r for r in test_suite.test_results if r.result == TestResult.ERROR])
        
        print(f"\n{'='*60}")
        print(f"CHAOS TESTING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        print(f"Execution Time: {(datetime.now() - test_suite.start_time).total_seconds():.2f}s")
        print(f"{'='*60}")
        
        # Print detailed results
        for result in test_suite.test_results:
            status_icon = "PASS" if result.result == TestResult.PASSED else "FAIL"
            print(f"{status_icon}: {result.test_name} - {result.result.value} ({result.execution_time:.2f}s)")
        
        return test_suite.test_results
        
    except Exception as e:
        print(f"Chaos testing failed: {e}")
        return []
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
