"""Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
"""
import importlib
import time
from datetime import datetime
from typing import Generator

import airflow
import pytest
from airflow.utils import db
from dagster import DagsterInstance
from dagster._core.test_utils import environ, instance_for_test
from dagster._utils import file_relative_path
from dagster_airflow.utils import (
    is_airflow_2_loaded_in_environment,
)
from sqlalchemy.exc import OperationalError


@pytest.fixture(name="docker_compose_file", scope="session")
def docker_compose_file_fixture() -> str:
    return file_relative_path(__file__, "docker-compose.yml")


RETRY_DELAY_SEC = 5
STARTUP_TIME_SEC = 120


@pytest.fixture(name="instance")
def instance_fixture() -> Generator[DagsterInstance, None, None]:
    with instance_for_test() as instance:
        yield instance


@pytest.fixture(name="postgres_airflow_db", scope="module")
def postgres_airflow_db(
    docker_compose_cm,
    docker_compose_file,
) -> Generator[str, None, None]:
    """Spins up an Airflow postgres database using docker-compose, and tears it down after the test.
    """
    with docker_compose_cm(
        docker_compose_yml=docker_compose_file,
    ) as hostnames:
        uri = f"postgresql+psycopg2://airflow:airflow@{hostnames['airflow-db']}:5432"
        with environ(
            {"AIRFLOW__DATABASE__SQL_ALCHEMY_CONN": uri, "AIRFLOW__CORE__SQL_ALCHEMY_CONN": uri}
        ):
            if is_airflow_2_loaded_in_environment():
                importlib.reload(airflow.configuration)
                importlib.reload(airflow.settings)
                importlib.reload(airflow)
            else:
                importlib.reload(airflow)

            # Poll while trying to initialize the database
            start_time = datetime.now()
            while True:
                now = datetime.now()
                if (now - start_time).seconds > STARTUP_TIME_SEC:
                    raise Exception("db instance failed to start in time")
                try:
                    db.initdb()
                    break
                except OperationalError as e:
                    print(e)  # noqa: T201
                time.sleep(RETRY_DELAY_SEC)
                print(  # noqa: T201
                    "Waiting for Airflow postgres database to start and initialize"
                    + "." * (3 + (now - start_time).seconds // RETRY_DELAY_SEC)
                )
            yield uri
