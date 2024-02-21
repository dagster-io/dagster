import os
import sqlite3

import pytest
from dagster import file_relative_path
from dagster_embedded_elt.sling import (
    SlingConnectionResource,
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
)


@pytest.fixture
def sqlite_connection(temp_db):
    yield sqlite3.connect(temp_db)


@pytest.fixture
def temp_db(tmp_path):
    dbpath = os.path.join(tmp_path, "sqlite.db")
    yield dbpath


@pytest.fixture
def sling_sqlite_resource(temp_db):
    return SlingResource(
        source_connection=SlingSourceConnection(type="file"),
        target_connection=SlingTargetConnection(
            type="sqlite", connection_string=f"sqlite://{temp_db}"
        ),
    )


@pytest.fixture
def sling_file_connection():
    return SlingConnectionResource(name="SLING_FILE", type="file")


@pytest.fixture
def sling_sqlite_connection(temp_db):
    return SlingConnectionResource(
        name="SLING_SQLITE", type="sqlite", connection_string=f"sqlite://{temp_db}"
    )


@pytest.fixture
def test_csv():
    return os.path.abspath(file_relative_path(__file__, "test.csv"))
