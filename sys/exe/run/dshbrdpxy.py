import yfinance as yf
import os
import pandas as pd
import numpy as np
from datetime import datetime
from predictpxy import predict_market_sentiment
from mktpxy import get_market_check
from smapxy import check_index_status
from clorpxy import SILVER, UNDERLINE, RED, GREEN, YELLOW, RESET, BRIGHT_YELLOW, BRIGHT_RED, BRIGHT_GREEN, BOLD, GREY
from cnstpxy import data_path

# Initialize variables and functions
mktpredict = predict_market_sentiment()

nonemincandlesequance, nmktpxy = get_market_check('^NSEI')
#booked = process_data_total_profit()
booked = 0
nsma = check_index_status('^NSEI')

try:
    from fundpxy import calculate_decision
    decision, optdecision, available_cash, live_balance, limit = calculate_decision()
except Exception as e:
    decision, optdecision, available_cash, live_balance, limit = "No", "No", 0, 0, 0

cashnow = round(live_balance / 100000, 2)

# Load combined_df from CSV
csv_file = data_path + 'pxycombined.csv'
if not os.path.exists(csv_file):
    print(f"Error: The file '{csv_file}' does not exist.")
    combined_df = pd.DataFrame()  # Create an empty DataFrame if file does not exist
else:
    combined_df = pd.read_csv(csv_file)

# Check if the required columns exist
required_columns = ['qty', 'product', 'source', 'close', 'ltp', 'PL%', 'PnL', 'Invested']
missing_columns = [col for col in required_columns if col not in combined_df.columns]

if missing_columns:
    print(f"Missing columns: {missing_columns}")
else:
    # Calculate required values
    CnC_tCap_rounded = round(
        combined_df.loc[
            (combined_df['product'] == 'CNC') & (combined_df['qty'] > 0),
            'Invested'
        ].sum() / 100000,
        2
    )
    run_spnl = combined_df[combined_df['product'] == 'CNC']['PnL'].sum()
    all_Stocks_df = combined_df[
        (combined_df['qty'] > 0) &
        (combined_df['product'] == 'CNC') &
        (combined_df['source'] == 'holdings')
    ].copy()

    all_Stocks_yworth = (all_Stocks_df['close'] * all_Stocks_df['qty']).sum().round(4)
    all_Stocks_worth = (all_Stocks_df['ltp'] * all_Stocks_df['qty']).sum().round(4)
    all_Stocks_worth_dpnl = all_Stocks_worth - all_Stocks_yworth

    filtered_df = combined_df[
        (combined_df['product'] == 'CNC') &
        (combined_df['qty'] > 0) &
        (combined_df['PL%'] > 0)
    ]
    green_Stocks_profit_loss = filtered_df['PnL'].sum()
    total_invested = filtered_df['Invested'].sum()
    green_Stocks_capital_percentage = (green_Stocks_profit_loss / total_invested) * 100 if total_invested > 0 else 0

    # Define arrow_map
    arrow_map = {"Buy": "⤴", "Sell": "⤵", "Bull": "⬆", "Bear": "⬇"}

    # Define formatting for output
    column_width = 30
    left_aligned_format = "{:<" + str(column_width) + "}"
    right_aligned_format = "{:>" + str(column_width) + "}"

    output_lines = []

    # Append formatted lines to output_lines

    output_lines.append(
        left_aligned_format.format(f"iCap:{BRIGHT_YELLOW}{str(CnC_tCap_rounded).zfill(6)}{RESET}") +
        right_aligned_format.format(       f"uPnL:{BRIGHT_RED if run_spnl < 0 else BRIGHT_GREEN}{str(round(run_spnl / 100000, 2)).zfill(6)}{RESET}")
    )
    # Calculate final PnL value
    final_pnl_value = round((CnC_tCap_rounded + cashnow) - 1.4, 2)
    # Append formatted strings to output_lines
    output_lines.append(
        left_aligned_format.format(
            f"{'tCap'.zfill(3)}:{BRIGHT_YELLOW}{str(round((cashnow + CnC_tCap_rounded), 2)).zfill(6)}"
            f"{BRIGHT_RED if mktpredict == 'FALL' else GREY if mktpredict == 'SIDE' else BRIGHT_GREEN}       {BOLD}RATS{RESET}"
        ) +
        right_aligned_format.format(
            f"{BRIGHT_GREEN if nmktpxy in ['Bull'] else (BRIGHT_RED if nmktpxy in ['Bear'] else GREY)}"
            f"{BOLD}®{RESET}{BRIGHT_YELLOW} {arrow_map.get(nmktpxy, '')}{RESET}       "
            f"{'tPnL'.zfill(3)}:{BRIGHT_GREEN if final_pnl_value >= 0 else BRIGHT_RED}{str(final_pnl_value).zfill(6)}{RESET}"
        )
    )
    output_lines.append(left_aligned_format.format(
            f"tCash:{BRIGHT_GREEN if cashnow > 10000 else BRIGHT_YELLOW}{round(cashnow, 2):05.2f}{RESET}") +
            right_aligned_format.format(f"dPnL:{BRIGHT_GREEN if all_Stocks_worth_dpnl > 0 else BRIGHT_RED}{str(int(round(all_Stocks_worth_dpnl, 0))).zfill(6)}{RESET}"
            ))
    #f"Flush:{BRIGHT_GREEN if green_Stocks_capital_percentage > 0 else BRIGHT_RED}{str(round(green_Stocks_capital_percentage, 2)).zfill(4)}% {int(green_Stocks_profit_loss / 1000)}K{RESET}"
    f"dPnL:{BRIGHT_GREEN if all_Stocks_worth_dpnl > 0 else BRIGHT_RED}{str(int(round(all_Stocks_worth_dpnl, 0))).zfill(6)}{RESET}"
    full_output = '\n'.join(output_lines)

    print(full_output)
    print("━" * 42)
