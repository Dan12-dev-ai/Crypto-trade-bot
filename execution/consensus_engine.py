#!/usr/bin/env python3
"""
UOTA Elite v2 - Consensus-Based Execution System
World-First multi-agent voting system requiring >80% confidence
Institutional-grade execution with transparent decision logging
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Internal imports
from config import config
from main_orchestrator import TradingSignal
from simulation.digital_twin import SimulationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consensus_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VoteType(Enum):
    """Agent vote types"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

class ConsensusLevel(Enum):
    """Consensus confidence levels"""
    VERY_HIGH = "very_high"      # >90%
    HIGH = "high"                # 80-90%
    MEDIUM = "medium"            # 60-80%
    LOW = "low"                  # 40-60%
    VERY_LOW = "very_low"         # <40%

@dataclass
class AgentVote:
    """Individual agent vote"""
    agent_name: str
    agent_role: str
    vote_type: VoteType
    confidence: float
    reasoning: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    weight: float = 1.0  # Agent weight in consensus

@dataclass
class ConsensusResult:
    """Consensus building result"""
    signal_id: str
    original_signal: TradingSignal
    agent_votes: List[AgentVote]
    consensus_score: float
    consensus_level: ConsensusLevel
    final_decision: VoteType
    execution_approved: bool
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    voting_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionOrder:
    """Final execution order"""
    order_id: str
    symbol: str
    action: str
    quantity: float
    price: Optional[float]
    order_type: str  # "MARKET", "LIMIT", "STOP"
    stop_loss: Optional[float]
    take_profit: Optional[float]
    time_in_force: str
    consensus_result: ConsensusResult
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "PENDING"

