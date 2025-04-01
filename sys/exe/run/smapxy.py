import yfinance as yf
import warnings
import time
from yfinance.exceptions import YFRateLimitError

def check_index_status(index_symbol):
    retries = 3
    delay = 60  # Wait 60 seconds between retries
    for attempt in range(retries):
        try:
            # Download historical data
            data = yf.Ticker(index_symbol).history(period="5d", interval="1m")
            # Calculate SMA
            data['50SMA'] = data['Close'].rolling(window=50).mean()
            data['200SMA'] = data['Close'].rolling(window=200).mean()
            # Get the last values of SMA and current price
            last_50sma = data['50SMA'].iloc[-1]
            last_200sma = data['200SMA'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            # Check trend
            if current_price > last_50sma:
                return "up"
            elif current_price < last_50sma:
                return "down"
            else:
                return "side"
        except YFRateLimitError:
            if attempt < retries - 1:
                print(f"Rate limit hit. Retrying in {delay} seconds... ({attempt + 1}/{retries})")
                time.sleep(delay)
                continue
            else:
                print(f"Failed after {retries} attempts due to rate limit.")
                return "side"  # Fallback value
        except Exception as e:
            print(f"Error fetching data for {index_symbol}: {e}")
            return "side"  # Fallback value
