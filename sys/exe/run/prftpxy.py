import sys
import numpy as np
import pandas as pd
from datetime import datetime
import traceback
from login_get_kite import get_kite, remove_token
from cnstpxy import dir_path, data_path, log_path
from toolkit.logger import Logger
from clorpxy import SILVER, UNDERLINE, RED, GREEN, YELLOW, RESET, BRIGHT_YELLOW, BRIGHT_RED, BRIGHT_GREEN, BOLD, GREY

logging = Logger(30, log_path + "main.log")

def get_holdings_info(file_path):
    try:
        df = pd.read_csv(file_path)
        df['source'] = 'holdings'
        return df
    except Exception as e:
        logging.error(f"Error occurred in get_holdings_info: {e}")
        return pd.DataFrame(columns=['tradingsymbol', 'product_x', 'used_quantity', 'average_price_x'])  # Default empty DF

def get_positions_info(file_path):
    try:
        df = pd.read_csv(file_path)
        df['source'] = 'positions'
        return df
    except Exception as e:
        logging.error(f"Error occurred in get_positions_info: {e}")
        return pd.DataFrame(columns=['tradingsymbol', 'average_price_y', 'unrealised', 'PnL', 'day_sell_quantity'])  # Default empty DF

def process_data_total_profit():
    sys.stdout = open(f'{data_path}output.txt', 'w')
    broker = None
    try:
        broker = get_kite()
    except Exception as e:
        remove_token(data_path)
        logging.error(f"Error in getting kite instance: {e}")
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        if sys.stdout != sys.__stdout__:
            sys.stdout.close()
            sys.stdout = sys.__stdout__

    try:
        total_profit_fo = 0
        holdings_df = get_holdings_info(f'{data_path}pxyholdings.csv')
        positions_df = get_positions_info(f'{data_path}pxypositions.csv')

        if holdings_df.empty and positions_df.empty:  # NEW: Handle empty case
            logging.info("No holdings or positions data available. Returning zero profits.")
            empty_df = pd.DataFrame(columns=['STOCK', 'QTY', 'PL%', 'PnL'])
            empty_df.to_csv(f'{data_path}pxycncprofit.csv', index=False)
            empty_df = pd.DataFrame(columns=['tradingsymbol', 'new_pnl_y'])
            empty_df.to_csv(f'{data_path}pxyoptprofit.csv', index=False)
            return 0

        if 'tradingsymbol' not in holdings_df.columns or 'tradingsymbol' not in positions_df.columns:  # MODIFIED: Log instead of raise
            logging.warning("'tradingsymbol' column missing. Assuming no CNC data.")
            holdings_df['tradingsymbol'] = holdings_df.get('tradingsymbol', pd.Series(dtype=str))
            positions_df['tradingsymbol'] = positions_df.get('tradingsymbol', pd.Series(dtype=str))

        merged_df = pd.merge(holdings_df, positions_df, on='tradingsymbol', how='outer')
        merged_df.to_csv('pxymergedcsv.csv', index=False)

        merged_df_filtered = merged_df[(merged_df['product_x'] == 'CNC') & (merged_df['used_quantity'] > 0)].copy()
        merged_df_filtered['PnL'] = merged_df_filtered.apply(
            lambda row: row['used_quantity'] * (row['average_price_y'] - row['average_price_x']),
            axis=1
        ).astype(int, errors='ignore')  # NEW: Handle NaN
        total_profit = merged_df_filtered['PnL'].sum() if not merged_df_filtered.empty else 0

        if not merged_df_filtered.empty:
            merged_df_filtered['STOCK'] = merged_df_filtered['tradingsymbol']
            merged_df_filtered['QTY'] = merged_df_filtered['used_quantity'].astype(int, errors='ignore')
            merged_df_filtered['PL%'] = ((merged_df_filtered['average_price_y'] - merged_df_filtered['average_price_x']) / merged_df_filtered['average_price_y']) * 100
            merged_df_filtered['PL%'] = merged_df_filtered['PL%'].round(2)
            merged_df_filtered = merged_df_filtered[['STOCK', 'QTY', 'PL%', 'PnL']]
            merged_df_filtered.to_csv(f'{data_path}pxycncprofit.csv', index=False)
        else:
            empty_df = pd.DataFrame(columns=['STOCK', 'QTY', 'PL%', 'PnL'])
            empty_df.to_csv(f'{data_path}pxycncprofit.csv', index=False)

        mergedfo_df = get_positions_info(f'{data_path}pxycombined.csv')
        if mergedfo_df.empty:  # NEW: Handle empty case
            logging.info("No NFO data available.")
            empty_df = pd.DataFrame(columns=['tradingsymbol', 'new_pnl_y'])
            empty_df.to_csv(f'{data_path}pxyoptprofit.csv', index=False)
            return total_profit

        mergedfo_df_filtered = mergedfo_df[(mergedfo_df['exchange'] == 'NFO') & (mergedfo_df['day_sell_quantity'] > 0)].copy()
        if not mergedfo_df_filtered.empty:
            mergedfo_df_filtered['PnL'] = mergedfo_df_filtered['PnL'].astype(int, errors='ignore')
            condition_qty_gt_0_and_sell_qty_gt_0 = (mergedfo_df_filtered['qty'] > 0) & (mergedfo_df_filtered['day_sell_quantity'] > 0)
            condition_qty_eq_0 = mergedfo_df_filtered['qty'] == 0
            mergedfo_df_filtered['new_pnl_y'] = np.where(
                condition_qty_gt_0_and_sell_qty_gt_0,
                (mergedfo_df_filtered['unrealised'] - mergedfo_df_filtered['PnL']).astype(int, errors='ignore'),
                np.where(
                    condition_qty_eq_0,
                    mergedfo_df_filtered['unrealised'],
                    mergedfo_df_filtered['unrealised']
                )
            )
            total_profit_fo = int(mergedfo_df_filtered['new_pnl_y'].sum())
            mergedfo_df_filtered = mergedfo_df_filtered[['tradingsymbol', 'new_pnl_y']]
            mergedfo_df_filtered.to_csv(f'{data_path}pxyoptprofit.csv', index=False)
        else:
            empty_df = pd.DataFrame(columns=['tradingsymbol', 'new_pnl_y'])
            empty_df.to_csv(f'{data_path}pxyoptprofit.csv', index=False)

        total_profit_all = total_profit_fo + total_profit
        return total_profit_all

    except Exception as e:
        logging.error(f"Error occurred in process_data_total_profit: {e}")
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return 0

def main():
    try:
        process_data_total_profit()
    except Exception as e:
        logging.error(f"Error occurred in main: {e}")
        print(f"An error occurred in main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()