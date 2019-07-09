'''Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
'''
# pylint doesn't understand the way that pytest constructs fixture dependnecies
# pylint: disable=redefined-outer-name, unused-argument
import os
import shutil
import subprocess
import tempfile
import uuid

import docker
import pytest


from click.testing import CliRunner

from dagster import check
from dagster.utils import load_yaml_from_path, mkdir_p, pushd, script_relative_path

from dagster_airflow.cli import scaffold

IMAGE = 'dagster-airflow-demo'


@pytest.fixture(scope='module')
def airflow_home():
    '''Check that AIRFLOW_HOME is set, and return it'''
    airflow_home_dir = os.getenv('AIRFLOW_HOME')
    assert airflow_home_dir, 'No AIRFLOW_HOME set -- is airflow installed?'
    airflow_home_dir = os.path.abspath(os.path.expanduser(airflow_home_dir))

    return airflow_home_dir


@pytest.fixture(scope='module')
def temp_dir():
    '''Context manager for temporary directories.

    pytest implicitly wraps in try/except.
    '''
    dir_path = os.path.join('/tmp', str(uuid.uuid4()))
    mkdir_p(dir_path)
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture(scope='module')
def clean_airflow_home(airflow_home):
    '''Ensure that the existing contents of AIRFLOW_HOME do not interfere with test.'''
    tempdir_path = tempfile.mkdtemp()

    file_paths = os.listdir(airflow_home)
    for file_path in file_paths:
        shutil.move(os.path.join(airflow_home, file_path), tempdir_path)

    yield

    file_paths = os.listdir(tempdir_path)
    for file_path in file_paths:
        shutil.move(os.path.join(tempdir_path, file_path), os.path.join(airflow_home, file_path))

    shutil.rmtree(tempdir_path)


@pytest.fixture(scope='module')
def create_airflow_dags(clean_airflow_home):
    runner = CliRunner()

    runner.invoke(
        scaffold,
        [
            '--dag-name',
            'toys_log_spew',
            '--module-name',
            'dagster_examples.toys.log_spew',
            '--pipeline-name',
            'log_spew',
        ],
    )
    runner.invoke(
        scaffold,
        [
            '--dag-name',
            'toys_many_events',
            '--module-name',
            'dagster_examples.toys.many_events',
            '--pipeline-name',
            'many_events',
        ],
    )
    runner.invoke(
        scaffold,
        [
            '--dag-name',
            'toys_resources',
            '--module-name',
            'dagster_examples.toys.resources',
            '--fn-name',
            'resource_pipeline',
        ],
    )
    runner.invoke(
        scaffold,
        [
            '--dag-name',
            'toys_sleepy',
            '--module-name',
            'dagster_examples.toys.sleepy',
            '--fn-name',
            'sleepy_pipeline',
        ],
    )


@pytest.fixture(scope='session')
def docker_client():
    '''Instantiate a Docker Python client.'''
    try:
        client = docker.from_env()
        client.info()
    except docker.errors.APIError:
        # pylint: disable=protected-access
        check.failed('Couldn\'t find docker at {url} -- is it running?'.format(url=client._url('')))
    return client


@pytest.fixture(scope='session')
def build_docker_image(docker_client):
    with pushd(script_relative_path('test_project')):
        subprocess.check_output(['./build.sh'], shell=True)

    return IMAGE


@pytest.fixture(scope='session')
def docker_image(docker_client, build_docker_image):
    '''Check that the airflow image exists.'''
    try:
        docker_client.images.get(build_docker_image)
    except docker.errors.ImageNotFound:
        check.failed(
            'Couldn\'t find docker image {image} required for test: please run the script at '
            '{script_path}'.format(
                image=build_docker_image, script_path=script_relative_path('test_project/build.sh')
            )
        )

    return build_docker_image


@pytest.fixture(scope='module')
def dags_path(airflow_home):
    '''Abspath to the magic Airflow DAGs folder.'''
    path = os.path.join(airflow_home, 'dags', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def plugins_path(airflow_home):
    '''Abspath to the magic Airflow plugins folder.'''
    path = os.path.join(airflow_home, 'plugins', '')
    mkdir_p(os.path.abspath(path))
    return path


@pytest.fixture(scope='module')
def environment_dict(s3_bucket):
    env_dict = load_yaml_from_path(script_relative_path('test_project/env.yaml'))
    env_dict['storage'] = {'s3': {'s3_bucket': s3_bucket}}
    yield env_dict


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-airflow-scratch'