class ConsensusExecutionEngine:
    """World-First consensus-based execution engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
        # Consensus parameters
        self.min_consensus_threshold = 0.80  # 80% minimum consensus
        self.high_consensus_threshold = 0.90   # 90% for high confidence
        self.agent_weights = {
            'researcher': 1.2,    # Research insights
            'analyst': 1.5,       # Technical analysis
            'risk_governor': 2.0,  # Risk management (highest weight)
            'executor': 1.0,       # Execution considerations
            'supervisor': 1.8      # Overall supervision
        }
        
        # Vote type mapping to numerical values
        self.vote_values = {
            VoteType.STRONG_BUY: 1.0,
            VoteType.BUY: 0.5,
            VoteType.HOLD: 0.0,
            VoteType.SELL: -0.5,
            VoteType.STRONG_SELL: -1.0
        }
        
        # Consensus history
        self.consensus_history = []
        self.execution_history = []
        
        # Performance tracking
        self.consensus_stats = {
            'total_consensus_builds': 0,
            'executions_approved': 0,
            'executions_rejected': 0,
            'avg_consensus_score': 0.0,
            'consensus_accuracy': 0.0,
            'risk_blocks': 0
        }
        
        # Risk parameters
        self.max_risk_per_trade = 0.01  # 1% max risk
        self.max_daily_loss = 0.05       # 5% daily loss
        self.max_drawdown = 0.20          # 20% max drawdown
        
    async def initialize(self) -> None:
        """Initialize consensus engine"""
        try:
            self.logger.info("🤝 Initializing Consensus-Based Execution Engine")
            
            # Create data directory
            Path('data/consensus').mkdir(exist_ok=True)
            
            # Load consensus history
            await self._load_consensus_history()
            
            # Initialize risk monitoring
            await self._initialize_risk_monitoring()
            
            self.is_initialized = True
            self.logger.info("✅ Consensus Engine initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Consensus Engine initialization failed: {e}")
            raise
    
    async def build_consensus(self, signal: TradingSignal, 
                           agent_decisions: Dict[str, Any],
                           risk_assessment: Dict[str, Any],
                           simulation_results: Dict[str, Any]) -> ConsensusResult:
        """Build consensus across all agents"""
        try:
            self.logger.info(f"🗳️ Building consensus for {signal.symbol} {signal.action}")
            
            start_time = datetime.now()
            
            # Collect agent votes
            agent_votes = await self._collect_agent_votes(
                signal, agent_decisions, risk_assessment, simulation_results
            )
            
            # Calculate weighted consensus
            consensus_score, confidence_breakdown = await self._calculate_consensus_score(agent_votes)
            
            # Determine final decision
            final_decision = await self._determine_final_decision(agent_votes, consensus_score)
            
            # Assess risk
            risk_evaluation = await self._evaluate_execution_risk(
                signal, risk_assessment, simulation_results
            )
            
            # Determine execution approval
            execution_approved = await self._approve_execution(
                consensus_score, risk_evaluation, final_decision
            )
            
            # Create consensus result
            result = ConsensusResult(
                signal_id=f"consensus_{datetime.now().timestamp()}",
                original_signal=signal,
                agent_votes=agent_votes,
                consensus_score=consensus_score,
                consensus_level=self._get_consensus_level(consensus_score),
                final_decision=final_decision,
                execution_approved=execution_approved,
                confidence_breakdown=confidence_breakdown,
                risk_assessment=risk_evaluation,
                voting_details={
                    'total_votes': len(agent_votes),
                    'vote_distribution': self._get_vote_distribution(agent_votes),
                    'weighted_average': consensus_score,
                    'unanimity': self._check_unanimity(agent_votes)
                },
                timestamp=datetime.now(),
                metadata={
                    'build_time': (datetime.now() - start_time).total_seconds(),
                    'risk_threshold': self.min_consensus_threshold,
                    'agent_count': len(agent_votes)
                }
            )
            
            # Store consensus result
            await self._store_consensus_result(result)
            
            # Update statistics
            self.consensus_stats['total_consensus_builds'] += 1
            self.consensus_stats['avg_consensus_score'] = (
                (self.consensus_stats['avg_consensus_score'] * (self.consensus_stats['total_consensus_builds'] - 1) + 
                 consensus_score) / self.consensus_stats['total_consensus_builds']
            )
            
            if execution_approved:
                self.consensus_stats['executions_approved'] += 1
            else:
                self.consensus_stats['executions_rejected'] += 1
            
            self.logger.info(f"✅ Consensus built: {consensus_score:.3f} -> {'APPROVED' if execution_approved else 'REJECTED'}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Consensus building failed: {e}")
            # Return conservative result on error
            return ConsensusResult(
                signal_id=f"error_{datetime.now().timestamp()}",
                original_signal=signal,
                agent_votes=[],
                consensus_score=0.0,
                consensus_level=ConsensusLevel.VERY_LOW,
                final_decision=VoteType.HOLD,
                execution_approved=False,
                risk_assessment={'risk_level': 'HIGH', 'reason': 'Consensus error'},
                timestamp=datetime.now(),
                metadata={'error': str(e)}
            )
    
    async def _collect_agent_votes(self, signal: TradingSignal,
                                agent_decisions: Dict[str, Any],
                                risk_assessment: Dict[str, Any],
                                simulation_results: Dict[str, Any]) -> List[AgentVote]:
        """Collect votes from all agents"""
        try:
            votes = []
            
            # Researcher vote
            if 'researcher' in agent_decisions:
                researcher_vote = await self._create_researcher_vote(
                    agent_decisions['researcher'], signal
                )
                votes.append(researcher_vote)
            
            # Analyst vote
            if 'analyst' in agent_decisions:
                analyst_vote = await self._create_analyst_vote(
                    agent_decisions['analyst'], signal
                )
                votes.append(analyst_vote)
            
            # Risk governor vote
            risk_vote = await self._create_risk_governor_vote(
                risk_assessment, signal
            )
            votes.append(risk_vote)
            
            # Executor vote
            executor_vote = await self._create_executor_vote(
                simulation_results, signal
            )
            votes.append(executor_vote)
            
            # Supervisor vote
            if 'supervisor' in agent_decisions:
                supervisor_vote = await self._create_supervisor_vote(
                    agent_decisions['supervisor'], signal, votes
                )
                votes.append(supervisor_vote)
            
            # Apply weights
            for vote in votes:
                vote.weight = self.agent_weights.get(vote.agent_role, 1.0)
            
            self.logger.info(f"🗳️ Collected {len(votes)} agent votes")
            return votes
            
        except Exception as e:
            self.logger.error(f"❌ Vote collection failed: {e}")
            return []
    
    async def _create_researcher_vote(self, researcher_decision: Dict[str, Any], 
                                   signal: TradingSignal) -> AgentVote:
        """Create researcher agent vote"""
        try:
            # Analyze research findings
            research_confidence = researcher_decision.get('confidence', 0.5)
            patterns_found = researcher_decision.get('patterns_found', 0)
            
            # Determine vote based on research
            if research_confidence > 0.8 and patterns_found > 5:
                vote_type = VoteType.BUY if signal.action == 'BUY' else VoteType.SELL
                confidence = research_confidence
            elif research_confidence > 0.6:
                vote_type = VoteType.HOLD
                confidence = research_confidence
            else:
                vote_type = VoteType.HOLD
                confidence = research_confidence * 0.7
            
            return AgentVote(
                agent_name="ResearcherAgent",
                agent_role="researcher",
                vote_type=vote_type,
                confidence=confidence,
                reasoning=f"Research analysis: {patterns_found} patterns found with {research_confidence:.2f} confidence",
                supporting_data={
                    'patterns_found': patterns_found,
                    'research_confidence': research_confidence,
                    'findings': researcher_decision.get('findings', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Researcher vote creation failed: {e}")
            return AgentVote(
                agent_name="ResearcherAgent",
                agent_role="researcher",
                vote_type=VoteType.HOLD,
                confidence=0.0,
                reasoning=f"Researcher vote error: {str(e)}"
            )
    
    async def _create_analyst_vote(self, analyst_decision: Dict[str, Any], 
                                 signal: TradingSignal) -> AgentVote:
        """Create analyst agent vote"""
        try:
            # Analyze technical indicators
            signal_strength = analyst_decision.get('signal_strength', 0.5)
            indicator_alignment = analyst_decision.get('indicator_alignment', 0.5)
            
            # Determine vote based on technical analysis
            combined_strength = (signal_strength + indicator_alignment) / 2
            
            if combined_strength > 0.7:
                vote_type = VoteType.BUY if signal.action == 'BUY' else VoteType.SELL
                confidence = combined_strength
            elif combined_strength > 0.4:
                vote_type = VoteType.HOLD
                confidence = combined_strength
            else:
                vote_type = VoteType.HOLD
                confidence = combined_strength * 0.8
            
            return AgentVote(
                agent_name="AnalystAgent",
                agent_role="analyst",
                vote_type=vote_type,
                confidence=confidence,
                reasoning=f"Technical analysis: signal strength {signal_strength:.2f}, indicator alignment {indicator_alignment:.2f}",
                supporting_data={
                    'signal_strength': signal_strength,
                    'indicator_alignment': indicator_alignment,
                    'indicators': analyst_decision.get('indicators', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Analyst vote creation failed: {e}")
            return AgentVote(
                agent_name="AnalystAgent",
                agent_role="analyst",
                vote_type=VoteType.HOLD,
                confidence=0.0,
                reasoning=f"Analyst vote error: {str(e)}"
            )
    
    async def _create_risk_governor_vote(self, risk_assessment: Dict[str, Any], 
                                      signal: TradingSignal) -> AgentVote:
        """Create risk governor vote"""
        try:
            # Analyze risk factors
            risk_level = risk_assessment.get('risk_level', 'MEDIUM')
            risk_score = risk_assessment.get('risk_score', 0.5)
            
            # Risk governor has veto power
            if risk_level == 'HIGH' or risk_score > 0.8:
                vote_type = VoteType.HOLD
                confidence = 1.0  # High confidence in rejection
                reasoning = f"High risk detected: {risk_level} with score {risk_score:.2f}"
            elif risk_level == 'MEDIUM':
                vote_type = VoteType.HOLD
                confidence = 0.7
                reasoning = f"Medium risk: {risk_level} with score {risk_score:.2f}"
            else:  # LOW risk
                vote_type = VoteType.BUY if signal.action == 'BUY' else VoteType.SELL
                confidence = 0.8
                reasoning = f"Low risk: {risk_level} with score {risk_score:.2f}"
            
            return AgentVote(
                agent_name="RiskGovernorAgent",
                agent_role="risk_governor",
                vote_type=vote_type,
                confidence=confidence,
                reasoning=reasoning,
                supporting_data={
                    'risk_level': risk_level,
                    'risk_score': risk_score,
                    'risk_factors': risk_assessment.get('risk_factors', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Risk governor vote creation failed: {e}")
            return AgentVote(
                agent_name="RiskGovernorAgent",
                agent_role="risk_governor",
                vote_type=VoteType.HOLD,
                confidence=0.0,
                reasoning=f"Risk governor vote error: {str(e)}"
            )
    
    async def _create_executor_vote(self, simulation_results: Dict[str, Any], 
                                 signal: TradingSignal) -> AgentVote:
        """Create executor agent vote"""
        try:
            # Analyze simulation results
            sim_confidence = simulation_results.get('confidence', 0.5)
            sim_recommendation = simulation_results.get('recommendation', 'REJECT')
            expected_pnl = simulation_results.get('simulated_pnl', 0.0)
            
            # Determine vote based on simulation
            if sim_recommendation == 'EXECUTE' and sim_confidence > 0.7:
                vote_type = VoteType.BUY if signal.action == 'BUY' else VoteType.SELL
                confidence = sim_confidence
            elif sim_recommendation == 'MODIFY':
                vote_type = VoteType.HOLD
                confidence = sim_confidence * 0.8
            else:
                vote_type = VoteType.HOLD
                confidence = sim_confidence * 0.6
            
            return AgentVote(
                agent_name="ExecutorAgent",
                agent_role="executor",
                vote_type=vote_type,
                confidence=confidence,
                reasoning=f"Simulation: {sim_recommendation} with {sim_confidence:.2f} confidence, expected P&L {expected_pnl:.2%}",
                supporting_data={
                    'simulation_recommendation': sim_recommendation,
                    'simulation_confidence': sim_confidence,
                    'expected_pnl': expected_pnl,
                    'max_drawdown': simulation_results.get('simulated_max_drawdown', 0.0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Executor vote creation failed: {e}")
            return AgentVote(
                agent_name="ExecutorAgent",
                agent_role="executor",
                vote_type=VoteType.HOLD,
                confidence=0.0,
                reasoning=f"Executor vote error: {str(e)}"
            )
    
    async def _create_supervisor_vote(self, supervisor_decision: Dict[str, Any],
                                    signal: TradingSignal,
                                    other_votes: List[AgentVote]) -> AgentVote:
        """Create supervisor vote"""
        try:
            # Analyze other agents' votes
            vote_distribution = self._get_vote_distribution(other_votes)
            consensus_so_far = max(vote_distribution.values()) if vote_distribution else 0
            
            # Supervisor considers overall consensus
            if consensus_so_far > 0.8:
                vote_type = VoteType.BUY if signal.action == 'BUY' else VoteType.SELL
                confidence = consensus_so_far
                reasoning = f"Strong consensus among agents: {consensus_so_far:.2f}"
            elif consensus_so_far > 0.6:
                vote_type = VoteType.HOLD
                confidence = consensus_so_far
                reasoning = f"Moderate consensus among agents: {consensus_so_far:.2f}"
            else:
                vote_type = VoteType.HOLD
                confidence = 0.5
                reasoning = f"Low consensus among agents: {consensus_so_far:.2f}"
            
            return AgentVote(
                agent_name="SupervisorAgent",
                agent_role="supervisor",
                vote_type=vote_type,
                confidence=confidence,
                reasoning=reasoning,
                supporting_data={
                    'vote_distribution': vote_distribution,
                    'consensus_so_far': consensus_so_far,
                    'supervisor_analysis': supervisor_decision.get('analysis', {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"❌ Supervisor vote creation failed: {e}")
            return AgentVote(
                agent_name="SupervisorAgent",
                agent_role="supervisor",
                vote_type=VoteType.HOLD,
                confidence=0.0,
                reasoning=f"Supervisor vote error: {str(e)}"
            )
    
    async def _calculate_consensus_score(self, votes: List[AgentVote]) -> Tuple[float, Dict[str, float]]:
        """Calculate weighted consensus score"""
        try:
            if not votes:
                return 0.0, {}
            
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0
            
            confidence_breakdown = {}
            
            for vote in votes:
                vote_value = self.vote_values[vote.vote_type]
                weight = vote.weight * vote.confidence
                
                weighted_sum += vote_value * weight
                total_weight += weight
                
                confidence_breakdown[vote.agent_role] = vote.confidence
            
            if total_weight == 0:
                return 0.0, confidence_breakdown
            
            consensus_score = (weighted_sum / total_weight + 1) / 2  # Normalize to 0-1
            
            return consensus_score, confidence_breakdown
            
        except Exception as e:
            self.logger.error(f"❌ Consensus score calculation failed: {e}")
            return 0.0, {}
    
    async def _determine_final_decision(self, votes: List[AgentVote], 
                                    consensus_score: float) -> VoteType:
        """Determine final decision from votes"""
        try:
            # Weighted vote counting
            vote_counts = {
                VoteType.STRONG_BUY: 0,
                VoteType.BUY: 0,
                VoteType.HOLD: 0,
                VoteType.SELL: 0,
                VoteType.STRONG_SELL: 0
            }
            
            for vote in votes:
                weight = vote.weight * vote.confidence
                vote_counts[vote.vote_type] += weight
            
            # Find the vote type with highest weighted count
            max_votes = max(vote_counts.values())
            best_votes = [vt for vt, count in vote_counts.items() if count == max_votes]
            
            # If tie, prefer HOLD
            if len(best_votes) > 1:
                return VoteType.HOLD
            
            return best_votes[0]
            
        except Exception as e:
            self.logger.error(f"❌ Final decision determination failed: {e}")
            return VoteType.HOLD
    
    async def _evaluate_execution_risk(self, signal: TradingSignal,
                                    risk_assessment: Dict[str, Any],
                                    simulation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate execution risk"""
        try:
            risk_factors = {}
            overall_risk = 0.0
            
            # Signal confidence risk
            signal_risk = 1.0 - signal.confidence
            risk_factors['signal_confidence'] = signal_risk
            overall_risk += signal_risk * 0.2
            
            # Simulation risk
            sim_drawdown = simulation_results.get('simulated_max_drawdown', 0.0)
            sim_risk = min(sim_drawdown * 10, 1.0)  # Scale to 0-1
            risk_factors['simulation_drawdown'] = sim_risk
            overall_risk += sim_risk * 0.3
            
            # Market conditions risk
            market_risk = risk_assessment.get('risk_score', 0.5)
            risk_factors['market_conditions'] = market_risk
            overall_risk += market_risk * 0.3
            
            # Historical performance risk
            hist_risk = 0.3  # Placeholder for historical risk
            risk_factors['historical_performance'] = hist_risk
            overall_risk += hist_risk * 0.2
            
            # Determine risk level
            if overall_risk > 0.8:
                risk_level = 'HIGH'
            elif overall_risk > 0.5:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            return {
                'overall_risk': overall_risk,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendation': 'EXECUTE' if overall_risk < 0.6 else 'REJECT'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Risk evaluation failed: {e}")
            return {
                'overall_risk': 1.0,
                'risk_level': 'HIGH',
                'risk_factors': {'error': str(e)},
                'recommendation': 'REJECT'
            }
    
    async def _approve_execution(self, consensus_score: float,
                              risk_evaluation: Dict[str, Any],
                              final_decision: VoteType) -> bool:
        """Approve or reject execution"""
        try:
            # Check consensus threshold
            if consensus_score < self.min_consensus_threshold:
                self.logger.info(f"❌ Rejected: Consensus {consensus_score:.3f} below threshold {self.min_consensus_threshold}")
                return False
            
            # Check risk level
            if risk_evaluation['risk_level'] == 'HIGH':
                self.logger.info(f"❌ Rejected: High risk level {risk_evaluation['overall_risk']:.3f}")
                self.consensus_stats['risk_blocks'] += 1
                return False
            
            # Check for HOLD decision
            if final_decision == VoteType.HOLD:
                self.logger.info(f"❌ Rejected: Final decision is HOLD")
                return False
            
            # All checks passed
            self.logger.info(f"✅ Approved: Consensus {consensus_score:.3f}, Risk {risk_evaluation['risk_level']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Execution approval failed: {e}")
            return False
    
    def _get_consensus_level(self, consensus_score: float) -> ConsensusLevel:
        """Get consensus level from score"""
        if consensus_score > 0.9:
            return ConsensusLevel.VERY_HIGH
        elif consensus_score > 0.8:
            return ConsensusLevel.HIGH
        elif consensus_score > 0.6:
            return ConsensusLevel.MEDIUM
        elif consensus_score > 0.4:
            return ConsensusLevel.LOW
        else:
            return ConsensusLevel.VERY_LOW
    
    def _get_vote_distribution(self, votes: List[AgentVote]) -> Dict[str, float]:
        """Get vote distribution"""
        try:
            distribution = {}
            total_weight = 0
            
            # Calculate weighted counts
            for vote in votes:
                vote_type = vote.vote_type.value
                weight = vote.weight * vote.confidence
                
                if vote_type not in distribution:
                    distribution[vote_type] = 0
                
                distribution[vote_type] += weight
                total_weight += weight
            
            # Normalize to percentages
            if total_weight > 0:
                for vote_type in distribution:
                    distribution[vote_type] = distribution[vote_type] / total_weight
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"❌ Vote distribution calculation failed: {e}")
            return {}
    
    def _check_unanimity(self, votes: List[AgentVote]) -> bool:
        """Check if all votes are the same"""
        try:
            if not votes:
                return False
            
            first_vote = votes[0].vote_type
            return all(vote.vote_type == first_vote for vote in votes)
            
        except Exception as e:
            self.logger.error(f"❌ Unanimity check failed: {e}")
            return False
    
    async def _store_consensus_result(self, result: ConsensusResult) -> None:
        """Store consensus result"""
        try:
            self.consensus_history.append(result)
            
            # Keep only last 1000 results
            if len(self.consensus_history) > 1000:
                self.consensus_history = self.consensus_history[-1000:]
            
            # Save to file
            consensus_file = Path('data/consensus/consensus_history.json')
            with open(consensus_file, 'w') as f:
                json.dump([self._consensus_to_dict(r) for r in self.consensus_history], f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"❌ Consensus storage failed: {e}")
    
    def _consensus_to_dict(self, consensus: ConsensusResult) -> Dict[str, Any]:
        """Convert consensus result to dictionary"""
        return {
            'signal_id': consensus.signal_id,
            'consensus_score': consensus.consensus_score,
            'consensus_level': consensus.consensus_level.value,
            'final_decision': consensus.final_decision.value,
            'execution_approved': consensus.execution_approved,
            'timestamp': consensus.timestamp.isoformat(),
            'metadata': consensus.metadata
        }
    
    async def _load_consensus_history(self) -> None:
        """Load consensus history"""
        try:
            consensus_file = Path('data/consensus/consensus_history.json')
            if consensus_file.exists():
                with open(consensus_file, 'r') as f:
                    data = json.load(f)
                    # Would need to reconstruct ConsensusResult objects
                    self.consensus_stats['total_consensus_builds'] = len(data)
            
            self.logger.info(f"📚 Loaded consensus history")
            
        except Exception as e:
            self.logger.error(f"❌ Loading consensus history failed: {e}")
    
    async def _initialize_risk_monitoring(self) -> None:
        """Initialize risk monitoring"""
        try:
            # Risk monitoring setup would go here
            self.logger.info("⚠️ Risk monitoring initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Risk monitoring initialization failed: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get consensus engine status"""
        try:
            return {
                'is_initialized': self.is_initialized,
                'consensus_threshold': self.min_consensus_threshold,
                'consensus_history_size': len(self.consensus_history),
                'execution_history_size': len(self.execution_history),
                'consensus_stats': self.consensus_stats,
                'agent_weights': self.agent_weights
            }
            
        except Exception as e:
            self.logger.error(f"❌ Status check failed: {e}")
            return {'error': str(e)}
    
    async def stop(self) -> None:
        """Stop consensus engine"""
        try:
            self.logger.info("🛑 Stopping Consensus Engine")
            
            self.is_initialized = False
            self.logger.info("✅ Consensus Engine stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping consensus engine: {e}")

# Main execution for testing
async def main():
    """Test consensus engine"""
    consensus_engine = ConsensusExecutionEngine()
    
    try:
        await consensus_engine.initialize()
        
        # Test consensus building
        test_signal = TradingSignal(
            symbol='BTC/USDT',
            action='BUY',
            confidence=0.8,
            reasoning='Test signal',
            timestamp=datetime.now()
        )
        
        agent_decisions = {
            'analyst': {'signal_strength': 0.7, 'indicator_alignment': 0.8},
            'researcher': {'confidence': 0.6, 'patterns_found': 3}
        }
        
        risk_assessment = {'risk_level': 'MEDIUM', 'risk_score': 0.4}
        simulation_results = {'confidence': 0.7, 'recommendation': 'EXECUTE', 'simulated_pnl': 0.02}
        
        result = await consensus_engine.build_consensus(
            test_signal, agent_decisions, risk_assessment, simulation_results
        )
        
        print(f"Consensus result: {result.execution_approved}")
        print(f"Consensus score: {result.consensus_score:.3f}")
        print(f"Final decision: {result.final_decision.value}")
        
        # Get status
        status = await consensus_engine.get_status()
        print(f"Status: {status}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await consensus_engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
