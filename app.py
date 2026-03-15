from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import asyncio
import auth
import config
import datetime
from options_manager import OptionsManager
from straddle_strategy import ShortStraddle
from scalping_strategy import ScalpingStrategy
from indicators import calculate_scalping_indicators
from execution import place_market_order
import logging
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared State
kite = auth.get_kite_client()
om = OptionsManager(kite)
straddle = None
sl_limit = -5000
tp_limit = 10000
running = False
nifty_spot = 0
logs = []

# Scalping State
scalp_strategy = ScalpingStrategy()
scalp_running = False
scalp_active_leg = None # symbol
scalp_entry_price = 0
scalp_sl_limit = 5
scalp_tp_limit = 10
scalp_qty = 25 # 1 lot

async def trading_loop():
    global straddle, running, nifty_spot, logs
    global scalp_running, scalp_active_leg, scalp_entry_price, scalp_qty

    counter = 0
    while True:
        try:
            # Update spot price regardless of running state
            nifty_spot = om.get_nifty_spot() or 0

            # --- 1. Straddle Logic ---
            if running and straddle:
                # 1. Fetch Leg Prices
                quotes = kite.ltp([f"NFO:{straddle.ce_symbol}", f"NFO:{straddle.pe_symbol}"])
                ce_ltp = quotes.get(f"NFO:{straddle.ce_symbol}", {}).get("last_price", 0)
                pe_ltp = quotes.get(f"NFO:{straddle.pe_symbol}", {}).get("last_price", 0)

                straddle.update_ltp(ce_ltp, pe_ltp)
                pnl = straddle.calculate_pnl()

                logging.info(f"P&L: {pnl}")

                # 2. Check Exit Conditions
                if straddle.check_exit(sl_limit, tp_limit):
                    logs.append(f"SL/TP Hit! P&L: {pnl}. Squaring off...")
                    square_off()

            # --- 2. Scalping Logic ---
            if scalp_running:
                # Scalping logic usually requires minute candles for indicators
                # To avoid rate limits, we fetch historical data every 60 seconds
                if not scalp_active_leg and counter % 60 == 0:
                    # Check for ENTRY
                    inst_token = 256265 # Nifty 50 token
                    hist = kite.historical_data(inst_token, datetime.datetime.now()-datetime.timedelta(days=2), datetime.datetime.now(), "minute")
                    df = pd.DataFrame(hist)
                    df = calculate_scalping_indicators(df)
                    signal = scalp_strategy.check_signals(df)

                    if signal:
                        # Entry logic: BUY ATM options
                        ce, pe = om.get_atm_options()
                        symbol = ce if signal == 'BUY' else pe
                        place_market_order(kite, symbol, "NFO", kite.TRANSACTION_TYPE_BUY, scalp_qty)

                        scalp_active_leg = symbol
                        scalp_entry_price = kite.ltp(f"NFO:{symbol}").get(f"NFO:{symbol}", {}).get("last_price", 0)
                        logs.append(f"Scalp Entry: {symbol} @ {scalp_entry_price}")
                else:
                    # Check for EXIT
                    curr_price = kite.ltp(f"NFO:{scalp_active_leg}").get(f"NFO:{scalp_active_leg}", {}).get("last_price", 0)
                    # For simplicity, we exit if strategy says opposite signal OR SL/Target hit
                    exit_reason = scalp_strategy.check_exit(scalp_entry_price, curr_price, 'BUY', scalp_sl_limit, scalp_tp_limit)
                    if exit_reason:
                        place_market_order(kite, scalp_active_leg, "NFO", kite.TRANSACTION_TYPE_SELL, scalp_qty)
                        logs.append(f"Scalp Exit: {scalp_active_leg} Reason: {exit_reason}")
                        scalp_active_leg = None

        except Exception as e:
            logging.error(f"Error in trading loop: {e}")

        counter += 1
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_loop())

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status")
async def get_status():
    global straddle, nifty_spot, running
    global scalp_running, scalp_active_leg, scalp_entry_price

    pnl = straddle.calculate_pnl() if straddle else 0

    scalp_pnl = 0
    scalp_ltp = 0
    if scalp_active_leg:
        scalp_ltp = kite.ltp(f"NFO:{scalp_active_leg}").get(f"NFO:{scalp_active_leg}", {}).get("last_price", 0)
        # Scalping is BUY only for simplicity in this example
        scalp_pnl = (scalp_ltp - scalp_entry_price) * scalp_qty

    return {
        "login_url": auth.get_login_url(),
        "nifty_spot": nifty_spot,
        "ce_symbol": straddle.ce_symbol if straddle else "-",
        "pe_symbol": straddle.pe_symbol if straddle else "-",
        "ce_ltp": straddle.ce_ltp if straddle else 0,
        "pe_ltp": straddle.pe_ltp if straddle else 0,
        "pnl": pnl,
        "running": running,
        "sl": sl_limit,
        "tp": tp_limit,
        "scalp": {
            "running": scalp_running,
            "symbol": scalp_active_leg or "-",
            "entry_price": scalp_entry_price,
            "ltp": scalp_ltp,
            "pnl": scalp_pnl
        }
    }

