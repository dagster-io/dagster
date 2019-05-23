import os

# pylint: disable=unused-argument
import pytest

from dagster import execute_pipeline, RunConfig

from dagster.utils import load_yaml_from_globs, script_relative_path

from dagster_examples.airline_demo.pipelines import (
    define_airline_demo_ingest_pipeline,
    define_airline_demo_warehouse_pipeline,
)

from .marks import db, nettest, py3, spark


def enviroment_overrides(config):
    if os.environ.get('DAGSTER_AIRLINE_DEMO_DB_HOST'):
        config['resources']['db_info']['config']['postgres_hostname'] = os.environ.get(
            'DAGSTER_AIRLINE_DEMO_DB_HOST'
        )
    return config


@db
@nettest
@py3
@spark
def test_airline_pipeline_0_ingest(docker_compose_db):
    ingest_config_object = load_yaml_from_globs(
        script_relative_path('../../dagster_examples/airline_demo/environments/local_base.yml'),
        script_relative_path(
            '../../dagster_examples/airline_demo/environments/local_fast_ingest.yml'
        ),
    )
    ingest_config_object = enviroment_overrides(ingest_config_object)
    result_ingest = execute_pipeline(
        define_airline_demo_ingest_pipeline(),
        ingest_config_object,
        run_config=RunConfig(mode='local'),
    )

    assert result_ingest.success


@db
@nettest
@py3
@spark
def test_airline_pipeline_1_warehouse(docker_compose_db):
    warehouse_config_object = load_yaml_from_globs(
        script_relative_path('../../dagster_examples/airline_demo/environments/local_base.yml'),
        script_relative_path(
            '../../dagster_examples/airline_demo/environments/local_warehouse.yml'
        ),
    )
    warehouse_config_object = enviroment_overrides(warehouse_config_object)
    result_warehouse = execute_pipeline(
        define_airline_demo_warehouse_pipeline(),
        warehouse_config_object,
        run_config=RunConfig(mode='local'),
    )
    assert result_warehouse.success


####################################################################################################
# These tests are provided to help distinguish issues using the S3 object store from issues using
# Airflow, but add too much overhead (~30m) to run on each push
@pytest.mark.skip
def test_airline_pipeline_s3_0_ingest(docker_compose_db):
    ingest_config_object = load_yaml_from_globs(
        script_relative_path('../../dagster_examples/airline_demo/environments/local_base.yml'),
        script_relative_path('../../dagster_examples/airline_demo/environments/local_airflow.yml'),
        script_relative_path(
            '../../dagster_examples/airline_demo/environments/local_fast_ingest.yml'
        ),
    )

    result_ingest = execute_pipeline(define_airline_demo_ingest_pipeline(), ingest_config_object)

    assert result_ingest.success


@pytest.mark.skip
def test_airline_pipeline_s3_1_warehouse(docker_compose_db):
    warehouse_config_object = load_yaml_from_globs(
        script_relative_path('../../dagster_examples/airline_demo/environments/local_base.yml'),
        script_relative_path('../../dagster_examples/airline_demo/environments/local_airflow.yml'),
        script_relative_path(
            '../../dagster_examples/airline_demo/environments/local_warehouse.yml'
        ),
    )

    result_warehouse = execute_pipeline(
        define_airline_demo_warehouse_pipeline(), warehouse_config_object
    )
    assert result_warehouse.success


####################################################################################################
