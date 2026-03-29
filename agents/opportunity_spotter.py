"""
Crypto trade bot - Opportunity Spotter Agent
Detects news shocks, volatility spikes, sentiment explosions, on-chain anomalies, sudden breakouts
"""

import asyncio
import logging
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import pandas as pd
from textblob import TextBlob
import vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from crewai import Agent, Task
from langchain.llms.base import LLM
from langchain.schema import HumanMessage, SystemMessage

@dataclass
class NewsEvent:
    """News event data"""
    title: str
    content: str
    source: str
    timestamp: datetime
    sentiment_score: float
    relevance_score: float
    impact_level: str  # 'low', 'medium', 'high', 'critical'
    symbols_mentioned: List[str]
    
@dataclass
class VolatilitySpike:
    """Volatility spike detection"""
    symbol: str
    timestamp: datetime
    current_volatility: float
    historical_volatility: float
    volatility_ratio: float
    price_change: float
    volume_spike: float
    
@dataclass
class SentimentSignal:
    """Sentiment analysis signal"""
    symbol: str
    source: str  # 'twitter', 'reddit', 'news'
    sentiment_score: float
    sentiment_change: float
    volume: int
    timestamp: datetime
    confidence: float
    
@dataclass
class OnChainAnomaly:
    """On-chain anomaly detection"""
    symbol: str
    metric: str
    current_value: float
    historical_average: float
    deviation: float
    timestamp: datetime
    significance: str
    
@dataclass
class TradingOpportunity:
    """Complete trading opportunity"""
    symbol: str
    opportunity_type: str
    confidence: float
    expected_return: float
    time_horizon: str  # 'short', 'medium', 'long'
    risk_level: str
    catalyst: str
    supporting_data: Dict[str, Any]
    timestamp: datetime
    urgency: float  # 0-1, how urgent the opportunity is

