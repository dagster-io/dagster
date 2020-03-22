import os

# pylint: disable=unused-argument
import pytest

from dagster import RunConfig, execute_pipeline, file_relative_path
from dagster.cli.load_handle import handle_for_pipeline_cli_args
from dagster.core.instance import DagsterInstance
from dagster.utils import load_yaml_from_globs

ingest_pipeline_handle = handle_for_pipeline_cli_args(
    {
        'module_name': 'dagster_examples.airline_demo.pipelines',
        'fn_name': 'define_airline_demo_ingest_pipeline',
    }
)
ingest_pipeline_def = ingest_pipeline_handle.build_pipeline_definition()

warehouse_pipeline_handle = handle_for_pipeline_cli_args(
    {
        'module_name': 'dagster_examples.airline_demo.pipelines',
        'fn_name': 'define_airline_demo_warehouse_pipeline',
    }
)
warehouse_pipeline_def = warehouse_pipeline_handle.build_pipeline_definition()


def config_path(relative_path):
    return file_relative_path(
        __file__, os.path.join('../../dagster_examples/airline_demo/environments/', relative_path)
    )


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_ingest_pipeline_fast(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'), config_path('local_fast_ingest.yaml')
    )
    result_ingest = execute_pipeline(
        ingest_pipeline_def,
        ingest_config_dict,
        run_config=RunConfig(mode='local'),
        instance=DagsterInstance.local_temp(),
    )

    assert result_ingest.success


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_ingest_pipeline_fast_filesystem_storage(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('local_fast_ingest.yaml'),
        config_path('filesystem_storage.yaml'),
    )
    result_ingest = execute_pipeline(
        ingest_pipeline_def,
        ingest_config_dict,
        run_config=RunConfig(mode='local'),
        instance=DagsterInstance.local_temp(),
    )

    assert result_ingest.success


@pytest.mark.db
@pytest.mark.nettest
@pytest.mark.py3
@pytest.mark.spark
def test_airline_pipeline_1_warehouse(postgres, pg_hostname):
    warehouse_config_object = load_yaml_from_globs(
        config_path('test_base.yaml'), config_path('local_warehouse.yaml')
    )
    result_warehouse = execute_pipeline(
        warehouse_pipeline_def,
        warehouse_config_object,
        run_config=RunConfig(mode='local'),
        instance=DagsterInstance.local_temp(),
    )
    assert result_warehouse.success


####################################################################################################
# These tests are provided to help distinguish issues using the S3 object store from issues using
# Airflow, but add too much overhead (~30m) to run on each push
@pytest.mark.skip
def test_airline_pipeline_s3_0_ingest(postgres, pg_hostname):
    ingest_config_dict = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('s3_storage.yaml'),
        config_path('local_fast_ingest.yaml'),
    )

    result_ingest = execute_pipeline(
        ingest_pipeline_def, ingest_config_dict, instance=DagsterInstance.local_temp()
    )

    assert result_ingest.success


@pytest.mark.skip
def test_airline_pipeline_s3_1_warehouse(postgres, pg_hostname):
    warehouse_config_object = load_yaml_from_globs(
        config_path('test_base.yaml'),
        config_path('s3_storage.yaml'),
        config_path('local_warehouse.yaml'),
    )

    result_warehouse = execute_pipeline(
        warehouse_pipeline_def, warehouse_config_object, instance=DagsterInstance.local_temp()
    )
    assert result_warehouse.success


####################################################################################################
