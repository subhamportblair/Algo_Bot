import datetime

class OptionsManager:
    def __init__(self, kite):
        self.kite = kite
        self.instruments = []

    def load_instruments(self):
        """Fetches NFO instruments."""
        self.instruments = self.kite.instruments("NFO")

    def get_nifty_spot(self):
        """Fetches Nifty 50 spot price."""
        quote = self.kite.ltp("NSE:NIFTY 50")
        return quote.get("NSE:NIFTY 50", {}).get("last_price")

    def get_nearest_expiry(self):
        """Identifies the nearest Nifty weekly expiry."""
        if not self.instruments:
            self.load_instruments()

        nifty_options = [i for i in self.instruments if i['name'] == 'NIFTY' and i['instrument_type'] in ['CE', 'PE']]
        expiries = sorted(list(set([i['expiry'] for i in nifty_options])))

        today = datetime.date.today()
        future_expiries = [e for e in expiries if e >= today]

        return future_expiries[0] if future_expiries else None

    def is_expiry_day(self):
        """Checks if today is the expiry day."""
        nearest_expiry = self.get_nearest_expiry()
        return nearest_expiry == datetime.date.today()

    def select_strikes(self, spot_price, offset_points=0, offset_percentage=0):
        """Selects CE and PE strikes based on offset."""
        if offset_percentage != 0:
            offset_points = spot_price * (offset_percentage / 100)

        # Round spot to nearest 50 for Nifty ATM
        atm_strike = round(spot_price / 50) * 50

        ce_strike = atm_strike + offset_points
        pe_strike = atm_strike - offset_points

        # Round to nearest 50 again
        ce_strike = round(ce_strike / 50) * 50
        pe_strike = round(pe_strike / 50) * 50

        return ce_strike, pe_strike

    def get_option_symbols(self, expiry, ce_strike, pe_strike):
        """Finds the tradingsymbols for given expiry and strikes."""
        if not self.instruments:
            self.load_instruments()

        ce_symbol = None
        pe_symbol = None

        for i in self.instruments:
            if i['name'] == 'NIFTY' and i['expiry'] == expiry:
                if i['strike'] == ce_strike and i['instrument_type'] == 'CE':
                    ce_symbol = i['tradingsymbol']
                elif i['strike'] == pe_strike and i['instrument_type'] == 'PE':
                    pe_symbol = i['tradingsymbol']

            if ce_symbol and pe_symbol:
                break

        return ce_symbol, pe_symbol
