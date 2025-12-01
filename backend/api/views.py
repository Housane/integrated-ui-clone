# Django backend and def 2 rest api endpoints
# 1) SentimentAnalysisView - Validates  JSON for Headline and Summary, then sends it to the HF API and returns the aggregate score + probabilities of Positive, Negative or Neutral
# 2) StockPredictionView -  Input a Stock ticker and get the prediction (either buy, hold or sell the stock), together with confidence score
# rmb comment out debug print

import requests
import joblib
import numpy as np
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_alpha_vantage_indicator(symbol, function, apikey, **kwargs):
    url = "https://www.alphavantage.co/query"
    params = {"function": function, "symbol": symbol, "apikey": apikey} # Required param, which indicator, ticker and API key
    params.update(kwargs) # updates keyword arguments (merge additional param)
    try:
        r = requests.get(url, params=params, timeout=12) # implemented to prevent resources from waiting forever. At least this dosent ghost the user
        if r.status_code == 200:
            return r.json() # return json if successful
        else:
            return None
    except Exception as e:
        #print(f"Error fetching {function} from AlphaVantage: {e}")
        return None

# Fetch AlphaVantage Quote for volume, instead of OHLC + V
def fetch_alpha_vantage_quote(symbol, apikey):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": apikey
    }
    try: # Fetches the global_quote which essentially is price + volume
        r = requests.get(url, params=params, timeout=12) # to prevent ghosting the user duringt he GET reqest
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception as e:
        #print(f"Error fetching GLOBAL_QUOTE from AlphaVantage: {e}")
        return None

# Fetch news articles for a symbol from Finnhub within the last 'hours_window' hours
def fetch_finnhub_news(symbol, api_key, hours_window=12):
    try:
        now = datetime.utcnow()
        window_ago = now - pd.Timedelta(hours=hours_window) # Calculate the cutoff timestamp
        from_str = window_ago.strftime('%Y-%m-%d')
        to_str = now.strftime('%Y-%m-%d')
        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol,
            "from": from_str,
            "to": to_str,
            "token": api_key
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            #print(f"Finnhub news API error: {resp.status_code}")
            return []
        articles = resp.json()
        # Only keep articles within the actual time window
        news_list = []
        for article in articles:
            if "datetime" in article:
                news_time = datetime.utcfromtimestamp(article["datetime"])
                if news_time >= window_ago:
                    news_list.append(article)
        return news_list
    except Exception as e:
        #print(f"Error fetching news: {e}")
        return []

