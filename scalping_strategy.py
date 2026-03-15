import logging

class ScalpingStrategy:
    def __init__(self):
        self.active_trade = None # 'BUY', 'SELL', or None

    def check_signals(self, df):
        """
        Scalping Logic:
        - BUY: Price > 9 EMA and Price > VWAP and RSI > 60
        - SELL: Price < 9 EMA and Price < VWAP and RSI < 40
        """
        if df.empty or len(df) < 14:
            return None

        last_row = df.iloc[-1]
        close = last_row['close']
        ema = last_row['ema_9']
        vwap = last_row['vwap']
        rsi = last_row['rsi_14']

        if close > ema and close > vwap and rsi > 60:
            return 'BUY'
        elif close < ema and close < vwap and rsi < 40:
            return 'SELL'

        return None

    def check_exit(self, entry_price, current_price, trade_type, sl_points, target_points):
        """
        Checks if SL or Target points are hit.
        """
        if trade_type == 'BUY':
            pnl = current_price - entry_price
        else: # SELL
            pnl = entry_price - current_price

        if pnl <= -sl_points:
            return 'SL'
        if pnl >= target_points:
            return 'TARGET'

        return None
