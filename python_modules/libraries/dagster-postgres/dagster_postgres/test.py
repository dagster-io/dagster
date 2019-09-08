import os
import subprocess
import time
from contextlib import contextmanager

import psycopg2
import psycopg2.extensions

from dagster.utils import pushd


def in_buildkite():
    return bool(os.getenv('BUILDKITE'))


def is_postgres_running():
    try:
        output = subprocess.check_output(
            ['docker', 'container', 'ps', '-f', 'name=test-postgres-db', '-f', 'status=running']
        )
        decoded = output.decode()

        lines = decoded.split('\n')

        # header, one line for container, trailing \n
        return len(lines) == 3
    except:  # pylint: disable=bare-except
        return False


def ensure_postgres_db_initialized():
    retry_limit = 20

    while retry_limit:
        try:
            psycopg2.connect(get_test_conn_string())
            return True
        except psycopg2.OperationalError:
            pass

        time.sleep(0.2)
        retry_limit -= 1

    assert retry_limit == 0
    raise Exception('too many retries')


@contextmanager
def implement_postgres_fixture(script_path):
    if in_buildkite():
        yield
        return

    if not is_postgres_running():
        with pushd(script_path):
            try:
                subprocess.check_output(['docker-compose', 'stop', 'test-postgres-db'])
                subprocess.check_output(['docker-compose', 'rm', '-f', 'test-postgres-db'])
            except Exception:  # pylint: disable=broad-except
                pass
            subprocess.check_output(['docker-compose', 'up', '-d', 'test-postgres-db'])

    ensure_postgres_db_initialized()

    yield


def get_hostname():
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    env_name = 'POSTGRES_TEST_DB_HOST'
    return os.environ.get(env_name, 'localhost')


def get_test_conn_string():
    username = 'test'
    password = 'test'
    hostname = get_hostname()
    db_name = 'test'
    return 'postgresql://{username}:{password}@{hostname}:5432/{db_name}'.format(
        username=username, password=password, hostname=hostname, db_name=db_name
    )
