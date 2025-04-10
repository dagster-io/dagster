from pathlib import Path

import pytest
from dagster_test.fixtures import docker_compose_cm

from dagster_postgres.utils import get_conn_string, wait_for_connection

compose_file = Path(__file__).parent / "docker-compose.yml"


@pytest.fixture(scope="session")
def postgres_hostname():
    with docker_compose_cm(docker_compose_yml=compose_file) as hostnames:
        yield hostnames["postgres"]


@pytest.fixture(scope="session")
def postgres_conn_str(postgres_hostname):
    conn_str = get_conn_string(
        username="test",
        password="test",
        hostname=postgres_hostname,
        db_name="test",
    )
    wait_for_connection(
        conn_str,
        retry_limit=10,
        retry_wait=3,
    )

    yield conn_str
