import pandas as pd
from indicators import calculate_scalping_indicators
from scalping_strategy import ScalpingStrategy
import datetime

def test_scalping_indicators():
    # Create mock data
    data = {
        'date': [datetime.datetime.now() - datetime.timedelta(minutes=i) for i in range(20)],
        'high': [105] * 20,
        'low': [95] * 20,
        'close': [100 + i for i in range(20)],
        'volume': [1000] * 20
    }
    df = pd.DataFrame(data)
    df = calculate_scalping_indicators(df)

    assert 'ema_9' in df.columns
    assert 'rsi_14' in df.columns
    assert 'vwap' in df.columns

def test_scalping_signals():
    strategy = ScalpingStrategy()

    # Mock DF that triggers BUY
    # Price > EMA, Price > VWAP, RSI > 60
    data = {
        'close': [110] * 20,
        'ema_9': [100] * 20,
        'vwap': [100] * 20,
        'rsi_14': [70] * 20
    }
    df = pd.DataFrame(data)
    assert strategy.check_signals(df) == 'BUY'

    # Mock DF that triggers SELL
    data['rsi_14'] = [30] * 20
    data['close'] = [90] * 20
    df = pd.DataFrame(data)
    assert strategy.check_signals(df) == 'SELL'

if __name__ == "__main__":
    test_scalping_indicators()
    test_scalping_signals()
    print("Scalping logic tests passed!")
