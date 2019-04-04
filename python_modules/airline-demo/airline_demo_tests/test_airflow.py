import os

from dagster.utils import script_relative_path

from airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow, slow


####################################################################################################
# These tests are "in-memory" because although they use the Airflow APIs to execute dockerized
# DAG nodes, they don't run through the full Airflow machinery (a separate scheduler and executor
# process, or even the single-node out-of-process invocation of `airflow test`)
@slow
@airflow
class TestInMemoryAirflow_0IngestExecution:
    pipeline = define_airline_demo_ingest_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_ingest.yml')),
    ]

    def test_airflow_run_ingest_pipeline(self, in_memory_airflow_run, clean_results_dir):
        pass

@slow
@airflow
class TestInMemoryAirflow_1WarehouseExecution:
    pipeline = define_airline_demo_warehouse_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'local_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_airflow.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_warehouse.yml')),
    ]

    def test_airflow_run_warehouse_pipeline(self, in_memory_airflow_run, clean_results_dir):
        pass


####################################################################################################
