from unittest import mock

import pandas as pd
import pytest
from dagster import execute_pipeline
from dagster.utils import load_yaml_from_globs, script_relative_path
from dagster_examples.event_pipeline_demo.pipelines import event_ingest_pipeline

from .conftest import events_jar, spark_home  # pylint: disable=unused-import


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
@pytest.mark.spark
@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_event_pipeline(
    snowflake_connect,
    events_jar,
    spark_home,
):  # pylint: disable=redefined-outer-name, unused-argument
    config = load_yaml_from_globs(
        script_relative_path("../../dagster_examples/event_pipeline_demo/environments/default.yaml")
    )
    config["solids"]["event_ingest"]["config"]["application_jar"] = events_jar

    result_pipeline = execute_pipeline(event_ingest_pipeline, config)
    assert result_pipeline.success

    # We're not testing Snowflake loads here, so at least test that we called the connect
    # appropriately
    snowflake_connect.assert_called_with(
        user="<< SET ME >>",
        password="<< SET ME >>",
        account="<< SET ME >>",
        database="TESTDB",
        schema="TESTSCHEMA",
        warehouse="TINY_WAREHOUSE",
    )
