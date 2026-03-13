class SMAStrategy:
    def __init__(self, window):
        self.window = window

    def calculate_sma(self, prices):
        """
        Calculates the Simple Moving Average for a list of prices.
        """
        if len(prices) < self.window:
            return None
        return sum(prices[-self.window:]) / self.window

    def generate_signal(self, current_price, sma):
        """
        Generates a trading signal based on the current price and SMA.
        """
        if sma is None:
            return 'HOLD'

        if current_price > sma:
            return 'BUY'
        elif current_price < sma:
            return 'SELL'
        else:
            return 'HOLD'
