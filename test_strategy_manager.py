import pandas as pd
import numpy as np
from strategy_manager import strategy_manager, TradingStrategy

def generate_mock_data(trend_type='trending'):
    """Generate mock price data for testing"""
    periods = 100
    close = np.linspace(100, 150, periods) if trend_type == 'trending' else np.full(periods, 100)
    
    if trend_type == 'ranging':
        close = 100 + np.sin(np.linspace(0, 10, periods)) * 2
    elif trend_type == 'volatile':
        close = 100 + np.random.normal(0, 10, periods)
        
    data = pd.DataFrame({
        'open': close * 0.99,
        'high': close * 1.02,
        'low': close * 0.98,
        'close': close,
        'volume': np.random.randint(100, 1000, periods)
    })
    return data

def test_strategy_switching():
    print("Testing Strategy Manager Switching Logic...")
    
    # 1. Test Trending Market
    print("\n1. Testing Trending Market (ADX > 25)")
    trending_data = generate_mock_data('trending')
    result = strategy_manager.analyze_market_conditions(trending_data)
    print(f"Recommended Strategy: {result['strategy_name']}")
    print(f"Reason: {result['reason']}")
    print(f"Metrics: {result['metrics']}")

    # 2. Test Ranging Market
    print("\n2. Testing Ranging Market (ADX < 20 and Low Volatility)")
    ranging_data = generate_mock_data('ranging')
    # Force low volatility for RangeStrategy to trigger in this mock
    ranging_data['high'] = ranging_data['close'] * 1.001
    ranging_data['low'] = ranging_data['close'] * 0.999
    result = strategy_manager.analyze_market_conditions(ranging_data)
    print(f"Recommended Strategy: {result['strategy_name']}")
    print(f"Reason: {result['reason']}")
    print(f"Metrics: {result['metrics']}")

    # 3. Test Volatile Market
    print("\n3. Testing Volatile Market (Rel Vol > Extreme Threshold)")
    volatile_data = generate_mock_data('volatile')
    # Force extreme volatility for ScalpingStrategy to trigger
    volatile_data['high'] = volatile_data['close'] * 1.1
    volatile_data['low'] = volatile_data['close'] * 0.9
    result = strategy_manager.analyze_market_conditions(volatile_data)
    print(f"Recommended Strategy: {result['strategy_name']}")
    print(f"Reason: {result['reason']}")
    print(f"Metrics: {result['metrics']}")

if __name__ == "__main__":
    test_strategy_switching()
