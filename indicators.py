import pandas as pd
import pandas_ta as ta

def calculate_scalping_indicators(df):
    """
    Calculates 9 EMA, VWAP, and RSI (14) for a given dataframe.
    Dataframe must have 'high', 'low', 'close', 'volume'.
    """
    # 9 EMA
    df['ema_9'] = ta.ema(df['close'], length=9)

    # RSI (14)
    df['rsi_14'] = ta.rsi(df['close'], length=14)

    # VWAP
    # pandas-ta requires a datetime index for VWAP
    df.set_index(pd.to_datetime(df['date']), inplace=True)
    df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
    df.reset_index(drop=True, inplace=True)

    return df
