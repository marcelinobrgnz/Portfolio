"""Validate Airflow DAG bag imports without syntax errors."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("airflow")

ROOT = Path(__file__).resolve().parent.parent
os.environ["AIRFLOW_HOME"] = str(ROOT / ".airflow_home")


def test_dag_bag_imports():
  from airflow.models import DagBag

  dag_bag = DagBag(dag_folder=str(ROOT / "dags"), include_examples=False)
  assert not dag_bag.import_errors, f"DAG import errors: {dag_bag.import_errors}"
  assert "wine_feature_pipeline" in dag_bag.dags
  assert "taxi_etl_pipeline" in dag_bag.dags

  wine_dag = dag_bag.dags["wine_feature_pipeline"]
  assert len(wine_dag.tasks) == 5
  task_ids = {t.task_id for t in wine_dag.tasks}
  assert "trigger_p1_retrain" in task_ids
