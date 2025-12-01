# Aim: Given a 13m price csv with technicals,

import pandas as pd
import os

# Finding Project root directory, need move 3 times
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# make these folders
PRICE_FOLDER = os.path.join(PROJECT_ROOT, "Data Files", "Price", "Processed")
NEWS_FOLDER = os.path.join(PROJECT_ROOT, "Data Files", "News Article")

TICKERS = [ #S&P sel, cover the industries essentially
    "AAPL", "AMZN", "DIS", "GOOGL", "JNJ",
    "JPM", "KO", "MSFT", "NVDA", "TSLA"
]

# IMPT! leave same format, just add the file names behind (with_indicators, complete_year, cleaned)

INDICATOR_SUFFIX = " - Sheet1_with_indicators.csv"
NEWS_SUFFIX = "_news_complete_year.csv"
CLEANED_SUFFIX = " - Sheet1_cleaned.csv"

indicator_cols = [ #Split into diff technicals
    'MACD', 'MACD_signal', 'MACD_diff',
    'RSI',
    'BB_bbm', 'BB_bbh', 'BB_bbl', 'BB_bbwidth',
    'OBV'
]

# fn must: read raw price and news csv, standardise column name and types, remove rows missing TI, make the date the same across sets
def clean_and_truncate(ticker):
    price_file = os.path.join(
        PRICE_FOLDER,
        f"13M Data {ticker}{INDICATOR_SUFFIX}"
    )

    news_file = os.path.join(
        NEWS_FOLDER,
        f"{ticker.lower()}{NEWS_SUFFIX}"
    )

    cleaned_output_file = os.path.join(
        PRICE_FOLDER,
        f"13M Data {ticker}{CLEANED_SUFFIX}"
    )

    # standardise the price file ('clean') column
    raw_df = pd.read_csv(price_file, encoding="latin1")
    # Strip and lowercase all column names (standardise), remove empty space
    raw_df.columns = [col.strip().lower() for col in raw_df.columns]
    # print(f"{ticker}: Cleaned price columns: {raw_df.columns.tolist()}") - for debug use
    if 'date' not in raw_df.columns:
        raise Exception(f"No 'date' column found in price file for {ticker}!") #for debug use

    raw_df['date'] = pd.to_datetime(raw_df['date'])

    # same as price, for standardisation
    news_df = pd.read_csv(news_file, encoding="latin1")
    news_df.columns = [col.strip().lower() for col in news_df.columns]
    # print(f"{ticker}: Cleaned news columns: {news_df.columns.tolist()}") for debug use
    if 'date' not in news_df.columns:
        raise Exception(f"No 'date' column found in news file for {ticker}!")
    news_df['date'] = pd.to_datetime(news_df['date'])

    #Remove missing indicators (match lowercased columns) -- Important for MACD EMA Data esp
    indicator_cols_lower = [col.lower() for col in indicator_cols]
    # keep indicator columns that exists in file
    existing_indicator_cols = [col for col in indicator_cols_lower if col in raw_df.columns]
    raw_df = raw_df.dropna(subset=existing_indicator_cols)

    # Keep only dates in both datasets - else might have poor data (dates w/o news but in reality have news)
    price_dates = set(raw_df['date'].dt.normalize())
    news_dates = set(news_df['date'].dt.normalize())
    common_dates = price_dates & news_dates
    mask = raw_df['date'].dt.normalize().isin(common_dates)
    cleaned_df = raw_df[mask].copy().sort_values('date')

    cleaned_df.to_csv(cleaned_output_file, index=False)
    # print(f"{ticker}: cleaned {len(cleaned_df)} rows saved to {cleaned_output_file}") - for debug use

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            clean_and_truncate(ticker)
        except Exception as e:
            pass
            #print(f"{ticker}: ERROR - {e}")
