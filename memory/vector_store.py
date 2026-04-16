#!/usr/bin/env python3
"""
UOTA Elite v2 - Vector Memory System
ChromaDB integration for storing and retrieving historical patterns
World-First Global Market Memory with semantic search capabilities
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# ChromaDB imports
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# ML imports
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ta

# Internal imports
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/vector_memory.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MarketPattern:
    """Market pattern data structure"""
    pattern_id: str
    symbol: str
    timeframe: str
    pattern_type: str  # 'liquidity_sweep', 'whale_movement', 'breakout', etc.
    features: Dict[str, float]
    context: Dict[str, Any]
    outcome: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None

@dataclass
class TradeMemory:
    """Trade outcome memory structure"""
    trade_id: str
    symbol: str
    action: str
    entry_price: float
    exit_price: float
    pnl: float
    risk_reward: float
    duration: timedelta
    strategy: str
    market_conditions: Dict[str, Any]
    lessons_learned: str
    timestamp: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None

class VectorMemoryManager:
    """Advanced vector memory system for pattern recognition and trade learning"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_initialized = False
        
        # ChromaDB configuration
        self.chroma_client = None
        self.patterns_collection = None
        self.trades_collection = None
        self.analysis_collection = None
        
        # Embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Collections
        self.collections = {
            'patterns': None,
            'trades': None,
            'analysis': None,
            'research': None
        }
        
        # Memory cache for performance
        self.pattern_cache = {}
        self.trade_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Pattern recognition thresholds
        self.similarity_threshold = 0.8
        self.confidence_threshold = 0.7
        
    async def initialize(self) -> None:
        """Initialize ChromaDB and collections"""
        try:
            self.logger.info("🧠 Initializing Vector Memory System")
            
            # Create data directory
            Path('data/vector_memory').mkdir(exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path="data/vector_memory/chroma",
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Initialize collections
            await self._initialize_collections()
            
            # Load existing data into cache
            await self._warm_cache()
            
            self.is_initialized = True
            self.logger.info("✅ Vector Memory System initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Vector Memory initialization failed: {e}")
            raise
    
    async def _initialize_collections(self) -> None:
        """Initialize ChromaDB collections"""
        try:
            # Patterns collection
            self.collections['patterns'] = self.chroma_client.get_or_create_collection(
                name="market_patterns",
                embedding_function=self.embedding_function,
                metadata={"description": "Historical market patterns"}
            )
            
            # Trades collection
            self.collections['trades'] = self.chroma_client.get_or_create_collection(
                name="trade_memories",
                embedding_function=self.embedding_function,
                metadata={"description": "Trade outcome memories"}
            )
            
            # Analysis collection
            self.collections['analysis'] = self.chroma_client.get_or_create_collection(
                name="market_analysis",
                embedding_function=self.embedding_function,
                metadata={"description": "Market analysis results"}
            )
            
            # Research collection
            self.collections['research'] = self.chroma_client.get_or_create_collection(
                name="research_findings",
                embedding_function=self.embedding_function,
                metadata={"description": "Research lab findings"}
            )
            
            self.logger.info("📚 ChromaDB collections initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Collection initialization failed: {e}")
            raise
    
    async def _warm_cache(self) -> None:
        """Warm up cache with recent data"""
        try:
            # Get recent patterns
            recent_patterns = await self.collections['patterns'].get(
                limit=100,
                include=["metadatas", "embeddings"]
            )
            
            # Cache patterns
            for i, pattern_id in enumerate(recent_patterns['ids']):
                self.pattern_cache[pattern_id] = {
                    'metadata': recent_patterns['metadatas'][i],
                    'embedding': recent_patterns['embeddings'][i],
                    'cached_at': datetime.now()
                }
            
            self.logger.info(f"🔥 Cache warmed with {len(self.pattern_cache)} patterns")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Cache warming failed: {e}")
    
    async def store_market_data(self, market_data: Dict[str, Any]) -> str:
        """Store market data with pattern extraction"""
        try:
            # Extract patterns from market data
            patterns = await self._extract_patterns(market_data)
            
            stored_ids = []
            for pattern in patterns:
                # Create document for embedding
                document = self._create_pattern_document(pattern)
                
                # Store in ChromaDB
                result = await self.collections['patterns'].add(
                    documents=[document],
                    metadatas=[self._pattern_to_metadata(pattern)],
                    ids=[pattern.pattern_id]
                )
                
                stored_ids.append(pattern.pattern_id)
                
                # Update cache
                self.pattern_cache[pattern.pattern_id] = {
                    'metadata': self._pattern_to_metadata(pattern),
                    'embedding': None,  # Will be populated by ChromaDB
                    'cached_at': datetime.now()
                }
            
            self.logger.info(f"📊 Stored {len(stored_ids)} market patterns")
            return stored_ids[0] if stored_ids else None
            
        except Exception as e:
            self.logger.error(f"❌ Market data storage failed: {e}")
            return None
    
    async def store_analysis(self, analysis: Dict[str, Any]) -> str:
        """Store market analysis results"""
        try:
            # Create analysis document
            document = json.dumps(analysis, default=str)
            
            # Store in analysis collection
            result = await self.collections['analysis'].add(
                documents=[document],
                metadatas=[{
                    'timestamp': datetime.now().isoformat(),
                    'symbol': analysis.get('symbol', 'UNKNOWN'),
                    'signal': analysis.get('signal', 'UNKNOWN'),
                    'confidence': analysis.get('confidence', 0.0)
                }],
                ids=[f"analysis_{datetime.now().timestamp()}"]
            )
            
            self.logger.info(f"📈 Analysis stored: {analysis.get('signal', 'UNKNOWN')}")
            return result[0]
            
        except Exception as e:
            self.logger.error(f"❌ Analysis storage failed: {e}")
            return None
    
    async def store_research(self, research_findings: Dict[str, Any]) -> str:
        """Store research lab findings"""
        try:
            # Create research document
            document = json.dumps(research_findings, default=str)
            
            # Store in research collection
            result = await self.collections['research'].add(
                documents=[document],
                metadatas=[{
                    'timestamp': datetime.now().isoformat(),
                    'research_type': research_findings.get('type', 'UNKNOWN'),
                    'patterns_found': len(research_findings.get('patterns', [])),
                    'confidence': research_findings.get('confidence', 0.0)
                }],
                ids=[f"research_{datetime.now().timestamp()}"]
            )
            
            self.logger.info(f"🔬 Research stored: {research_findings.get('type', 'UNKNOWN')}")
            return result[0]
            
        except Exception as e:
            self.logger.error(f"❌ Research storage failed: {e}")
            return None
    
    async def store_execution(self, execution_result: Dict[str, Any]) -> str:
        """Store trade execution results"""
        try:
            # Create trade memory
            trade_memory = TradeMemory(
                trade_id=execution_result.get('trade_id', f"trade_{datetime.now().timestamp()}"),
                symbol=execution_result.get('symbol', 'UNKNOWN'),
                action=execution_result.get('action', 'UNKNOWN'),
                entry_price=execution_result.get('entry_price', 0.0),
                exit_price=execution_result.get('exit_price', 0.0),
                pnl=execution_result.get('pnl', 0.0),
                risk_reward=execution_result.get('risk_reward', 0.0),
                duration=timedelta(seconds=execution_result.get('duration_seconds', 0)),
                strategy=execution_result.get('strategy', 'UNKNOWN'),
                market_conditions=execution_result.get('market_conditions', {}),
                lessons_learned=execution_result.get('lessons_learned', ''),
                timestamp=datetime.now()
            )
            
            # Create trade document
            document = self._create_trade_document(trade_memory)
            
            # Store in trades collection
            result = await self.collections['trades'].add(
                documents=[document],
                metadatas=[self._trade_to_metadata(trade_memory)],
                ids=[trade_memory.trade_id]
            )
            
            # Update cache
            self.trade_cache[trade_memory.trade_id] = {
                'metadata': self._trade_to_metadata(trade_memory),
                'embedding': None,
                'cached_at': datetime.now()
            }
            
            self.logger.info(f"💰 Trade execution stored: {trade_memory.trade_id}")
            return trade_memory.trade_id
            
        except Exception as e:
            self.logger.error(f"❌ Execution storage failed: {e}")
            return None
    
    async def find_similar_patterns(self, market_data: Dict[str, Any], 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Find similar historical patterns"""
        try:
            # Create query document
            query_document = json.dumps(market_data, default=str)
            
            # Search patterns collection
            results = await self.collections['patterns'].query(
                query_texts=[query_document],
                n_results=limit,
                include=["metadatas", "distances", "documents"]
            )
            
            # Filter by similarity threshold
            similar_patterns = []
            for i, pattern_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                
                if similarity >= self.similarity_threshold:
                    similar_patterns.append({
                        'pattern_id': pattern_id,
                        'similarity': similarity,
                        'metadata': results['metadatas'][0][i],
                        'document': results['documents'][0][i]
                    })
            
            self.logger.info(f"🔍 Found {len(similar_patterns)} similar patterns")
            return similar_patterns
            
        except Exception as e:
            self.logger.error(f"❌ Pattern search failed: {e}")
            return []
    
    async def get_trade_history(self, symbol: str = None, 
                              days_back: int = 30) -> List[Dict[str, Any]]:
        """Get historical trade data"""
        try:
            # Build filter
            where_filter = {}
            if symbol:
                where_filter['symbol'] = symbol
            
            # Get trades from collection
            results = await self.collections['trades'].get(
                where=where_filter,
                limit=1000,
                include=["metadatas", "documents"]
            )
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_trades = []
            
            for i, trade_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                trade_date = datetime.fromisoformat(metadata['timestamp'])
                
                if trade_date >= cutoff_date:
                    filtered_trades.append({
                        'trade_id': trade_id,
                        'metadata': metadata,
                        'document': results['documents'][i]
                    })
            
            self.logger.info(f"📊 Retrieved {len(filtered_trades)} trades")
            return filtered_trades
            
        except Exception as e:
            self.logger.error(f"❌ Trade history retrieval failed: {e}")
            return []
    
    async def _extract_patterns(self, market_data: Dict[str, Any]) -> List[MarketPattern]:
        """Extract patterns from market data"""
        try:
            patterns = []
            
            # Extract technical indicators
            if 'price_history' in market_data:
                df = pd.DataFrame(market_data['price_history'])
                
                # Calculate indicators
                df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                df['macd'] = ta.trend.MACD(df['close']).macd()
                df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.volatility.BollingerBands(df['close']).bollinger_hband(), ta.volatility.BollingerBands(df['close']).bollinger_mavg(), ta.volatility.BollingerBands(df['close']).bollinger_lband()
                
                # Detect patterns
                patterns.extend(self._detect_technical_patterns(df, market_data))
            
            # Detect liquidity sweeps
            if 'order_book' in market_data:
                patterns.extend(self._detect_liquidity_sweeps(market_data))
            
            # Detect whale movements
            if 'trades' in market_data:
                patterns.extend(self._detect_whale_movements(market_data))
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"❌ Pattern extraction failed: {e}")
            return []
    
    def _detect_technical_patterns(self, df: pd.DataFrame, 
                                  market_data: Dict[str, Any]) -> List[MarketPattern]:
        """Detect technical analysis patterns"""
        patterns = []
        
        try:
            # RSI divergence
            if len(df) > 20:
                rsi_divergence = self._detect_rsi_divergence(df)
                if rsi_divergence:
                    patterns.append(rsi_divergence)
            
            # Bollinger Band squeeze
            bb_squeeze = self._detect_bb_squeeze(df)
            if bb_squeeze:
                patterns.append(bb_squeeze)
            
            # MACD crossover
            macd_cross = self._detect_macd_crossover(df)
            if macd_cross:
                patterns.append(macd_cross)
                
        except Exception as e:
            self.logger.error(f"❌ Technical pattern detection failed: {e}")
        
        return patterns
    
    def _detect_liquidity_sweeps(self, market_data: Dict[str, Any]) -> List[MarketPattern]:
        """Detect liquidity sweep patterns"""
        patterns = []
        
        try:
            order_book = market_data['order_book']
            
            # Check for liquidity below/above recent highs/lows
            # Implementation would go here
            
        except Exception as e:
            self.logger.error(f"❌ Liquidity sweep detection failed: {e}")
        
        return patterns
    
    def _detect_whale_movements(self, market_data: Dict[str, Any]) -> List[MarketPattern]:
        """Detect whale movement patterns"""
        patterns = []
        
        try:
            trades = market_data['trades']
            
            # Check for large volume trades
            # Implementation would go here
            
        except Exception as e:
            self.logger.error(f"❌ Whale movement detection failed: {e}")
        
        return patterns
    
    def _detect_rsi_divergence(self, df: pd.DataFrame) -> Optional[MarketPattern]:
        """Detect RSI divergence patterns"""
        # Implementation for RSI divergence detection
        return None
    
    def _detect_bb_squeeze(self, df: pd.DataFrame) -> Optional[MarketPattern]:
        """Detect Bollinger Band squeeze patterns"""
        # Implementation for BB squeeze detection
        return None
    
    def _detect_macd_crossover(self, df: pd.DataFrame) -> Optional[MarketPattern]:
        """Detect MACD crossover patterns"""
        # Implementation for MACD crossover detection
        return None
    
    def _create_pattern_document(self, pattern: MarketPattern) -> str:
        """Create document for pattern embedding"""
        return json.dumps({
            'pattern_type': pattern.pattern_type,
            'symbol': pattern.symbol,
            'timeframe': pattern.timeframe,
            'features': pattern.features,
            'context': pattern.context
        }, default=str)
    
    def _create_trade_document(self, trade: TradeMemory) -> str:
        """Create document for trade embedding"""
        return json.dumps({
            'symbol': trade.symbol,
            'action': trade.action,
            'strategy': trade.strategy,
            'market_conditions': trade.market_conditions,
            'lessons_learned': trade.lessons_learned
        }, default=str)
    
    def _pattern_to_metadata(self, pattern: MarketPattern) -> Dict[str, Any]:
        """Convert pattern to metadata format"""
        return {
            'pattern_id': pattern.pattern_id,
            'symbol': pattern.symbol,
            'timeframe': pattern.timeframe,
            'pattern_type': pattern.pattern_type,
            'confidence': pattern.confidence,
            'timestamp': pattern.timestamp.isoformat(),
            'features': pattern.features,
            'context': pattern.context,
            'outcome': pattern.outcome
        }
    
    def _trade_to_metadata(self, trade: TradeMemory) -> Dict[str, Any]:
        """Convert trade to metadata format"""
        return {
            'trade_id': trade.trade_id,
            'symbol': trade.symbol,
            'action': trade.action,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'pnl': trade.pnl,
            'risk_reward': trade.risk_reward,
            'duration_seconds': trade.duration.total_seconds(),
            'strategy': trade.strategy,
            'market_conditions': trade.market_conditions,
            'lessons_learned': trade.lessons_learned,
            'timestamp': trade.timestamp.isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get vector memory system status"""
        try:
            # Get collection stats
            stats = {}
            for name, collection in self.collections.items():
                if collection:
                    count = await collection.count()
                    stats[name] = count
            
            return {
                'is_initialized': self.is_initialized,
                'collections': stats,
                'cache_size': {
                    'patterns': len(self.pattern_cache),
                    'trades': len(self.trade_cache)
                },
                'chroma_client': 'connected' if self.chroma_client else 'disconnected'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Status check failed: {e}")
            return {'error': str(e)}
    
    async def stop(self) -> None:
        """Stop vector memory system"""
        try:
            self.logger.info("🛑 Stopping Vector Memory System")
            
            # Clear cache
            self.pattern_cache.clear()
            self.trade_cache.clear()
            
            # Disconnect ChromaDB client
            if self.chroma_client:
                self.chroma_client = None
            
            self.is_initialized = False
            self.logger.info("✅ Vector Memory System stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping vector memory: {e}")

# Main execution for testing
async def main():
    """Test vector memory system"""
    vector_memory = VectorMemoryManager()
    
    try:
        await vector_memory.initialize()
        
        # Test storing market data
        test_data = {
            'symbol': 'BTC/USDT',
            'price': 45000.0,
            'volume': 1000000.0,
            'timestamp': datetime.now().isoformat()
        }
        
        pattern_id = await vector_memory.store_market_data(test_data)
        print(f"Stored pattern: {pattern_id}")
        
        # Test finding similar patterns
        similar = await vector_memory.find_similar_patterns(test_data)
        print(f"Found {len(similar)} similar patterns")
        
        # Get status
        status = await vector_memory.get_status()
        print(f"Status: {status}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await vector_memory.stop()

if __name__ == "__main__":
    asyncio.run(main())
