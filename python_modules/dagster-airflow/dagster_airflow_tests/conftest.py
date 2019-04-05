'''Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
'''
# pylint doesn't understand the way that pytest constructs fixture dependnecies
# pylint: disable=redefined-outer-name, unused-argument
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

import airflow.plugins_manager
import docker
import pytest

from dagster import check, seven
from dagster.utils import load_yaml_from_path, mkdir_p, pushd, script_relative_path

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
def host_tmp_dir():
    '''We don't clean this up / make it a context manager because it may already exist...'''
    mkdir_p('/tmp/results')
    return '/tmp/results'


@pytest.fixture(scope='module')
def airflow_test(docker_image, dags_path, plugins_path, host_tmp_dir):
    '''Install the docker-airflow plugin & reload airflow.operators so the plugin is available.'''
    assert docker_image

    plugin_definition_filename = 'dagster_plugin.py'

    plugin_path = os.path.abspath(os.path.join(plugins_path, plugin_definition_filename))

    temporary_plugin_path = None

    try:
        # If there is already a docker-airflow plugin installed, we set it aside for safekeeping
        if os.path.exists(plugin_path):
            temporary_plugin_file = tempfile.NamedTemporaryFile(delete=False)
            temporary_plugin_file.close()
            temporary_plugin_path = temporary_plugin_file.name
            shutil.copyfile(plugin_path, temporary_plugin_path)

        shutil.copyfile(
            script_relative_path(os.path.join('..', 'dagster_airflow', plugin_definition_filename)),
            plugin_path,
        )

        mkdir_p(os.path.abspath(dags_path))
        sys.path.append(os.path.abspath(dags_path))

        # Set up the DAGs directory if needed
        created_init_py = False
        init_py_path = os.path.join(os.path.abspath(dags_path), '__init__.py')
        if not os.path.exists(init_py_path):
            with open(init_py_path, 'a'):
                pass
            created_init_py = True

        subprocess.check_output(['airflow', 'initdb'])

        # Necromancy; follows airflow.operators.__init__
        # This reloads airflow.operators so that the import statement below is possible
        seven.reload_module(airflow.plugins_manager)
        for operators_module in airflow.plugins_manager.operators_modules:
            sys.modules[operators_module.__name__] = operators_module
            globals()[operators_module._name] = operators_module  # pylint:disable=protected-access

        # Test that we can now actually import the DagsterDockerOperator
        # pylint: disable=import-error
        from airflow.operators.dagster_plugin import DagsterDockerOperator

        # Clean up
        del DagsterDockerOperator

        yield (docker_image, dags_path, host_tmp_dir)

    finally:
        if os.path.exists(plugin_path):
            os.remove(plugin_path)

        if temporary_plugin_path is not None:
            shutil.copyfile(temporary_plugin_path, plugin_path)
            os.remove(temporary_plugin_path)

        if created_init_py:
            os.remove(init_py_path)

        sys.path = sys.path[:-1]


@pytest.fixture(scope='module')
def pipeline():
    yield define_demo_execution_pipeline()


@pytest.fixture(scope='module')
def env_config(s3_bucket):
    config = load_yaml_from_path(script_relative_path('test_project/env.yml'))
    config['storage'] = {'s3': {'s3_bucket': s3_bucket}}
    yield config


@pytest.fixture(scope='session')
def s3_bucket():
    yield 'dagster-airflow-scratch'
