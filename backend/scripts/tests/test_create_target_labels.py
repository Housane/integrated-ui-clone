import pandas as pd
from backend.scripts.create_target_labels import create_target_labels

def test_create_target_labels(): # forces it to be run as a test
    mock_data = {
        "date": ["2025-01-03", "2025-01-04", "2025-01-05", "2025-01-06"],
        "ticker": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "close": [100, 102, 104, 90] # price up by 2 each day, but since we are looking for 2% each day, will not work
    }
    df = pd.DataFrame(mock_data)
    result = create_target_labels(df, future_days=1, buy_threshold=0.02, sell_threshold=-0.02)

    # check if labels are correct, test 1 buy, 1 hold and 1 sell. `
    assert result.loc[0, 'target'] == 1, "Expected Buy label" # Buy (1) is the correct action,
    assert result.loc[1, 'target'] == 0, "Expected Hold label" # Other 2 are the same
    assert result.loc[2, 'target'] == -1, "Expected Sell label"
