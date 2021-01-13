"""Unit and pipeline tests for the airline_demo.

As is common in real-world pipelines, we want to test some fairly heavy-weight operations,
requiring, e.g., a connection to S3, Spark, and a database.

We lever pytest marks to isolate subsets of tests with different requirements. E.g., to run only
those tests that don't require Spark, `pytest -m "not spark"`.
"""

import pytest
from airline_demo.solids import sql_solid
from dagster import ModeDefinition
from dagster.core.storage.temp_file_manager import tempfile_resource

tempfile_mode = ModeDefinition(name="tempfile", resource_defs={"tempfile": tempfile_resource})


def test_sql_solid_with_bad_materialization_strategy():
    with pytest.raises(Exception) as excinfo:
        sql_solid("foo", "select * from bar", "view")
    assert str(excinfo.value) == "Invalid materialization strategy view, must be one of ['table']"


def test_sql_solid_without_table_name():
    with pytest.raises(Exception) as excinfo:
        sql_solid("foo", "select * from bar", "table")
    assert str(excinfo.value) == "Missing table_name: required for materialization strategy 'table'"


def test_sql_solid():
    solid = sql_solid("foo", "select * from bar", "table", "quux")
    assert solid
