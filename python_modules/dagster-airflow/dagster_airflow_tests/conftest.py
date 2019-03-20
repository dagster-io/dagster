'''Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
'''
# pylint doesn't understand the way that pytest constructs fixture dependnecies
# pylint: disable=redefined-outer-name
import datetime
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
from dagster.core.execution import create_execution_plan
from dagster.utils import load_yaml_from_path, mkdir_p, script_relative_path

from dagster_airflow import scaffold_airflow_dag

from .test_project.dagster_airflow_demo import (
    define_demo_error_pipeline,
    define_demo_execution_pipeline,
)

from .utils import reload_module

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
def docker_client():
    '''Instantiate a Docker Python client.'''
    try:
        client = docker.from_env()
        client.info()
    except docker.errors.APIError:
        check.failed('Couldn\'t find docker at {url} -- is it running?'.format(url=client._url('')))
    return client


@pytest.fixture(scope='module')
def docker_image(docker_client):
    '''Check that the airflow image exists.
    
    This image is created by dagster_airflow_tests/test_project/build.sh -- we might want to move
    image build into a test fixture of its own.
    '''
    try:
        docker_client.images.get(IMAGE)
    except docker.errors.ImageNotFound:
        check.failed(
            'Couldn\'t find docker image {image} required for test: please run the script at '
            '{script_path}'.format(
                image=IMAGE, script_path=script_relative_path('test_project/build.sh')
            )
        )

    return IMAGE


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
        reload_module(airflow.plugins_manager)
        for operators_module in airflow.plugins_manager.operators_modules:
            sys.modules[operators_module.__name__] = operators_module
            globals()[operators_module._name] = operators_module  # pylint:disable=protected-access

        # Test that we can now actually import the DagsterOperator
        from airflow.operators.dagster_plugin import DagsterOperator

        # Clean up
        del DagsterOperator

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
def scaffold_dag(airflow_test):
    '''Scaffolds an Airflow dag and installs it.

    We should probably use test classes for these tests and set attributes like pipeline/env_config
    on the classes to make this more reusable.
    '''
    docker_image, dags_path, _ = airflow_test
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    tempdir = tempfile.gettempdir()

    static_path, editable_path = scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=docker_image,
        output_path=tempdir,
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )

    # Ensure that the scaffolded files parse correctly
    subprocess.check_output(['python', editable_path])

    shutil.copyfile(
        static_path, os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)))
    )

    shutil.copyfile(
        editable_path, os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)))
    )

    os.remove(static_path)
    os.remove(editable_path)

    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    pipeline_name = pipeline.name

    execution_plan = create_execution_plan(pipeline, env_config)

    yield (
        pipeline_name,
        execution_plan,
        execution_date,
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )

    # Clean up the installed DAGs
    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))))
    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))))

    # Including any bytecode cruft
    try:
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)[:-3] + '.pyc'))
        )
    except (seven.FileNotFoundError, OSError):
        pass

    try:
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)[:-3] + '.pyc'))
        )
    except (seven.FileNotFoundError, OSError):
        pass


@pytest.fixture(scope='module')
def scaffold_error_dag(airflow_test):
    '''See comment on scaffold_dag for a strategy to reduce repetition here.'''
    docker_image, dags_path, _ = airflow_test
    pipeline = define_demo_error_pipeline()
    env_config = {}

    tempdir = tempfile.gettempdir()

    static_path, editable_path = scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=docker_image,
        output_path=tempdir,
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )

    # Ensure that the scaffolded files parse correctly
    subprocess.check_output(['python', editable_path])

    shutil.copyfile(
        static_path, os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)))
    )

    shutil.copyfile(
        editable_path, os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)))
    )

    os.remove(static_path)
    os.remove(editable_path)

    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    pipeline_name = pipeline.name

    execution_plan = create_execution_plan(pipeline, env_config)

    yield (
        pipeline_name,
        execution_plan,
        execution_date,
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )

    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))))
    os.remove(os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))))

    try:
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(static_path)[:-3] + '.pyc'))
        )
        os.remove(
            os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path)[:-3] + '.pyc'))
        )

    except (seven.FileNotFoundError, OSError):
        pass
