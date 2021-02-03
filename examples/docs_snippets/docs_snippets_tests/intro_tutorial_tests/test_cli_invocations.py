import json
import os
import runpy

import pytest
from click.testing import CliRunner
from dagit.app import create_app_from_workspace
from dagster.cli.pipeline import pipeline_execute_command
from dagster.cli.workspace import get_workspace_from_kwargs
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import instance_for_test
from dagster.utils import check_script, pushd, script_relative_path

PIPELINES_OR_ERROR_QUERY = """
{
    repositoriesOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryConnection {
            nodes {
                pipelines {
                    name
                }
            }
        }
    }
}
"""

cli_args = [
    # dirname, filename, fn_name, env_yaml, mode, preset, return_code, exception
    (
        "basics/e01_first_pipeline/",
        "hello_cereal.py",
        "hello_cereal_pipeline",
        None,
        None,
        None,
        0,
        None,
    ),
    ("basics/e02_solids/", "inputs.py", "inputs_pipeline", "inputs_env.yaml", None, None, 0, None),
    (
        "basics/e02_solids/",
        "config_bad_1.py",
        "config_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e02_solids/",
        "config_bad_2.py",
        "config_pipeline",
        "config_bad_2.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e02_solids/",
        "config.py",
        "config_pipeline",
        "config_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e02_solids/",
        "multiple_outputs.py",
        "multiple_outputs_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    ("basics/e03_pipelines/", "serial_pipeline.py", "serial_pipeline", None, None, None, 0, None),
    ("basics/e03_pipelines/", "complex_pipeline.py", "complex_pipeline", None, None, None, 0, None),
    (
        "basics/e04_quality/",
        "inputs_typed.py",
        "inputs_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types.py",
        "custom_type_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types_2.py",
        "custom_type_pipeline",
        "custom_types_2.yaml",
        None,
        None,
        1,
        Exception,
    ),
    (
        "basics/e04_quality/",
        "custom_types_3.py",
        "custom_type_pipeline",
        "custom_type_input.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types_4.py",
        "custom_type_pipeline",
        "custom_type_input.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types_5.py",
        "custom_type_pipeline",
        "custom_type_input.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types_mypy_verbose.py",
        "custom_type_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "basics/e04_quality/",
        "custom_types_mypy_typing_trick.py",
        "custom_type_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/solids/",
        "reusable_solids.py",
        "reusable_solids_pipeline",
        "reusable_solids.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/solids/",
        "composite_solids.py",
        "composite_solids_pipeline",
        "composite_solids.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/pipelines/",
        "resources.py",
        "resources_pipeline",
        "resources.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/pipelines/",
        "required_resources.py",
        "resources_pipeline",
        "resources.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/pipelines/",
        "modes.py",
        "modes_pipeline",
        "resources.yaml",
        "unittest",
        None,
        0,
        None,
    ),
    ("advanced/pipelines/", "presets.py", "presets_pipeline", None, None, "unittest", 0, None),
    (
        "advanced/materializations/",
        "materializations.py",
        "materialization_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/materializations/",
        "output_materialization.py",
        "output_materialization_pipeline",
        "output_materialization.yaml",
        None,
        None,
        0,
        None,
    ),
    (
        "advanced/scheduling/",
        "scheduler.py",
        "hello_cereal_pipeline",
        "inputs_env.yaml",
        None,
        None,
        0,
        None,
    ),
]


def path_to_tutorial_file(path):
    return script_relative_path(os.path.join("../../docs_snippets/intro_tutorial/", path))


def load_dagit_for_workspace_cli_args(n_pipelines=1, **kwargs):
    instance = DagsterInstance.ephemeral()
    with get_workspace_from_kwargs(kwargs) as workspace:
        app = create_app_from_workspace(workspace, instance)

        client = app.test_client()

        res = client.get(
            "/graphql?query={query_string}".format(query_string=PIPELINES_OR_ERROR_QUERY)
        )
        json_res = json.loads(res.data.decode("utf-8"))
        assert "data" in json_res
        assert "repositoriesOrError" in json_res["data"]
        assert "nodes" in json_res["data"]["repositoriesOrError"]
        assert len(json_res["data"]["repositoriesOrError"]["nodes"][0]["pipelines"]) == n_pipelines

    return res


def dagster_pipeline_execute(args, return_code):
    with instance_for_test():
        runner = CliRunner()
        res = runner.invoke(pipeline_execute_command, args)
    assert res.exit_code == return_code, res.exception

    return res


@pytest.mark.parametrize(
    "dirname,filename,fn_name,_env_yaml,_mode,_preset,_return_code,_exception", cli_args
)
# dagit -f filename -n fn_name
def test_load_pipeline(
    dirname, filename, fn_name, _env_yaml, _mode, _preset, _return_code, _exception
):
    with pushd(path_to_tutorial_file(dirname)):
        filepath = path_to_tutorial_file(os.path.join(dirname, filename))
        load_dagit_for_workspace_cli_args(python_file=filepath, fn_name=fn_name)


@pytest.mark.parametrize(
    "dirname,filename,fn_name,env_yaml,mode,preset,return_code,_exception", cli_args
)
# dagster pipeline execute -f filename -n fn_name -e env_yaml --preset preset
def test_dagster_pipeline_execute(
    dirname, filename, fn_name, env_yaml, mode, preset, return_code, _exception
):
    with pushd(path_to_tutorial_file(dirname)):
        filepath = path_to_tutorial_file(os.path.join(dirname, filename))
        yamlpath = path_to_tutorial_file(os.path.join(dirname, env_yaml)) if env_yaml else None
        dagster_pipeline_execute(
            ["-f", filepath, "-a", fn_name]
            + (["-c", yamlpath] if yamlpath else [])
            + (["--mode", mode] if mode else [])
            + (["--preset", preset] if preset else []),
            return_code,
        )


@pytest.mark.parametrize(
    "dirname,filename,_fn_name,_env_yaml,_mode,_preset,return_code,_exception", cli_args
)
def test_script(dirname, filename, _fn_name, _env_yaml, _mode, _preset, return_code, _exception):
    with pushd(path_to_tutorial_file(dirname)):
        filepath = path_to_tutorial_file(os.path.join(dirname, filename))
        check_script(filepath, return_code)


@pytest.mark.parametrize(
    "dirname,filename,_fn_name,_env_yaml,_mode,_preset,_return_code,exception", cli_args
)
def test_runpy(dirname, filename, _fn_name, _env_yaml, _mode, _preset, _return_code, exception):
    with pushd(path_to_tutorial_file(dirname)):
        filepath = path_to_tutorial_file(os.path.join(dirname, filename))
        if exception:
            with pytest.raises(exception):
                runpy.run_path(filepath, run_name="__main__")
        else:
            runpy.run_path(filepath, run_name="__main__")
