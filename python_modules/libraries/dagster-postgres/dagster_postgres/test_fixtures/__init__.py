import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from dagster._core.test_utils import instance_for_test
from dagster._utils.merger import merge_dicts
from dagster_test.fixtures import docker_compose_cm, network_name_from_yml

from dagster_postgres.utils import get_conn_string, wait_for_connection

compose_file = Path(__file__).parent / "docker-compose.yml"


@pytest.fixture(scope="session")
def postgres_network():
    yield network_name_from_yml(compose_file)


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
        params=dict(connect_timeout=5),
    )
    wait_for_connection(
        conn_str,
        retry_limit=10,
        retry_wait=3,
    )

    yield conn_str


@pytest.fixture
def postgres_instance(postgres_conn_str):
    @contextmanager
    def _instance(overrides=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            with instance_for_test(
                temp_dir=temp_dir,
                overrides=merge_dicts(
                    {
                        "run_storage": {
                            "module": "dagster_postgres.run_storage.run_storage",
                            "class": "PostgresRunStorage",
                            "config": {"postgres_url": postgres_conn_str},
                        },
                        "event_log_storage": {
                            "module": "dagster_postgres.event_log.event_log",
                            "class": "PostgresEventLogStorage",
                            "config": {"postgres_url": postgres_conn_str},
                        },
                        "schedule_storage": {
                            "module": "dagster_postgres.schedule_storage.schedule_storage",
                            "class": "PostgresScheduleStorage",
                            "config": {"postgres_url": postgres_conn_str},
                        },
                    },
                    overrides if overrides else {},
                ),
            ) as instance:
                instance.wipe()
                yield instance

    return _instance
