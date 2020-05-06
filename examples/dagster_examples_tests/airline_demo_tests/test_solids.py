"""Unit and pipeline tests for the airline_demo.

As is common in real-world pipelines, we want to test some fairly heavy-weight operations,
requiring, e.g., a connection to S3, Spark, and a database.

We lever pytest marks to isolate subsets of tests with different requirements. E.g., to run only
those tests that don't require Spark, `pytest -m "not spark"`.
"""

import pytest
from dagster_aws.s3 import s3_plus_default_storage_defs, s3_resource
from dagster_examples.airline_demo.solids import sql_solid
from dagster_pyspark import pyspark_resource

from dagster import ModeDefinition
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster.core.storage.temp_file_manager import tempfile_resource

tempfile_mode = ModeDefinition(name='tempfile', resource_defs={'tempfile': tempfile_resource})

spark_mode = ModeDefinition(
    name='spark',
    resource_defs={
        'pyspark': pyspark_resource,
        'tempfile': tempfile_resource,
        's3': s3_resource,
        'pyspark_step_launcher': no_step_launcher,
    },
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
