"""Training pipeline smoke tests."""

from pathlib import Path

import pandas as pd

from src.config import FEATURE_COLUMNS, TARGET_COLUMN
from src.data import load_raw_wine_data, prepare_features, save_reference_dataset


def test_load_wine_data_has_expected_columns(tmp_path: Path):
    df = load_raw_wine_data(data_dir=tmp_path)
    for col in FEATURE_COLUMNS + [TARGET_COLUMN]:
        assert col in df.columns
    assert len(df) > 1000


def test_prepare_features_shape(tmp_path: Path):
    df = load_raw_wine_data(data_dir=tmp_path)
    X, y = prepare_features(df)
    assert X.shape[1] == len(FEATURE_COLUMNS)
    assert len(y) == len(X)


def test_save_reference_parquet(tmp_path: Path):
    df = load_raw_wine_data(data_dir=tmp_path)
    path = save_reference_dataset(df, tmp_path / "reference.parquet")
    assert path.exists()
    loaded = pd.read_parquet(path)
    assert len(loaded) == len(df)