# call sentiment api for each article and return the avg sentiment.
def get_aggregated_news_sentiment(articles, api_base_url):
    sentiment_scores = []
    for article in articles:
        headline = article.get("headline") or article.get("title") or ""
        summary = article.get("summary") or ""
        if not (headline or summary):
            continue
        try:
            resp = requests.post(
                f"{api_base_url}/sentiment/",
                json={"headline": headline, "summary": summary},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                score = data.get('final_sentiment_score')
                if score is not None:
                    sentiment_scores.append(score)
        except Exception as e:
            #print(f"Sentiment API error: {e} for article: {headline}")
            if sentiment_scores:
                return float(sum(sentiment_scores)/len(sentiment_scores))
            else:
                return 0.0

class SentimentAnalysisView(APIView):
    def post(self, request):
        headline = request.data.get('headline', '')
        summary = request.data.get('summary', '')
        text = (headline + ' ' + summary).strip()
        if not text:
            return Response({'error': 'No text provided.'}, status=status.HTTP_400_BAD_REQUEST) # checks that some text was sent
        headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}"
        }
        url = "https://api-inference.huggingface.co/models/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
        response = requests.post(url, headers=headers, json={"inputs": text})
        if response.status_code != 200:
            return Response({'error': 'Hugging Face API error', 'details': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        sentiments = response.json()[0]  # should be a list of dicts
        # map scores into -1 for negative, neutral 0 and positive +1
        scores = {item['label']: item['score'] for item in sentiments}
        final_score = (-1 * scores.get('negative', 0)) + (0 * scores.get('neutral', 0)) + (1 * scores.get('positive', 0))
        return Response({ # must return both aggregate and indiv score
            "final_sentiment_score": final_score,
            "details": scores
        })


class StockPredictionView(APIView):
    def __init__(self):
        super().__init__()
        self.model = None
        self.feature_columns = None
        self.load_model()

    #Load trained model and feature columns
    def load_model(self):
        try:
            current_file = os.path.abspath(__file__)
            backend_dir = os.path.dirname(os.path.dirname(current_file))
            project_root = os.path.dirname(backend_dir)
            model_dir = os.path.join(project_root, 'Data Files', 'Models')

            model_path = os.path.join(model_dir, 'stock_prediction_model.pkl')
            features_path = os.path.join(model_dir, 'feature_columns.pkl')
            # Build full paths for the model and feature columns

            if not os.path.exists(model_path) or not os.path.exists(features_path):
                #print("Files not found at expected location")
                return

            self.model = joblib.load(model_path)
            self.feature_columns = joblib.load(features_path)
            #print(f"Feature columns ({len(self.feature_columns)}): {self.feature_columns}") -- Impt for debug

        except Exception as e:
            #print(f"Error loading model: {e}")
            self.model = None
            self.feature_columns = None

    #Fetch real-time stock data (OCLH) from finnhub, V + technicals from AlphaVantage (V, MACD, RSI, BB, OBV), and news sentiment
    def fetch_real_time_data(self, symbol):
        try:
            finnhub_api_key = getattr(settings, 'FINNHUB_API_KEY', None)
            alphavantage_api_key = getattr(settings, 'ALPHAVANTAGE_API_KEY', None)
            api_base_url = "http://localhost:8000/api" if "localhost" in os.environ.get("HOSTNAME", "") else "https://ggwoman-b3a74177016a.herokuapp.com/api"
            # local host component added for easy conversion btw local and deployed

            if not finnhub_api_key or not alphavantage_api_key:
                return None, "API key(s) not configured"

            # Get basic price data from Finnhub - OCLH
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={finnhub_api_key}"
            response = requests.get(quote_url, timeout=10)
            if response.status_code != 200:
                return None, f"Finnhub API error: {response.status_code}"
            quote_data = response.json()

            # Validate response
            if not quote_data or 'c' not in quote_data or quote_data['c'] == 0:
                return None, f"Invalid or missing price data from Finnhub: {quote_data}"

            # Getting OHLC frm Finnhub. AV will get V
            current_price = quote_data['c']
            high_price = quote_data['h']
            low_price = quote_data['l']
            open_price = quote_data['o']
            previous_close = quote_data['pc']

            # Get volume from AlphaVantage (will have more but compartmentalised to OCLHV + Technicals )
            quote_json = fetch_alpha_vantage_quote(symbol, alphavantage_api_key)
            if quote_json and "Global Quote" in quote_json:
                global_quote = quote_json["Global Quote"]
                volume = float(global_quote.get("06. volume", 0))
            else:
                volume = 0.0

            #Get indicators from AlphaVantage (latest daily) (MACD, RSI, BB, OBV)

            # MACD - Used MACDEXT to get around the Alphavantage Free Tier issue
            macd_json = fetch_alpha_vantage_indicator( symbol, 'MACDEXT', alphavantage_api_key, interval='daily', series_type='close', fastperiod=12, slowperiod=26, signalperiod=9, fastmatype=1, slowmatype=1, signalmatype=1)
            macd_data = macd_json.get('Technical Analysis: MACDEXT', {}) if macd_json else {}
            latest_macd = next(iter(macd_data.values()), {}) if macd_data else {}
            macd = float(latest_macd.get('MACD', 0))
            macd_signal = float(latest_macd.get('MACD_Signal', 0))
            macd_diff = float(latest_macd.get('MACD_Hist', 0))

            # RSI
            rsi_json = fetch_alpha_vantage_indicator(symbol, 'RSI', alphavantage_api_key, interval='daily', time_period=14, series_type='close')
            rsi_data = rsi_json.get('Technical Analysis: RSI', {}) if rsi_json else {}
            latest_rsi = next(iter(rsi_data.values()), {}) if rsi_data else {}
            rsi = float(latest_rsi.get('RSI', 0))

            # Bollinger Bands
            bb_json = fetch_alpha_vantage_indicator(symbol, 'BBANDS', alphavantage_api_key, interval='daily', time_period=20, series_type='close')
            bb_data = bb_json.get('Technical Analysis: BBANDS', {}) if bb_json else {}
            latest_bb = next(iter(bb_data.values()), {}) if bb_data else {}
            bb_bbm = float(latest_bb.get('Real Middle Band', 0))
            bb_bbh = float(latest_bb.get('Real Upper Band', 0))
            bb_bbl = float(latest_bb.get('Real Lower Band', 0))
            bb_bbwidth = float(bb_bbh - bb_bbl) if bb_bbh and bb_bbl else 0

            # OBV
            obv_json = fetch_alpha_vantage_indicator(symbol, 'OBV', alphavantage_api_key, interval='daily')
            obv_data = obv_json.get('Technical Analysis: OBV', {}) if obv_json else {}
            latest_obv = next(iter(obv_data.values()), {}) if obv_data else {}
            obv = float(latest_obv.get('OBV', 0))

            # Get avg news Sentiment
            articles = fetch_finnhub_news(symbol, finnhub_api_key)
            news_sentiment = get_aggregated_news_sentiment(articles, api_base_url)
            #print(f"Aggregated news sentiment for {symbol}: {news_sentiment}")

            # Compose features (sentiment is now real)
            features = {
                'open': float(open_price),
                'high': float(high_price),
                'low': float(low_price),
                'close': float(current_price),
                'volume': float(volume),
                'macd': macd,
                'macd_signal': macd_signal,
                'macd_diff': macd_diff,
                'rsi': rsi,
                'bb_bbm': bb_bbm,
                'bb_bbh': bb_bbh,
                'bb_bbl': bb_bbl,
                'bb_bbwidth': bb_bbwidth,
                'obv': obv,
                'news_sentiment': news_sentiment
            }

            #print(f"Features from APIs: {features}") # Make sure its not 0. If 0, means that it is not working
            return features, None

        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.RequestException as e:
            return None
        except Exception as e:
            return None

# Prediction for given ticker
    def post(self, request):
        # Check if model is loaded
        if not self.model or not self.feature_columns:
            print('Model not loaded properly')
            return Response({
                'error': 'Model not loaded. Check Django console for details.',
                'model_loaded': self.model is not None,
                'features_loaded': self.feature_columns is not None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get symbol from request
        symbol = request.data.get('symbol', '').upper().strip()
        if not symbol:
            return Response({
                'error': 'Symbol is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch real-time data
        features, error = self.fetch_real_time_data(symbol)
        if error:
            #print(f"data fetch error: {error}")
            return Response({
                'error': error
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Prepare features for model (ensure all required features are present)
            missing_features = [col for col in self.feature_columns if col not in features]
            if missing_features:
                #print(f"missing features: {missing_features}")
                return Response({
                    'error': f'Missing features: {missing_features}',
                    'available_features': list(features.keys()),
                    'required_features': self.feature_columns
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create feature vector in correct order
            feature_vector = [features[col] for col in self.feature_columns]
            feature_array = np.array(feature_vector).reshape(1, -1)

            # Makes prediction
            prediction = self.model.predict(feature_array)[0]
            prediction_proba = self.model.predict_proba(feature_array)[0]

            # mapping of the prediction
            prediction_map = {-1: 'SELL', 0: 'HOLD', 1: 'BUY'}
            prediction_label = prediction_map[prediction]

            # calc confidence/probability score
            classes = self.model.classes_
            confidence_scores = {
                prediction_map[classes[i]]: float(prediction_proba[i])
                for i in range(len(classes))
            }

            #print(f"Prediction: {prediction_label} ({prediction})")
            #print(f"Confidence: {confidence_scores}")

            return Response({
                'symbol': symbol,
                'prediction': prediction_label,
                'prediction_code': int(prediction),
                'confidence_scores': confidence_scores,
                'features_used': features,
                'timestamp': pd.Timestamp.now().isoformat(),
                'model_info': {
                    'features_count': len(self.feature_columns),
                    'classes': [prediction_map[c] for c in classes]
                }
            })

        except Exception as e:
            return Response({
                'error': f'Prediction error: {str(e)}',
                'features_received': features,
                'model_features': self.feature_columns
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)