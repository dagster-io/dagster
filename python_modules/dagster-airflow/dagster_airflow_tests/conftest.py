import errno
import os
import shutil
import subprocess
import tempfile
import uuid

import docker
import pytest

from dagster.utils import mkdir_p, script_relative_path


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


@pytest.fixture(scope='module')
def airflow_home():
    airflow_home_dir = os.getenv('AIRFLOW_HOME')
    assert airflow_home_dir, 'No AIRFLOW_HOME set -- is airflow installed?'
    airflow_home_dir = os.path.abspath(os.path.expanduser(airflow_home_dir))

    return airflow_home_dir


@pytest.fixture(scope='module')
def temp_dir():
    dir_path = os.path.join('/tmp', str(uuid.uuid4()))
    mkdir_p(dir_path)
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture(scope='module')
def docker_client():
    try:
        client = docker.from_env()
        client.info()
    except docker.errors.APIError:
        raise Exception(
            'Couldn\'t find docker at {url} -- is it running?'.format(url=client._url(''))
        )
    return client


@pytest.fixture(scope='module')
def dags_path(airflow_home):
    path = os.path.join(airflow_home, 'dags', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def plugins_path(airflow_home):
    path = os.path.join(airflow_home, 'plugins', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def host_tmp_dir():
    mkdir_p('/tmp/results')


@pytest.fixture(scope='module')
def airflow_test(airflow_home, docker_client, dags_path, plugins_path, host_tmp_dir):

    plugin_definition_filename = 'dagster_plugin.py'
    shutil.copyfile(
        script_relative_path(os.path.join('..', 'dagster_airflow', plugin_definition_filename)),
        os.path.abspath(os.path.join(plugins_path, plugin_definition_filename)),
    )

    mkdir_p(os.path.abspath(dags_path))

    subprocess.check_output(['airflow', 'initdb'])
