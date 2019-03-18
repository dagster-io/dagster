import datetime

from dagster import execute_pipeline

from dagster.utils import script_relative_path
from dagster.utils.yaml_utils import load_yaml_from_glob_list

from airline_demo.pipelines import (
    define_airline_demo_download_pipeline,
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import db, nettest, slow, spark


@nettest
@slow
def test_pipeline_download():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/local_base.yml'),
            script_relative_path('../environments/local_fast_download.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_download_pipeline(), config_object)

    assert result.success


@slow
@spark
def test_pipeline_ingest():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/local_base.yml'),
            script_relative_path('../environments/local_ingest.yml'),
        ]
    )

    result = execute_pipeline(define_airline_demo_ingest_pipeline(), config_object)
    assert result.success


@db
@slow
@spark
def test_pipeline_warehouse():
    config_object = load_yaml_from_glob_list(
        [
            script_relative_path('../environments/local_base.yml'),
            script_relative_path('../environments/local_warehouse.yml'),
        ]
    )
    result = execute_pipeline(define_airline_demo_warehouse_pipeline(), config_object)

    assert result.success
