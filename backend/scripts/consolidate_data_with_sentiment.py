# Used to process stock data from multiple CSV files into one training dataset + gather news sentiment data via API
#need to use existing django sentiment component (hf api)
# New Sentiment Data Logic
# News Exists: Calculate as per normal. News does not exist: Assign 0
# Start from June 26, 2024, because most news start from then

import pandas as pd
import numpy as np
import os
import requests
import time
from datetime import datetime


# Finding Project root directory, need move 3 times, same as others
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# Make sure they exist, else make
PRICE_FOLDER = os.path.join(PROJECT_ROOT, "Data Files", "Price", "Processed")
NEWS_FOLDER = os.path.join(PROJECT_ROOT, "Data Files", "News Article")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "Data Files", "Consolidated")

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Stock tickers
TICKERS = [
    "AAPL", "AMZN", "DIS", "GOOGL", "JNJ",
    "JPM", "KO", "MSFT", "NVDA", "TSLA"
]

# File naming patterns
PRICE_SUFFIX = " - Sheet1_with_indicators.csv"
NEWS_SUFFIX = "_news_complete_year.csv"

#start date ( news start date across all tickers)
START_DATE = "26/06/2024"

# API for sentiment
SENTIMENT_API_URL = "http://127.0.0.1:8000/api/sentiment/"
BATCH_SIZE = 100  #batch processing to avoid overloading


# Parse date string in DD/MM/YYYY format
def parse_date(date_str):
    try:
        return datetime.strptime(date_str.split()[0], '%d/%m/%Y') # parse into dd/mm/yyyy
    except:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y') # No split
        except:
            return None #will remove invalid roles

