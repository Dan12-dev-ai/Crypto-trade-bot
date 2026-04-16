"""
Crypto trade bot - Enhanced Supervisor with Future-Proof Integration
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from crewai import Agent, Task
from langchain.llms.base import LLM

# Import future-proof modules
from self_correction_layer # import self_correction_layer  # Moved to function to avoid circular import
from n8n_guard # import n8n_guard  # Moved to function to avoid circular import
from anti_hallucination # import anti_hallucination  # Moved to function to avoid circular import, AIDecision

class EnhancedSupervisorAgent:
    """Enhanced supervisor with future-proof capabilities"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.decision_history: List[Dict] = []
        self.last_grounding_check = datetime.now()
        
    async def make_grounding_protected_decision(self, decision_data: Dict) -> Dict:
        """Make decision with anti-hallucination grounding"""
        try:
            # Create AI decision object
            ai_decision = AIDecision(
                decision_type=decision_data.get('action', 'hold'),
                symbol=decision_data.get('symbol', ''),
                confidence=decision_data.get('confidence', 0.5),
                reasoning=decision_data.get('reasoning', ''),
                expected_outcome=decision_data.get('expected_outcome', ''),
                risk_score=decision_data.get('risk_score', 0.5),
                timestamp=datetime.now()
            )
            
            # Ground the decision
            grounded_decision = await anti_hallucination.ground_ai_decision(ai_decision)
            
            # Check n8n guard status
            if n8n_guard.execution_paused:
                self.logger.warning("n8n guard has paused execution")
                return {
                    'action': 'HOLD',
                    'confidence': 0.0,
                    'reasoning': 'Execution paused by n8n guard',
                    'grounding_result': grounded_decision.verification_result.__dict__
                }
                
            # Apply self-correction insights
            mistake_probability = await self_correction_layer.predict_mistake_probability(decision_data)
            if mistake_probability > 0.7:
                self.logger.warning(f"High mistake probability ({mistake_probability:.1%}) detected")
                return {
                    'action': 'HOLD',
                    'confidence': grounded_decision.adjusted_confidence * 0.5,
                    'reasoning': f'High mistake probability ({mistake_probability:.1%})',
                    'grounding_result': grounded_decision.verification_result.__dict__
                }
                
            # Return grounded decision
            final_decision = {
                'action': grounded_decision.final_decision,
                'confidence': grounded_decision.adjusted_confidence,
                'reasoning': grounded_decision.original_decision.reasoning,
                'grounding_factors': grounded_decision.grounding_factors,
                'warnings': grounded_decision.warnings,
                'grounding_result': grounded_decision.verification_result.__dict__
            }
            
            self.decision_history.append(final_decision)
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Error in grounding protected decision: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'Decision grounding failed: {str(e)}'
            }
            
    async def analyze_trade_for_learning(self, trade_result: Dict):
        """Analyze completed trade for self-correction learning"""
        try:
            mistake = await self_correction_layer.analyze_trade_mistake(trade_result)
            if mistake:
                self.logger.info(f"Trade mistake identified: {mistake.mistake_type} - {mistake.lesson_learned}")
                
                # Get optimization suggestions
                suggestions = await self_correction_layer.get_top_suggestions(3)
                for suggestion in suggestions:
                    self.logger.info(f"Optimization suggestion: {suggestion.component} - {suggestion.reasoning}")
                    
        except Exception as e:
            self.logger.error(f"Error analyzing trade for learning: {e}")
            
    async def get_system_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        try:
            grounding_report = await anti_hallucination.get_grounding_report()
            n8n_report = await n8n_guard.get_workflow_health_report()
            risk_status = risk_manager.get_engine_status()
            
            # Get self-correction insights
            suggestions = await self_correction_layer.get_top_suggestions(5)
            
            return {
                'timestamp': datetime.now(),
                'grounding_system': grounding_report,
                'n8n_guard': n8n_report,
                'risk_engine': risk_status,
                'self_correction': {
                    'total_mistakes_analyzed': len(self_correction_layer.mistakes),
                    'active_suggestions': len(suggestions),
                    'learning_model_trained': self_correction_layer.is_trained
                },
                'overall_health': self._calculate_overall_health(grounding_report, n8n_report, risk_status)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return {'error': str(e), 'timestamp': datetime.now()}
            
    def _calculate_overall_health(self, grounding: Dict, n8n: Dict, risk: Dict) -> float:
        """Calculate overall system health score"""
        try:
            grounding_score = grounding.get('grounding_effectiveness', 0.5)
            n8n_score = n8n.get('health_score', 0.5)
            risk_score = 1.0 if not risk.get('circuit_breaker_active', False) else 0.0
            
            overall = (grounding_score + n8n_score + risk_score) / 3
            return overall
            
        except Exception as e:
            self.logger.error(f"Error calculating overall health: {e}")
            return 0.5
