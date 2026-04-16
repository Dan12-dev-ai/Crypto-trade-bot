#!/usr/bin/env python3
"""
UOTA Elite v2 - Main Orchestrator
Central Decision Engine using LangGraph for stateful workflows and agent handoffs
World-First Autonomous Quant Operating System
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.llms import Ollama

# CrewAI imports
from crewai import Agent, Task, Crew, Process

# Internal imports
from config import config
from memory.vector_store import VectorMemoryManager
from simulation.digital_twin import DigitalTwinEnvironment
from research.autonomous_research import AutonomousResearchLab
from execution.consensus_engine import ConsensusExecutionEngine
from security.ip_validator import validate_ip, validate_execution_environment
from agents.researcher_agent import ResearcherAgent
from agents.analyst_agent import AnalystAgent
from agents.risk_governor_agent import RiskGovernorAgent
from agents.executor_agent import ExecutorAgent
from agents.supervisor_agent import SupervisorAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    VALIDATING = "validating"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    PAUSED = "paused"
    EMERGENCY = "emergency"

class AgentRole(Enum):
    """Agent roles in the system"""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    RISK_GOVERNOR = "risk_governor"
    EXECUTOR = "executor"
    SUPERVISOR = "supervisor"

@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    timestamp: datetime
    agent_votes: Dict[str, float] = field(default_factory=dict)
    consensus_score: float = 0.0
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OrchestratorState(TypedDict):
    """LangGraph state structure"""
    system_state: SystemState
    current_symbol: str
    market_data: Dict[str, Any]
    trading_signals: List[TradingSignal]
    agent_decisions: Dict[str, Any]
    consensus_results: Dict[str, Any]
    risk_metrics: Dict[str, Any]
    memory_context: Dict[str, Any]
    simulation_results: Dict[str, Any]
    research_findings: Dict[str, Any]
    execution_status: Dict[str, Any]
    timestamp: datetime
    checkpoint_data: Dict[str, Any]

class MainOrchestrator:
    """Central Decision Engine for UOTA Elite v2"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.checkpoint_saver = MemorySaver()
        
        # Initialize LLM
        self.llm = Ollama(
            model=config.agents.llm_model,
            base_url=config.agents.ollama_base_url
        )
        
        # Initialize core components
        self.vector_memory = VectorMemoryManager()
        self.digital_twin = DigitalTwinEnvironment()
        self.research_lab = AutonomousResearchLab()
        self.consensus_engine = ConsensusExecutionEngine()
        
        # Initialize agents
        self.agents = {
            AgentRole.RESEARCHER: ResearcherAgent(self.llm),
            AgentRole.ANALYST: AnalystAgent(self.llm),
            AgentRole.RISK_GOVERNOR: RiskGovernorAgent(self.llm),
            AgentRole.EXECUTOR: ExecutorAgent(self.llm),
            AgentRole.SUPERVISOR: SupervisorAgent(self.llm)
        }
        
        # Initialize LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile(checkpointer=self.checkpoint_saver)
        
        # System state
        self.current_state: Optional[OrchestratorState] = None
        self.last_checkpoint = None
        
        # Performance metrics
        self.metrics = {
            'total_decisions': 0,
            'successful_executions': 0,
            'consensus_reached': 0,
            'risk_blocks': 0,
            'system_uptime': datetime.now()
        }
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine workflow"""
        
        # Create workflow graph
        workflow = StateGraph(OrchestratorState)
        
        # Define nodes
        workflow.add_node("initialize", self._initialize_system)
        workflow.add_node("scan_markets", self._scan_markets)
        workflow.add_node("analyze_data", self._analyze_market_data)
        workflow.add_node("research_patterns", self._research_patterns)
        workflow.add_node("validate_simulation", self._validate_with_digital_twin)
        workflow.add_node("build_consensus", self._build_consensus)
        workflow.add_node("execute_trade", self._execute_trade)
        workflow.add_node("monitor_results", self._monitor_results)
        workflow.add_node("emergency_stop", self._emergency_stop)
        
        # Define edges (workflow transitions)
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "scan_markets")
        workflow.add_edge("scan_markets", "analyze_data")
        workflow.add_edge("analyze_data", "research_patterns")
        workflow.add_edge("research_patterns", "validate_simulation")
        workflow.add_edge("validate_simulation", "build_consensus")
        
        # Conditional edges for consensus
        workflow.add_conditional_edges(
            "build_consensus",
            self._should_execute,
            {
                "execute": "execute_trade",
                "reject": "scan_markets",
                "emergency": "emergency_stop"
            }
        )
        
        workflow.add_edge("execute_trade", "monitor_results")
        workflow.add_edge("monitor_results", "scan_markets")
        workflow.add_edge("emergency_stop", "scan_markets")
        
        return workflow
    
    async def _initialize_system(self, state: OrchestratorState) -> OrchestratorState:
        """Initialize system components"""
        try:
            self.logger.info("🚀 Initializing UOTA Elite v2 Autonomous Quant OS")
            
            # Validate execution environment
            if not validate_execution_environment():
                raise RuntimeError("Execution environment validation failed")
            
            # Initialize vector memory
            await self.vector_memory.initialize()
            
            # Initialize digital twin
            await self.digital_twin.initialize()
            
            # Initialize research lab
            await self.research_lab.initialize()
            
            # Initialize consensus engine
            await self.consensus_engine.initialize()
            
            # Initialize agents
            for agent in self.agents.values():
                await agent.initialize()
            
            # Update state
            state['system_state'] = SystemState.SCANNING
            state['timestamp'] = datetime.now()
            state['checkpoint_data'] = {
                'initialized_at': datetime.now().isoformat(),
                'components': ['vector_memory', 'digital_twin', 'research_lab', 'consensus_engine', 'agents']
            }
            
            self.logger.info("✅ System initialization complete")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _scan_markets(self, state: OrchestratorState) -> OrchestratorState:
        """Scan markets for opportunities"""
        try:
            self.logger.info("🔍 Scanning markets for opportunities")
            
            # Get market data from exchanges
            market_data = await self._get_market_data()
            
            # Store in vector memory for pattern recognition
            await self.vector_memory.store_market_data(market_data)
            
            # Update state
            state['system_state'] = SystemState.ANALYZING
            state['market_data'] = market_data
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"📊 Scanned {len(market_data)} market pairs")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Market scanning failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _analyze_market_data(self, state: OrchestratorState) -> OrchestratorState:
        """Analyze market data with analyst agent"""
        try:
            self.logger.info("📈 Analyzing market data")
            
            # Get analyst agent decision
            analyst_decision = await self.agents[AgentRole.ANALYST].analyze(state['market_data'])
            
            # Store analysis in memory
            await self.vector_memory.store_analysis(analyst_decision)
            
            # Update state
            state['system_state'] = SystemState.RESEARCHING
            state['agent_decisions']['analyst'] = analyst_decision
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"🧠 Analysis complete: {analyst_decision.get('signal', 'UNKNOWN')}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Market analysis failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _research_patterns(self, state: OrchestratorState) -> OrchestratorState:
        """Research historical patterns with researcher agent"""
        try:
            self.logger.info("🔬 Researching historical patterns")
            
            # Get relevant patterns from vector memory
            similar_patterns = await self.vector_memory.find_similar_patterns(state['market_data'])
            
            # Research with researcher agent
            research_findings = await self.agents[AgentRole.RESEARCHER].research(
                state['market_data'], 
                similar_patterns
            )
            
            # Store research findings
            await self.vector_memory.store_research(research_findings)
            
            # Update state
            state['system_state'] = SystemState.VALIDATING
            state['research_findings'] = research_findings
            state['memory_context'] = similar_patterns
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"📚 Research complete: {len(research_findings.get('patterns', []))} patterns found")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Pattern research failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _validate_with_digital_twin(self, state: OrchestratorState) -> OrchestratorState:
        """Validate decisions with digital twin simulation"""
        try:
            self.logger.info("🎭 Validating with digital twin")
            
            # Create trading signal from agent decisions
            signal = self._create_trading_signal(state)
            
            # Validate with digital twin
            simulation_results = await self.digital_twin.validate_signal(signal)
            
            # Update state
            state['system_state'] = SystemState.EXECUTING
            state['simulation_results'] = simulation_results
            state['trading_signals'] = [signal]
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"🎯 Digital twin validation: {simulation_results.get('recommendation', 'UNKNOWN')}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Digital twin validation failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _build_consensus(self, state: OrchestratorState) -> OrchestratorState:
        """Build consensus across all agents"""
        try:
            self.logger.info("🤝 Building agent consensus")
            
            # Get risk governor assessment
            risk_assessment = await self.agents[AgentRole.RISK_GOVERNOR].assess_risk(state)
            
            # Build consensus with all agents
            consensus_results = await self.consensus_engine.build_consensus(
                signal=state['trading_signals'][0],
                agent_decisions=state['agent_decisions'],
                risk_assessment=risk_assessment,
                simulation_results=state['simulation_results']
            )
            
            # Update signal with consensus
            state['trading_signals'][0].consensus_score = consensus_results['confidence_score']
            state['trading_signals'][0].agent_votes = consensus_results['agent_votes']
            
            # Update state
            state['consensus_results'] = consensus_results
            state['risk_metrics'] = risk_assessment
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"🎯 Consensus score: {consensus_results['confidence_score']:.2f}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Consensus building failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    def _should_execute(self, state: OrchestratorState) -> str:
        """Determine if trade should be executed"""
        try:
            consensus_score = state['trading_signals'][0].consensus_score
            risk_level = state['risk_metrics'].get('risk_level', 'HIGH')
            
            # Check consensus threshold (80%)
            if consensus_score >= 0.8 and risk_level != 'HIGH':
                return "execute"
            elif risk_level == 'HIGH':
                return "emergency"
            else:
                return "reject"
                
        except Exception as e:
            self.logger.error(f"❌ Execution decision failed: {e}")
            return "emergency"
    
    async def _execute_trade(self, state: OrchestratorState) -> OrchestratorState:
        """Execute trade with executor agent"""
        try:
            self.logger.info("⚡ Executing trade")
            
            # Execute with executor agent
            execution_result = await self.agents[AgentRole.EXECUTOR].execute(
                state['trading_signals'][0]
            )
            
            # Store execution in memory
            await self.vector_memory.store_execution(execution_result)
            
            # Update metrics
            self.metrics['total_decisions'] += 1
            if execution_result.get('success', False):
                self.metrics['successful_executions'] += 1
            
            # Update state
            state['system_state'] = SystemState.MONITORING
            state['execution_status'] = execution_result
            state['timestamp'] = datetime.now()
            
            self.logger.info(f"✅ Trade executed: {execution_result.get('status', 'UNKNOWN')}")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Trade execution failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _monitor_results(self, state: OrchestratorState) -> OrchestratorState:
        """Monitor trade results and update system"""
        try:
            self.logger.info("📊 Monitoring results")
            
            # Monitor execution results
            monitoring_results = await self.agents[AgentRole.SUPERVISOR].monitor(
                state['execution_status']
            )
            
            # Update system metrics
            self.metrics.update(monitoring_results.get('metrics', {}))
            
            # Update state for next cycle
            state['system_state'] = SystemState.SCANNING
            state['timestamp'] = datetime.now()
            
            self.logger.info("🔄 Monitoring complete, ready for next cycle")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Result monitoring failed: {e}")
            state['system_state'] = SystemState.EMERGENCY
            return state
    
    async def _emergency_stop(self, state: OrchestratorState) -> OrchestratorState:
        """Handle emergency situations"""
        try:
            self.logger.warning("🚨 Emergency stop activated")
            
            # Emergency stop with all agents
            for agent in self.agents.values():
                await agent.emergency_stop()
            
            # Update metrics
            self.metrics['risk_blocks'] += 1
            
            # Update state
            state['system_state'] = SystemState.PAUSED
            state['timestamp'] = datetime.now()
            
            self.logger.warning("⏸️ System paused due to emergency")
            return state
            
        except Exception as e:
            self.logger.error(f"❌ Emergency stop failed: {e}")
            return state
    
    def _create_trading_signal(self, state: OrchestratorState) -> TradingSignal:
        """Create trading signal from agent decisions"""
        return TradingSignal(
            symbol=state['market_data'].get('symbol', 'BTC/USDT'),
            action=state['agent_decisions'].get('analyst', {}).get('signal', 'HOLD'),
            confidence=state['agent_decisions'].get('analyst', {}).get('confidence', 0.0),
            reasoning=state['agent_decisions'].get('analyst', {}).get('reasoning', ''),
            timestamp=datetime.now(),
            metadata={
                'market_data': state['market_data'],
                'research_findings': state.get('research_findings', {}),
                'simulation_results': state.get('simulation_results', {})
            }
        )
    
    async def _get_market_data(self) -> Dict[str, Any]:
        """Get market data from exchanges"""
        # This would integrate with your existing market data systems
        # For now, return mock data
        return {
            'symbol': 'BTC/USDT',
            'price': 45000.0,
            'volume': 1000000.0,
            'change_24h': 0.02,
            'rsi': 55.0,
            'macd': 0.5,
            'bollinger_position': 0.6,
            'timestamp': datetime.now().isoformat()
        }
    
    async def start(self, thread_id: str = "main") -> None:
        """Start the orchestrator"""
        try:
            self.logger.info("🚀 Starting UOTA Elite v2 Main Orchestrator")
            
            # Initialize state
            initial_state: OrchestratorState = {
                'system_state': SystemState.INITIALIZING,
                'current_symbol': 'BTC/USDT',
                'market_data': {},
                'trading_signals': [],
                'agent_decisions': {},
                'consensus_results': {},
                'risk_metrics': {},
                'memory_context': {},
                'simulation_results': {},
                'research_findings': {},
                'execution_status': {},
                'timestamp': datetime.now(),
                'checkpoint_data': {}
            }
            
            self.is_running = True
            
            # Run the workflow
            async for event in self.app.astream(initial_state, thread_id):
                self.logger.info(f"🔄 Workflow event: {event}")
                
                # Update current state
                if 'values' in event:
                    self.current_state = event['values']
                
                # Save checkpoint
                self.last_checkpoint = datetime.now()
                
                # Check for emergency stop
                if self.current_state.get('system_state') == SystemState.EMERGENCY:
                    self.logger.warning("⚠️ Emergency state detected, pausing")
                    await asyncio.sleep(30)  # Wait 30 seconds before resuming
                    
        except Exception as e:
            self.logger.error(f"❌ Orchestrator failed: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """Stop the orchestrator"""
        try:
            self.logger.info("🛑 Stopping UOTA Elite v2 Main Orchestrator")
            
            self.is_running = False
            
            # Stop all agents
            for agent in self.agents.values():
                await agent.stop()
            
            # Stop components
            await self.vector_memory.stop()
            await self.digital_twin.stop()
            await self.research_lab.stop()
            await self.consensus_engine.stop()
            
            self.logger.info("✅ Orchestrator stopped successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping orchestrator: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'is_running': self.is_running,
            'current_state': self.current_state.get('system_state') if self.current_state else None,
            'last_checkpoint': self.last_checkpoint.isoformat() if self.last_checkpoint else None,
            'metrics': self.metrics,
            'agents': {role.value: agent.get_status() for role, agent in self.agents.items()},
            'components': {
                'vector_memory': await self.vector_memory.get_status(),
                'digital_twin': await self.digital_twin.get_status(),
                'research_lab': await self.research_lab.get_status(),
                'consensus_engine': await self.consensus_engine.get_status()
            }
        }

# Main execution
async def main():
    """Main entry point"""
    orchestrator = MainOrchestrator()
    
    try:
        await orchestrator.start()
        
        # Keep running
        while orchestrator.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 UOTA Elite v2 shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
