import argparse
import os
import subprocess
import sys
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sagemaker_training import environment

# Ensure a container-compatible version of xgboost is installed
subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost<2.0.0"])
import xgboost as xgb  # type: ignore

def train_model():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAINING'))
    parser.add_argument('--validation', type=str, default=os.environ.get('SM_CHANNEL_VALIDATION'))
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--eta', type=float, default=0.3)
    parser.add_argument('--num-round', type=int, default=100)
    
    args = parser.parse_args()
    
    # Load data
    train_data = pd.read_parquet(f"{args.train}/train.parquet")
    val_data = pd.read_parquet(f"{args.validation}/val.parquet")

    # Basic type casting for known numeric fields
    for col in ["rating", "price_raw"]:
        if col in train_data.columns:
            train_data[col] = train_data[col].astype(float)
            val_data[col] = val_data[col].astype(float)
    if "has_brand" in train_data.columns:
        train_data["has_brand"] = train_data["has_brand"].astype(int)
        val_data["has_brand"] = val_data["has_brand"].astype(int)

    # Encode categorical/object columns as integer indices for XGBoost
    cat_cols = [
        c
        for c in ["user_id", "item_id", "event_type", "main_category", "price_bucket"]
        if c in train_data.columns
    ]
    if cat_cols:
        combined = pd.concat([train_data, val_data], axis=0, ignore_index=True)
        for c in cat_cols:
            codes, _ = pd.factorize(combined[c])
            combined[c + "_idx"] = codes.astype("int32")
        combined = combined.drop(columns=cat_cols)
        n_train = len(train_data)
        train_data = combined.iloc[:n_train].reset_index(drop=True)
        val_data = combined.iloc[n_train:].reset_index(drop=True)

    # Feature / label split
    X_train = train_data.drop(["label"], axis=1)
    y_train = train_data["label"]
    X_val = val_data.drop(["label"], axis=1)
    y_val = val_data["label"]
    
    # Train XGBoost model
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    # Use logloss as a stable objective metric for HPO (AUC can be NaN with all-positive labels)
    params = {
        'max_depth': args.max_depth,
        'eta': args.eta,
        'objective': 'binary:logistic',
        'eval_metric': 'logloss'
    }
    
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=args.num_round,
        evals=[(dtrain, 'train'), (dval, 'val')],
        early_stopping_rounds=10
    )
    
    # Save model
    model_path = os.path.join(args.model_dir, 'model.pkl')
    pickle.dump(model, open(model_path, 'wb'))
    
    print("Training completed successfully")

if __name__ == '__main__':
    train_model()