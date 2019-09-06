import os
import subprocess

import pytest

from dagster.utils import pushd, script_relative_path

BUILDKITE = os.getenv('BUILDKITE')


# Spins up a database using docker-compose and tears it down after tests complete.
# We disable this on Buildkite.
@pytest.fixture(scope='session')
def docker_compose_db():
    if BUILDKITE:
        yield
        return

    with pushd(script_relative_path('../')):
        try:
            subprocess.check_output(['docker-compose', 'stop', 'test-postgres-db'])
            subprocess.check_output(['docker-compose', 'rm', '-f', 'test-postgres-db'])
        except Exception:  # pylint: disable=broad-except
            pass
        subprocess.check_output(['docker-compose', 'up', '-d', 'test-postgres-db'])

    yield

    with pushd(script_relative_path('../')):
        subprocess.check_output(['docker-compose', 'stop', 'test-postgres-db'])
        subprocess.check_output(['docker-compose', 'rm', '-f', 'test-postgres-db'])

    return


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-scratch-80542c2'
