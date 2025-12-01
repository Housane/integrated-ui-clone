import pandas as pd
from backend.scripts.train_model import prepare_features

# Note: This component is for Feature Preparation part of the Train Model file.

def test_prepare_features_missing_values():
    # missing values included w mock data
    mock_data = {
        "MACD": [0.5, None, 0.8],
        "RSI": [70, 60, None],
        "BB_bbm": [100, 101, 102],
        "BB_bbh": [105, None, 110],
        "BB_bbl": [95, 96, None],
        "OBV": [1000, None, 1500],
        "target": [1, -1, 0], #aka what we will predict
        "date": ["2025-06-25", "2025-06-26", "2025-06-27"],
        "ticker": ["AAPL", "AAPL", "AAPL"]
    }
    df = pd.DataFrame(mock_data)

    # Run feature preparation thru extracting feature columns, fills missing values
    X, feature_cols = prepare_features(df)

    #assert missing values are filled
    assert X.isnull().values.any() == False, "Missing values were not filled" # essentially, if tf there are NO empty space, condition is passed
    assert len(feature_cols) > 0, "Feature columns not identified correctly" # if you delete all feature col, then will return error