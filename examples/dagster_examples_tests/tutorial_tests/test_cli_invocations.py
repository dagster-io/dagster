import json
import os
import subprocess

from click.testing import CliRunner
from dagit.app import create_app

from dagster import DagsterInvalidConfigError
from dagster.cli.load_handle import handle_for_repo_cli_args
from dagster.cli.pipeline import pipeline_execute_command
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.utils import DEFAULT_REPOSITORY_YAML_FILENAME, script_relative_path

PIPELINES_OR_ERROR_QUERY = '{ pipelinesOrError { ... on PipelineConnection { nodes { name } } } }'


def path_to_tutorial_file(path):
    return script_relative_path(os.path.join('../../dagster_examples/intro_tutorial/', path))


def load_dagit_for_repo_cli_args(n_pipelines=1, **kwargs):
    handle = handle_for_repo_cli_args(kwargs)
    pipeline_run_storage = InMemoryRunStorage()

    app = create_app(handle, pipeline_run_storage)

    client = app.test_client()

    res = client.get('/graphql?query={query_string}'.format(query_string=PIPELINES_OR_ERROR_QUERY))
    json_res = json.loads(res.data.decode('utf-8'))
    assert 'data' in json_res
    assert 'pipelinesOrError' in json_res['data']
    assert 'nodes' in json_res['data']['pipelinesOrError']
    assert len(json_res['data']['pipelinesOrError']['nodes']) == n_pipelines

    return res


def dagster_pipeline_execute(args, exc=None):
    runner = CliRunner()
    res = runner.invoke(pipeline_execute_command, args)
    if exc:
        assert res.exception
        assert isinstance(res.exception, exc)
    else:
        assert res.exit_code == 0

    return res


# dagit -f hello_world.py -n hello_world_pipeline
def test_load_hello_world_pipeline():
    load_dagit_for_repo_cli_args(
        python_file=path_to_tutorial_file('hello_world.py'), fn_name='hello_world_pipeline'
    )


# dagit -f inputs.py -n hello_inputs_pipeline
def test_load_hello_inputs_pipeline():
    load_dagit_for_repo_cli_args(
        python_file=path_to_tutorial_file('inputs.py'), fn_name='hello_inputs_pipeline'
    )


# dagit -f config.py -n hello_with_config_pipeline
def test_load_hello_with_config_pipeline():
    load_dagit_for_repo_cli_args(
        python_file=path_to_tutorial_file('config.py'), fn_name='hello_with_config_pipeline'
    )


# dagit -f repos.py -n define_repo
def test_load_repo_demo_pipeline():
    load_dagit_for_repo_cli_args(
        python_file=path_to_tutorial_file('repos.py'), fn_name='define_repo'
    )


# dagit -f reusing_solids.py -n reusing_solids_pipeline
def test_load_reusing_solids_pipeline():
    load_dagit_for_repo_cli_args(
        python_file=path_to_tutorial_file('reusing_solids.py'), fn_name='reusing_solids_pipeline'
    )


# python hello_world.py
def test_run_hello_world_py():
    subprocess.check_output(['python', path_to_tutorial_file('hello_world.py')])


# dagster pipeline execute -f hello_world.py -n hello_world_pipeline
def test_dagster_pipeline_execute_hello_world_pipeline():
    dagster_pipeline_execute(
        ['-f', path_to_tutorial_file('hello_world.py'), '-n', 'hello_world_pipeline']
    )


# dagster pipeline execute -f hello_dag.py -n hello_dag_pipeline
def test_dagster_pipeline_execute_hello_dag_pipeline():
    dagster_pipeline_execute(
        ['-f', path_to_tutorial_file('hello_dag.py'), '-n', 'hello_dag_pipeline']
    )


# dagster pipeline execute -f actual_dag.py -n actual_dag_pipeline
def test_dagster_pipeline_execute_diamond_dag_pipeline():
    dagster_pipeline_execute(
        ['-f', path_to_tutorial_file('actual_dag.py'), '-n', 'actual_dag_pipeline']
    )


# dagster pipeline execute -f inputs.py -n hello_inputs_pipeline -e inputs_env.yaml
def test_dagster_pipeline_execute_inputs_pipeline():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('inputs.py'),
            '-n',
            'hello_inputs_pipeline',
            '-e',
            path_to_tutorial_file('inputs_env.yaml'),
        ]
    )


