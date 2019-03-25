from dagster import execute_pipeline

from dagster.utils import load_yaml_from_globs, script_relative_path

from airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import db, nettest, py3, spark


@db
@nettest
@py3
@spark
def test_all_airline_pipelines():
    ingest_config_object = load_yaml_from_globs(
        script_relative_path('../environments/local_base.yml'),
        script_relative_path('../environments/local_fast_ingest.yml'),
    )

    result_ingest = execute_pipeline(define_airline_demo_ingest_pipeline(), ingest_config_object)

    assert result_ingest.success

    warehouse_config_object = load_yaml_from_globs(
        script_relative_path('../environments/local_base.yml'),
        script_relative_path('../environments/local_warehouse.yml'),
    )

    result_warehouse = execute_pipeline(
        define_airline_demo_warehouse_pipeline(), warehouse_config_object
    )
    assert result_warehouse.success