class OpportunitySpotterAgent:
    """Opportunity Spotter Agent - Detects high-probability trading opportunities"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Data sources configuration
        self.news_sources = [
            'https://api.coindesk.com/v1/news/search',
            'https://min-api.cryptocompare.com/data/v2/news/',
            'https://www.alphavantage.co/query?function=NEWS_SENTIMENT'
        ]
        
        # Social media sources
        self.social_sources = {
            'twitter': 'https://api.twitter.com/2/tweets/search/recent',
            'reddit': 'https://www.reddit.com/r/cryptocurrency/new.json'
        }
        
        # Opportunity tracking
        self.recent_opportunities: List[TradingOpportunity] = []
        self.volatility_history: Dict[str, List[float]] = {}
        self.sentiment_history: Dict[str, List[float]] = {}
        
        # Thresholds
        self.volatility_spike_threshold = 2.0  # 2x normal volatility
        self.sentiment_spike_threshold = 0.3  # 30% sentiment change
        self.volume_spike_threshold = 3.0  # 3x normal volume
        
    def create_crewai_agent(self) -> Agent:
        """Create CrewAI agent instance"""
        return Agent(
            role='Opportunity Spotter',
            goal='Detect high-probability trading opportunities from news, sentiment, and market anomalies',
            backstory="""You are an expert market opportunity hunter with a sixth sense for 
            detecting profitable trading setups before they become obvious. You combine 
            real-time news analysis, social media sentiment tracking, volatility pattern 
            recognition, and on-chain data analysis to identify explosive opportunities. 
            You've built systems that consistently spot opportunities hours before the 
            crowd catches on.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[],
            system_template="""You are the Opportunity Spotter Agent for Crypto trade bot.
            
            Your core responsibilities:
            1. Monitor news sources for market-moving events
            2. Analyze social media sentiment for explosive changes
            3. Detect volatility spikes and unusual volume patterns
            4. Identify on-chain anomalies and blockchain metrics
            5. Spot sudden breakouts and technical pattern failures
            
            Opportunity Types:
            - News shocks (earnings, regulations, partnerships)
            - Sentiment explosions (viral social media, influencer mentions)
            - Volatility spikes (unusual price movements, gamma squeezes)
            - On-chain anomalies (whale movements, exchange flows)
            - Breakout patterns (support/resistance breaks, pattern completions)
            
            Always provide:
            - Opportunity confidence level (0-100%)
            - Expected return and time horizon
            - Risk assessment and entry/exit considerations
            - Urgency level and catalyst description
            
            Focus on opportunities with asymmetric risk/reward profiles."""
        )
        
    async def scan_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan for all types of opportunities"""
        try:
            opportunities = []
            
            # Parallel scanning
            tasks = [
                self._scan_news_opportunities(symbols),
                self._scan_sentiment_opportunities(symbols),
                self._scan_volatility_opportunities(symbols),
                self._scan_onchain_opportunities(symbols),
                self._scan_breakout_opportunities(symbols)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    opportunities.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Error in opportunity scanning: {result}")
                    
            # Rank opportunities by confidence and urgency
            opportunities.sort(key=lambda x: (x.confidence * x.urgency), reverse=True)
            
            # Keep only top opportunities
            top_opportunities = opportunities[:10]
            
            self.recent_opportunities = top_opportunities
            self.logger.info(f"Found {len(top_opportunities)} high-quality opportunities")
            
            return top_opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning opportunities: {e}")
            return []
            
    async def _scan_news_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan news for trading opportunities"""
        try:
            opportunities = []
            
            async with aiohttp.ClientSession() as session:
                # Fetch news from multiple sources
                news_tasks = []
                for source in self.news_sources:
                    task = self._fetch_news_from_source(session, source, symbols)
                    news_tasks.append(task)
                    
                news_results = await asyncio.gather(*news_tasks, return_exceptions=True)
                
                all_news = []
                for result in news_results:
                    if isinstance(result, list):
                        all_news.extend(result)
                        
                # Analyze news for opportunities
                for news_item in all_news:
                    opportunity = await self._analyze_news_opportunity(news_item, symbols)
                    if opportunity:
                        opportunities.append(opportunity)
                        
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning news opportunities: {e}")
            return []
            
    async def _fetch_news_from_source(self, session: aiohttp.ClientSession, source: str, symbols: List[str]) -> List[NewsEvent]:
        """Fetch news from a specific source"""
        try:
            # This is a placeholder - implement actual API calls based on source
            # For demonstration, return mock data
            mock_news = [
                NewsEvent(
                    title="Major Crypto Exchange Announces New Listing",
                    content="A leading cryptocurrency exchange announced the listing of several new trading pairs...",
                    source="coindesk",
                    timestamp=datetime.now(),
                    sentiment_score=0.6,
                    relevance_score=0.8,
                    impact_level="high",
                    symbols_mentioned=symbols[:2]
                )
            ]
            
            await asyncio.sleep(0.1)  # Simulate API delay
            return mock_news
            
        except Exception as e:
            self.logger.error(f"Error fetching news from {source}: {e}")
            return []
            
    async def _analyze_news_opportunity(self, news: NewsEvent, symbols: List[str]) -> Optional[TradingOpportunity]:
        """Analyze news item for trading opportunity"""
        try:
            # Check if news mentions our symbols
            relevant_symbols = [s for s in symbols if s.lower() in news.title.lower() or s.lower() in news.content.lower()]
            
            if not relevant_symbols:
                return None
                
            # Analyze sentiment and impact
            if news.sentiment_score > 0.5 and news.impact_level in ['high', 'critical']:
                for symbol in relevant_symbols:
                    opportunity = TradingOpportunity(
                        symbol=symbol,
                        opportunity_type='news_shock',
                        confidence=news.relevance_score * abs(news.sentiment_score),
                        expected_return=0.05 if news.impact_level == 'high' else 0.10,
                        time_horizon='short',
                        risk_level='medium',
                        catalyst=f"News: {news.title}",
                        supporting_data={
                            'source': news.source,
                            'sentiment': news.sentiment_score,
                            'impact': news.impact_level
                        },
                        timestamp=news.timestamp,
                        urgency=0.8 if news.impact_level == 'critical' else 0.6
                    )
                    return opportunity
                    
        except Exception as e:
            self.logger.error(f"Error analyzing news opportunity: {e}")
            
        return None
        
    async def _scan_sentiment_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan social media for sentiment explosions"""
        try:
            opportunities = []
            
            for symbol in symbols:
                # Analyze sentiment from multiple sources
                sentiment_signals = await self._analyze_sentiment_for_symbol(symbol)
                
                # Look for sentiment spikes
                for signal in sentiment_signals:
                    if abs(signal.sentiment_change) > self.sentiment_spike_threshold:
                        opportunity_type = 'sentiment_explosion' if signal.sentiment_change > 0 else 'sentiment_crash'
                        
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type=opportunity_type,
                            confidence=abs(signal.sentiment_change),
                            expected_return=0.03 * abs(signal.sentiment_change),
                            time_horizon='short',
                            risk_level='high' if opportunity_type == 'sentiment_crash' else 'medium',
                            catalyst=f"Sentiment spike from {signal.source}",
                            supporting_data={
                                'sentiment_score': signal.sentiment_score,
                                'sentiment_change': signal.sentiment_change,
                                'volume': signal.volume
                            },
                            timestamp=signal.timestamp,
                            urgency=0.7
                        )
                        opportunities.append(opportunity)
                        
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning sentiment opportunities: {e}")
            return []
            
    async def _analyze_sentiment_for_symbol(self, symbol: str) -> List[SentimentSignal]:
        """Analyze sentiment for a specific symbol"""
        try:
            signals = []
            
            # Mock sentiment analysis - replace with actual API calls
            mock_sentiment = SentimentSignal(
                symbol=symbol,
                source='twitter',
                sentiment_score=0.6,
                sentiment_change=0.4,
                volume=1000,
                timestamp=datetime.now(),
                confidence=0.8
            )
            
            signals.append(mock_sentiment)
            await asyncio.sleep(0.05)  # Simulate API delay
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return []
            
    async def _scan_volatility_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan for volatility spikes"""
        try:
            opportunities = []
            
            for symbol in symbols:
                # Get current volatility data
                volatility_spike = await self._detect_volatility_spike(symbol)
                
                if volatility_spike and volatility_spike.volatility_ratio > self.volatility_spike_threshold:
                    opportunity = TradingOpportunity(
                        symbol=symbol,
                        opportunity_type='volatility_spike',
                        confidence=min(volatility_spike.volatility_ratio / 3, 1.0),
                        expected_return=0.04 * min(volatility_spike.volatility_ratio / 2, 1.0),
                        time_horizon='short',
                        risk_level='high',
                        catalyst=f"Volatility spike: {volatility_spike.volatility_ratio:.1f}x normal",
                        supporting_data={
                            'volatility_ratio': volatility_spike.volatility_ratio,
                            'price_change': volatility_spike.price_change,
                            'volume_spike': volatility_spike.volume_spike
                        },
                        timestamp=volatility_spike.timestamp,
                        urgency=0.9
                    )
                    opportunities.append(opportunity)
                    
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning volatility opportunities: {e}")
            return []
            
    async def _detect_volatility_spike(self, symbol: str) -> Optional[VolatilitySpike]:
        """Detect volatility spike for a symbol"""
        try:
            # Mock volatility detection - replace with actual data
            mock_spike = VolatilitySpike(
                symbol=symbol,
                timestamp=datetime.now(),
                current_volatility=0.05,
                historical_volatility=0.02,
                volatility_ratio=2.5,
                price_change=0.03,
                volume_spike=2.0
            )
            
            await asyncio.sleep(0.05)
            return mock_spike
            
        except Exception as e:
            self.logger.error(f"Error detecting volatility spike for {symbol}: {e}")
            return None
            
    async def _scan_onchain_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan for on-chain anomalies"""
        try:
            opportunities = []
            
            for symbol in symbols:
                # Analyze on-chain metrics
                anomalies = await self._detect_onchain_anomalies(symbol)
                
                for anomaly in anomalies:
                    if anomaly.deviation > 2.0:  # 2 standard deviations
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type='onchain_anomaly',
                            confidence=min(anomaly.deviation / 3, 1.0),
                            expected_return=0.03 * min(anomaly.deviation / 2, 1.0),
                            time_horizon='medium',
                            risk_level='medium',
                            catalyst=f"On-chain anomaly: {anomaly.metric}",
                            supporting_data={
                                'metric': anomaly.metric,
                                'deviation': anomaly.deviation,
                                'significance': anomaly.significance
                            },
                            timestamp=anomaly.timestamp,
                            urgency=0.5
                        )
                        opportunities.append(opportunity)
                        
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning on-chain opportunities: {e}")
            return []
            
    async def _detect_onchain_anomalies(self, symbol: str) -> List[OnChainAnomaly]:
        """Detect on-chain anomalies for a symbol"""
        try:
            # Mock on-chain analysis - replace with actual blockchain data
            mock_anomaly = OnChainAnomaly(
                symbol=symbol,
                metric='exchange_outflow',
                current_value=1000000,
                historical_average=200000,
                deviation=3.0,
                timestamp=datetime.now(),
                significance='high'
            )
            
            await asyncio.sleep(0.05)
            return [mock_anomaly]
            
        except Exception as e:
            self.logger.error(f"Error detecting on-chain anomalies for {symbol}: {e}")
            return []
            
    async def _scan_breakout_opportunities(self, symbols: List[str]) -> List[TradingOpportunity]:
        """Scan for sudden breakouts"""
        try:
            opportunities = []
            
            for symbol in symbols:
                # Analyze price patterns for breakouts
                breakout = await self._detect_breakout(symbol)
                
                if breakout:
                    opportunity = TradingOpportunity(
                        symbol=symbol,
                        opportunity_type='breakout',
                        confidence=breakout['confidence'],
                        expected_return=breakout['expected_return'],
                        time_horizon='short',
                        risk_level='medium',
                        catalyst=f"Breakout from {breakout['pattern']}",
                        supporting_data=breakout,
                        timestamp=datetime.now(),
                        urgency=0.8
                    )
                    opportunities.append(opportunity)
                    
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error scanning breakout opportunities: {e}")
            return []
            
    async def _detect_breakout(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Detect breakout patterns"""
        try:
            # Mock breakout detection - replace with actual technical analysis
            mock_breakout = {
                'pattern': 'resistance_break',
                'confidence': 0.7,
                'expected_return': 0.04,
                'breakout_level': 100.0,
                'current_price': 102.0,
                'volume_confirmation': True
            }
            
            await asyncio.sleep(0.05)
            return mock_breakout
            
        except Exception as e:
            self.logger.error(f"Error detecting breakout for {symbol}: {e}")
            return None
            
    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text"""
        try:
            # Use VADER for sentiment analysis
            scores = self.sentiment_analyzer.polarity_scores(text)
            return scores['compound']  # Compound score between -1 and 1
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return 0.0
            
    def calculate_urgency(self, opportunity: TradingOpportunity) -> float:
        """Calculate urgency score for opportunity"""
        try:
            urgency = 0.5  # Base urgency
            
            # Time-based urgency
            if opportunity.time_horizon == 'short':
                urgency += 0.3
            elif opportunity.time_horizon == 'medium':
                urgency += 0.1
                
            # Catalyst-based urgency
            if 'news' in opportunity.opportunity_type:
                urgency += 0.2
            elif 'volatility' in opportunity.opportunity_type:
                urgency += 0.3
            elif 'breakout' in opportunity.opportunity_type:
                urgency += 0.2
                
            return min(urgency, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating urgency: {e}")
            return 0.5
            
    def get_opportunity_summary(self) -> Dict[str, Any]:
        """Get summary of recent opportunities"""
        try:
            if not self.recent_opportunities:
                return {'total': 0, 'by_type': {}, 'by_risk': {}}
                
            summary = {
                'total': len(self.recent_opportunities),
                'by_type': {},
                'by_risk': {},
                'average_confidence': np.mean([opp.confidence for opp in self.recent_opportunities]),
                'high_urgency_count': len([opp for opp in self.recent_opportunities if opp.urgency > 0.7])
            }
            
            for opp in self.recent_opportunities:
                # Count by type
                summary['by_type'][opp.opportunity_type] = summary['by_type'].get(opp.opportunity_type, 0) + 1
                
                # Count by risk level
                summary['by_risk'][opp.risk_level] = summary['by_risk'].get(opp.risk_level, 0) + 1
                
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating opportunity summary: {e}")
            return {}
            
    def create_crewai_task(self) -> Task:
        """Create CrewAI task for opportunity spotting"""
        return Task(
            description="""Scan the market for high-probability trading opportunities across multiple data sources.
            
            Your task:
            1. Monitor news feeds for market-moving events
            2. Analyze social media sentiment for explosive changes
            3. Detect unusual volatility and volume patterns
            4. Identify on-chain anomalies and blockchain metrics
            5. Spot technical breakouts and pattern failures
            
            For each opportunity found:
            - Identify the catalyst and opportunity type
            - Calculate confidence level and expected return
            - Assess risk level and time horizon
            - Determine urgency and entry considerations
            - Provide supporting data and reasoning
            
            Focus on opportunities with:
            - High confidence scores (>70%)
            - Asymmetric risk/reward profiles
            - Clear catalysts and time sensitivity
            - Multiple confirming signals
            
            Rank opportunities by combined confidence and urgency.""",
            expected_output="List of high-quality trading opportunities with detailed analysis, confidence scores, and action plans.",
            agent=self.create_crewai_agent()
        )
