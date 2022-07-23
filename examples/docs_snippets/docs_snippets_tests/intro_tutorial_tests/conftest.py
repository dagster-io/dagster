import os

import pytest

from dagster._utils import file_relative_path
from dagster._utils.test.postgres_instance import TestPostgresInstance


@pytest.fixture(scope="function")
def postgres():  # pylint: disable=redefined-outer-name
    with TestPostgresInstance.docker_service_up_or_skip(
        file_relative_path(__file__, os.path.join("..", "..", "docker-compose.yml")),
        "test-postgres-db-docs-snippets",
    ) as conn_string:
        yield conn_string
