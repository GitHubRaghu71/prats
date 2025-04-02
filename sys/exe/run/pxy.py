import os
import sys
import subprocess
import importlib
from rich.console import Console
from clorpxy import RESET, BRIGHT_YELLOW, BRIGHT_RED, BRIGHT_GREEN, GREY

console = Console()

def get_user_input(prompt, default='l'):
    user_input = input(prompt).strip()
    if user_input == '':
        return default
    return user_input

def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ImportError as e:
            print(f"Import error: {e}")
        except Exception as ex:
            print(f"An error occurred: {ex}")
    return wrapper

# Prompt for user input
run_type = get_user_input("How do you want to run 🗺️⁀જ✈︎ short/long:")

# Run cpritepxy.pyc
subprocess.run(['python3', 'cpritepxy.pyc'])
subprocess.run(['python3', 'worldpxy.pyc'])

while True:
    @handle_exceptions
    def reload_sleeppxy():
        try:
            import sleeppxy
            importlib.reload(sleeppxy)
            from sleeppxy import progress_bar
            return progress_bar
        except ModuleNotFoundError as e:
            print(f"Module 'sleeppxy' not found: {e}")
        except AttributeError as e:
            print(f"Function 'progress_bar' not found in 'sleeppxy': {e}")
            
    @handle_exceptions
    def reload_cyclepxy():
        try:
            import cyclepxy
            importlib.reload(cyclepxy)
            from cyclepxy import cycle
            return cycle
        except ModuleNotFoundError as e:
            print(f"Module 'cyclepxy' not found: {e}")
        except AttributeError as e:
            print(f"Function 'cycle' not found in 'cyclepxy': {e}")

    # Reload modules and functions
    progress_bar = reload_sleeppxy()
    cycle = reload_cyclepxy()

    @handle_exceptions
    def reload_mktpxy():
        importlib.reload(sys.modules['mktpxy'])
        from mktpxy import get_market_check  # Re-import the function
        return get_market_check(symbol) 

    @handle_exceptions
    def cycle_handler():
        from cyclepxy import cycle
        importlib.reload(sys.modules['cyclepxy'])  # Reload module after import
        return cycle()

    @handle_exceptions
    def peak_time_handler():
        from utcpxy import peak_time
        importlib.reload(sys.modules['utcpxy'])  # Reload module after import
        return peak_time()

    @handle_exceptions
    def predict_market_sentiment_handler():
        from predictpxy import predict_market_sentiment
        importlib.reload(sys.modules['predictpxy'])  # Reload module after import
        return predict_market_sentiment()

    @handle_exceptions
    def get_market_check_handler(symbol):
        from mktpxy import get_market_check
        importlib.reload(sys.modules['mktpxy'])  # Reload module after import
        return get_market_check(symbol)

    @handle_exceptions
    def get_nse_action_handler():
        from nftpxy import get_nse_action
        importlib.reload(sys.modules['nftpxy'])  # Reload module after import
        return get_nse_action()

    @handle_exceptions
    def calculate_macd_signal_handler(symbol):
        from macdpxy import calculate_macd_signal
        return calculate_macd_signal(symbol)

    @handle_exceptions
    def check_index_status_handler(symbol):
        from smapxy import check_index_status
        return check_index_status(symbol)
    
    try:
        peak = peak_time_handler()
        if os.name == 'nt':
            os.system('cls')
        else:
            if peak == 'NONPEAK':
                os.system('clear -x')
    except Exception as e:
        print(f"Error handling peak time: {e}")
    try:
        mktpredict = predict_market_sentiment_handler()
    except Exception as e:
        print(f"Error handling market sentiment prediction: {e}")
        mktpredict = None
    try:
        onemincandlesequance, mktpxy = get_market_check_handler('^NSEI')
    except Exception as e:
        print(f"Error handling market check for ^NSEI: {e}")
        onemincandlesequance, mktpxy = "none", "none"
    try:
        bnkonemincandlesequance, bmktpxy = get_market_check_handler('^NSEBANK')
    except Exception as e:
        print(f"Error handling market check for ^NSEBANK: {e}")
        bnkonemincandlesequance, bmktpxy = "none", "none"
    try:
        ha_nse_action, nse_power, Day_Change, Open_Change = get_nse_action_handler()
    except Exception as e:
        print(f"Error handling NSE action: {e}")
        ha_nse_action, nse_power, Day_Change, Open_Change = 0.5, 0.5, 0.5, 0.5
    try:
        macd = calculate_macd_signal_handler("^NSEI")
    except Exception as e:
        print(f"Error handling MACD signal calculation: {e}")
        macd = None
    try:
        nsma = check_index_status_handler('^NSEI')
        bsma = check_index_status_handler('^NSEBANK')
    except Exception as e:
        print(f"Error handling index status: {e}")
        nsma, bsma = None, None
    
    ############################################"PRATS® Raghu Automated Trading System™############################################ 
    print((BRIGHT_GREEN + "🏛  PRATS®  Automated Trading System ™  🏛".center(42) if ha_nse_action == 'Bullish' else BRIGHT_RED + "🏛 PRATS® Raghu Automated Trading System™ 🏛".center(42) if ha_nse_action == 'Bearish' else "🏛 PRATS® Raghu Automated Trading System™ 🏛".center(42)) + RESET)    
    print("*" * 42)
    subprocess.run(['python3', 'tistpxy.pyc']) 
    ############################################"PRATS® Raghu Automated Trading System™############################################ 
    if run_type == 'l':
        subprocess.run(['python3', 'niftychartpxy.pyc'])
        subprocess.run(['python3', 'daypxy.pyc'])
        subprocess.run(['python3', 'cndlpxy.pyc'])
        if 'nsma' in locals():
            color = BRIGHT_GREEN if nsma == "up" else BRIGHT_RED if nsma == "down" else BRIGHT_YELLOW
            print(color + "ﮩ٨ﮩ٨ـﮩ٨ﮩ٨ـﮩ٨ـﮩﮩ٨ﮩ٨NIFTY٨ﮩ٨ـﮩ٨ـﮩﮩ٨ﮩ٨ـﮩ٨ﮩ٨ـﮩ" + RESET)
        #subprocess.run(['python3', 'worldpxy.pyc']) if run_type == 'l' else None
    ############################################"PRATS® Raghu Automated Trading System™############################################ 
    if (mktpredict in ['FALL', 'SIDE', 'RISE'] and (mktpxy == 'Buy' or mktpxy == 'Bull')) or peak == "PEAKEND":
        print(f"{'🛒┈┈┈┈ BUY Action - NIFTY on Rise  🛒🛒🛒':>38}{RESET}")
        subprocess.run(['python3', 'buycncpxy.pyc'])
    else:
        print(f"{GREY}{'𓆝 ⋆｡𖦹°‧🫧⋆.ೃ࿔*:･ No Buy - Waiting for Rise':>38}{RESET}")
    ############################################"PRATS® Raghu Automated Trading System™############################################ 
    #print(f"{'🛒┈┈┈┈ Loop Action - CtrlCnCPxy  🛒🛒🛒':>38}{RESET}")
    subprocess.run(['python3', 'cntrlcncpxy.pyc'])
    subprocess.run(['python3', 'dshbrdpxy.pyc', 'l'])
    subprocess.run(['python3', 'selfpxy.pyc'])
    progress_bar(cycle, (mktpxy if peak in ["PEAKSART", "PEAKEND", "NONPEAK"] else None))
    ############################################"PRATS® Raghu Automated Trading System™############################################ 
   