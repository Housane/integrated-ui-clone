# essentially a shortcut for the technical indicator instead of using excel formula. Also transcribes it to a processed folder suhc that it dosent change initial csv

import os
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator

# Path
PRICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Data Files/Price')) # where files are found
PROCESSED_DIR = os.path.join(PRICE_DIR, 'Processed') #Basically just make a smol folder

# Helper: find all CSVs in PRICE_DIR (exclude the 'Processed' folder)
price_files = [
    f for f in os.listdir(PRICE_DIR) #essentially for every filename, we will def it as f and include it at the list
    if f.endswith('.csv') and os.path.isfile(os.path.join(PRICE_DIR, f))
]

def calculate_indicators(df):
    # Must have Date, Open, High, Low, Close, Volume
    df.columns = [c.lower().strip() for c in df.columns] #Incase OHLCV not standardised
    # find out which column corresponds to Date + OHLCV
    date_col = next((c for c in df.columns if "date" in c), None)
    open_col = next((c for c in df.columns if "open" in c), None)
    high_col = next((c for c in df.columns if "high" in c), None)
    low_col = next((c for c in df.columns if "low" in c), None)
    close_col = next((c for c in df.columns if "close" in c), None)
    volume_col = next((c for c in df.columns if "volume" in c), None)

    # Check all needed columns
    for col in [date_col, open_col, high_col, low_col, close_col, volume_col]:
        if col is None:
            raise ValueError(f"Missing expected column in input: {col}")

    # Sort by date ascending if not already
    df = df.sort_values(date_col)

    #MACD - Technical Definition
    macd = MACD(
        close=df[close_col],
        window_slow=26, #ema
        window_fast=12, #ema
        window_sign=9 #signal c/o
    )
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['MACD_diff'] = macd.macd_diff()

    #RSi - Technical Definition
    rsi = RSIIndicator(close=df[close_col], window=14)
    df['RSI'] = rsi.rsi()

    #Bollinger Bands - Technical Definition
    bb = BollingerBands(close=df[close_col], window=20, window_dev=2)
    df['BB_bbm'] = bb.bollinger_mavg() # BB - Mid
    df['BB_bbh'] = bb.bollinger_hband() # BB - High
    df['BB_bbl'] = bb.bollinger_lband() # BB - Low
    df['BB_bbwidth'] = df['BB_bbh'] - df['BB_bbl']

    #OBV - Technical Definition
    obv = OnBalanceVolumeIndicator(close=df[close_col], volume=df[volume_col])
    df['OBV'] = obv.on_balance_volume()

    return df #make sure these columns exist first

def main():
    for file in price_files:
        input_path = os.path.join(PRICE_DIR, file)
        #print(f"Current file: {file}...") - For Debug
        df = pd.read_csv(input_path)
        try:
            df_ind = calculate_indicators(df)
        except Exception as e:
            #print(f" error in {file}: {e}") - For Debug
            continue
        # saved as (original_name)_with_indicators.csv
        base = os.path.splitext(file)[0]
        output_path = os.path.join(PROCESSED_DIR, f"{base}_with_indicators.csv")
        df_ind.to_csv(output_path, index=False)
