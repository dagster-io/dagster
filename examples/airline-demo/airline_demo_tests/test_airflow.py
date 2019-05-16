# pylint: disable=redefined-outer-name
import os

from dagster import ExecutionTargetHandle
from dagster.utils import script_relative_path

try:
    # pylint: disable=unused-import
    from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline
except ImportError:
    pass

from airline_demo.pipelines import (  # pylint: disable=unused-import
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow, slow  # pylint: disable=wrong-import-position


@slow
@airflow
class TestAirflowPython_0IngestExecution:
    exc_target_handle = ExecutionTargetHandle.for_pipeline_fn(define_airline_demo_ingest_pipeline)
    pipeline_name = 'airline_demo_ingest_pipeline'
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_ingest.yml')),
    ]
    mode = 'local'

    def test_airflow_run_ingest_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass


@slow
@airflow
class TestAirflowPython_1WarehouseExecution:
    exc_target_handle = ExecutionTargetHandle.for_pipeline_fn(
        define_airline_demo_warehouse_pipeline
    )
    pipeline_name = 'airline_demo_warehouse_pipeline'
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_warehouse.yml')),
    ]
    mode = 'local'

    def test_airflow_run_warehouse_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
