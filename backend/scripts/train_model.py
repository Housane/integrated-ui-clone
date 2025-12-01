# Learning Method: Random Decision Forests. Since this is a classification (decide amongst 3 states), the output of the random
# forest is the class which would be selected by the most amount of trees (aka the highest out oof the 3 choices)
# Test and Learning data are from the same table, 80% Training Set, 20% Test Set.

# Main idea: How does 3-fold cross validation work? Split the Training set (80%) into 3 near equal/equal chunks, F1, F2, F3
# Rnd 1: Train on F1 + F2, Validate on F3, Rnd 2: Train on F2 + F3, Validate on F1, Rnd 3: Train on F3 + F1, Validate on F2
# Validation Accu is aggregated, 3 fold is slightly more efficient than 5 or 10 fold.

import pandas as pd # Data Handling
import numpy as np # Data Handling
from sklearn.ensemble import RandomForestClassifier # Main model
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV # data splitting, cross validation and grid search for hyperparam tuning
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score # Performance metrics
import joblib # save trained model and related stuff
import os
from datetime import datetime

# Main intuition => Instead of manually hard coding a MACD, RSI, BB range or OBV, model will ownself find out the best value and make a decision from there

def prepare_features(df):
    # feature columns (exclude target, date, ticker, and future_return), this way predictive columns remain
    exclude_cols = ['target', 'date', 'ticker', 'future_return']
    feature_cols = [col for col in df.columns if col not in exclude_cols]

    print(f"Total features available: {len(feature_cols)}") # to confirm and ensure its 15 avail

    # Handle missing values
    X = df[feature_cols].copy()

    # Fill missing values with forward fill, then backward fill, then 0
    X = X.fillna(method='ffill').fillna(method='bfill').fillna(0)

    # Check for infinite values and replace with NaN, then fill
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    print(f"Features prepared: {X.shape}") # shows how many features will be fed to model
    return X, feature_cols


def train_random_forest_model(X, y):
# Random Forest training with Hyperparam Tuning
# Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y # 80% Trng, 20% Test, 42 is just a random seed number to guarantee reproducibility.
        # vv impt to stratify by Y to ensure than the proportion of splits in training and test are the same. (prevent skewed data)
    )

    # Show the number of samples in each split
    print(f"Training set: {X_train.shape[0]:,} samples")
    print(f"Test set: {X_test.shape[0]:,} samples")

    # Hyperparameter tuning
    param_grid = { # Chosen arbitarily, by default n estimators is 100, None for Max Depth, split is 2, leaf is 1, max features is sqrt
        'n_estimators': [100, 200], # End up choosing 200
        'max_depth': [10, 11, 12, 13, 14, 15], # End Up choosing 11
        'min_samples_split': [5, 10, 15], # End up choosing 15
        'min_samples_leaf': [2, 4, 6], # End up choosing 6
        'max_features': ['sqrt'] # Default
    }
# Random forest
    rf_base = RandomForestClassifier(random_state=42, n_jobs=-1, class_weight='balanced')
    grid_search = GridSearchCV(
        rf_base, param_grid, cv=3, scoring='accuracy', # wrapping a base rf in GridSearchCV for a 3-fold cross validation
        n_jobs=-1, verbose=1
    )

    grid_search.fit(X_train, y_train) # Forces it to loop over the combi in param grid then do Inner CV, compute mean validation accuracies,
# and select the best params (with highest cv accuracy). Will then  retrain on all of (X train and Y train)

    # Best model
    best_rf = grid_search.best_estimator_
    print(f"Best parameters: {grid_search.best_params_}") # Ref to comments at Hyperparam testing component

    # Evaluate model
    train_score = best_rf.score(X_train, y_train)
    test_score = best_rf.score(X_test, y_test)

    # Logged under Readme
    print(f"Training accuracy: {train_score:.3f}") # Tng Accuracy => 0.897 (Aft Mod: 0.803)
    print(f"Test accuracy: {test_score:.3f}") # Test Accuracy => 0.536 (Aft Mod: 0.501)

    # Cross-validation
    cv_scores = cross_val_score(best_rf, X_train, y_train, cv=5)
    print(f"CV accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})") # CV Accuracy => 0.548 +/- 0.055 (Aft Mod: 0.488)

    # Predictions
    y_pred = best_rf.predict(X_test)

    # Detailed classification report
    print(f"\n Detailed stats:")
    target_names = ['SELL', 'HOLD', 'BUY']
    print(classification_report(y_test, y_pred, target_names=target_names)) # Precision, reall, f1 score per class (Sell, Hold, Buy)

    return best_rf, X_test, y_test, y_pred # Return retrained model

# Analyse and show feature importance
def analyse_feature_importance(model, feature_cols):
    # Get feature importance
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_ #extracts feature importance from rf
    }).sort_values('importance', ascending=False)

    print(f"List of Features + Gini Importance:") #essentially, a high impt class is when you split, it helps the classifier separate class effectively
    print(importance_df.head(15).to_string(index=False))

    return importance_df

# Impt - Used to save the model + relevant files
def save_model_artifacts(model, feature_importance, feature_cols):
    # Create models folder for it to be stored
    models_dir = '../../Data Files/Models'
    os.makedirs(models_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(models_dir, 'stock_prediction_model.pkl')
    joblib.dump(model, model_path)

    # Save feature importance
    importance_path = os.path.join(models_dir, 'feature_importance.csv')
    feature_importance.to_csv(importance_path, index=False)

    # Save feature columns
    features_path = os.path.join(models_dir, 'feature_columns.pkl')
    joblib.dump(feature_cols, features_path)

    # Save model metadata
    metadata = {
        'created_date': datetime.now().isoformat(),
        'model_type': 'RandomForestClassifier',
        'n_features': len(feature_cols),
        'target_classes': ['SELL (-1)', 'HOLD (0)', 'BUY (1)']
    }

    metadata_path = os.path.join(models_dir, 'model_metadata.json')
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def main(): #essentially the main function which calls the other fn above
    # Load the labeled training data
    input_file = '../../Data Files/Consolidated/ml_training_data.csv'

    if not os.path.exists(input_file):
        return

    df = pd.read_csv(input_file)

    # Prepare features
    X, feature_cols = prepare_features(df)
    y = df['target']

    print(f"\n Buy/Hold/Sell Distribution")
    target_counts = y.value_counts().sort_index()
    for target, count in target_counts.items():
        label = "SELL" if target == -1 else "HOLD" if target == 0 else "BUY"
        print(f"{target:2d} ({label}): {count:4,} samples")

    # Train model
    print("Model Training Starts")
    model, X_test, y_test, y_pred = train_random_forest_model(X, y)

    # Analyse feature importance
    feature_importance = analyse_feature_importance(model, feature_cols)

    # Save everything
    save_model_artifacts(model, feature_importance, feature_cols)


if __name__ == "__main__":
    main() # Main running