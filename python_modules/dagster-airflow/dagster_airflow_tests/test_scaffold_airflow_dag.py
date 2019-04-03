import datetime
import os

import pytest

from dagster.utils import load_yaml_from_path, script_relative_path

from dagster_airflow.scaffold import scaffold_airflow_dag
from .test_project.dagster_airflow_demo import define_demo_execution_pipeline


PIPELINE = define_demo_execution_pipeline()

ENV_CONFIG = load_yaml_from_path(script_relative_path('test_project/env.yml'))

IMAGE = 'dagster-airflow-demo'


def _exclude_timestamp(file_contents):
    return [
        line
        for line in file_contents.split('\n')
        if '\'start_date\': datetime.datetime(' not in line
    ]


def test_scaffold_airflow_dag_bad_path_type():
    with pytest.raises(Exception, match='must be a tuple'):
        scaffold_airflow_dag(pipeline=PIPELINE, env_config=ENV_CONFIG, image=IMAGE, output_path=4)


def test_scaffold_airflow_dag_bad_path_no_directory():
    with pytest.raises(Exception, match='No directory found'):
        scaffold_airflow_dag(
            pipeline=PIPELINE,
            env_config=ENV_CONFIG,
            image=IMAGE,
            output_path=script_relative_path('foo.py'),
        )


def test_scaffold_airflow_dag_bad_path_relative():
    with pytest.raises(Exception, match='expected an absolute path,'):
        scaffold_airflow_dag(pipeline=PIPELINE, env_config=ENV_CONFIG, image=IMAGE, output_path='~')


def test_scaffold_airflow_dag_bad_paths_relative():
    with pytest.raises(Exception, match='expected a tuple of absolute paths,'):
        scaffold_airflow_dag(
            pipeline=PIPELINE,
            env_config=ENV_CONFIG,
            image=IMAGE,
            output_path=('~', script_relative_path('foo.py')),
        )


def test_scaffold_airflow_dag_bad_paths_len():
    with pytest.raises(Exception, match='Got a tuple with bad length'):
        scaffold_airflow_dag(
            pipeline=PIPELINE,
            env_config=ENV_CONFIG,
            image=IMAGE,
            output_path=(script_relative_path('foo.py'),),
        )


def test_scaffold_airflow_dag_bad_paths_not_py():
    with pytest.raises(Exception, match='expected a tuple of absolute paths to python files'):
        scaffold_airflow_dag(
            pipeline=PIPELINE,
            env_config=ENV_CONFIG,
            image=IMAGE,
            output_path=(script_relative_path('foo.bar'), script_relative_path('baz.quux')),
        )


def test_scaffold_airflow_dag_bad_paths_module():
    with pytest.raises(Exception, match='no dots permitted in filenames.'):
        scaffold_airflow_dag(
            pipeline=PIPELINE,
            env_config=ENV_CONFIG,
            image=IMAGE,
            output_path=(script_relative_path('foo.bar.py'), script_relative_path('baz.quux.py')),
        )


def test_scaffold_airflow_dag(snapshot):
    static_path, editable_path = scaffold_airflow_dag(
        pipeline=PIPELINE, env_config=ENV_CONFIG, image=IMAGE
    )
    try:
        with open(static_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
        with open(editable_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
    finally:
        os.remove(static_path)
        os.remove(editable_path)


def test_scaffold_airflow_dag_specify_paths(snapshot):
    static_path, editable_path = scaffold_airflow_dag(
        pipeline=PIPELINE,
        env_config=ENV_CONFIG,
        image=IMAGE,
        output_path=(script_relative_path('foo.py'), script_relative_path('bar.py')),
    )
    try:
        with open(static_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
        with open(editable_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
    finally:
        os.remove(static_path)
        os.remove(editable_path)


def test_scaffold_airflow_dag_specify_dir(snapshot):
    static_path, editable_path = scaffold_airflow_dag(
        pipeline=PIPELINE, env_config=ENV_CONFIG, image=IMAGE, output_path=script_relative_path('.')
    )
    try:
        with open(static_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
        with open(editable_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
    finally:
        os.remove(static_path)
        os.remove(editable_path)


def test_scaffold_airflow_override_args(snapshot):
    static_path, editable_path = scaffold_airflow_dag(
        pipeline=PIPELINE,
        env_config=ENV_CONFIG,
        image=IMAGE,
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )
    try:
        with open(static_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
        with open(editable_path, 'r') as fd:
            snapshot.assert_match(_exclude_timestamp(fd.read()))
    finally:
        os.remove(static_path)
        os.remove(editable_path)


def test_scaffold_dag(airflow_test):
    docker_image, dags_path, _ = airflow_test
    pipeline = define_demo_execution_pipeline()
    env_config = load_yaml_from_path(script_relative_path('test_project/env.yml'))

    scaffold_airflow_dag(
        pipeline=pipeline,
        env_config=env_config,
        image=docker_image,
        output_path=script_relative_path('test_project'),
        dag_kwargs={'default_args': {'start_date': datetime.datetime(1900, 1, 1)}},
    )
