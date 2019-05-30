# pylint: disable=redefined-outer-name
import os

import pytest

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path

try:
    # pylint: disable=unused-import
    from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline
except ImportError:
    pass

from dagster_examples.airline_demo.pipelines import (  # pylint: disable=unused-import
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)


@pytest.mark.slow
@pytest.mark.airflow
class TestAirflowPython_0IngestExecution:
    handle = ExecutionTargetHandle.for_pipeline_fn(define_airline_demo_ingest_pipeline)
    pipeline_name = 'airline_demo_ingest_pipeline'
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yaml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yaml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_ingest.yaml')),
    ]
    mode = 'local'

    def test_airflow_run_ingest_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass


@pytest.mark.slow
@pytest.mark.airflow
class TestAirflowPython_1WarehouseExecution:
    handle = ExecutionTargetHandle.for_pipeline_fn(define_airline_demo_warehouse_pipeline)
    pipeline_name = 'airline_demo_warehouse_pipeline'
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yaml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yaml')),
        script_relative_path(os.path.join('..', 'environments', 'local_warehouse.yaml')),
    ]
    mode = 'local'

    def test_airflow_run_warehouse_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
