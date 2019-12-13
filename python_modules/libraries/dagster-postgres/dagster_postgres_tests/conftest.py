import os
import subprocess

import pytest
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.utils import get_conn_string, wait_for_connection

from dagster.utils import pushd, script_relative_path

BUILDKITE = bool(os.getenv('BUILDKITE'))


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


@pytest.fixture(scope='function')
def postgres():
    if BUILDKITE:
        yield
        return

    if not is_postgres_running():
        with pushd(script_relative_path('.')):
            try:
                subprocess.check_output(['docker-compose', 'stop', 'test-postgres-db'])
                subprocess.check_output(['docker-compose', 'rm', '-f', 'test-postgres-db'])
            except Exception:  # pylint: disable=broad-except
                pass
            subprocess.check_output(['docker-compose', 'up', '-d', 'test-postgres-db'])

    wait_for_connection(_conn_string())

    yield


@pytest.fixture(scope='module')
def multi_postgres():  # pylint: disable=redefined-outer-name
    if BUILDKITE:
        yield
        return
        # It's not clear why none of this works -- we can debug after 0.6.0
        # See, maybe, https://success.docker.com/article/multiple-docker-networks for
        # further debug strategy
        # https://github.com/dagster-io/dagster/issues/1791
        # event_log_storage_conn_string = _conn_string(
        #     hostname=get_hostname('POSTGRES_TEST_EVENT_LOG_STORAGE_DB_HOST'), port='5433'
        # )
        # run_storage_conn_string = _conn_string(
        #     hostname=get_hostname('POSTGRES_TEST_RUN_STORAGE_DB_HOST'), port='5434'
        # )

        # print(subprocess.check_output(['docker', 'ps']))
        # wait_for_connection(event_log_storage_conn_string)
        # wait_for_connection(run_storage_conn_string)

        # yield (run_storage_conn_string, event_log_storage_conn_string)
        # return

    with pushd(script_relative_path('.')):
        try:
            subprocess.check_output(['docker-compose', '-f', 'docker-compose-multi.yml', 'stop'])
            subprocess.check_output(['docker-compose', '-f', 'docker-compose-multi.yml', 'rm'])
        except Exception:  # pylint: disable=broad-except
            pass
        subprocess.check_output(['docker-compose', '-f', 'docker-compose-multi.yml', 'up', '-d'])

        event_log_storage_conn_string = _conn_string(port='5433')
        run_storage_conn_string = _conn_string(port='5434')

        wait_for_connection(event_log_storage_conn_string)
        wait_for_connection(run_storage_conn_string)

        yield (run_storage_conn_string, event_log_storage_conn_string)


def get_hostname(env_name='POSTGRES_TEST_DB_HOST'):
    # In buildkite we get the ip address from this variable (see buildkite code for commentary)
    # Otherwise assume local development and assume localhost
    return os.environ.get(env_name, 'localhost')


def _conn_string(**kwargs):
    return get_conn_string(
        **dict(
            dict(username='test', password='test', hostname=get_hostname(), db_name='test'),
            **kwargs
        )
    )


@pytest.fixture(scope='function')
def hostname(postgres):  # pylint: disable=redefined-outer-name, unused-argument
    return get_hostname()


@pytest.fixture(scope='function')
def conn_string(postgres):  # pylint: disable=redefined-outer-name, unused-argument
    return _conn_string()


@pytest.fixture(scope='function')
def clean_storage(conn_string):  # pylint: disable=redefined-outer-name
    storage = PostgresRunStorage.create_clean_storage(conn_string)
    assert storage
    return storage
