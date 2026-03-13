from options_manager import OptionsManager
from straddle_strategy import ShortStraddle
from unittest.mock import MagicMock
import datetime

def test_strike_selection():
    om = OptionsManager(MagicMock())
    # Spot 24020, offset 100
    ce, pe = om.select_strikes(24020, offset_points=100)
    assert ce == 24100 # ATM 24000 + 100
    assert pe == 23900 # ATM 24000 - 100

def test_pnl_calculation():
    strategy = ShortStraddle("CE", "PE", 50)
    strategy.set_entry_prices(100, 100) # Total 200 premium collected

    # Prices go down to 80 (Good for short)
    strategy.update_ltp(80, 80) # Total 160
    assert strategy.calculate_pnl() == (200 - 160) * 50 # 40 * 50 = 2000

    # Prices go up to 150 (Bad for short)
    strategy.update_ltp(150, 150) # Total 300
    assert strategy.calculate_pnl() == (200 - 300) * 50 # -100 * 50 = -5000

def test_exit_conditions():
    strategy = ShortStraddle("CE", "PE", 50)
    strategy.set_entry_prices(100, 100)
    strategy.update_ltp(150, 150) # P&L = -5000

    assert strategy.check_exit(-5000, 10000) is True
    assert strategy.check_exit(-6000, 10000) is False
    assert strategy.check_exit(-5000, 4000) is True # TP hit (actually P&L is -5000, but test logic)

if __name__ == "__main__":
    test_strike_selection()
    test_pnl_calculation()
    test_exit_conditions()
    print("Logic tests passed!")
