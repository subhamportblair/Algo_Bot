import time
import logging
from datetime import datetime, timedelta
import config
import auth
from strategy import SMAStrategy
from execution import place_market_order

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_instrument_token(kite, symbol, exchange):
    """
    Finds the instrument_token for a given symbol and exchange.
    """
    instruments = kite.instruments(exchange)
    for inst in instruments:
        if inst['tradingsymbol'] == symbol:
            return inst['instrument_token']
    return None

def main():
    kite = auth.get_kite_client()

    # Check for authentication
    if not config.ACCESS_TOKEN:
        print("Access Token missing!")
        print(f"Please login here to get the request_token: {auth.get_login_url()}")
        request_token = input("Enter the request_token from the redirect URL: ")
        try:
            access_token = auth.generate_session(request_token)
            print(f"Login successful! Your Access Token is: {access_token}")
            print("You can set this in your environment as KITE_ACCESS_TOKEN")
            kite.set_access_token(access_token)
        except Exception as e:
            logging.error(f"Login failed: {e}")
            return

    symbol = config.SYMBOL
    exchange = config.EXCHANGE
    window = 20
    quantity = 1

    strategy = SMAStrategy(window)
    current_position = 0 # 0 for None, 1 for Long, -1 for Short

    logging.info(f"Starting bot for {exchange}:{symbol}")

    # 1. Get instrument token
    instrument_token = get_instrument_token(kite, symbol, exchange)
    if not instrument_token:
        logging.error(f"Could not find instrument token for {symbol} on {exchange}")
        return

    # 2. Initial data fetching for SMA
    to_date = datetime.now()
    from_date = to_date - timedelta(days=5) # Fetching last 5 days for enough minute data

    try:
        historical = kite.historical_data(instrument_token, from_date, to_date, "minute")
        prices = [d['close'] for d in historical]
        logging.info(f"Fetched {len(prices)} historical candles.")
    except Exception as e:
        logging.error(f"Error fetching historical data: {e}")
        prices = []

    # 3. Main Loop
    while True:
        try:
            # Fetch latest price
            ltp_data = kite.ltp(f"{exchange}:{symbol}")
            current_price = ltp_data[f"{exchange}:{symbol}"]['last_price']

            prices.append(current_price)

            # Keep enough prices for SMA but don't let it grow indefinitely
            if len(prices) > 1000:
                prices = prices[-1000:]

            sma = strategy.calculate_sma(prices)
            signal = strategy.generate_signal(current_price, sma)

            logging.info(f"Price: {current_price}, SMA: {sma}, Signal: {signal}, Position: {current_position}")

            # Implement position management to avoid order spamming
            # For simplicity, we toggle between Long (1) and Flat (0).
            # Shorting (-1) in CNC is not possible, so we treat SELL as exiting a position.
            if signal == 'BUY' and current_position == 0:
                order_id = place_market_order(kite, symbol, exchange, kite.TRANSACTION_TYPE_BUY, quantity)
                if order_id:
                    current_position = 1
            elif signal == 'SELL' and current_position == 1:
                order_id = place_market_order(kite, symbol, exchange, kite.TRANSACTION_TYPE_SELL, quantity)
                if order_id:
                    current_position = 0

        except Exception as e:
            logging.error(f"Error in main loop: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
