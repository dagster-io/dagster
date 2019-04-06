import os
import subprocess

import pandas as pd
import pytest

from dagster import execute_pipeline

from dagster.seven import mock

from dagster.utils import load_yaml_from_globs, script_relative_path

from event_pipeline_demo.pipelines import define_event_ingest_pipeline

spark = pytest.mark.spark
'''Tests that require Spark.'''

skip = pytest.mark.skip


def create_mock_connector(*_args, **_kwargs):
    return connect_with_fetchall_returning(pd.DataFrame())


def connect_with_fetchall_returning(value):
    cursor_mock = mock.MagicMock()
    cursor_mock.fetchall.return_value = value
    snowflake_connect = mock.MagicMock()
    snowflake_connect.cursor.return_value = cursor_mock
    m = mock.Mock()
    m.return_value = snowflake_connect
    return m


# To support this test, we need to do the following:
# 1. Have CircleCI publish Scala/Spark jars when that code changes
# 2. Ensure we have Spark available to CircleCI
# 3. Include example / test data in this repository
@spark
@mock.patch('snowflake.connector.connect', new_callable=create_mock_connector)
def test_event_pipeline(snowflake_connect):

    spark_home_set = True

    if os.getenv('SPARK_HOME') is None:
        spark_home_set = False

    try:
        if not spark_home_set:
            try:
                pyspark_show = subprocess.check_output(['pip', 'show', 'pyspark'])
            except subprocess.CalledProcessError:
                pass
            else:
                os.environ['SPARK_HOME'] = os.path.join(
                    list(
                        filter(lambda x: 'Location' in x, pyspark_show.decode('utf-8').split('\n'))
                    )[0].split(' ')[1],
                    'pyspark',
                )

        config = load_yaml_from_globs(script_relative_path('../environments/default.yml'))
        result_pipeline = execute_pipeline(define_event_ingest_pipeline(), config)
        assert result_pipeline.success

        # We're not testing Snowflake loads here, so at least test that we called the connect
        # appropriately
        snowflake_connect.assert_called_once_with(
            user='<< SET ME >>',
            password='<< SET ME >>',
            account='<< SET ME >>',
            database='TESTDB',
            schema='TESTSCHEMA',
            warehouse='TINY_WAREHOUSE',
        )

    finally:
        if not spark_home_set:
            try:
                del os.environ['SPARK_HOME']
            except KeyError:
                pass
