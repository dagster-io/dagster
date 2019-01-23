import datetime
import os
import shutil
import subprocess
import uuid

import docker

from dagster.utils import mkdir_p, script_relative_path


def test_minimal_dockerized_dagster_dag():
    airflow_home = os.getenv('AIRFLOW_HOME')
    assert airflow_home, 'No AIRFLOW_HOME set -- is airflow installed?'

    # check that docker is running
    try:
        docker_client = docker.client.APIClient()
        docker_client.info()
    except docker.errors.APIError:
        raise Exception(
            'Couldn\'t find docker at {url} -- is it running?'.format(url=docker_client._url(''))
        )
    dags_path = os.path.join(airflow_home, 'dags', '')

    dag_definition_filename = 'minimal_dockerized_dagster_dag.py'
    mkdir_p(dags_path)
    shutil.copyfile(
        script_relative_path(dag_definition_filename),
        os.path.join(dags_path, dag_definition_filename),
    )

    task_id = 'minimal_dockerized_dagster_airflow_node'
    execution_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    res = subprocess.check_output(
        ['airflow', 'test', 'minimal_dockerized_dagster_airflow_demo', task_id, execution_date]
    )
    raise Exception()
