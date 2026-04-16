"""
UOTA Elite v2 - Opportunity Scanner
Real-time scanning for trading opportunities across multiple data sources
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import aiohttp  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import numpy  # Moved to function to avoid circular import as np
# import pandas  # Moved to function to avoid circular import as pd
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
# import ccxt  # Moved to function to avoid circular import
from textblob import TextBlob
# import schedule  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import

from config # import config  # Moved to function to avoid circular import
from agents.opportunity_spotter import TradingOpportunity, NewsEvent, VolatilitySpike, SentimentSignal

@dataclass
class MarketData:
    """Real-time market data"""
    symbol: str
    timestamp: datetime
    price: float
    volume: float
    change_24h: float
    volatility: float
    rsi: float
    macd: float
    bollinger_position: float
    volume_ratio: float
    
@dataclass
class ScanResult:
    """Complete scan result"""
    timestamp: datetime
    opportunities: List[TradingOpportunity]
    market_data: Dict[str, MarketData]
    news_events: List[NewsEvent]
    sentiment_signals: List[SentimentSignal]
    volatility_spikes: List[VolatilitySpike]
    scan_duration: float

class OpportunityScanner:
    """Real-time opportunity scanner"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # Data sources
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.news_sources = []
        self.social_sources = []
        
        # Scanning parameters
        self.scan_interval = 30  # seconds
        self.symbols_to_scan = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT',
            'XRP/USDT', 'DOGE/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT'
        ]
        
        # Data storage
        self.market_data_history: Dict[str, List[MarketData]] = {}
        self.latest_opportunities: List[TradingOpportunity] = []
        self.scan_results: List[ScanResult] = []
        
        # Thresholds
        self.min_opportunity_confidence = 0.6
        self.volatility_spike_threshold = 2.0
        self.volume_spike_threshold = 3.0
        self.price_change_threshold = 0.05  # 5%
        
        # Initialize exchanges
        self._initialize_exchanges()
        
    def _initialize_exchanges(self) -> None:
        """Initialize exchange connections for data"""
        try:
            for exchange_name in config.get_active_exchanges():
                exchange_config = config.exchanges[exchange_name]
                
                # Create exchange instance for data only
                exchange_class = getattr(ccxt, exchange_name)
                
                exchange_params = {
                    'apiKey': exchange_config.api_key,
                    'secret': exchange_config.api_secret,
                    'sandbox': exchange_config.sandbox,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # Use spot for market data
                    }
                }
                
                if exchange_config.passphrase:
                    exchange_params['passphrase'] = exchange_config.passphrase
                    
                exchange = exchange_class(exchange_params)
                
                if exchange.check_required_credentials():
                    self.exchanges[exchange_name] = exchange
                    self.logger.info(f"Connected to {exchange_name} for data")
                    
        except Exception as e:
            self.logger.error(f"Error initializing exchanges for scanning: {e}")
            
    async def start_scanning(self) -> None:
        """Start continuous scanning"""
        try:
            self.is_running = True
            self.logger.info("Starting opportunity scanner...")
            
            while self.is_running:
                try:
                    start_time = time.time()
                    
                    # Perform comprehensive scan
                    scan_result = await self.perform_scan()
                    
                    # Store results
                    self.scan_results.append(scan_result)
                    
                    # Keep only recent results
                    if len(self.scan_results) > 100:
                        self.scan_results = self.scan_results[-100:]
                        
                    # Update latest opportunities
                    self.latest_opportunities = scan_result.opportunities
                    
                    scan_duration = time.time() - start_time
                    self.logger.info(f"Scan completed in {scan_duration:.2f}s, found {len(scan_result.opportunities)} opportunities")
                    
                    # Wait for next scan
                    await asyncio.sleep(self.scan_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in scanning loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error starting scanner: {e}")
            
    async def perform_scan(self) -> ScanResult:
        """Perform complete opportunity scan"""
        try:
            timestamp = datetime.now()
            
            # Parallel data collection
            tasks = [
                self._scan_market_data(),
                self._scan_news_events(),
                self._scan_social_sentiment(),
                self._scan_volatility_patterns(),
                self._scan_onchain_data()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            market_data = results[0] if not isinstance(results[0], Exception) else {}
            news_events = results[1] if not isinstance(results[1], Exception) else []
            sentiment_signals = results[2] if not isinstance(results[2], Exception) else []
            volatility_spikes = results[3] if not isinstance(results[3], Exception) else []
            onchain_data = results[4] if not isinstance(results[4], Exception) else {}
            
            # Generate opportunities
            opportunities = await self._generate_opportunities(
                market_data, news_events, sentiment_signals, 
                volatility_spikes, onchain_data
            )
            
            scan_duration = (datetime.now() - timestamp).total_seconds()
            
            return ScanResult(
                timestamp=timestamp,
                opportunities=opportunities,
                market_data=market_data,
                news_events=news_events,
                sentiment_signals=sentiment_signals,
                volatility_spikes=volatility_spikes,
                scan_duration=scan_duration
            )
            
        except Exception as e:
            self.logger.error(f"Error performing scan: {e}")
            return ScanResult(
                timestamp=datetime.now(),
                opportunities=[],
                market_data={},
                news_events=[],
                sentiment_signals=[],
                volatility_spikes=[],
                scan_duration=0
            )
            
    async def _scan_market_data(self) -> Dict[str, MarketData]:
        """Scan real-time market data"""
        try:
            market_data = {}
            
            for symbol in self.symbols_to_scan:
                try:
                    # Get ticker data
                    ticker = await self._get_ticker_data(symbol)
                    if not ticker:
                        continue
                        
                    # Get OHLCV for technical analysis
                    ohlcv = await self._get_ohlcv_data(symbol, '1h', 100)
                    if len(ohlcv) < 50:
                        continue
                        
                    # Calculate technical indicators
                    technicals = self._calculate_technicals(ohlcv)
                    
                    # Create market data object
                    data = MarketData(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        price=ticker['last'],
                        volume=ticker['baseVolume'] or 0,
                        change_24h=ticker.get('percentage', 0),
                        volatility=technicals['volatility'],
                        rsi=technicals['rsi'],
                        macd=technicals['macd'],
                        bollinger_position=technicals['bb_position'],
                        volume_ratio=technicals['volume_ratio']
                    )
                    
                    market_data[symbol] = data
                    
                    # Store in history
                    if symbol not in self.market_data_history:
                        self.market_data_history[symbol] = []
                    self.market_data_history[symbol].append(data)
                    
                    # Keep only recent data
                    if len(self.market_data_history[symbol]) > 1000:
                        self.market_data_history[symbol] = self.market_data_history[symbol][-1000:]
                        
                except Exception as e:
                    self.logger.error(f"Error scanning {symbol}: {e}")
                    continue
                    
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error scanning market data: {e}")
            return {}
            
    async def _get_ticker_data(self, symbol: str) -> Optional[Dict]:
        """Get ticker data for symbol"""
        try:
            for exchange_name, exchange in self.exchanges.items():
                try:
                    ticker = await exchange.fetch_ticker(symbol)
                    return ticker
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Error getting ticker for {symbol}: {e}")
            
        return None
        
    async def _get_ohlcv_data(self, symbol: str, timeframe: str, limit: int) -> List:
        """Get OHLCV data"""
        try:
            for exchange_name, exchange in self.exchanges.items():
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    return ohlcv
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Error getting OHLCV for {symbol}: {e}")
            
        return []
        
    def _calculate_technicals(self, ohlcv: List) -> Dict[str, float]:
        """Calculate technical indicators"""
        try:
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            macd = exp1 - exp2
            
            # Bollinger Bands
            sma = df['close'].rolling(20).mean()
            std = df['close'].rolling(20).std()
            bb_upper = sma + (std * 2)
            bb_lower = sma - (std * 2)
            bb_position = (df['close'].iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            
            # Volatility (ATR-based)
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            tr = high_low.combine(high_close, max).combine(low_close, max)
            atr = tr.rolling(14).mean()
            volatility = atr.iloc[-1] / df['close'].iloc[-1]
            
            # Volume ratio
            volume_sma = df['volume'].rolling(20).mean()
            volume_ratio = df['volume'].iloc[-1] / volume_sma.iloc[-1]
            
            return {
                'rsi': rsi.iloc[-1],
                'macd': macd.iloc[-1],
                'bb_position': bb_position,
                'volatility': volatility,
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating technicals: {e}")
            return {
                'rsi': 50,
                'macd': 0,
                'bb_position': 0.5,
                'volatility': 0.02,
                'volume_ratio': 1.0
            }
            
    async def _scan_news_events(self) -> List[NewsEvent]:
        """Scan for news events"""
        try:
            news_events = []
            
            # Mock news scanning - replace with actual news APIs
            mock_news = [
                NewsEvent(
                    title="Bitcoin Surges Past $50,000 Mark",
                    content="Bitcoin has successfully broken through the $50,000 resistance level...",
                    source="coindesk",
                    timestamp=datetime.now(),
                    sentiment_score=0.7,
                    relevance_score=0.9,
                    impact_level="high",
                    symbols_mentioned=["BTC/USDT"]
                )
            ]
            
            # In production, integrate with:
            # - CoinDesk API
            # - Cointelegraph API
            # - CryptoCompare News API
            # - Alpha Vantage News API
            # - Twitter API for real-time news
            
            return mock_news
            
        except Exception as e:
            self.logger.error(f"Error scanning news events: {e}")
            return []
            
    async def _scan_social_sentiment(self) -> List[SentimentSignal]:
        """Scan social media sentiment"""
        try:
            sentiment_signals = []
            
            # Mock sentiment scanning - replace with actual social APIs
            mock_sentiment = [
                SentimentSignal(
                    symbol="BTC/USDT",
                    source="twitter",
                    sentiment_score=0.6,
                    sentiment_change=0.3,
                    volume=5000,
                    timestamp=datetime.now(),
                    confidence=0.8
                )
            ]
            
            # In production, integrate with:
            # - Twitter API v2
            # - Reddit API
            # - Telegram channels
            # - Discord servers
            # - StockTwits
            
            return mock_sentiment
            
        except Exception as e:
            self.logger.error(f"Error scanning social sentiment: {e}")
            return []
            
    async def _scan_volatility_patterns(self) -> List[VolatilitySpike]:
        """Scan for volatility spikes"""
        try:
            volatility_spikes = []
            
            for symbol in self.symbols_to_scan:
                if symbol not in self.market_data_history:
                    continue
                    
                history = self.market_data_history[symbol]
                if len(history) < 50:
                    continue
                    
                # Calculate current vs historical volatility
                current_vol = history[-1].volatility
                historical_vols = [data.volatility for data in history[-50:-1]]
                historical_avg = np.mean(historical_vols)
                
                if current_vol > historical_avg * self.volatility_spike_threshold:
                    spike = VolatilitySpike(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        current_volatility=current_vol,
                        historical_volatility=historical_avg,
                        volatility_ratio=current_vol / historical_avg,
                        price_change=history[-1].change_24h,
                        volume_spike=history[-1].volume_ratio
                    )
                    volatility_spikes.append(spike)
                    
            return volatility_spikes
            
        except Exception as e:
            self.logger.error(f"Error scanning volatility patterns: {e}")
            return []
            
    async def _scan_onchain_data(self) -> Dict[str, Any]:
        """Scan on-chain data for crypto assets"""
        try:
            onchain_data = {}
            
            # Mock on-chain data - replace with actual blockchain APIs
            for symbol in self.symbols_to_scan:
                if '/USDT' in symbol:
                    base_asset = symbol.split('/')[0]
                    onchain_data[base_asset] = {
                        'exchange_flow': np.random.normal(0, 1),
                        'whale_movements': np.random.poisson(5),
                        'active_addresses': np.random.randint(1000, 10000),
                        'network_activity': 'normal'
                    }
                    
            # In production, integrate with:
            # - Glassnode API
            # - CryptoQuant API
            # - Dune Analytics
            # - Etherscan API
            # - Blockchain.com API
            
            return onchain_data
            
        except Exception as e:
            self.logger.error(f"Error scanning on-chain data: {e}")
            return {}
            
    async def _generate_opportunities(self,
                                     market_data: Dict[str, MarketData],
                                     news_events: List[NewsEvent],
                                     sentiment_signals: List[SentimentSignal],
                                     volatility_spikes: List[VolatilitySpike],
                                     onchain_data: Dict[str, Any]) -> List[TradingOpportunity]:
        """Generate trading opportunities from all data sources"""
        try:
            opportunities = []
            
            # Generate opportunities from market data
            for symbol, data in market_data.items():
                opp = await self._analyze_market_opportunity(symbol, data)
                if opp:
                    opportunities.append(opp)
                    
            # Generate opportunities from news events
            for news in news_events:
                for symbol in news.symbols_mentioned:
                    if symbol in market_data:
                        opp = await self._analyze_news_opportunity(news, symbol, market_data[symbol])
                        if opp:
                            opportunities.append(opp)
                            
            # Generate opportunities from sentiment
            for sentiment in sentiment_signals:
                if sentiment.symbol in market_data:
                    opp = await self._analyze_sentiment_opportunity(sentiment, market_data[sentiment.symbol])
                    if opp:
                        opportunities.append(opp)
                        
            # Generate opportunities from volatility spikes
            for spike in volatility_spikes:
                if spike.symbol in market_data:
                    opp = await self._analyze_volatility_opportunity(spike, market_data[spike.symbol])
                    if opp:
                        opportunities.append(opp)
                        
            # Rank and filter opportunities
            opportunities.sort(key=lambda x: x.confidence * x.urgency, reverse=True)
            
            # Filter by minimum confidence
            filtered_opportunities = [
                opp for opp in opportunities 
                if opp.confidence >= self.min_opportunity_confidence
            ]
            
            return filtered_opportunities[:10]  # Return top 10
            
        except Exception as e:
            self.logger.error(f"Error generating opportunities: {e}")
            return []
            
    async def _analyze_market_opportunity(self, symbol: str, data: MarketData) -> Optional[TradingOpportunity]:
        """Analyze market data for opportunities"""
        try:
            confidence = 0.0
            catalyst = ""
            expected_return = 0.0
            
            # RSI-based opportunities
            if data.rsi < 30:
                confidence += 0.3
                catalyst += "RSI oversold; "
                expected_return += 0.02
            elif data.rsi > 70:
                confidence += 0.3
                catalyst += "RSI overbought; "
                expected_return -= 0.02
                
            # Bollinger Band opportunities
            if data.bollinger_position < 0.1:
                confidence += 0.2
                catalyst += "Near lower Bollinger Band; "
                expected_return += 0.015
            elif data.bollinger_position > 0.9:
                confidence += 0.2
                catalyst += "Near upper Bollinger Band; "
                expected_return -= 0.015
                
            # Volume spike opportunities
            if data.volume_ratio > self.volume_spike_threshold:
                confidence += 0.2
                catalyst += f"Volume spike {data.volume_ratio:.1f}x; "
                expected_return += 0.01
                
            # Price momentum
            if abs(data.change_24h) > self.price_change_threshold:
                confidence += 0.3
                catalyst += f"Strong momentum {data.change_24h:.1%}; "
                expected_return += data.change_24h * 0.5
                
            if confidence >= self.min_opportunity_confidence:
                side = 'buy' if expected_return > 0 else 'sell'
                
                return TradingOpportunity(
                    symbol=symbol,
                    opportunity_type='technical_signal',
                    confidence=confidence,
                    expected_return=abs(expected_return),
                    time_horizon='short',
                    risk_level='medium',
                    catalyst=catalyst,
                    supporting_data={
                        'rsi': data.rsi,
                        'bb_position': data.bollinger_position,
                        'volume_ratio': data.volume_ratio,
                        'price_change': data.change_24h
                    },
                    timestamp=data.timestamp,
                    urgency=0.6
                )
                
        except Exception as e:
            self.logger.error(f"Error analyzing market opportunity for {symbol}: {e}")
            
        return None
        
    async def _analyze_news_opportunity(self, news: NewsEvent, symbol: str, data: MarketData) -> Optional[TradingOpportunity]:
        """Analyze news-based opportunity"""
        try:
            if news.impact_level not in ['high', 'critical']:
                return None
                
            confidence = news.relevance_score * abs(news.sentiment_score)
            
            if confidence < self.min_opportunity_confidence:
                return None
                
            side = 'buy' if news.sentiment_score > 0 else 'sell'
            expected_return = 0.03 if news.impact_level == 'high' else 0.05
            
            return TradingOpportunity(
                symbol=symbol,
                opportunity_type='news_event',
                confidence=confidence,
                expected_return=expected_return,
                time_horizon='short',
                risk_level='medium',
                catalyst=f"News: {news.title}",
                supporting_data={
                    'news_source': news.source,
                    'sentiment': news.sentiment_score,
                    'impact': news.impact_level
                },
                timestamp=news.timestamp,
                urgency=0.8
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing news opportunity: {e}")
            return None
        
    async def _analyze_sentiment_opportunity(self, sentiment: SentimentSignal, data: MarketData) -> Optional[TradingOpportunity]:
        """Analyze sentiment-based opportunity"""
        try:
            if abs(sentiment.sentiment_change) < 0.2:
                return None
                
            confidence = sentiment.confidence * abs(sentiment.sentiment_change)
            
            if confidence < self.min_opportunity_confidence:
                return None
                
            side = 'buy' if sentiment.sentiment_change > 0 else 'sell'
            expected_return = abs(sentiment.sentiment_change) * 0.05
            
            return TradingOpportunity(
                symbol=sentiment.symbol,
                opportunity_type='sentiment_shift',
                confidence=confidence,
                expected_return=expected_return,
                time_horizon='short',
                risk_level='high',
                catalyst=f"Sentiment shift from {sentiment.source}",
                supporting_data={
                    'sentiment_score': sentiment.sentiment_score,
                    'sentiment_change': sentiment.sentiment_change,
                    'volume': sentiment.volume
                },
                timestamp=sentiment.timestamp,
                urgency=0.7
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment opportunity: {e}")
            return None
            
    async def _analyze_volatility_opportunity(self, spike: VolatilitySpike, data: MarketData) -> Optional[TradingOpportunity]:
        """Analyze volatility spike opportunity"""
        try:
            confidence = min(spike.volatility_ratio / 3, 1.0)
            
            if confidence < self.min_opportunity_confidence:
                return None
                
            # Determine direction based on price movement
            side = 'buy' if spike.price_change > 0 else 'sell'
            expected_return = abs(spike.price_change) * 0.3
            
            return TradingOpportunity(
                symbol=spike.symbol,
                opportunity_type='volatility_spike',
                confidence=confidence,
                expected_return=expected_return,
                time_horizon='short',
                risk_level='high',
                catalyst=f"Volatility spike {spike.volatility_ratio:.1f}x",
                supporting_data={
                    'volatility_ratio': spike.volatility_ratio,
                    'price_change': spike.price_change,
                    'volume_spike': spike.volume_spike
                },
                timestamp=spike.timestamp,
                urgency=0.9
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing volatility opportunity: {e}")
            return None
            
    def stop_scanning(self) -> None:
        """Stop the scanner"""
        self.is_running = False
        self.logger.info("Opportunity scanner stopped")
        
    def get_high_confidence_opportunities(self, min_confidence: float = 0.8, markets: List[str] = None) -> List[TradingOpportunity]:
        """Get high-confidence opportunities using SMC (Smart Money Concepts) analysis"""
        try:
            if markets is None:
                markets = list(self.latest_market_data.keys())
            
            high_confidence_opps = []
            
            for market in markets:
                if market not in self.latest_market_data:
                    continue
                    
                market_data = self.latest_market_data[market]
                
                # SMC Analysis: Identify Order Blocks & Liquidity Sweeps
                opp = self._analyze_smc_opportunity(market, market_data, min_confidence)
                if opp and opp.confidence_score >= min_confidence:
                    high_confidence_opps.append(opp)
            
            # Sort by confidence and return top opportunities
            high_confidence_opps.sort(key=lambda x: x.confidence_score, reverse=True)
            
            self.logger.info(f"🎯 Found {len(high_confidence_opps)} high-confidence opportunities (min: {min_confidence})")
            return high_confidence_opps
            
        except Exception as e:
            self.logger.error(f"Error getting high-confidence opportunities: {e}")
            return []
    
    def _analyze_smc_opportunity(self, symbol: str, market_data: MarketData, min_confidence: float) -> Optional[TradingOpportunity]:
        """Analyze using Smart Money Concepts - Order Blocks & Liquidity Sweeps"""
        try:
            # SMC Signal 1: Order Block Identification
            order_block_signal = self._identify_order_block(symbol, market_data)
            
            # SMC Signal 2: Liquidity Sweep Detection  
            liquidity_sweep_signal = self._detect_liquidity_sweep(symbol, market_data)
            
            # SMC Signal 3: Market Structure Shift
            structure_signal = self._analyze_market_structure(symbol, market_data)
            
            # Combine SMC signals for high confidence
            combined_confidence = (
                order_block_signal * 0.4 +      # Order blocks weighted highest
                liquidity_sweep_signal * 0.35 +  # Liquidity sweeps
                structure_signal * 0.25           # Market structure
            )
            
            if combined_confidence < min_confidence:
                return None
            
            # Determine trade direction based on SMC analysis
            if order_block_signal > 0.7 and liquidity_sweep_signal > 0.6:
                trade_side = 'buy'  # Bullish order block + sweep
                entry_price = market_data.price * 0.998  # Slight discount
                stop_loss = market_data.price * 0.992
                take_profit = market_data.price * 1.015
            elif order_block_signal < 0.3 and liquidity_sweep_signal < 0.4:
                trade_side = 'sell'  # Bearish order block + sweep
                entry_price = market_data.price * 1.002  # Slight premium
                stop_loss = market_data.price * 1.008
                take_profit = market_data.price * 0.985
            else:
                return None  # No clear SMC setup
            
            return TradingOpportunity(
                symbol=symbol,
                side=trade_side,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence_score=combined_confidence,
                time_horizon='short',
                risk_level='medium',
                catalyst='SMC Order Block & Liquidity Sweep',
                supporting_data={
                    'order_block_signal': order_block_signal,
                    'liquidity_sweep_signal': liquidity_sweep_signal,
                    'structure_signal': structure_signal,
                    'rsi': market_data.rsi,
                    'volume_ratio': market_data.volume_ratio,
                    'volatility': market_data.volatility
                },
                timestamp=datetime.now(),
                urgency=combined_confidence
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing SMC opportunity for {symbol}: {e}")
            return None
    
    def _identify_order_block(self, symbol: str, market_data: MarketData) -> float:
        """Identify Order Block patterns (Smart Money accumulation zones)"""
        try:
            # Order Block characteristics:
            # 1. Strong momentum move followed by consolidation
            # 2. High volume at the turning point
            # 3. RSI showing exhaustion before reversal
            
            momentum_score = min(abs(market_data.change_24h) / 0.05, 1.0)  # 5% move = full score
            volume_score = min(market_data.volume_ratio / 2.0, 1.0)  # 2x volume = full score
            rsi_exhaustion = 1.0 - abs(market_data.rsi - 50) / 50  # RSI near 50 = exhaustion
            
            # Bollinger Band position (consolidation zone)
            bb_position = abs(market_data.bollinger_position)
            consolidation_score = 1.0 - bb_position  # Near middle = consolidation
            
            order_block_confidence = (
                momentum_score * 0.3 +
                volume_score * 0.3 +
                rsi_exhaustion * 0.2 +
                consolidation_score * 0.2
            )
            
            return min(order_block_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error identifying order block for {symbol}: {e}")
            return 0.0
    
    def _detect_liquidity_sweep(self, symbol: str, market_data: MarketData) -> float:
        """Detect liquidity sweep patterns (Smart Money stop hunting)"""
        try:
            # Liquidity Sweep characteristics:
            # 1. Sharp price spike beyond key levels
            # 2. Quick reversal after spike
            # 3. High volatility during sweep
            
            volatility_spike = min(market_data.volatility / 0.03, 1.0)  # 3% vol = full score
            price_extreme = abs(market_data.bollinger_position)  # Price at BB extremes
            
            # MACD divergence (reversal signal)
            macd_divergence = abs(market_data.macd) / 0.002  # Normalized MACD
            divergence_score = min(macd_divergence, 1.0)
            
            # Volume confirmation (low volume on sweep = manipulation)
            volume_manipulation = 1.0 - min(market_data.volume_ratio / 0.5, 1.0)  # Low vol = manipulation
            
            liquidity_sweep_confidence = (
                volatility_spike * 0.4 +
                price_extreme * 0.3 +
                divergence_score * 0.2 +
                volume_manipulation * 0.1
            )
            
            return min(liquidity_sweep_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error detecting liquidity sweep for {symbol}: {e}")
            return 0.0
    
    def _analyze_market_structure(self, symbol: str, market_data: MarketData) -> float:
        """Analyze market structure for Smart Money patterns"""
        try:
            # Market Structure analysis:
            # 1. Trend alignment with volume
            # 2. Support/Respectance levels
            # 3. Volatility normalization
            
            trend_strength = abs(market_data.change_24h) / 0.02  # 2% trend = full score
            volume_confirmation = min(market_data.volume_ratio / 1.5, 1.0)  # 1.5x volume = confirmation
            
            # RSI momentum (not overbought/oversold)
            rsi_optimal = 1.0 - abs(market_data.rsi - 50) / 30  # RSI 20-80 = optimal
            rsi_score = max(rsi_optimal, 0)
            
            # Volatility normalization (not too volatile, not too flat)
            optimal_volatility = 1.0 - abs(market_data.volatility - 0.02) / 0.02  # 2% vol = optimal
            vol_score = max(optimal_volatility, 0)
            
            structure_confidence = (
                trend_strength * 0.4 +
                volume_confirmation * 0.3 +
                rsi_score * 0.2 +
                vol_score * 0.1
            )
            
            return min(structure_confidence, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error analyzing market structure for {symbol}: {e}")
            return 0.0

    def get_latest_opportunities(self) -> List[TradingOpportunity]:
        """Get latest opportunities"""
        return self.latest_opportunities
        
    def get_scan_summary(self) -> Dict[str, Any]:
        """Get summary of recent scans"""
        try:
            if not self.scan_results:
                return {'total_scans': 0}
                
            recent_scans = self.scan_results[-10:]  # Last 10 scans
            
            total_opportunities = sum(len(scan.opportunities) for scan in recent_scans)
            avg_scan_duration = np.mean([scan.scan_duration for scan in recent_scans])
            
            opportunity_types = {}
            for scan in recent_scans:
                for opp in scan.opportunities:
                    opportunity_types[opp.opportunity_type] = opportunity_types.get(opp.opportunity_type, 0) + 1
                    
            return {
                'total_scans': len(self.scan_results),
                'recent_opportunities': total_opportunities,
                'avg_scan_duration': avg_scan_duration,
                'opportunity_types': opportunity_types,
                'last_scan': self.scan_results[-1].timestamp.isoformat() if self.scan_results else None,
                'symbols_tracked': len(self.market_data_history)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating scan summary: {e}")
            return {}

# Global scanner instance
opportunity_scanner = OpportunityScanner()

if __name__ == "__main__":
    # Test scanner
    async def test_scanner():
        scanner = OpportunityScanner()
        
        # Perform single scan
        result = await scanner.perform_scan()
        
        print(f"Scan completed: {len(result.opportunities)} opportunities found")
        for opp in result.opportunities:
            print(f"- {opp.symbol}: {opp.opportunity_type} (confidence: {opp.confidence:.2f})")
            
    asyncio.run(test_scanner())
