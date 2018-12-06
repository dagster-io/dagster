"""Unit and pipeline tests for the airline_demo.

As is common in real-world pipelines, we want to test some fairly heavy-weight operations,
requiring, e.g., a connection to S3, Spark, and a database.

We lever pytest marks to isolate subsets of tests with different requirements. E.g., to run only
those tests that don't require Spark, `pytest -m "not spark"`.
"""
import logging
import os

import pyspark
import pytest

from collections import namedtuple

from dagster import (
    config,
    DependencyDefinition,
    ExecutionContext,
    lambda_solid,
    PipelineContextDefinition,
    PipelineDefinition,
    ResourceDefinition,
    SolidInstance,
)
from dagster.utils.test import (define_stub_solid, execute_solid)

from airline_demo.solids import (
    sql_solid,
    download_from_s3,
    ingest_csv_to_spark,
    thunk,
    unzip_file,
)
from airline_demo.pipelines import (
    define_lambda_resource,
    define_tempfile_resource,
)
from airline_demo.utils import (
    create_s3_session,
    create_spark_session_local,
)


def _tempfile_context():
    return {
        'test':
        PipelineContextDefinition(
            context_fn=lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
            resources={
                'tempfile': define_tempfile_resource(),
            }
        )
    }


def _s3_context():
    return {
        'test':
        PipelineContextDefinition(
            context_fn=lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
            resources={
                's3': define_lambda_resource(create_s3_session, signed=False),
                'tempfile': define_tempfile_resource(),
            }
        )
    }


def _spark_context():
    return {
        'test':
        PipelineContextDefinition(
            context_fn=lambda info: ExecutionContext.console_logging(log_level=logging.DEBUG),
            resources={'spark': define_lambda_resource(create_spark_session_local)}
        )
    }


def test_sql_solid_with_bad_materialization_strategy():
    with pytest.raises(Exception) as excinfo:
        sql_solid('foo', 'select * from bar', 'view')
    assert str(excinfo.value) == \
        'Invalid materialization strategy view, must be one of [\'table\']'


def test_sql_solid_without_table_name():
    with pytest.raises(Exception) as excinfo:
        sql_solid('foo', 'select * from bar', 'table')
    assert str(excinfo.value) == \
        'Missing table_name: required for materialization strategy \'table\''


def test_sql_solid():
    result = sql_solid('foo', 'select * from bar', 'table', 'quux')
    assert result
    # TODO: test execution?


def test_thunk():
    result = execute_solid(
        PipelineDefinition([thunk]), 'thunk', environment={'solids': {
            'thunk': {
                'config': 'foo'
            }
        }}
    )
    assert result.success
    assert result.transformed_value() == 'foo'


@pytest.mark.nettest
def test_download_from_s3():
    result = execute_solid(
        PipelineDefinition([download_from_s3], context_definitions=_s3_context()),
        'download_from_s3',
        environment={
            'context': {
                'test': {}
            },
            'solids': {
                'download_from_s3': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'test/test_file',
                        'target_path': 'test/test_file',
                    }
                }
            }
        }
    )
    assert result.success
    assert result.transformed_value() == 'test/test_file'
    assert os.path.isfile(result.transformed_value())
    with open(result.transformed_value(), 'r') as fd:
        assert fd.read() == 'test\n'


@pytest.mark.nettest
def test_download_from_s3_tempfile():
    result = execute_solid(
        PipelineDefinition([download_from_s3], context_definitions=_s3_context()),
        'download_from_s3',
        environment={
            'context': {
                'test': {}
            },
            'solids': {
                'download_from_s3': {
                    'config': {
                        'bucket': 'dagster-airline-demo-source-data',
                        'key': 'test/test_file',
                    }
                }
            }
        }
    )
    assert result.success
    assert result.transformed_value()
    assert not os.path.isfile(result.transformed_value())


def test_unzip_file_tempfile():
    @lambda_solid
    def nonce():
        return None

    result = execute_solid(
        PipelineDefinition(
            solids=[nonce, unzip_file],
            dependencies={
                'unzip_file': {
                    'archive_path': DependencyDefinition('nonce'),
                    'archive_member': DependencyDefinition('nonce')
                }
            },
            context_definitions=_tempfile_context(),
        ),
        'unzip_file',
        inputs={
            'archive_path': os.path.join(os.path.dirname(__file__), 'data/test.zip'),
            'archive_member': 'test/test_file'
        },
        environment={'solids': {
            'unzip_file': {
                'config': {
                    'skip_if_present': False
                }
            }
        }}
    )
    assert result.success
    assert result.transformed_value()
    assert not os.path.isfile(result.transformed_value())


@pytest.mark.spark
@pytest.mark.slow
def test_ingest_csv_to_spark():
    @lambda_solid
    def nonce():
        return None

    result = execute_solid(
        PipelineDefinition(
            [nonce, ingest_csv_to_spark],
            dependencies={'ingest_csv_to_spark': {
                'input_csv': DependencyDefinition('nonce'),
            }},
            context_definitions=_spark_context(),
        ),
        'ingest_csv_to_spark',
        inputs={
            'input_csv': os.path.join(os.path.dirname(__file__), 'data/test.csv'),
        },
        environment={
            'context': {
                'test': {}
            },
            'solids': {
                'ingest_csv_to_spark': {
                    'config': {}
                }
            }
        }
    )
    assert result.success
    assert isinstance(result.transformed_value(), pyspark.sql.dataframe.DataFrame)
    assert result.transformed_value().head()[0] == '1'


@pytest.mark.spark
@pytest.mark.postgres
@pytest.mark.slow
def test_load_data_to_postgres_from_spark_postgres():
    raise NotImplementedError()


@pytest.mark.nettest
@pytest.mark.spark
@pytest.mark.redshift
@pytest.mark.slow
def test_load_data_to_redshift_from_spark():
    raise NotImplementedError()


@pytest.mark.spark
@pytest.mark.slow
def test_subsample_spark_dataset():
    raise NotImplementedError()


@pytest.mark.spark
@pytest.mark.slow
def test_join_spark_data_frame():
    raise NotImplementedError()
