# DO NOT run this document on Web Deployment, run it locally ONLY. This links to the local django server, not to the online one
# To modify, change those 127.0.0.1... to ${apiBase}/sentiment/ for sentiment

import pandas as pd
import requests
import time
import os

# ensure django backend can be accessed
def test_backend_connection():
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/sentiment/",
            json={"headline": "Test headline", "summary": "Test summary"},
            timeout=5 # Sends a single test post to sentiment with dummy text, with 5s timeout
        )
        if response.status_code == 200: # means that the Backend is working
            return True
        else: # If not 200, backend is not working
            #print(f"Backend not working {response.status_code}")
            return False
    except Exception as e: #catch all errors
        return False

# Analyse sentiment for a batch of articles
def analyse_sentiment_batch(headlines, summaries):
    results = []

    for i, (headline, summary) in enumerate(zip(headlines, summaries)):
        try:
            # Clean the data
            headline = str(headline) if pd.notna(headline) else "" # if NaN, convert into "" to avoid sending None (will be interpreted as Sentiment = 0)
            summary = str(summary) if pd.notna(summary) else ""

            # Call Django API
            response = requests.post(
                "http://127.0.0.1:8000/api/sentiment/",
                json={"headline": headline, "summary": summary},
                timeout=10
            )
# essentially, anyt wrong js give sentiment = 0
            if response.status_code == 200:
                data = response.json()
                sentiment_score = data.get('final_sentiment_score', 0)
                results.append(sentiment_score)
            else:
                results.append(0)  # Default neutral sentiment

        except Exception as e:
            results.append(0)  # Default neutral sentiment

        # Rate limiting because API sometimes lags/cnnt process
        time.sleep(0.05)  # 50ms delay between requests

    return results


def main():
    if not test_backend_connection(): #if server is not working then we stop
        return

    # master dataset (contains all stock news)
    input_file = 'all_stocks_news_master_dataset.csv'

    try:
        df = pd.read_csv(input_file)
        #print(f"Loaded {len(df):,} articles from {input_file}") # for debug use
    except FileNotFoundError:
        #print("file not found")
        return

    # Process in batches to avoid overwhelming the API
    batch_size = 100
    all_sentiment_scores = []

    for batch_start in range(0, len(df), batch_size):
        batch_end = min(batch_start + batch_size, len(df))

        batch_headlines = df.iloc[batch_start:batch_end]['Headline'].tolist()
        batch_summaries = df.iloc[batch_start:batch_end]['Summary'].tolist()

        batch_results = analyse_sentiment_batch(batch_headlines, batch_summaries)
        all_sentiment_scores.extend(batch_results)

    # append computed scores to a new column
    df['sentiment_score'] = all_sentiment_scores

    # save to a new csv
    output_file = 'all_stocks_news_with_sentiment.csv'
    df.to_csv(output_file, index=False)

    # summary showing just to ensure its running fine
    #sentiment_stats = df['sentiment_score'].describe()
    #print("Sentiment Score Stats:")
    #print(f" Mean: {sentiment_stats['mean']:.3f}")
    #print(f" Min: {sentiment_stats['min']:.3f}")
    #print(f" Max: {sentiment_stats['max']:.3f}")

if __name__ == "__main__":
    main()