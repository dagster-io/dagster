# pylint: disable=redefined-outer-name
import os

from dagster.utils import script_relative_path
try:
    from dagster_airflow.test_fixtures import dagster_airflow_python_operator_pipeline
except ImportError:
    pass

from airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow, slow


@slow
@airflow
class TestAirflowPython_0IngestExecution:
    pipeline = define_airline_demo_ingest_pipeline()
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_ingest.yml')),
    ]

    def test_airflow_run_ingest_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass


@slow
@airflow
class TestAirflowPython_1WarehouseExecution:
    pipeline = define_airline_demo_warehouse_pipeline()
    config_yaml = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_warehouse.yml')),
    ]

    def test_airflow_run_warehouse_pipeline(self, dagster_airflow_python_operator_pipeline):
        pass
