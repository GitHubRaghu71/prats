import sys
import numpy as np
import traceback
import pandas as pd
from login_get_kite import get_kite, remove_token
from cnstpxy import dir_path, log_path, data_path
from toolkit.logger import Logger
import csv
import os
import sys
import traceback
import logging
logging = Logger(30, log_path + "main.log")

def get_holdingsinfo(resp_list, broker):
    try:
        df = pd.DataFrame(resp_list)
        df['source'] = 'holdings'
        return df
    except Exception as e:
        print(f"An error occurred in holdings: {e}")
        return None
def get_positionsinfo(resp_list, broker):
    try:
        df = pd.DataFrame(resp_list)
        df['source'] = 'positions'
        return df
    except Exception as e:
        print(f"An error occurred in positions: {e}")
        return None
try:
    sys.stdout = open(f'{log_path}output.txt', 'w')
    broker = get_kite()
except Exception as e:
    remove_token(data_path)
    print(traceback.format_exc())
    logging.error(f"{str(e)} unable to get holdings")
    sys.exit(1)
finally:
    # Ensure to close the file and restore stdout
    if sys.stdout != sys.__stdout__:
        sys.stdout.close()
        sys.stdout = sys.__stdout__
def process_data():
    try:
        holdings_response = broker.kite.holdings()
        positions_response = broker.kite.positions()['net']
        holdings_df = get_holdingsinfo(holdings_response, broker)
        holdings_df.to_csv(f'{data_path}pxyholdings.csv', index=False)
        positions_df = get_positionsinfo(positions_response, broker)
        positions_df.to_csv(f'{data_path}pxypositions.csv', index=False)
        holdings_df['key'] = holdings_df['exchange'] + ":" + holdings_df['tradingsymbol'] if not holdings_df.empty else None
        positions_df['key'] = positions_df['exchange'] + ":" + positions_df['tradingsymbol'] if not positions_df.empty else None
        combined_df = pd.concat([holdings_df, positions_df], ignore_index=True)
        
        # lst = combined_df['key'].tolist()
        lst = combined_df['key'].dropna().tolist()    # Drop Nan keys from empty DFs
        if not lst:
            logging.info("No holdings or positions found. Skipping OHLC fetch.")
            # Create empty combined_df with expected columns
            combined_df = pd.DataFrame(columns=[
                'tradingsymbol', 'exchange', 'quantity', 'average_price', 't1_quantity', 'pnl', 'unrealised',
                'day_sell_quantity', 'day_sell_price', 'ltp', 'open', 'high', 'low', 'close', 'qty', 'oPL%',
                'dPL%', 'avg', 'Invested', 'value', 'PnL', 'PL%', 'Yvalue', 'dPnL', 'booked', 'bpnl', 'pnlrec_'
            ])
            combined_df.to_csv(f'{data_path}pxycombined.csv', index=False)
            print(f"combined_df: \n {combined_df}")
            return combined_df
        #print(f'Combined_DF Key list: {lst}')

        #resp = broker.kite.ohlc(lst)
        #dct = {
        #    k: {
        #        'ltp': v['ohlc'].get('ltp', v['last_price']),
        #        'open': v['ohlc']['open'],
        #        'high': v['ohlc']['high'],
        #        'low': v['ohlc']['low'],
        #        'close_price': v['ohlc']['close'],
        #    }
        #    for k, v in resp.items()
        #}
        #combined_df['ltp'] = combined_df.apply(lambda row: dct.get(row['key'], {}).get('ltp', row['last_price']), axis=1)
        #combined_df['high'] = combined_df['key'].map(lambda x: dct.get(x, {}).get('high', 0))
        #combined_df['low'] = combined_df['key'].map(lambda x: dct.get(x, {}).get('low', 0))
        #combined_df['open'] = combined_df['key'].map(lambda x: dct.get(x, {}).get('open', 0))
        #combined_df['close'] = combined_df['key'].map(lambda x: dct.get(x, {}).get('close_price', 0))

        combined_df['ltp'] = combined_df['last_price']
        combined_df['close'] = combined_df['close_price']
        combined_df['high'] = np.maximum(combined_df['ltp'], combined_df['close'])
        combined_df['low'] = np.minimum(combined_df['ltp'], combined_df['close'])
        combined_df['open'] = (combined_df['ltp'] + combined_df['close']) / 2
        
        combined_df['qty'] = combined_df.apply(lambda row: int(row['quantity'] + row['t1_quantity']) if row['source'] == 'holdings' else int(row['quantity']), axis=1)
        combined_df['oPL%'] = combined_df.apply(lambda row: round((((row['ltp'] - row['open']) / row['open']) * 100), 2) if row['open'] != 0 else 0, axis=1)
        combined_df['dPL%'] = combined_df.apply(lambda row: round((((row['ltp'] - row['close']) / row['close']) * 100), 2) if row['close'] != 0 else 0, axis=1)
        combined_df['pnl'] = combined_df['pnl'].astype(int)
        combined_df['avg'] = combined_df['average_price']
        #np.where((combined_df['day_sell_quantity'] > 0) & (combined_df['exchange'] == "NFO"), 
                                      #combined_df['average_price'] * 1.05, 
                                      #combined_df['average_price'])
        combined_df['Invested'] = (combined_df['qty'] * combined_df['avg']).round(0).astype(int)
        combined_df['value'] = combined_df['qty'] * combined_df['ltp']
        combined_df['PnL'] = (combined_df['value'] - combined_df['Invested']).astype(int)
        combined_df['PL%'] = ((combined_df['PnL'] / combined_df['Invested']) * 100).round(2)
        combined_df['Yvalue'] = combined_df['qty'] * combined_df['close']
        combined_df['dPnL'] = combined_df['value'] - combined_df['Yvalue']
        if 'day_sell_price' in combined_df.columns and 'day_sell_quantity' in combined_df.columns:
            combined_df['booked'] = (combined_df['day_sell_price'] - combined_df['average_price']) * combined_df['day_sell_quantity']
            combined_df['bpnl'] = round(combined_df['unrealised'] - combined_df['booked'], 2)
            combined_df['pnlrec_'] = round((combined_df['bpnl'] / combined_df['Invested'] * 100), 2)
        else:
            combined_df['booked'] = 0  # Handle missing data case
            combined_df['bpnl'] = 0  # Handle missing data case
            combined_df['pnlrec_'] = 0  # Handle missing data case
        
        # Filter rows where 'key' starts with "NFO:"
        nfo_df = combined_df[combined_df['key'].str.startswith('NFO:')]
        
        combined_df.to_csv(f'{data_path}pxycombined.csv', index=False)
        return combined_df
    except Exception as e:
        logging.error(f"An error occurred in process_data: {e}")
        traceback.print_exc()
        # return None # Return empty DataFrame instead of None
        combined_df = pd.DataFrame(columns=[
            'tradingsymbol', 'exchange', 'quantity', 'average_price', 't1_quantity', 'pnl', 'unrealised',
            'day_sell_quantity', 'day_sell_price', 'ltp', 'open', 'high', 'low', 'close', 'qty', 'oPL%',
            'dPL%', 'avg', 'Invested', 'value', 'PnL', 'PL%', 'Yvalue', 'dPnL', 'booked', 'bpnl', 'pnlrec_'
        ])
        combined_df.to_csv(f'{data_path}pxycombined.csv', index=False)
        return combined_df
