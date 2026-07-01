"""Train an XGBoost wine quality classifier and log to MLflow."""

from __future__ import annotations

import argparse
import json

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.config import (
    FEATURE_COLUMNS,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
    MODEL_METADATA_PATH,
    MODEL_PATH,
    MODELS_DIR,
    REGISTERED_MODEL_NAME,
    TARGET_COLUMN,
)
from src.data import load_training_data, prepare_features, save_reference_dataset


def _quality_to_tier(quality: np.ndarray) -> np.ndarray:
    """Map 3–9 quality scores to low / medium / high tiers for classification."""
    return np.where(quality <= 5, 0, np.where(quality <= 7, 1, 2))


def train(
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 200,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    register_model: bool = True,
    data_source: str = "auto",
    feature_store_path: str | None = None,
) -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    df = load_training_data(data_source=data_source, feature_store_path=feature_store_path)
    save_reference_dataset(df)

    X, y_raw = prepare_features(df)
    y = _quality_to_tier(y_raw.to_numpy())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    params = {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "learning_rate": learning_rate,
        "random_state": random_state,
        "test_size": test_size,
        "objective": "multi:softprob",
        "num_class": 3,
        "eval_metric": "mlogloss",
    }

    with mlflow.start_run(run_name="xgboost-wine-quality") as run:
        model = XGBClassifier(**{k: v for k, v in params.items() if k != "test_size"})
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "f1_macro": float(f1_score(y_test, y_pred, average="macro")),
        }

        mlflow.log_param("data_source", data_source)
        if feature_store_path:
            mlflow.log_param("feature_store_path", feature_store_path)

        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.log_param("feature_columns", ",".join(FEATURE_COLUMNS))
        mlflow.log_param("target", "quality_tier")

        report = classification_report(y_test, y_pred, output_dict=True)
        report_path = MODELS_DIR / "classification_report.json"
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2))
        mlflow.log_artifact(str(report_path))

        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name=REGISTERED_MODEL_NAME if register_model else None,
            input_example=X_train.head(3),
        )

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)

        metadata = {
            "run_id": run.info.run_id,
            "model_name": REGISTERED_MODEL_NAME,
            "feature_columns": FEATURE_COLUMNS,
            "target_column": TARGET_COLUMN,
            "quality_tiers": {"low": "3-5", "medium": "6-7", "high": "8-9"},
            "metrics": metrics,
            "params": params,
        }
        MODEL_METADATA_PATH.write_text(json.dumps(metadata, indent=2))
        mlflow.log_artifact(str(MODEL_METADATA_PATH))

        return {
            "run_id": run.info.run_id,
            "metrics": metrics,
            "model_path": str(MODEL_PATH),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train wine quality classifier")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument(
        "--no-register",
        action="store_true",
        help="Skip MLflow model registry",
    )
    parser.add_argument(
        "--data-source",
        choices=["auto", "csv", "feature_store"],
        default="auto",
    )
    parser.add_argument("--feature-store-path", default=None)
    args = parser.parse_args()

    result = train(
        test_size=args.test_size,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        register_model=not args.no_register,
        data_source=args.data_source,
        feature_store_path=args.feature_store_path,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
