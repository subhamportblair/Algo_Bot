import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")
SYMBOL = os.getenv("TRADING_SYMBOL", "INFY")
EXCHANGE = os.getenv("TRADING_EXCHANGE", "NSE")
