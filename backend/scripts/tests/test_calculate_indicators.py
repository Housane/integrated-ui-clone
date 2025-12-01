import pandas as pd
from backend.scripts.calculate_indicators import calculate_indicators

def test_calculate_indicators_valid_data():
    mock_data = {
        "date": ["2025-01-03", "2025-01-04"],
        "open": [100, 105],
        "high": [110, 108],
        "low": [99, 104],
        "close": [105, 107],
        "volume": [1000, 1500]
    }
    df = pd.DataFrame(mock_data)
    result = calculate_indicators(df)

    # checks for the existance of technical indicator columns
    expected_columns = ['MACD', 'MACD_signal', 'MACD_diff', 'RSI', 'BB_bbm', 'BB_bbh', 'BB_bbl', 'BB_bbwidth', 'OBV']
    for column in expected_columns:
          assert column in result.columns, f"Missing column: {column}" #if its not the same, will raise error