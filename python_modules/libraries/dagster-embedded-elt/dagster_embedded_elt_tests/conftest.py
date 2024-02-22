import os
import sqlite3
from pathlib import Path

import pytest
import yaml
from dagster import file_relative_path
from dagster_embedded_elt.sling import (
    SlingConnectionResource,
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
)

base_replication_config_path = (
    Path(__file__).joinpath("..", "replication_configs/test_base_config/replication.yaml").resolve()
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


def base_replication_config():
    with base_replication_config_path.open("r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def replication_params(request):
    if request.param == "base_replication_config":
        return base_replication_config()
    elif request.param == "base_replication_config_path":
        return base_replication_config_path
    elif request.param == "os_fspath":
        return os.fspath(base_replication_config_path)


@pytest.fixture
def replication_config():
    return base_replication_config()
