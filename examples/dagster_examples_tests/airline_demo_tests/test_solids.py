"""Unit and pipeline tests for the airline_demo.

As is common in real-world pipelines, we want to test some fairly heavy-weight operations,
requiring, e.g., a connection to S3, Spark, and a database.

We lever pytest marks to isolate subsets of tests with different requirements. E.g., to run only
those tests that don't require Spark, `pytest -m "not spark"`.
"""
import os

import pyspark
import pytest

from dagster import (
    DependencyDefinition,
    execute_solid,
    lambda_solid,
    ModeDefinition,
    PipelineDefinition,
    RunConfig,
)

from dagster_examples.airline_demo.solids import sql_solid, ingest_csv_to_spark, unzip_file
from dagster_examples.airline_demo.resources import spark_session_local, tempfile_resource
from dagster_aws.s3.system_storage import s3_plus_default_storage_defs


tempfile_mode = ModeDefinition(name='tempfile', resources={'tempfile': tempfile_resource})

spark_mode = ModeDefinition(
    name='spark',
    resources={'spark': spark_session_local, 'tempfile': tempfile_resource},
    system_storage_defs=s3_plus_default_storage_defs,
)


def test_sql_solid_with_bad_materialization_strategy():
    with pytest.raises(Exception) as excinfo:
        sql_solid('foo', 'select * from bar', 'view')
    assert str(excinfo.value) == 'Invalid materialization strategy view, must be one of [\'table\']'


def test_sql_solid_without_table_name():
    with pytest.raises(Exception) as excinfo:
        sql_solid('foo', 'select * from bar', 'table')
    assert (
        str(excinfo.value) == 'Missing table_name: required for materialization strategy \'table\''
    )


def test_sql_solid():
    result = sql_solid('foo', 'select * from bar', 'table', 'quux')
    assert result
    # TODO: test execution?


def test_unzip_file_tempfile():
    @lambda_solid
    def nonce():
        return None

    with open(os.path.join(os.path.dirname(__file__), 'data/test.zip'), 'rb') as fd:
        archive_file = fd.read()

    result = execute_solid(
        PipelineDefinition(
            solids=[nonce, unzip_file],
            dependencies={
                'unzip_file': {
                    'archive_file': DependencyDefinition('nonce'),
                    'archive_member': DependencyDefinition('nonce'),
                }
            },
            mode_definitions=[tempfile_mode],
        ),
        'unzip_file',
        inputs={'archive_file': archive_file, 'archive_member': 'test/test_file'},
        environment_dict={},
        run_config=RunConfig(mode='tempfile'),
    )
    assert result.success
    assert result.result_value().read() == b'test\n'


@pytest.mark.spark
def test_ingest_csv_to_spark():
    @lambda_solid
    def nonce():
        return None

    with open(os.path.join(os.path.dirname(__file__), 'data/test.csv'), 'rb') as fd:
        input_csv_file = fd.read()
    result = execute_solid(
        PipelineDefinition(
            [nonce, ingest_csv_to_spark],
            dependencies={'ingest_csv_to_spark': {'input_csv_file': DependencyDefinition('nonce')}},
            mode_definitions=[spark_mode],
        ),
        'ingest_csv_to_spark',
        inputs={'input_csv_file': input_csv_file},
        environment_dict={},
        run_config=RunConfig(mode='spark'),
    )
    assert result.success
    assert isinstance(result.result_value(), pyspark.sql.dataframe.DataFrame)
    # We can't make this assertion because the tempfile is cleaned up after the solid executes --
    # a fuller test would have another solid make this assertion
    # assert result.result_value().head()[0] == '1'


@pytest.mark.postgres
@pytest.mark.skip
@pytest.mark.spark
def test_load_data_to_postgres_from_spark_postgres():
    raise NotImplementedError()


@pytest.mark.nettest
@pytest.mark.redshift
@pytest.mark.skip
@pytest.mark.spark
def test_load_data_to_redshift_from_spark():
    raise NotImplementedError()


@pytest.mark.skip
@pytest.mark.spark
def test_subsample_spark_dataset():
    raise NotImplementedError()


@pytest.mark.skip
@pytest.mark.spark
def test_join_spark_data_frame():
    raise NotImplementedError()
