from strategy import SMAStrategy

def test_calculate_sma():
    strategy = SMAStrategy(window=3)
    prices = [10, 20, 30, 40, 50]

    # Last 3 are 30, 40, 50. Average = 40
    assert strategy.calculate_sma(prices) == 40

    # Not enough data
    assert strategy.calculate_sma([10, 20]) is None

def test_generate_signal():
    strategy = SMAStrategy(window=3)

    # Buy signal
    assert strategy.generate_signal(50, 40) == 'BUY'

    # Sell signal
    assert strategy.generate_signal(30, 40) == 'SELL'

    # Hold signal
    assert strategy.generate_signal(40, 40) == 'HOLD'

    # No SMA
    assert strategy.generate_signal(50, None) == 'HOLD'

if __name__ == "__main__":
    test_calculate_sma()
    test_generate_signal()
    print("Tests passed!")