#Get sentiment score from Django API
def get_sentiment_score(headline, summary=""):
    try:
        payload = {
            'headline': str(headline) if headline else "",
            'summary': str(summary) if summary else ""
        }

        response = requests.post(SENTIMENT_API_URL, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get('final_sentiment_score', 0)
        else:
            return 0
    # handles connection/timeouts
    except requests.exceptions.RequestException as e:
        return 0
    except Exception as e:
        return 0

#Process news dataframe and add sentiment scores
def process_news_sentiment(news_df, ticker):
    if news_df is None or len(news_df) == 0:
        return None # none returned if no news

    # start off with the same data as news_df but is distinct in memory [aka its own obj] to prevent mutation
    df = news_df.copy()

    # Initialize sentiment column
    df['sentiment_score'] = 0.0

    #process in batches to prevent the error which happened
    total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
    successful_sentiments = 0 # for debug purposes

    for i in range(0, len(df), BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch_end = min(i + BATCH_SIZE, len(df))
        batch = df.iloc[i:batch_end]

        for idx, row in batch.iterrows():
            headline = row.get('headline', '')
            summary = row.get('summary', '')
            sentiment = get_sentiment_score(headline, summary) # Get sentiment score
            df.at[idx, 'sentiment_score'] = sentiment

            if sentiment != 0:
                successful_sentiments += 1 #essentially for debug

            # delay mechanism, 0.2s
            time.sleep(0.2)
    return df

# Load price data with technical indicators for a specific ticker
def load_price_data(ticker):
    file_path = os.path.join(PRICE_FOLDER, f"13M Data {ticker}{PRICE_SUFFIX}")
    try:
        df = pd.read_csv(file_path, encoding="latin1")

        #clean column names
        df.columns = [col.strip().lower() for col in df.columns]

        # Parse dates (to remove time)
        df['date_parsed'] = df['date'].apply(parse_date)
        df = df.dropna(subset=['date_parsed'])

        #filter from start date (def above) onw
        start_dt = parse_date(START_DATE)
        df = df[df['date_parsed'] >= start_dt].copy()

        # Add ticker column
        df['ticker'] = ticker

        # all the columns + date parsed
        price_columns = [
            'date', 'date_parsed', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'macd', 'macd_signal', 'macd_diff', 'rsi',
            'bb_bbm', 'bb_bbh', 'bb_bbl', 'bb_bbwidth', 'obv'
        ]

        df = df[price_columns]
        return df

    except Exception as e:
        print(f"Error loading {ticker} price data: {e}")
        return None

#Load news data and calculate sentiment scores
def load_news_data(ticker):
    file_path = os.path.join(NEWS_FOLDER, f"{ticker.lower()}{NEWS_SUFFIX}")
    try:
        df = pd.read_csv(file_path, encoding="latin1")

        # Clean column names
        df.columns = [col.strip().lower() for col in df.columns]

        # Parse dates
        df['date_parsed'] = df['date'].apply(parse_date)
        df = df.dropna(subset=['date_parsed'])

        # Filter from start date
        start_dt = parse_date(START_DATE)
        df = df[df['date_parsed'] >= start_dt].copy()

        if len(df) == 0:
            return None

        # Process sentiment for the tickers news
        df_with_sentiment = process_news_sentiment(df, ticker)

        if df_with_sentiment is None:
            return None

        # Group by date and calculate average sentiment
        daily_sentiment = df_with_sentiment.groupby('date_parsed')['sentiment_score'].mean().reset_index()
        daily_sentiment.rename(columns={'sentiment_score': 'news_sentiment'}, inplace=True)

        return daily_sentiment

    except Exception as e:
        return None

#Consolidate price and news data for a single ticker, then aftw x10 (aft this fn)
def consolidate_ticker_data(ticker):
    #load price data
    price_df = load_price_data(ticker)
    if price_df is None:
        return None

    # Load news data with sentiment
    news_df = load_news_data(ticker)

    # Merge price and news data
    if news_df is not None:
        # Merge on date_parsed
        merged_df = pd.merge(price_df, news_df, on='date_parsed', how='left')

        # no news data => sentiment = 0
        merged_df['news_sentiment'] = merged_df['news_sentiment'].fillna(0)

        # Count days with news vs without
        news_days = (merged_df['news_sentiment'] != 0).sum()
        no_news_days = (merged_df['news_sentiment'] == 0).sum()
        print(f"Days with news: {news_days}") # for you to know -- Impt to prevent mulfunction
        print(f"Days without news: {no_news_days}")

    else:
        # No news data available - set sentiment to 0
        price_df['news_sentiment'] = 0
        merged_df = price_df

    # Sort by date
    merged_df = merged_df.sort_values('date_parsed')
    return merged_df

# consoldiate data for all tickers
def consolidate_all_data():
    # Debug use - test API connection. API Key alr checked
    try:
        test_response = requests.post(SENTIMENT_API_URL, json={'headline': 'test', 'summary': ''}, timeout=5)
        if test_response.status_code == 200:
            print("HF Sentiment API connection successful")
        else:
            print(f"Sentiment API test failed: {test_response.status_code}")
    except Exception as e:
        print(f"Sentiment API not accessible: {e}")
        return None

    all_data = []
    successful_tickers = []
    failed_tickers = []

    for ticker in TICKERS:
        ticker_data = consolidate_ticker_data(ticker)

        if ticker_data is not None:
            all_data.append(ticker_data)
            successful_tickers.append(ticker)
        else:
            failed_tickers.append(ticker)

    if not all_data:
        return None

    #combine all ticker data
    consolidated_df = pd.concat(all_data, ignore_index=True)

    # clean + sort data
    consolidated_df = consolidated_df.sort_values(['ticker', 'date_parsed'])

    # remove date_parsed column for final output
    final_columns = [
        'date', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'macd', 'macd_signal', 'macd_diff', 'rsi', 'bb_bbm',
        'bb_bbh', 'bb_bbl', 'bb_bbwidth', 'obv', 'news_sentiment'
    ]

    consolidated_df = consolidated_df[final_columns]

    # Save consolidated data
    output_file = os.path.join(OUTPUT_FOLDER, "(OG 10 Stocks) consolidated_data_with_sentiment.csv")
    consolidated_df.to_csv(output_file, index=False)

    # Get proper date range
    dates = consolidated_df['date'].apply(parse_date)
    dates = dates.dropna()
    if len(dates) > 0:
        min_date = dates.min().strftime('%d/%m/%Y')
        max_date = dates.max().strftime('%d/%m/%Y')
        print(f" Date range: {min_date} to {max_date}") #Impt for seeing truncation (13m -> <12m)

    # Techncal indicator summary (aka ensuring that every price has a corr Technical indicator to ensure proper analysis)
    for col in ['macd', 'rsi', 'bb_bbm', 'obv']:
        non_null = consolidated_df[col].notna().sum()
        total = len(consolidated_df)
        print(f"   {col.upper()}: {non_null:,}/{total:,} ({non_null / total * 100:.1f}%)")

    # Sentiment score statistics - just to ensure the data is evenly spread out
    sentiment_scores = consolidated_df[consolidated_df['news_sentiment'] != 0]['news_sentiment']
    if len(sentiment_scores) > 0:
        print(f"   Mean: {sentiment_scores.mean():.3f}")
        print(f"   Std: {sentiment_scores.std():.3f}")
        print(f"   Min: {sentiment_scores.min():.3f}")
        print(f"   Max: {sentiment_scores.max():.3f}")

    return consolidated_df


if __name__ == "__main__":
    consolidated_data = consolidate_all_data()

    if consolidated_data is not None:
        print("fail lmao")
    else:
        print("Great Success - Borat")