@app.post("/start")
async def start_strategy(
    offset_points: float = Form(0),
    offset_percentage: float = Form(0),
    sl: float = Form(-5000),
    tp: float = Form(10000),
    expiry_only: str = Form("off")
):
    global straddle, running, sl_limit, tp_limit, logs
    is_expiry_only = (expiry_only == "on")

    sl_limit = sl
    tp_limit = tp

    try:
        if is_expiry_only and not om.is_expiry_day():
            return JSONResponse({"status": "error", "message": "Today is not expiry day. Disable 'Expiry Only' to proceed."})

        spot = om.get_nifty_spot()
        ce_strike, pe_strike = om.select_strikes(spot, offset_points=offset_points, offset_percentage=offset_percentage)
        expiry = om.get_nearest_expiry()
        ce_symbol, pe_symbol = om.get_option_symbols(expiry, ce_strike, pe_strike)

        # Place Sell Orders (Short Straddle)
        ce_order = place_market_order(kite, ce_symbol, "NFO", kite.TRANSACTION_TYPE_SELL, 50)
        pe_order = place_market_order(kite, pe_symbol, "NFO", kite.TRANSACTION_TYPE_SELL, 50)

        if not ce_order or not pe_order:
             return JSONResponse({"status": "error", "message": "Failed to place one or more orders."})

        # Fetch Entry Prices
        quotes = kite.ltp([f"NFO:{ce_symbol}", f"NFO:{pe_symbol}"])
        ce_entry = quotes.get(f"NFO:{ce_symbol}", {}).get("last_price", 0)
        pe_entry = quotes.get(f"NFO:{pe_symbol}", {}).get("last_price", 0)

        straddle = ShortStraddle(ce_symbol, pe_symbol, 50)
        straddle.set_entry_prices(ce_entry, pe_entry)
        running = True
        logs.append(f"Started Straddle: CE {ce_symbol} @ {ce_entry}, PE {pe_symbol} @ {pe_entry}")

        return JSONResponse({"status": "success"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/auth")
async def authenticate(request_token: str = Form(...)):
    global kite
    try:
        access_token = auth.generate_session(request_token)
        kite.set_access_token(access_token)
        return {"status": "success", "access_token": access_token}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

@app.post("/scalp/start")
async def start_scalping(qty_lots: int = Form(1), scalp_sl: float = Form(5), scalp_target: float = Form(10)):
    global scalp_running, scalp_qty, scalp_sl_limit, scalp_tp_limit
    scalp_running = True
    scalp_qty = qty_lots * 25 # Current Nifty lot size
    scalp_sl_limit = scalp_sl
    scalp_tp_limit = scalp_target
    return {"status": "success"}

@app.post("/scalp/stop")
async def stop_scalping():
    global scalp_running, scalp_active_leg
    if scalp_active_leg:
        # Exit active position
        place_market_order(kite, scalp_active_leg, "NFO", kite.TRANSACTION_TYPE_SELL, scalp_qty)
        scalp_active_leg = None
    scalp_running = False
    return {"status": "success"}

@app.post("/squareoff")
async def squareoff_endpoint():
    square_off()
    return {"status": "success"}

def square_off():
    global straddle, running, kite
    if straddle and running:
        # Buy back to exit short straddle
        place_market_order(kite, straddle.ce_symbol, "NFO", kite.TRANSACTION_TYPE_BUY, straddle.quantity)
        place_market_order(kite, straddle.pe_symbol, "NFO", kite.TRANSACTION_TYPE_BUY, straddle.quantity)
        running = False
        straddle = None
