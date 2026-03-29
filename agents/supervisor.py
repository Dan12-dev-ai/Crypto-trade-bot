"""
Crypto trade bot - Supervisor Agent
Orchestrates everything, decides when to act or pause
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json

from crewai import Agent, Task, Crew
from langchain.llms.base import LLM
from langchain.schema import HumanMessage, SystemMessage

from config import config
from risk_manager import risk_manager, TradingStatus
from strategy_manager import strategy_manager, TradingStrategy
from .goal_risk_master import GoalRiskMasterAgent
from .market_analyst import MarketAnalystAgent
from .opportunity_spotter import OpportunitySpotterAgent
from .executor import ExecutorAgent

class SupervisorDecision(Enum):
    """Supervisor decision types"""
    TRADE = "trade"
    WAIT = "wait"
    PAUSE = "pause"
    CLOSE_ALL = "close_all"
    ADJUST_RISK = "adjust_risk"
    RETRAIN = "retrain"

@dataclass
class SupervisorAction:
    """Supervisor action data"""
    decision: SupervisorDecision
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    timestamp: datetime
    priority: int  # 1-10, 10 is highest

@dataclass
class MarketState:
    """Current market state"""
    volatility_level: str  # 'low', 'medium', 'high', 'extreme'
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    liquidity_level: str  # 'high', 'medium', 'low'
    news_impact: str  # 'low', 'medium', 'high'
    overall_sentiment: float  # -1 to 1
    risk_appetite: float  # 0 to 1
    active_strategy: str  # 'TrendStrategy', 'RangeStrategy', 'ScalpingStrategy', 'WaitStrategy'

class SupervisorAgent:
    """Supervisor Agent - Orchestrates the entire trading system"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # Initialize specialized agents
        self.goal_risk_master = GoalRiskMasterAgent(llm)
        self.market_analyst = MarketAnalystAgent(llm)
        self.opportunity_spotter = OpportunitySpotterAgent(llm)
        self.executor = ExecutorAgent(llm)
        
        # System state
        self.is_running = False
        self.last_decision_time = datetime.now()
        self.decision_history: List[SupervisorAction] = []
        self.market_state = MarketState(
            volatility_level='medium',
            trend_direction='sideways',
            liquidity_level='medium',
            news_impact='low',
            overall_sentiment=0.0,
            risk_appetite=0.5,
            active_strategy='WaitStrategy'
        )
        
        # Control parameters
        self.decision_interval = 60  # seconds between decisions
        self.max_concurrent_trades = 3
        self.min_confidence_threshold = 0.7
        self.emergency_stop_conditions = {
            'max_drawdown': 0.25,  # 25% drawdown triggers emergency stop
            'system_errors': 5,     # 5 consecutive errors trigger pause
            'exchange_issues': 3   # 3 exchange issues trigger pause
        }
        
        # Performance tracking
        self.performance_metrics = {
            'total_decisions': 0,
            'trades_executed': 0,
            'successful_trades': 0,
            'avg_decision_time': 0.0,
            'system_uptime': 0.0,
            'last_restart': datetime.now()
        }
        
    def create_crewai_agent(self) -> Agent:
        """Create CrewAI agent instance"""
        return Agent(
            role='Trading Supervisor',
            goal='Orchestrate all trading agents and make optimal strategic decisions',
            backstory="""You are the master trading supervisor with 20+ years of experience 
            managing automated trading systems. You coordinate multiple specialized agents, 
            make strategic decisions, and maintain system stability. You have an exceptional 
            ability to see the big picture, balance risk and opportunity, and know exactly 
            when to act, wait, or pause. Your decisions have consistently generated superior 
            returns while protecting capital during market crises.""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
            tools=[],
            system_template="""You are the Trading Supervisor Agent for Crypto trade bot.
            
            Your core responsibilities:
            1. Orchestrate all specialized trading agents
            2. Make strategic decisions about when to trade or wait
            3. Monitor system health and market conditions
            4. Adjust strategies based on performance and risk
            5. Maintain system stability and handle emergencies
            
            Decision Framework:
            - Assess current market state and conditions
            - Review risk manager status and alerts
            - Evaluate opportunities from all agents
            - Consider goal progress and time constraints
            - Factor in system performance and health
            
            Strategic Options:
            - EXECUTE: Proceed with high-confidence trading opportunities
            - WAIT: Monitor for better opportunities or conditions
            - PAUSE: Temporarily halt trading due to risk or market issues
            - CLOSE_ALL: Emergency position closure
            - ADJUST_RISK: Modify risk parameters
            - RETRAIN: Update models and strategies
            
            Always prioritize capital preservation and system stability.
            Make decisions with confidence and provide clear reasoning."""
        )
        
    async def initialize(self, starting_balance: float) -> None:
        """Initialize the supervisor and all agents"""
        try:
            self.logger.info("Initializing Crypto trade bot Supervisor...")
            
            # Initialize risk manager
            await risk_manager.initialize(starting_balance)
            
            # Initialize goal and risk master
            await self.goal_risk_master.calculate_daily_goal(starting_balance)
            
            # Initialize market analyst (train models if needed)
            # This would typically load historical data and train models
            
            self.is_running = True
            self.performance_metrics['last_restart'] = datetime.now()
            
            self.logger.info("Supervisor initialization complete")
            
        except Exception as e:
            self.logger.error(f"Error initializing supervisor: {e}")
            raise
            
    async def run_supervision_loop(self) -> None:
        """Main supervision loop"""
        try:
            self.logger.info("Starting supervision loop...")
            
            while self.is_running:
                try:
                    start_time = datetime.now()
                    
                    # Make strategic decision
                    action = await self.make_strategic_decision()
                    
                    # Execute decision
                    await self.execute_decision(action)
                    
                    # Record decision
                    self.decision_history.append(action)
                    
                    # Update performance metrics
                    decision_time = (datetime.now() - start_time).total_seconds()
                    self.performance_metrics['total_decisions'] += 1
                    self.performance_metrics['avg_decision_time'] = (
                        (self.performance_metrics['avg_decision_time'] * (self.performance_metrics['total_decisions'] - 1) + decision_time) /
                        self.performance_metrics['total_decisions']
                    )
                    
                    # Wait for next decision cycle
                    await asyncio.sleep(self.decision_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in supervision loop: {e}")
                    await asyncio.sleep(5)  # Brief pause on error
                    
        except Exception as e:
            self.logger.critical(f"Critical error in supervision loop: {e}")
            await self.emergency_shutdown()
            
    async def make_strategic_decision(self, price_data: Optional[pd.DataFrame] = None) -> SupervisorAction:
        """Make strategic trading decision"""
        try:
            # Gather intelligence from all agents
            market_analysis = await self._gather_market_intelligence()
            risk_status = risk_manager.get_risk_summary()
            goal_status = self.goal_risk_master.get_status_report()
            opportunities = await self.opportunity_spotter.scan_opportunities([])
            execution_status = self.executor.get_execution_summary()
            
            # Update market state
            self._update_market_state(market_analysis, opportunities, price_data)
            
            # Check emergency conditions
            emergency_action = await self._check_emergency_conditions(risk_status)
            if emergency_action:
                return emergency_action
                
            # Analyze and decide
            decision = await self._analyze_and_decide(
                market_analysis, risk_status, goal_status, opportunities, execution_status
            )
            
            self.last_decision_time = datetime.now()
            return decision
            
        except Exception as e:
            self.logger.error(f"Error making strategic decision: {e}")
            return SupervisorAction(
                decision=SupervisorDecision.PAUSE,
                confidence=1.0,
                reasoning=f"Error in decision making: {str(e)}",
                parameters={},
                timestamp=datetime.now(),
                priority=10
            )
            
    async def _gather_market_intelligence(self) -> Dict[str, Any]:
        """Gather market intelligence from analyst agent"""
        try:
            # This would typically analyze multiple symbols and timeframes
            intelligence = {
                'overall_sentiment': 0.1,
                'volatility_level': 'medium',
                'trend_direction': 'bullish',
                'key_signals': [],
                'market_health': 'good',
                'liquidity_status': 'adequate'
            }
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error gathering market intelligence: {e}")
            return {}
            
    def _update_market_state(self, market_analysis: Dict[str, Any], opportunities: List, price_data: Optional[pd.DataFrame] = None) -> None:
        """Update current market state"""
        try:
            self.market_state.overall_sentiment = market_analysis.get('overall_sentiment', 0.0)
            self.market_state.volatility_level = market_analysis.get('volatility_level', 'medium')
            self.market_state.trend_direction = market_analysis.get('trend_direction', 'sideways')
            self.market_state.liquidity_level = market_analysis.get('liquidity_status', 'medium')
            
            # Use StrategyManager to determine active strategy based on technicals
            if price_data is not None and not price_data.empty:
                strategy_info = strategy_manager.analyze_market_conditions(price_data)
                self.market_state.active_strategy = strategy_info.get('strategy_name', 'WaitStrategy')
                self.logger.info(f"Market analysis updated strategy to: {self.market_state.active_strategy}")
            
            # Adjust risk appetite based on conditions
            base_risk_appetite = 0.5
            
            if self.market_state.volatility_level == 'extreme':
                base_risk_appetite -= 0.3
            elif self.market_state.volatility_level == 'high':
                base_risk_appetite -= 0.2
                
            if self.market_state.overall_sentiment > 0.5:
                base_risk_appetite += 0.1
            elif self.market_state.overall_sentiment < -0.5:
                base_risk_appetite -= 0.1
                
            self.market_state.risk_appetite = max(0.1, min(1.0, base_risk_appetite))
            
        except Exception as e:
            self.logger.error(f"Error updating market state: {e}")
            
    async def _check_emergency_conditions(self, risk_status: Dict[str, Any]) -> Optional[SupervisorAction]:
        """Check for emergency conditions"""
        try:
            # Check drawdown
            if risk_status.get('current_drawdown', 0) > self.emergency_stop_conditions['max_drawdown']:
                return SupervisorAction(
                    decision=SupervisorDecision.CLOSE_ALL,
                    confidence=1.0,
                    reasoning=f"Emergency: Maximum drawdown ({risk_status['current_drawdown']:.1%}) exceeded",
                    parameters={'reason': 'max_drawdown'},
                    timestamp=datetime.now(),
                    priority=10
                )
                
            # Check trading status
            if risk_status.get('trading_status') == 'emergency':
                return SupervisorAction(
                    decision=SupervisorDecision.PAUSE,
                    confidence=1.0,
                    reasoning="Emergency: Risk manager triggered emergency stop",
                    parameters={},
                    timestamp=datetime.now(),
                    priority=10
                )
                
            # Check daily loss limit
            daily_loss_pct = risk_status.get('daily_loss_pct', 0)
            if daily_loss_pct > 0.9:  # 90% of daily limit
                return SupervisorAction(
                    decision=SupervisorDecision.PAUSE,
                    confidence=0.9,
                    reasoning=f"Emergency: Daily loss limit ({daily_loss_pct:.1%}) nearly reached",
                    parameters={},
                    timestamp=datetime.now(),
                    priority=9
                )
                
        except Exception as e:
            self.logger.error(f"Error checking emergency conditions: {e}")
            
        return None
        
    async def _analyze_and_decide(self,
                                market_analysis: Dict[str, Any],
                                risk_status: Dict[str, Any],
                                goal_status: Dict[str, Any],
                                opportunities: List,
                                execution_status: Dict[str, Any]) -> SupervisorAction:
        """Analyze all data and make strategic decision using LLM"""
        try:
            # Prepare context for LLM
            context = {
                'market_analysis': market_analysis,
                'risk_status': risk_status,
                'goal_status': goal_status,
                'opportunities': [vars(opp) for opp in opportunities[:5]],  # Top 5
                'execution_status': execution_status,
                'market_state': vars(self.market_state)
            }
            
            # Format message for LLM
            prompt = f"""
            As the Crypto trade bot Trading Supervisor, analyze the following market and system state to make a strategic decision.
            
            Current Context:
            {json.dumps(context, indent=2, default=str)}
            
            Decision Options:
            1. TRADE: Execute a high-confidence trading opportunity
            2. WAIT: Monitor for better conditions
            3. PAUSE: Temporarily halt trading due to risk/market issues
            4. CLOSE_ALL: Emergency position closure
            5. ADJUST_RISK: Modify risk parameters
            
            Your response must be in JSON format with the following fields:
            - decision: One of the options above (lowercase: trade, wait, pause, close_all, adjust_risk)
            - confidence: 0.0 to 1.0
            - reasoning: Detailed explanation for your decision
            - parameters: Dictionary of parameters for the decision (e.g., symbol for trade, risk_level for adjust_risk)
            - priority: 1-10 (10 is highest)
            
            Prioritize capital preservation and adherence to risk limits.
            """
            
            # Get decision from LLM
            response = await self.llm.ainvoke([
                SystemMessage(content="You are the Crypto trade bot Trading Supervisor Agent."),
                HumanMessage(content=prompt)
            ])
            
            # Parse response
            try:
                # Handle potential formatting issues in LLM response
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                    
                decision_data = json.loads(content)
                
                # Validate decision
                decision_type = SupervisorDecision(decision_data['decision'].lower())
                
                return SupervisorAction(
                    decision=decision_type,
                    confidence=float(decision_data.get('confidence', 0.5)),
                    reasoning=decision_data.get('reasoning', "LLM-driven decision"),
                    parameters=decision_data.get('parameters', {}),
                    timestamp=datetime.now(),
                    priority=int(decision_data.get('priority', 5))
                )
                
            except Exception as parse_error:
                self.logger.error(f"Error parsing LLM response: {parse_error}")
                # Fallback to score-based decision if LLM fails
                return await self._fallback_analyze_and_decide(
                    market_analysis, risk_status, goal_status, opportunities, execution_status
                )
                
        except Exception as e:
            self.logger.error(f"Error in analysis and decision: {e}")
            return SupervisorAction(
                decision=SupervisorDecision.PAUSE,
                confidence=1.0,
                reasoning=f"Analysis error: {str(e)}",
                parameters={},
                timestamp=datetime.now(),
                priority=10
            )

    async def _fallback_analyze_and_decide(self,
                                market_analysis: Dict[str, Any],
                                risk_status: Dict[str, Any],
                                goal_status: Dict[str, Any],
                                opportunities: List,
                                execution_status: Dict[str, Any]) -> SupervisorAction:
        """Score-based fallback decision making"""
        try:
            # Calculate decision factors
            risk_factor = self._calculate_risk_factor(risk_status)
            opportunity_factor = self._calculate_opportunity_factor(opportunities)
            goal_factor = self._calculate_goal_factor(goal_status)
            market_factor = self._calculate_market_factor(market_analysis)
            
            # Weight factors
            weights = {
                'risk': 0.35,
                'opportunity': 0.25,
                'goal': 0.25,
                'market': 0.15
            }
            
            # Calculate overall score
            overall_score = (
                risk_factor * weights['risk'] +
                opportunity_factor * weights['opportunity'] +
                goal_factor * weights['goal'] +
                market_factor * weights['market']
            )
            
            # Make decision based on score
            if overall_score > 0.7:
                return await self._create_trade_decision(opportunities, overall_score)
            elif overall_score > 0.4:
                return SupervisorAction(
                    decision=SupervisorDecision.WAIT,
                    confidence=overall_score,
                    reasoning="Conditions are moderate - waiting for better opportunities (Fallback)",
                    parameters={'score': overall_score},
                    timestamp=datetime.now(),
                    priority=5
                )
            else:
                return SupervisorAction(
                    decision=SupervisorDecision.PAUSE,
                    confidence=1.0 - overall_score,
                    reasoning="Conditions are unfavorable - pausing trading (Fallback)",
                    parameters={'score': overall_score},
                    timestamp=datetime.now(),
                    priority=7
                )
                
        except Exception as e:
            self.logger.error(f"Error in fallback analysis: {e}")
            return SupervisorAction(
                decision=SupervisorDecision.PAUSE,
                confidence=1.0,
                reasoning=f"Fallback analysis error: {str(e)}",
                parameters={},
                timestamp=datetime.now(),
                priority=10
            )
            
    def _calculate_risk_factor(self, risk_status: Dict[str, Any]) -> float:
        """Calculate risk factor (0-1, higher is better)"""
        try:
            risk_score = risk_status.get('risk_score', 0)
            
            # Convert risk score to factor (inverse - lower risk is better)
            risk_factor = max(0, 1 - (risk_score / 100))
            
            # Adjust for drawdown
            drawdown = risk_status.get('current_drawdown', 0)
            if drawdown > 0.15:  # 15% drawdown
                risk_factor *= 0.5
                
            return risk_factor
            
        except Exception as e:
            self.logger.error(f"Error calculating risk factor: {e}")
            return 0.5
            
    def _calculate_opportunity_factor(self, opportunities: List) -> float:
        """Calculate opportunity factor (0-1)"""
        try:
            if not opportunities:
                return 0.0
                
            # Score opportunities by confidence and urgency
            total_score = 0
            for opp in opportunities[:5]:  # Top 5 opportunities
                total_score += opp.confidence * opp.urgency
                
            # Normalize to 0-1
            max_possible_score = 5.0  # 5 opportunities * max confidence (1) * max urgency (1)
            factor = min(total_score / max_possible_score, 1.0)
            
            return factor
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity factor: {e}")
            return 0.0
            
    def _calculate_goal_factor(self, goal_status: Dict[str, Any]) -> float:
        """Calculate goal factor (0-1)"""
        try:
            progress = goal_status.get('daily_goal', {}).get('progress_percentage', 0) / 100
            
            # If behind schedule, increase urgency
            if progress < 0.3:  # Less than 30% of goal
                return 0.8
            elif progress < 0.6:  # Less than 60% of goal
                return 0.6
            else:
                return 0.4  # On track or ahead
                
        except Exception as e:
            self.logger.error(f"Error calculating goal factor: {e}")
            return 0.5
            
    def _calculate_market_factor(self, market_analysis: Dict[str, Any]) -> float:
        """Calculate market factor (0-1)"""
        try:
            factor = 0.5  # Base factor
            
            # Adjust for volatility
            volatility = market_analysis.get('volatility_level', 'medium')
            if volatility == 'low':
                factor += 0.2
            elif volatility == 'high':
                factor -= 0.1
            elif volatility == 'extreme':
                factor -= 0.3
                
            # Adjust for sentiment
            sentiment = market_analysis.get('overall_sentiment', 0)
            factor += sentiment * 0.2  # Sentiment between -1 and 1
            
            # Adjust for trend
            trend = market_analysis.get('trend_direction', 'sideways')
            if trend == 'bullish':
                factor += 0.1
            elif trend == 'bearish':
                factor -= 0.1
                
            return max(0.0, min(1.0, factor))
            
        except Exception as e:
            self.logger.error(f"Error calculating market factor: {e}")
            return 0.5
            
    async def _create_trade_decision(self, opportunities: List, overall_score: float) -> SupervisorAction:
        """Create trade decision from opportunities"""
        try:
            if not opportunities:
                return SupervisorAction(
                    decision=SupervisorDecision.WAIT,
                    confidence=0.5,
                    reasoning="No suitable opportunities found",
                    parameters={},
                    timestamp=datetime.now(),
                    priority=5
                )
                
            # Select best opportunity
            best_opp = max(opportunities, key=lambda x: x.confidence * x.urgency)
            
            # Create position plan
            position_plan = await self.goal_risk_master.create_position_plan(
                symbol=best_opp.symbol,
                side='buy' if best_opp.expected_return > 0 else 'sell',
                entry_price=0,  # Will be determined by executor
                stop_loss=0,   # Will be determined by risk manager
                take_profit=0, # Will be determined by risk manager
                confidence=best_opp.confidence
            )
            
            if position_plan:
                return SupervisorAction(
                    decision=SupervisorDecision.TRADE,
                    confidence=overall_score,
                    reasoning=f"High-confidence opportunity: {best_opp.symbol} - {best_opp.catalyst}",
                    parameters={
                        'opportunity': best_opp,
                        'position_plan': position_plan
                    },
                    timestamp=datetime.now(),
                    priority=8
                )
            else:
                return SupervisorAction(
                    decision=SupervisorDecision.WAIT,
                    confidence=0.6,
                    reasoning="Opportunity found but position plan failed validation",
                    parameters={'opportunity': best_opp},
                    timestamp=datetime.now(),
                    priority=5
                )
                
        except Exception as e:
            self.logger.error(f"Error creating trade decision: {e}")
            return SupervisorAction(
                decision=SupervisorDecision.WAIT,
                confidence=0.5,
                reasoning=f"Error creating trade decision: {str(e)}",
                parameters={},
                timestamp=datetime.now(),
                priority=5
            )
            
    async def execute_decision(self, action: SupervisorAction) -> None:
        """Execute the supervisor's decision"""
        try:
            self.logger.info(f"Executing decision: {action.decision.value} - {action.reasoning}")
            
            if action.decision == SupervisorDecision.TRADE:
                await self._execute_trade(action.parameters)
            elif action.decision == SupervisorDecision.WAIT:
                await self._execute_wait()
            elif action.decision == SupervisorDecision.PAUSE:
                await self._execute_pause(action.parameters)
            elif action.decision == SupervisorDecision.CLOSE_ALL:
                await self._execute_close_all(action.parameters)
            elif action.decision == SupervisorDecision.ADJUST_RISK:
                await self._execute_adjust_risk(action.parameters)
            elif action.decision == SupervisorDecision.RETRAIN:
                await self._execute_retrain()
                
        except Exception as e:
            self.logger.error(f"Error executing decision {action.decision.value}: {e}")
            
    async def _execute_trade(self, parameters: Dict[str, Any]) -> None:
        """Execute trade decision"""
        try:
            opportunity = parameters.get('opportunity')
            position_plan = parameters.get('position_plan')
            
            if not opportunity or not position_plan:
                self.logger.error("Missing opportunity or position plan for trade execution")
                return
                
            # Execute trade through executor
            order_id = await self.executor.execute_trade(
                symbol=position_plan.symbol,
                side=position_plan.side,
                amount=position_plan.position_size,
                stop_loss=position_plan.stop_loss,
                take_profit=position_plan.take_profit,
                leverage=position_plan.leverage
            )
            
            if order_id:
                self.performance_metrics['trades_executed'] += 1
                self.logger.info(f"Trade executed successfully: {order_id}")
            else:
                self.logger.error("Trade execution failed")
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            
    async def _execute_wait(self) -> None:
        """Execute wait decision"""
        try:
            # Monitor positions and market conditions
            await self.executor.monitor_positions()
            
            # Update market analysis
            # This would typically involve checking for new signals
            
        except Exception as e:
            self.logger.error(f"Error executing wait: {e}")
            
    async def _execute_pause(self, parameters: Dict[str, Any]) -> None:
        """Execute pause decision"""
        try:
            reason = parameters.get('reason', 'Supervisor decision')
            risk_manager.pause_trading(reason)
            self.logger.info(f"Trading paused: {reason}")
            
        except Exception as e:
            self.logger.error(f"Error executing pause: {e}")
            
    async def _execute_close_all(self, parameters: Dict[str, Any]) -> None:
        """Execute close all positions decision"""
        try:
            reason = parameters.get('reason', 'Emergency close')
            
            # Close all positions
            execution_summary = self.executor.get_execution_summary()
            positions = execution_summary.get('positions', {})
            
            for symbol in positions:
                await self.executor.close_position(symbol, reason)
                
            self.logger.critical(f"All positions closed: {reason}")
            
        except Exception as e:
            self.logger.error(f"Error executing close all: {e}")
            
    async def _execute_adjust_risk(self, parameters: Dict[str, Any]) -> None:
        """Execute risk adjustment decision"""
        try:
            # This would adjust risk parameters based on conditions
            # Implementation depends on specific requirements
            self.logger.info("Risk parameters adjusted")
            
        except Exception as e:
            self.logger.error(f"Error adjusting risk: {e}")
            
    async def _execute_retrain(self) -> None:
        """Execute model retraining"""
        try:
            # This would trigger model retraining with new data
            self.logger.info("Model retraining initiated")
            
        except Exception as e:
            self.logger.error(f"Error executing retrain: {e}")
            
    async def emergency_shutdown(self) -> None:
        """Emergency shutdown procedure"""
        try:
            self.logger.critical("Initiating emergency shutdown...")
            
            self.is_running = False
            
            # Close all positions
            await self._execute_close_all({'reason': 'Emergency shutdown'})
            
            # Cancel all orders
            # This would cancel all pending orders
            
            self.logger.critical("Emergency shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")
            
    def get_supervisor_status(self) -> Dict[str, Any]:
        """Get comprehensive supervisor status"""
        try:
            return {
                'is_running': self.is_running,
                'last_decision_time': self.last_decision_time.isoformat(),
                'decision_count': len(self.decision_history),
                'market_state': {
                    'volatility_level': self.market_state.volatility_level,
                    'trend_direction': self.market_state.trend_direction,
                    'overall_sentiment': self.market_state.overall_sentiment,
                    'risk_appetite': self.market_state.risk_appetite
                },
                'performance_metrics': self.performance_metrics,
                'recent_decisions': [
                    {
                        'decision': action.decision.value,
                        'confidence': action.confidence,
                        'reasoning': action.reasoning,
                        'timestamp': action.timestamp.isoformat()
                    }
                    for action in self.decision_history[-10:]
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting supervisor status: {e}")
            return {}
            
    def create_crewai_task(self) -> Task:
        """Create CrewAI task for supervision"""
        return Task(
            description="""Analyze the current situation and make optimal strategic decisions for the trading system.
            
            Current Situation:
            - Market State: {market_state}
            - Risk Status: {risk_status}
            - Goal Progress: {goal_progress}
            - Available Opportunities: {opportunities}
            - System Performance: {performance}
            
            Your task:
            1. Assess all available information from specialized agents
            2. Evaluate current market conditions and risk factors
            3. Consider goal progress and time constraints
            4. Make strategic decision (TRADE/WAIT/PAUSE/CLOSE_ALL/ADJUST_RISK/RETRAIN)
            5. Provide clear reasoning and confidence level
            6. Specify any parameters needed for execution
            
            Decision Framework:
            - TRADE: High-confidence opportunities with acceptable risk
            - WAIT: Moderate conditions, monitoring for better setups
            - PAUSE: High risk or unfavorable conditions
            - CLOSE_ALL: Emergency situations or critical risk levels
            - ADJUST_RISK: Modify risk parameters based on performance
            - RETRAIN: Update models when performance degrades
            
            Always prioritize capital preservation and system stability.
            Provide specific, actionable decisions with clear rationale.""",
            expected_output="Strategic decision with detailed reasoning, confidence level, and execution parameters.",
            agent=self.create_crewai_agent()
        )
