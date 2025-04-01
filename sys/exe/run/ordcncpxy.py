import sys
import logging
import asyncio
import yfinance as yf
import telegram
from login_get_kite import get_kite
from cnstpxy import CNFG, log_path
from fundpxy import calculate_decision
from toolkit.currency import round_to_paise

# Hardcoded constants
dct = CNFG["telegram"]
BOT_TOKEN = dct["bot_token"]
USER_ID = dct["chat_id"]

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def send_telegram_message(bot_token, user_id, message_text):
    bot = telegram.Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=user_id, text=message_text)
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")

def get_ltp_yf(random_symbol):
    try:
        ticker = yf.Ticker(f"{random_symbol}.NS")  # Append '.NS' for NSE tickers
        ltp_nse = ticker.history(period='1d')['Close'].iloc[-1]  # Get the last closing price
        logger.debug(f"Last Traded Price (LTP) for {random_symbol}: {ltp_nse}")
        return ltp_nse
    except Exception as e:
        logger.error(f"Error fetching LTP for {random_symbol}: {str(e)}")
        return None
    
def place_buy_order(random_symbol):
    try:
        # Fetch trading decision and available cash
        decision, optdecision, available_cash, live_balance, limit = calculate_decision()
        logger.debug(f"Decision: {decision}, Available Cash: {available_cash}, Live Balance: {live_balance}, Limit: {limit}")

        if decision != "YES":
            logger.info("Decision is not 'YES', skipping order placement.")
            return
        
        # Redirect stdout and stderr to a file
        with open(f'{log_path}broker_errors.log', 'a') as f:
            sys.stdout = f  # Redirect standard output to the file
            sys.stderr = f  # Redirect standard error to the file
            
            try:
                # Get broker instance
                broker = get_kite()
            except Exception as e:
                # Log the exception to the file
                print(f"An error occurred: {e}")
            finally:
                # Restore stdout and stderr to their original state
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

        # Fetch Last Traded Price using yfinance
        ltp_nse = get_ltp_yf(random_symbol)
        if ltp_nse is None or ltp_nse >= 5000:
            logger.warning(f"Skipping {random_symbol}: price is too high or LTP fetch failed")
            return
  
        # Fetch current holdings, orders, and positions
        try:
            # Ensure that positions, orders, and holdings are fetched correctly and are lists or dictionaries
            lst_dct_positions = broker.kite.positions() if callable(broker.kite.positions) else {}
            positions_symbols = [pos["tradingsymbol"] for pos in (lst_dct_positions.get("day", []) + lst_dct_positions.get("net", [])) if pos]

            lst_dct_orders = broker.orders() if callable(broker.orders) else []
            orders_symbols = [order.get("tradingsymbol", "Unknown Symbol") for order in lst_dct_orders if order]

            holdings = broker.kite.holdings() if callable(broker.kite.holdings) else []
            holdings_symbols = [holding["tradingsymbol"] for holding in holdings if holding]
        except Exception as e:
            logger.error(f"Error fetching positions, orders, or holdings: {str(e)}")
            return
        
        # Determine purchase limit
        purchase_limit = 0
        if random_symbol in holdings_symbols and random_symbol not in orders_symbols and random_symbol not in positions_symbols:
            pass
            #purchase_limit = 10000
        elif random_symbol not in holdings_symbols and random_symbol not in orders_symbols and random_symbol not in positions_symbols:
            purchase_limit = 5000

        if purchase_limit <= 0:
            logger.info(f"Skipping {random_symbol}: purchase_limit is not set")
            return

        quantity = int(purchase_limit / ltp_nse)
        if quantity <= 0:
            logger.info(f"Skipping {random_symbol}: calculated quantity is zero or negative")
            return

        # Place order
        try:
            order_id = broker.order_place(
                tradingsymbol=random_symbol,
                exchange='NSE',
                transaction_type='BUY',
                quantity=quantity,
                order_type='LIMIT',
                product='CNC',
                variety='regular',
                price=round_to_paise(ltp_nse, 0.2)
            )
            if order_id:
                logger.info(f"BUY {order_id} placed for {random_symbol} successfully")
                print(f"BUY {order_id} placed for {random_symbol} successfully")
                remaining_cash = available_cash - (quantity * ltp_nse)
                logger.debug(f"Order placed successfully for {random_symbol}")
                print(f"Order placed successfully for {random_symbol}")
                logger.debug(f"Remaining Cash: {int(round(remaining_cash / 1000))}K")
                print(f"Remaining Cash: {int(round(remaining_cash / 1000))}K")
                message_text = (f"📊 Let's Buy {random_symbol}!\n"
                                f"📈 Current Price (LTP): {ltp_nse}\n"
                                f"🔍 Check it out on TradingView: https://www.tradingview.com/chart/?symbol={random_symbol}")
                asyncio.run(send_telegram_message(BOT_TOKEN, USER_ID, message_text))
                print(message_text)
                if remaining_cash < limit:
                    logger.warning(f"Cash: {int(remaining_cash)}, stopping further orders.")
                    return
            else:
                logger.warning(f"Failed to place order for {random_symbol}")
        except Exception as e:
            logger.error(f"Error while placing order for {random_symbol}: {str(e)}")
    except Exception as e:
        logger.error(f"Error while executing place_buy_order function: {str(e)}")
