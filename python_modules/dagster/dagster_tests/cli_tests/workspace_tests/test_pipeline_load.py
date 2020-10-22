import sys

import click
import pytest
from click.testing import CliRunner

from dagster import seven
from dagster.cli.workspace.cli_target import (
    get_external_pipeline_from_kwargs,
    pipeline_target_argument,
)
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.utils import file_relative_path

WINDOWS_PY36 = seven.IS_WINDOWS and sys.version_info[0] == 3 and sys.version_info[1] == 6


def load_pipeline_via_cli_runner(cli_args):
    capture_result = {"external_pipeline": None}

    @click.command(name="test_pipeline_command")
    @pipeline_target_argument
    def command(**kwargs):
        with get_external_pipeline_from_kwargs(
            kwargs, DagsterInstance.ephemeral()
        ) as external_pipeline:
            capture_result["external_pipeline"] = external_pipeline

    runner = CliRunner()
    result = runner.invoke(command, cli_args)

    external_pipeline = capture_result["external_pipeline"]
    return result, external_pipeline


def successfully_load_pipeline_via_cli(cli_args):
    result, external_pipeline = load_pipeline_via_cli_runner(cli_args)
    assert result.exit_code == 0
    assert isinstance(external_pipeline, ExternalPipeline)
    return external_pipeline


PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE = file_relative_path(
    __file__, "hello_world_in_file/python_file_with_named_location_workspace.yaml"
)


def get_all_loading_combos():
    def _iterate_combos():
        possible_location_args = [[], ["-l", "hello_world_location"]]
        possible_repo_args = [[], ["-r", "hello_world_repository"]]
        possible_pipeline_args = [[], ["-p", "hello_world_pipeline"]]

        for location_args in possible_location_args:
            for repo_args in possible_repo_args:
                for pipeline_args in possible_pipeline_args:
                    yield [
                        "-w",
                        PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE,
                    ] + location_args + repo_args + pipeline_args

    return tuple(_iterate_combos())


@pytest.mark.parametrize("cli_args", get_all_loading_combos())
@pytest.mark.skipif(WINDOWS_PY36, reason="Failing due to https://bugs.python.org/issue37380")
def test_valid_loading_combos_single_pipeline_repo_location(cli_args):
    external_pipeline = successfully_load_pipeline_via_cli(cli_args)
    assert isinstance(external_pipeline, ExternalPipeline)
    assert external_pipeline.name == "hello_world_pipeline"


@pytest.mark.skipif(WINDOWS_PY36, reason="Failing due to https://bugs.python.org/issue37380")
def test_repository_target_argument_one_repo_and_specified_wrong():
    result, _ = load_pipeline_via_cli_runner(
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-p", "not_present"]
    )

    assert result.exit_code == 2
    assert (
        """Pipeline "not_present" not found in repository """
        """"hello_world_repository". Found ['hello_world_pipeline'] instead."""
    ) in result.stdout


MULTI_PIPELINE_WORKSPACE = file_relative_path(__file__, "multi_pipeline/multi_pipeline.yaml")


@pytest.mark.skipif(WINDOWS_PY36, reason="Failing due to https://bugs.python.org/issue37380")
def test_successfully_find_pipeline():
    assert (
        successfully_load_pipeline_via_cli(
            ["-w", MULTI_PIPELINE_WORKSPACE, "-p", "pipeline_one"]
        ).name
        == "pipeline_one"
    )

    assert (
        successfully_load_pipeline_via_cli(
            ["-w", MULTI_PIPELINE_WORKSPACE, "-p", "pipeline_two"]
        ).name
        == "pipeline_two"
    )


@pytest.mark.skipif(WINDOWS_PY36, reason="Failing due to https://bugs.python.org/issue37380")
def test_must_provide_name_to_multi_pipeline():
    result, _ = load_pipeline_via_cli_runner(["-w", MULTI_PIPELINE_WORKSPACE])

    assert result.exit_code == 2
    assert (
        """Must provide --pipeline as there is more than one pipeline in """
        """multi_pipeline. Options are: ['pipeline_one', 'pipeline_two']."""
    ) in result.stdout
