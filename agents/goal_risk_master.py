"""
DEDANBOT - Goal & Risk Master Agent
Calculates daily targets, position sizes, and enforces strict risk rules
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from crewai import Agent, Task
from langchain.llms.base import LLM
from langchain.schema import HumanMessage, SystemMessage

from config import config
from risk_manager import risk_manager, TradingStatus

@dataclass
class DailyGoal:
    """Daily trading goal breakdown"""
    target_profit: float
    daily_target: float
    weekly_target: float
    monthly_target: float
    max_trades_per_day: int
    max_risk_per_day: float
    progress_percentage: float
    days_remaining: int
    
@dataclass
class PositionPlan:
    """Position sizing plan"""
    symbol: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    leverage: float
    confidence_score: float
    reasoning: str

class GoalRiskMasterAgent:
    """Goal & Risk Master Agent - Central risk and goal management"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.daily_goal: Optional[DailyGoal] = None
        self.position_plans: List[PositionPlan] = []
        self.last_goal_update = datetime.now()
        self.trade_history: List[Dict] = []
        
        # Goal calculation parameters
        self.starting_balance = config.trading.starting_balance
        self.target_balance = config.trading.target_balance
        self.goal_command = config.trading.goal_command
        
    def create_crewai_agent(self) -> Agent:
        """Create CrewAI agent instance"""
        return Agent(
            role='Goal & Risk Master',
            goal='Calculate precise trading targets and enforce strict risk management rules',
            backstory="""You are an elite risk manager with 15+ years of experience in 
            quantitative trading and portfolio management. You have managed billions in 
            assets and never had a losing year. Your specialty is breaking down large 
            financial goals into precise, achievable daily targets while maintaining 
            iron-clad risk discipline. You calculate position sizes with mathematical 
            precision and enforce risk rules with zero tolerance.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
            system_template="""You are the Goal & Risk Master Agent for DEDANBOT.
            
            Your core responsibilities:
            1. Break down the user's goal into precise daily/weekly/monthly targets
            2. Calculate exact position sizes based on 1% risk rule
            3. Enforce all risk limits (daily loss 5%, max drawdown 20%)
            4. Monitor progress toward goals and adjust strategies
            5. Approve or reject trade plans based on risk criteria
            
            Risk Rules (NON-NEGOTIABLE):
            - Max risk per trade: 1% of current balance
            - Max daily loss: 5% of current balance  
            - Max drawdown: 20% from peak
            - Position size calculated using: (Balance × Risk%) / Stop Distance
            - Reduce size in high volatility markets
            
            Always provide specific numbers and calculations. Never guess."""
        )
        
    async def calculate_daily_goal(self, current_balance: float) -> DailyGoal:
        """Calculate daily trading targets based on user's goal"""
        try:
            # Parse goal command to extract targets
            monthly_target = self._parse_goal_target()
            
            # Calculate time-based targets
            days_in_month = 30
            daily_target = monthly_target / days_in_month
            weekly_target = monthly_target / 4
            
            # Calculate progress
            total_needed = self.target_balance - self.starting_balance
            current_progress = current_balance - self.starting_balance
            progress_percentage = (current_progress / total_needed) * 100 if total_needed > 0 else 0
            
            # Estimate days remaining based on current progress rate
            if progress_percentage > 0:
                days_elapsed = (datetime.now() - self.last_goal_update).days or 1
                daily_rate = progress_percentage / days_elapsed
                remaining_percentage = 100 - progress_percentage
                days_remaining = int(remaining_percentage / daily_rate) if daily_rate > 0 else 999
            else:
                days_remaining = 30
                
            # Calculate trading limits
            max_risk_per_day = current_balance * config.trading.max_daily_loss
            max_trades_per_day = min(10, int(max_risk_per_day / (current_balance * config.trading.max_risk_per_trade)))
            
            self.daily_goal = DailyGoal(
                target_profit=monthly_target,
                daily_target=daily_target,
                weekly_target=weekly_target,
                monthly_target=monthly_target,
                max_trades_per_day=max_trades_per_day,
                max_risk_per_day=max_risk_per_day,
                progress_percentage=progress_percentage,
                days_remaining=days_remaining
            )
            
            self.logger.info(f"Daily goal calculated: ${daily_target:.2f} target, {progress_percentage:.1f}% progress")
            return self.daily_goal
            
        except Exception as e:
            self.logger.error(f"Error calculating daily goal: {e}")
            raise
            
    def _parse_goal_target(self) -> float:
        """Parse monthly target from goal command"""
        try:
            goal_lower = self.goal_command.lower()
            
            # Extract percentage-based targets
            if '%' in goal_lower:
                import re
                percentage_match = re.search(r'(\d+\.?\d*)\s*%?', goal_lower)
                if percentage_match:
                    percentage = float(percentage_match.group(1))
                    return self.starting_balance * (percentage / 100)
                    
            # Extract absolute targets
            if 'to' in goal_lower:
                parts = goal_lower.split('to')
                if len(parts) > 1:
                    target_str = parts[1].split()[0].replace('$', '').replace(',', '')
                    try:
                        target = float(target_str)
                        return target - self.starting_balance
                    except:
                        pass
                        
            # Default to 15% monthly if parsing fails
            return self.starting_balance * 0.15
            
        except Exception as e:
            self.logger.error(f"Error parsing goal target: {e}")
            return self.starting_balance * 0.15
            
    async def create_position_plan(self,
                                 symbol: str,
                                 side: str,
                                 entry_price: float,
                                 stop_loss: float,
                                 take_profit: float,
                                 volatility: float = 0.0,
                                 confidence: float = 0.7) -> Optional[PositionPlan]:
        """Create detailed position plan with risk calculations"""
        try:
            # Calculate position size using risk manager
            position_size, risk_amount = risk_manager.calculate_position_size(
                entry_price, stop_loss, volatility
            )
            
            if position_size <= 0:
                self.logger.warning(f"Invalid position size for {symbol}")
                return None
                
            # Validate trade with risk manager
            is_valid, reason = risk_manager.validate_trade(
                symbol, side, position_size, entry_price, stop_loss
            )
            
            if not is_valid:
                self.logger.warning(f"Trade rejected for {symbol}: {reason}")
                return None
                
            # Calculate expected return
            if side.lower() == 'long':
                expected_return = (take_profit - entry_price) / entry_price
            else:
                expected_return = (entry_price - take_profit) / entry_price
                
            # Generate reasoning using LLM
            reasoning = await self._generate_position_reasoning(
                symbol, side, entry_price, stop_loss, take_profit, 
                position_size, risk_amount, confidence, volatility
            )
            
            position_plan = PositionPlan(
                symbol=symbol,
                side=side,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                risk_amount=risk_amount,
                leverage=config.trading.max_leverage,
                confidence_score=confidence,
                reasoning=reasoning
            )
            
            self.position_plans.append(position_plan)
            self.logger.info(f"Position plan created for {symbol}: {position_size:.4f} units, risk ${risk_amount:.2f}")
            
            return position_plan
            
        except Exception as e:
            self.logger.error(f"Error creating position plan for {symbol}: {e}")
            return None
            
    async def _generate_position_reasoning(self,
                                         symbol: str,
                                         side: str,
                                         entry_price: float,
                                         stop_loss: float,
                                         take_profit: float,
                                         position_size: float,
                                         risk_amount: float,
                                         confidence: float,
                                         volatility: float) -> str:
        """Generate AI reasoning for position plan"""
        try:
            prompt = f"""
            Analyze this trading position plan and provide reasoning:
            
            Symbol: {symbol}
            Side: {side}
            Entry: ${entry_price:.4f}
            Stop Loss: ${stop_loss:.4f}
            Take Profit: ${take_profit:.4f}
            Position Size: {position_size:.4f}
            Risk Amount: ${risk_amount:.2f}
            Confidence: {confidence:.1%}
            Volatility: {volatility:.2%}
            
            Current Balance: ${risk_manager.metrics.current_balance:.2f}
            Daily Target: ${self.daily_goal.daily_target if self.daily_goal else 0:.2f}
            
            Provide concise reasoning for this trade including:
            1. Risk/Reward ratio
            2. How it fits daily goals
            3. Risk management considerations
            4. Market context assessment
            """
            
            messages = [
                SystemMessage(content="You are an elite risk manager providing precise trade analysis."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating position reasoning: {e}")
            return f"Position plan generated with risk amount ${risk_amount:.2f} and confidence {confidence:.1%}"
            
    async def evaluate_opportunity(self,
                                 opportunity_data: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluate trading opportunity against goals and risk criteria"""
        try:
            symbol = opportunity_data.get('symbol', '')
            signal_strength = opportunity_data.get('signal_strength', 0.0)
            volatility = opportunity_data.get('volatility', 0.0)
            expected_return = opportunity_data.get('expected_return', 0.0)
            
            # Check if we're in a state to trade
            if risk_manager.trading_status != TradingStatus.TRADING:
                return False, 0.0, f"Trading status: {risk_manager.trading_status.value}"
                
            # Check daily progress
            if self.daily_goal:
                daily_progress = abs(risk_manager.metrics.daily_pnl) / max(self.daily_goal.daily_target, 1)
                
                # Reduce activity if daily target nearly reached
                if daily_progress >= 0.9:
                    return False, 0.0, "Daily target nearly reached - reducing risk"
                    
            # Risk-adjusted evaluation
            risk_score = self._calculate_risk_score(signal_strength, volatility, expected_return)
            
            # Minimum score threshold
            if risk_score < 0.6:
                return False, risk_score, f"Risk score too low: {risk_score:.2f}"
                
            # Check position limits
            if len(risk_manager.positions) >= config.trading.max_positions:
                return False, risk_score, "Maximum positions reached"
                
            # Check if within risk limits
            if risk_manager.metrics.daily_loss >= config.trading.max_daily_loss * 0.8:
                return False, risk_score, "Daily loss limit approaching"
                
            return True, risk_score, "Opportunity approved"
            
        except Exception as e:
            self.logger.error(f"Error evaluating opportunity: {e}")
            return False, 0.0, f"Evaluation error: {str(e)}"
            
    def _calculate_risk_score(self, signal_strength: float, volatility: float, expected_return: float) -> float:
        """Calculate risk-adjusted score for opportunity"""
        try:
            # Signal strength (40%)
            signal_component = signal_strength * 0.4
            
            # Volatility adjustment (20%) - lower volatility is better
            volatility_component = max(0, (1 - volatility / 0.1)) * 0.2
            
            # Expected return (30%)
            return_component = min(expected_return / 0.05, 1.0) * 0.3  # Cap at 5% expected return
            
            # Current risk state (10%) - lower risk is better
            risk_component = max(0, 1 - risk_manager.calculate_risk_score() / 100) * 0.1
            
            total_score = signal_component + volatility_component + return_component + risk_component
            return min(total_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 0.0
            
    async def update_progress(self, trade_result: Dict[str, Any]) -> None:
        """Update goal progress after trade completion"""
        try:
            self.trade_history.append(trade_result)
            
            # Update daily goal if needed
            if self.daily_goal:
                current_balance = risk_manager.metrics.current_balance
                await self.calculate_daily_goal(current_balance)
                
            # Log progress
            if self.daily_goal:
                progress_pct = self.daily_goal.progress_percentage
                self.logger.info(f"Goal progress: {progress_pct:.1f}%, Daily P&L: ${risk_manager.metrics.daily_pnl:.2f}")
                
        except Exception as e:
            self.logger.error(f"Error updating progress: {e}")
            
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive goal and risk status"""
        try:
            return {
                'daily_goal': {
                    'target_profit': self.daily_goal.target_profit if self.daily_goal else 0,
                    'daily_target': self.daily_goal.daily_target if self.daily_goal else 0,
                    'progress_percentage': self.daily_goal.progress_percentage if self.daily_goal else 0,
                    'days_remaining': self.daily_goal.days_remaining if self.daily_goal else 0,
                    'max_trades_per_day': self.daily_goal.max_trades_per_day if self.daily_goal else 0
                },
                'risk_status': risk_manager.get_risk_summary(),
                'active_positions': len(risk_manager.positions),
                'pending_plans': len(self.position_plans),
                'trades_today': len([t for t in self.trade_history if 
                                   (datetime.now() - t['timestamp']).days == 0]),
                'last_update': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error generating status report: {e}")
            return {}
            
    def create_crewai_task(self) -> Task:
        """Create CrewAI task for goal and risk management"""
        return Task(
            description="""Analyze current trading performance and calculate precise targets for tomorrow.
            
            Current situation:
            - Starting Balance: ${starting_balance}
            - Target Balance: ${target_balance}
            - Current Balance: ${current_balance}
            - Goal Command: "{goal_command}"
            - Today's P&L: ${daily_pnl}
            - Current Drawdown: ${current_drawdown}
            
            Your task:
            1. Calculate tomorrow's exact profit target
            2. Determine maximum position sizes for different risk levels
            3. Set daily trade limits based on risk rules
            4. Provide specific recommendations for goal achievement
            5. Flag any risk concerns that need attention
            
            Provide specific numbers and actionable recommendations.""",
            expected_output="Detailed daily trading plan with specific targets, position sizes, and risk management rules.",
            agent=self.create_crewai_agent()
        )
