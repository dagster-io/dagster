"""Session-scoped ClickHouse fixtures for integration tests (Docker + testcontainers).

Imported by ``dagster_clickhouse_tests.conftest`` and by sibling packages' ``conftest`` files.
Using a plain module avoids ``pytest_plugins`` double-registration when running multiple
packages in one pytest session.
"""

import os

import pytest

try:
    import docker
except ImportError:
    docker = None  # ty: ignore[invalid-assignment]


def _docker_available() -> bool:
    if docker is None:
        return False
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def clickhouse_connection():
    """Expose connection parameters for ``clickhouse-driver`` against a real ClickHouse server."""
    if not _docker_available():
        pytest.skip("Docker is not available (required for ClickHouse testcontainers)")

    from testcontainers.clickhouse import ClickHouseContainer

    # Pin image for reproducible CI; native protocol on 9000. CI overrides the tag
    # via env so the image it pre-pulls is the one started here.
    image = os.environ.get("CLICKHOUSE_TEST_IMAGE", "clickhouse/clickhouse-server:24.8")
    with ClickHouseContainer(image) as ch:
        yield {
            "host": ch.get_container_host_ip(),
            "port": int(ch.get_exposed_port(9000)),
            "user": ch.username,
            "password": ch.password,
            "database": ch.dbname,
        }
