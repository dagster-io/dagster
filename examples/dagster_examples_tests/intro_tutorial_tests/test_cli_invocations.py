import json
import os
import runpy

import pytest
from click.testing import CliRunner
from dagit.app import create_app_from_workspace

from dagster.cli.pipeline import pipeline_execute_command
from dagster.cli.workspace import get_workspace_from_kwargs
from dagster.core.instance import DagsterInstance
from dagster.utils import (
    DEFAULT_REPOSITORY_YAML_FILENAME,
    check_script,
    pushd,
    script_relative_path,
)

PIPELINES_OR_ERROR_QUERY = '''
{
    repositoryLocationsOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryLocationConnection {
            nodes {
                repositories {
                    pipelines {
                        name
                    }
                }
            }
        }
    }
}
'''


def path_to_tutorial_file(path):
    return script_relative_path(os.path.join('../../dagster_examples/intro_tutorial/', path))


def load_dagit_for_workspace_cli_args(n_pipelines=1, **kwargs):
    workspace = get_workspace_from_kwargs(kwargs)

    app = create_app_from_workspace(workspace, DagsterInstance.ephemeral())

    client = app.test_client()

    res = client.get('/graphql?query={query_string}'.format(query_string=PIPELINES_OR_ERROR_QUERY))
    json_res = json.loads(res.data.decode('utf-8'))
    assert 'data' in json_res
    assert 'repositoryLocationsOrError' in json_res['data']
    assert 'nodes' in json_res['data']['repositoryLocationsOrError']
    assert (
        len(
            json_res['data']['repositoryLocationsOrError']['nodes'][0]['repositories'][0][
                'pipelines'
            ]
        )
        == n_pipelines
    )

    return res


def dagster_pipeline_execute(args, return_code):
    runner = CliRunner()
    res = runner.invoke(pipeline_execute_command, args)
    assert res.exit_code == return_code, res.exception

    return res


cli_args = [
    # filename, fn_name, env_yaml, mode, preset, return_code, exception
    ('hello_cereal.py', 'hello_cereal_pipeline', None, None, None, 0, None),
    ('serial_pipeline.py', 'serial_pipeline', None, None, None, 0, None),
    ('complex_pipeline.py', 'complex_pipeline', None, None, None, 0, None),
    ('inputs.py', 'inputs_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('config_bad_1.py', 'config_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('config_bad_2.py', 'config_pipeline', 'config_bad_2.yaml', None, None, 0, None,),
    ('config.py', 'config_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('config.py', 'config_pipeline', 'config_env_bad.yaml', None, None, 0, None),
    ('inputs_typed.py', 'inputs_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('custom_types.py', 'custom_type_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('custom_types_2.py', 'custom_type_pipeline', 'custom_types_2.yaml', None, None, 1, Exception,),
    ('custom_types_3.py', 'custom_type_pipeline', 'custom_type_input.yaml', None, None, 0, None),
    ('custom_types_4.py', 'custom_type_pipeline', 'custom_type_input.yaml', None, None, 0, None),
    ('custom_types_5.py', 'custom_type_pipeline', 'custom_type_input.yaml', None, None, 0, None),
    (
        'custom_types_mypy_verbose.py',
        'custom_type_pipeline',
        'inputs_env.yaml',
        None,
        None,
        0,
        None,
    ),
    (
        'custom_types_mypy_typing_trick.py',
        'custom_type_pipeline',
        'inputs_env.yaml',
        None,
        None,
        0,
        None,
    ),
    ('materializations.py', 'materialization_pipeline', 'inputs_env.yaml', None, None, 0, None),
    (
        'output_materialization.py',
        'output_materialization_pipeline',
        'output_materialization.yaml',
        None,
        None,
        0,
        None,
    ),
    ('materializations.py', 'materialization_pipeline', 'intermediates.yaml', None, None, 0, None),
    (
        'serialization_strategy.py',
        'serialization_strategy_pipeline',
        'inputs_env.yaml',
        None,
        None,
        0,
        None,
    ),
    ('resources.py', 'resources_pipeline', 'resources.yaml', None, None, 0, None),
    ('required_resources.py', 'resources_pipeline', 'resources.yaml', None, None, 0, None),
    ('modes.py', 'modes_pipeline', 'resources.yaml', 'unittest', None, 0, None),
    ('presets.py', 'presets_pipeline', None, None, 'unittest', 0, None),
    ('multiple_outputs.py', 'multiple_outputs_pipeline', 'inputs_env.yaml', None, None, 0, None),
    ('reusable_solids.py', 'reusable_solids_pipeline', 'reusable_solids.yaml', None, None, 0, None),
    (
        'composite_solids.py',
        'composite_solids_pipeline',
        'composite_solids.yaml',
        None,
        None,
        0,
        None,
    ),
    ('scheduler.py', 'hello_cereal_pipeline', None, None, None, 0, None),
]


@pytest.mark.parametrize(
    'filename,fn_name,_env_yaml,_mode,_preset,_return_code,_exception', cli_args
)
# dagit -f filename -n fn_name
def test_load_pipeline(filename, fn_name, _env_yaml, _mode, _preset, _return_code, _exception):
    with pushd(path_to_tutorial_file('')):
        load_dagit_for_workspace_cli_args(
            python_file=path_to_tutorial_file(filename), fn_name=fn_name
        )


@pytest.mark.parametrize('filename,fn_name,env_yaml,mode,preset,return_code,_exception', cli_args)
# dagster pipeline execute -f filename -n fn_name -e env_yaml --preset preset
def test_dagster_pipeline_execute(
    filename, fn_name, env_yaml, mode, preset, return_code, _exception
):
    with pushd(path_to_tutorial_file('')):
        dagster_pipeline_execute(
            ['-f', path_to_tutorial_file(filename), '-a', fn_name]
            + (['-e', env_yaml] if env_yaml else [])
            + (['-d', mode] if mode else [])
            + (['--preset', preset] if preset else []),
            return_code,
        )


@pytest.mark.parametrize(
    'filename,_fn_name,_env_yaml,_mode,_preset,return_code,_exception', cli_args
)
def test_script(filename, _fn_name, _env_yaml, _mode, _preset, return_code, _exception):
    with pushd(path_to_tutorial_file('')):
        check_script(path_to_tutorial_file(filename), return_code)


@pytest.mark.parametrize(
    'filename,_fn_name,_env_yaml,_mode,_preset,_return_code,exception', cli_args
)
def test_runpy(filename, _fn_name, _env_yaml, _mode, _preset, _return_code, exception):
    with pushd(path_to_tutorial_file('')):
        if exception:
            with pytest.raises(exception):
                runpy.run_path(filename, run_name='__main__')
        else:
            runpy.run_path(filename, run_name='__main__')


# TODO python command line

# dagit
def test_load_repo():
    load_dagit_for_workspace_cli_args(
        n_pipelines=2, repository_yaml=path_to_tutorial_file(DEFAULT_REPOSITORY_YAML_FILENAME)
    )
