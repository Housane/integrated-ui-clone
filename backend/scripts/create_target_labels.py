# Used to load a consolidated price + sentiment data, then calc a fwd return over a 5 day window and assign
# #buy/sell/hold labels based on the PnL

import pandas as pd
import numpy as np
import os

# create buy/sell/hold labels [buy when >= +2%, sell when <= -2%]
def create_target_labels(df, future_days=5, buy_threshold=0.02, sell_threshold=-0.02):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
    df = df.sort_values(['ticker', 'date']) # Sort by icker, then ascending date for proper alignment of calc
    df['future_return'] = df.groupby('ticker')['close'].pct_change(periods=future_days).shift(-future_days) #for each ticker, calc % change over next 5 days, and then move the return back to the current row

    conditions = [ #essentially assignment of the buy/sell/hold label
        df['future_return'] >= buy_threshold,  # Buy signal (1)
        df['future_return'] <= sell_threshold,  # Sell signal (-1)
    ]
    choices = [1, -1]  # Buy = 1, Sell = -1, Hold = 0

    df['target'] = np.select(conditions, choices, default=0) # Selection Algo
    df = df.dropna(subset=['future_return'])
    return df

# Analyse the distribution of target labels
def analyse_target_distribution(df):
    target_counts = df['target'].value_counts().sort_index() #tallies each target value (-1,0,1)
    total_samples = len(df)

    for target, count in target_counts.items():
        percentage = (count / total_samples) * 100
        label = "SELL" if target == -1 else "HOLD" if target == 0 else "BUY"
        print(f"{target} ({label}): {count} samples ({percentage:.1f}%)") #To ensure nth wrong

    ticker_dist = df.groupby(['ticker', 'target']).size().unstack(fill_value=0) # Groups by ticker and target, counts the rows and
    # ensures each ticker has columns for -1, 0, 1

# loop per ticker
    for ticker in df['ticker'].unique(): # forces no duplicates
        ticker_data = ticker_dist.loc[ticker]
        ticker_total = ticker_data.sum()
        print(f"{ticker}: {ticker_total} samples", end=" - ")
        for target in [-1, 0, 1]:
            if target in ticker_data.index:
                count = ticker_data[target]
                pct = (count / ticker_total) * 100
                label = "SELL" if target == -1 else "HOLD" if target == 0 else "BUY"
                print(f"{label}: {pct:.1f}%", end=",") #1dp, then comma to 'split'
        print() # move to another line

    return target_counts


def main(): # files are written this way because we imported OS earlier + to ensure it can be runned
    input_file = '../../Data Files/Consolidated/(OG 10 Stocks) consolidated_data_with_sentiment.csv'  #Take note OG File Rename
    output_file = '../../Data Files/Consolidated/ml_training_data.csv'
    # Check if input file exists
    if not os.path.exists(input_file):
        print("check file path for input_file location and verify against input_file")
        return

    # Load the file consolidated_data_with_sentiment
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        return


    # Create target labels
    df_labeled = create_target_labels(df) # compute future_return and target fn

    # Analyse target distribution
    target_counts = analyse_target_distribution(df_labeled)

    # Save the labeled dataset
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df_labeled.to_csv(output_file, index=False)

    except Exception as e:
        print("error saving fle")
        return

if __name__ == "__main__":
    main()