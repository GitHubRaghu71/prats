from toolkit.logger import Logger
from toolkit.currency import round_to_paise
from toolkit.utilities import Utilities
from login_get_kite import get_kite, remove_token
from cnstpxy import log_path, data_path, max_target, CNFG
from trndlnpxy import Trendlyne
import pandas as pd
import traceback
import sys
import os
from fundpxy import calculate_decision
import asyncio
import logging
import telegram

# Configure logging
logging.basicConfig(level=logging.WARNING)
logging = Logger(30, log_path + "main.log")

black_file = data_path + "blacklist.txt"
bot_dct = CNFG["telegram"]
bot_token = bot_dct["bot_token"]
bot_user = bot_dct["chat_id"]
bot_id = bot_dct["chat_id"] 

# Save the original sys.stdout
original_stdout = sys.stdout

try:
    # Redirect sys.stdout to 'output.txt'
    with open(f'{log_path}output.txt', 'w') as file:
        sys.stdout = file
        try:
            broker = get_kite()
        except Exception as e:
            remove_token(data_path)
            print(traceback.format_exc())
            logging.error(f"{str(e)} unable to get holdings")
            sys.exit(1)
finally:
    sys.stdout = original_stdout

# Call the calculate_decision function to get the decision
decision, optdecision, available_cash, live_balance, limit = calculate_decision()

