import os

from dagster.utils import script_relative_path

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import airflow


####################################################################################################
# These tests are "in-memory" because although they use the Airflow APIs to execute dockerized
# DAG nodes, they don't run through the full Airflow machinery (a separate scheduler and executor
# process, or even the single-node out-of-process invocation of `airflow test`)
@airflow
class TestInMemoryAirflow_0DownloadDagExecution:
    pipeline = define_airline_demo_download_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_fast_download.yml')),
    ]

    def test_airflow_run_download_pipeline(self, in_memory_airflow_run):
        pass


@airflow
class TestInMemoryAirflow_1IngestExecution:
    pipeline = define_airline_demo_ingest_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_ingest.yml')),
    ]

    def test_airflow_run_ingest_pipeline(self, in_memory_airflow_run):
        pass


@airflow
class TestInMemoryAirflow_2WarehouseExecution:
    pipeline = define_airline_demo_warehouse_pipeline()
    config = [
        script_relative_path(os.path.join('..', 'environments', 'airflow_base.yml')),
        script_relative_path(os.path.join('..', 'environments', 'local_warehouse.yml')),
    ]

    def test_airflow_run_warehouse_pipeline(self, in_memory_airflow_run):
        pass


####################################################################################################
