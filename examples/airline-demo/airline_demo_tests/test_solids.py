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
    PipelineContextDefinition,
    PipelineDefinition,
    execute_solid,
    lambda_solid,
)

from airline_demo.solids import sql_solid, ingest_csv_to_spark, unzip_file
from airline_demo.resources import spark_session_local, tempfile_resource

from .marks import nettest, postgres, redshift, skip, spark


def _tempfile_context():
    return {'test': PipelineContextDefinition(resources={'tempfile': tempfile_resource})}


def _spark_context():
    return {
        'test': PipelineContextDefinition(
            resources={'spark': spark_session_local, 'tempfile': tempfile_resource}
        )
    }


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
            context_definitions=_tempfile_context(),
        ),
        'unzip_file',
        inputs={'archive_file': archive_file, 'archive_member': 'test/test_file'},
        environment_dict={},
    )
    assert result.success
    assert result.transformed_value().read() == b'test\n'


@spark
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
            context_definitions=_spark_context(),
        ),
        'ingest_csv_to_spark',
        inputs={'input_csv_file': input_csv_file},
        environment_dict={'context': {'test': {}}},
    )
    assert result.success
    assert isinstance(result.transformed_value(), pyspark.sql.dataframe.DataFrame)
    # We can't make this assertion because the tempfile is cleaned up after the solid executes --
    # a fuller test would have another solid make this assertion
    # assert result.transformed_value().head()[0] == '1'


@postgres
@skip
@spark
def test_load_data_to_postgres_from_spark_postgres():
    raise NotImplementedError()


@nettest
@redshift
@skip
@spark
def test_load_data_to_redshift_from_spark():
    raise NotImplementedError()


@skip
@spark
def test_subsample_spark_dataset():
    raise NotImplementedError()


@skip
@spark
def test_join_spark_data_frame():
    raise NotImplementedError()