if decision == "YES":
    try:
        df_pxycombined = pd.read_csv(f'{data_path}pxycombined.csv')
        lst = df_pxycombined['tradingsymbol'].to_list()
        lst_tlyne = []
        lst_dct_tlyne = Trendlyne().entry()
        if lst_dct_tlyne and any(lst_dct_tlyne):
            lst_tlyne = [dct['tradingsymbol'] for dct in lst_dct_tlyne]
    except Exception as e:
        print(traceback.format_exc())
        logging.error(f"{str(e)} unable to read Trendlyne calls")
        sys.exit(1)

    try:
        if any(lst_tlyne):
            logging.info(f"reading Trendlyne ...{lst_tlyne}")
            lst_tlyne = [x for x in lst_tlyne if x not in lst]
            logging.info(f"filtered from holdings and positions: {lst}")
            lst_dct_orders = broker.orders
            if lst_dct_orders and any(lst_dct_orders):
                symbols_orders = [dct['symbol'] for dct in lst_dct_orders]
            else:
                symbols_orders = []
            all_symbols = symbols_orders
            lst_tlyne = lst_tlyne if lst_tlyne else []  # Initialize lst_tlyne if not defined
            lst_tlyne = [x for x in lst_tlyne if x not in all_symbols]
            logging.info(f"filtered from orders, these are not in orders ...{lst_tlyne}")
    except Exception as e:
        print(traceback.format_exc())
        logging.error(f"{str(e)} unable to read positions")
        sys.exit(1)

    def calc_target(ltp, perc):
        resistance = round_to_paise(ltp, perc)
        target = round_to_paise(ltp, max_target)
        return max(resistance, target)
    
    def transact(dct, remaining_cash, broker):
        try:
            # Use the LTP from dct (capitalized key 'LTP')
            ltp = dct['LTP']
            
            # Remove commas if present in LTP and convert to float
            ltp = ltp.replace(',', '')  # Remove commas
            ltp = float(ltp)  # Convert to float
            
            logging.info(f"LTP for {dct['tradingsymbol']} is {ltp}")
    
            if ltp > 0 and remaining_cash > limit:
                # Ensure quantity is a valid number and calculate the order price correctly
                quantity = max(1, round(float(dct['QTY'])))
                price = round_to_paise(ltp, 0.2)  # Round LTP to 2 decimal places as price
        
                # Ensure price is a valid positive value
                if price <= 0:
                    logging.error(f"Invalid price calculated for {dct['tradingsymbol']}: {price}")
                    return remaining_cash
        
                # Try placing the order on NSE first
                try:
                    order_id = broker.order_place(
                        tradingsymbol=dct['tradingsymbol'],
                        exchange='NSE',
                        transaction_type='BUY',
                        quantity=quantity,
                        order_type='LIMIT',
                        product='CNC',
                        variety='regular',
                        price=price  # Use the LTP from dct for price calculation
                    )
                    logging.info(f"Order placed successfully on NSE: {order_id}")
                except Exception as e:
                    # If placing on NSE fails, try placing on BSE
                    logging.error(f"Error placing order on NSE for {dct['tradingsymbol']}: {e}")
                    logging.info("Retrying on BSE...")
    
                    try:
                        order_id = broker.order_place(
                            tradingsymbol=dct['tradingsymbol'],
                            exchange='BSE',  # Retry on BSE
                            transaction_type='BUY',
                            quantity=quantity,
                            order_type='LIMIT',
                            product='CNC',
                            variety='regular',
                            price=price
                        )
                        logging.info(f"Order placed successfully on BSE: {order_id}")
                    except Exception as e:
                        logging.error(f"Error placing order on BSE for {dct['tradingsymbol']}: {e}")
                        return remaining_cash  # If both exchanges fail, return remaining cash
    
                # Send notification to Telegram
                try:
                    message_text = f"📊 Let's Buy {dct['tradingsymbol']}!\n📈 Current Price (LTP): {ltp}\n🔍 Check it out on TradingView: https://www.tradingview.com/chart/?symbol={dct['tradingsymbol']}"
                    async def send_telegram_message(message_text):
                        bot = telegram.Bot(token=bot_token)
                        await bot.send_message(chat_id=bot_id, text=message_text)
                    asyncio.run(send_telegram_message(message_text))
                except Exception as e:
                    logging.error(f"Error sending message to Telegram: {e}")
                
                remaining_cash -= int(float(dct['QTY'].replace(',', ''))) * ltp
                print(f"Order placed successfully for {dct['tradingsymbol']} and cash remaining {int(remaining_cash)}")
                return remaining_cash
            else:
                logging.warning(f"Skipping {dct['tradingsymbol']}: No valid LTP or insufficient cash")
                return remaining_cash
    
        except KeyError as e:
            logging.error(f"LTP key missing in dictionary for {dct['tradingsymbol']}: {e}")
        except Exception as e:
            logging.error(f"Error placing order for {dct['tradingsymbol']}: {e}")
            if hasattr(e, 'response'):
                logging.error(f"Error Response: {e.response.text}")
            else:
                logging.error("No response available in the exception")
            return remaining_cash
    
    if not os.path.exists(black_file):  # Check if blacklist file doesn't exist
        with open(black_file, 'w') as file:
            pass  # Create an empty file if it doesn't exist

    lst_failed_symbols = []
    if any(lst_tlyne):
        new_list = []
        lst_all_orders = [d for d in lst_dct_tlyne if d['tradingsymbol'] in lst_tlyne]
        
        # Read the blacklist symbols from the file
        with open(black_file, 'r') as file:
            blacklisted_symbols = file.readlines()
        blacklisted_symbols = [symbol.strip() for symbol in blacklisted_symbols]
        
        logging.info(f"Ignored symbols: {lst_failed_symbols}")
        
        # Filter out orders that are blacklisted
        lst_orders = [d for d in lst_all_orders if d['tradingsymbol'] not in lst_failed_symbols and d['tradingsymbol'] not in blacklisted_symbols]
        
        response = broker.kite.margins()
        remaining_cash = response["equity"]["available"]["live_balance"]
        
        for d in lst_orders:
            remaining_cash = transact(d, remaining_cash, broker)
            Utilities().slp_til_nxt_sec()

            if remaining_cash < 6000:
                break
        
        # Add newly blacklisted symbols to the blacklist file
        if any(new_list):
            with open(black_file, 'w') as file:
                for symbol in new_list:
                    file.write(symbol + '\n')
        
        print(f"Remaining Cash💰: {int(round(remaining_cash/1000))}K")

elif decision == "NO":
    # Perform actions for "NO"
    print(f"\033[91mNo sufficient funds available Cash💰: {int(round(available_cash/1000))}K\033[0m")
    print("-" * 42)
