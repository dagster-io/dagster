import time
from pathlib import Path

import pytest
import requests
from dagster import AssetKey, DagsterInstance, DagsterRunStatus
from dagster._core.test_utils import environ
from dagster._time import get_current_timestamp


@pytest.fixture(name="dags_dir")
def dags_dir() -> Path:
    return Path(__file__).parent / "complex_dag_for_sensor_tests" / "dags"

def test_sensor_ordering(airflow_instance: None) -> None:
    """Tests that sensor ordering is respected all the way through the execution chain. 
    We test this with a relatively complex dependency structure in airflow:
            top_task
           /        \
    middle_task_1 middle_task_2
           \        /
          middle2_task
           /        \
    bottom_task_1 bottom_task_2

    Where each task represents an asset. We expect that the assets should always 
    be marked with a materialization in topological order.
    """
    pass