# dagster pipeline execute -f config.py -n hello_with_config_pipeline -e config_env.yaml
def test_dagster_pipeline_execute_config_pipeline():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('config.py'),
            '-n',
            'hello_with_config_pipeline',
            '-e',
            path_to_tutorial_file('config_env.yaml'),
        ]
    )


# dagster pipeline execute \
#   -f configuration_schemas.py \
#   -n configuration_schema_pipeline \
#   -e configuration_schemas.yaml
def test_dagster_pipeline_execute_configuration_schema_pipeline():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('configuration_schemas.py'),
            '-n',
            'configuration_schema_pipeline',
            '-e',
            path_to_tutorial_file('configuration_schemas.yaml'),
        ]
    )


# dagster pipeline execute \
#   -f configuration_schemas.py \
#   -n configuration_schema_pipeline \
#   -e configuration_schemas_bad_config.yaml
def test_dagster_pipeline_execute_configuration_schema_pipeline_bad_config():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('configuration_schemas.py'),
            '-n',
            'configuration_schema_pipeline',
            '-e',
            path_to_tutorial_file('configuration_schemas_bad_config.yaml'),
        ],
        exc=DagsterInvalidConfigError,
    )


# dagster pipeline execute -f configuration_schemas.py -n configuration_schema_pipeline -e configuration_schemas_wrong_field.yaml
def test_dagster_pipeline_execute_configuration_schema_pipeline_wrong_field_config():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('configuration_schemas.py'),
            '-n',
            'configuration_schema_pipeline',
            '-e',
            path_to_tutorial_file('configuration_schemas_wrong_field.yaml'),
        ],
        exc=DagsterInvalidConfigError,
    )


# dagster pipeline execute -f execution_context.py -n execution_context_pipeline
def test_dagster_pipeline_execute_execution_context_pipeline():
    dagster_pipeline_execute(
        ['-f', path_to_tutorial_file('execution_context.py'), '-n', 'execution_context_pipeline']
    )


# dagster pipeline execute \
#   -f execution_context.py \
#   -n execution_context_pipeline \
#   -e execution_context.yaml
def test_dagster_pipeline_execute_execution_context_pipeline_config():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('execution_context.py'),
            '-n',
            'execution_context_pipeline',
            '-e',
            path_to_tutorial_file('execution_context.yaml'),
        ]
    )


# dagster pipeline execute demo_execution_pipeline -e env.yaml
def test_dagster_pipeline_execute_repo_demo_execution_pipeline():
    dagster_pipeline_execute(
        [
            'demo_execution_pipeline',
            '-y',
            path_to_tutorial_file('pipeline_execution_repository.yaml'),
            '-e',
            path_to_tutorial_file('pipeline_execution_env.yaml'),
        ]
    )


# dagster pipeline execute demo_execution_pipeline -e constant_env.yaml -e specific_env.yaml
def test_dagster_pipeline_execute_repo_demo_execution_pipeline_multi_config():
    dagster_pipeline_execute(
        [
            'demo_execution_pipeline',
            '-y',
            path_to_tutorial_file('pipeline_execution_repository.yaml'),
            '-e',
            path_to_tutorial_file('constant_env.yaml'),
            '-e',
            path_to_tutorial_file('specific_env.yaml'),
        ]
    )


# dagster pipeline execute \
#   -f expectations.py \
#   -n expectations_tutorial_pipeline \
#   -e expectations_pass.yaml
def test_dagster_pipeline_execute_expectations_pipeline():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('expectations.py'),
            '-n',
            'expectations_tutorial_pipeline',
            '-e',
            path_to_tutorial_file('expectations_pass.yaml'),
        ]
    )


# dagster pipeline execute \
#   -f expectations.py \
#   -n expectations_tutorial_pipeline \
#   -e expectations_fail.yaml
def test_dagster_pipeline_execute_expectations_pipeline_fail():
    dagster_pipeline_execute(
        [
            '-f',
            path_to_tutorial_file('expectations.py'),
            '-n',
            'expectations_tutorial_pipeline',
            '-e',
            path_to_tutorial_file('expectations_fail.yaml'),
        ]
    )


# dagit
def test_load_repo():
    load_dagit_for_repo_cli_args(
        n_pipelines=8, repository_yaml=path_to_tutorial_file(DEFAULT_REPOSITORY_YAML_FILENAME)
    )
