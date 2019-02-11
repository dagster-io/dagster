# pylint doesn't understand the way that pytest constructs fixture dependnecies
# pylint: disable=redefined-outer-name
import datetime
import os
import shutil
import subprocess
import uuid

import docker
import pytest

from dagster.core.execution import create_execution_plan
from dagster.utils import load_yaml_from_path, mkdir_p, script_relative_path

from dagster_airflow import scaffold_airflow_dag

from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


IMAGE = 'dagster-airflow-demo'


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
def docker_image(docker_client):
    try:
        docker_client.images.get(IMAGE)
    except docker.errors.ImageNotFound:
        raise Exception(
            'Couldn\'t find docker image {image} required for test: please run the script at '
            '{script_path}'.format(
                image=IMAGE, script_path=script_relative_path('test_project/build.sh')
            )
        )

    return IMAGE


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
    return '/tmp/results'


@pytest.fixture(scope='module')
def airflow_test(docker_image, dags_path, plugins_path, host_tmp_dir):

    assert docker_image

    plugin_definition_filename = 'dagster_plugin.py'
    shutil.copyfile(
        script_relative_path(os.path.join('..', 'dagster_airflow', plugin_definition_filename)),
        os.path.abspath(os.path.join(plugins_path, plugin_definition_filename)),
    )

    mkdir_p(os.path.abspath(dags_path))

    subprocess.check_output(['airflow', 'initdb'])

    return (docker_image, dags_path, host_tmp_dir)


@pytest.fixture(scope='module')
def scaffold_dag(airflow_test):
    docker_image, dags_path, _ = airflow_test
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    static_path, editable_path = scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=docker_image,
        output_path=script_relative_path('test_project'),
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )

    # Ensure that the scaffolded files parse correctly
    subprocess.check_output(['python', editable_path])

    shutil.copyfile(
        script_relative_path(static_path),
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
    )

    shutil.copyfile(
        script_relative_path(editable_path),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )
    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    pipeline_name = pipeline.name

    execution_plan = create_execution_plan(pipeline, env_config)

    return (
        pipeline_name,
        execution_plan,
        execution_date,
        os.path.abspath(os.path.join(dags_path, os.path.basename(static_path))),
        os.path.abspath(os.path.join(dags_path, os.path.basename(editable_path))),
    )
