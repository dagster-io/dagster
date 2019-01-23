import datetime
import errno
import os
import shutil
import subprocess

import docker

from dagster.utils import script_relative_path


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def test_minimal_dockerized_dagster_dag():
    # check for airflow home
    airflow_home = os.getenv('AIRFLOW_HOME')
    assert airflow_home, 'No AIRFLOW_HOME set -- is airflow installed?'

    # check that docker is running
    try:
        docker_client = docker.from_env()
        docker_client.info()
    except docker.errors.APIError:
        raise Exception(
            'Couldn\'t find docker at {url} -- is it running?'.format(url=docker_client._url(''))
        )

    plugins_path = os.path.join(airflow_home, 'plugins', '')
    dags_path = os.path.join(airflow_home, 'dags', '')

    plugin_definition_filename = 'dagster_plugin.py'
    mkdir_p(plugins_path)
    shutil.copyfile(
        script_relative_path(os.path.join('..', 'dagster_airflow', plugin_definition_filename)),
        os.path.abspath(os.path.join(plugins_path, plugin_definition_filename)),
    )

    dag_definition_filename = 'minimal_dockerized_dagster_dag.py'
    mkdir_p(dags_path)
    shutil.copyfile(
        script_relative_path(dag_definition_filename),
        os.path.abspath(os.path.join(dags_path, dag_definition_filename)),
    )

    task_id = 'minimal_dockerized_dagster_airflow_node'
    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    res = subprocess.check_output(
        ['airflow', 'test', 'minimal_dockerized_dagster_airflow_demo', task_id, execution_date]
    )
