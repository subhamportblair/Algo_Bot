class ShortStraddle:
    def __init__(self, ce_symbol, pe_symbol, quantity):
        self.ce_symbol = ce_symbol
        self.pe_symbol = pe_symbol
        self.quantity = quantity

        self.ce_entry_price = 0
        self.pe_entry_price = 0

        self.ce_ltp = 0
        self.pe_ltp = 0

        self.sl_points = 0
        self.tp_points = 0

        self.active = False

    def set_entry_prices(self, ce_price, pe_price):
        self.ce_entry_price = ce_price
        self.pe_entry_price = pe_price
        self.active = True

    def update_ltp(self, ce_ltp, pe_ltp):
        self.ce_ltp = ce_ltp
        self.pe_ltp = pe_ltp

    def calculate_pnl(self):
        if not self.active:
            return 0

        # Short Straddle: Profit if LTP < Entry (Premium Decays)
        ce_pnl = (self.ce_entry_price - self.ce_ltp) * self.quantity
        pe_pnl = (self.pe_entry_price - self.pe_ltp) * self.quantity
        return ce_pnl + pe_pnl

    def check_exit(self, sl_target, tp_target):
        """
        Returns True if exit conditions are met.
        sl_target and tp_target are in absolute currency units (P&L).
        """
        if not self.active:
            return False

        pnl = self.calculate_pnl()

        # SL is negative, e.g., -5000. If pnl <= -5000, trigger SL.
        if sl_target is not None and pnl <= sl_target:
            return True

        # TP is positive, e.g., 10000. If pnl >= 10000, trigger TP.
        if tp_target is not None and pnl >= tp_target:
            return True

        return False
