import os

import pytest
from dagster_postgres.test import implement_postgres_fixture

from dagster.utils import script_relative_path

BUILDKITE = os.getenv('BUILDKITE')


@pytest.fixture(scope='session')
def docker_compose_db():
    with implement_postgres_fixture(script_relative_path('..')):
        yield


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-scratch-80542c2'
