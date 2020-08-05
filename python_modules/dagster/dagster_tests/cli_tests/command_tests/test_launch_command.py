from __future__ import print_function

import re

import pytest
from click.testing import CliRunner

from dagster.cli.pipeline import execute_launch_command, pipeline_launch_command

from .test_cli_commands import (
    default_instance,
    grpc_server_bar_cli_args,
    launch_command_contexts,
    python_bar_cli_args,
    valid_pipeline_target_cli_args,
)


def run_launch(kwargs, instance, expected_count=None):
    run = execute_launch_command(instance, kwargs)
    assert run
    if expected_count:
        assert instance.get_runs_count() == expected_count
    instance.run_launcher.join()


def run_launch_cli(execution_args, instance, expected_count=None):
    runner = CliRunner()
    result = runner.invoke(pipeline_launch_command, execution_args)
    assert result.exit_code == 0, result.stdout
    if expected_count:
        assert instance.get_runs_count() == expected_count


@pytest.mark.parametrize('gen_pipeline_args', launch_command_contexts())
def test_launch_pipeline(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, uses_legacy_repository_yaml_format, instance):
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                run_launch(cli_args, instance, expected_count=1)
        else:
            run_launch(cli_args, instance, expected_count=1)


@pytest.mark.parametrize('pipeline_cli_args', valid_pipeline_target_cli_args())
def test_launch_pipeline_cli(pipeline_cli_args):
    with default_instance() as instance:
        cli_args, uses_legacy_repository_yaml_format = pipeline_cli_args
        if uses_legacy_repository_yaml_format:
            with pytest.warns(
                UserWarning,
                match=re.escape(
                    'You are using the legacy repository yaml format. Please update your file '
                ),
            ):
                run_launch_cli(cli_args, instance, expected_count=1)
        else:
            run_launch_cli(cli_args, instance, expected_count=1)


@pytest.mark.parametrize(
    'gen_pipeline_args',
    [
        python_bar_cli_args('foo'),
        pytest.param(grpc_server_bar_cli_args('foo'), marks=pytest.mark.deployed_grpc),
    ],
)
def test_launch_subset_pipeline_single_clause_solid_name(gen_pipeline_args):
    runner = CliRunner()
    with default_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command, args + ['--solid-selection', 'do_something',],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert run.solid_selection == ['do_something']
            assert run.solids_to_execute == {'do_something'}


@pytest.mark.parametrize(
    'gen_pipeline_args',
    [
        python_bar_cli_args('foo'),
        pytest.param(grpc_server_bar_cli_args('foo'), marks=pytest.mark.deployed_grpc),
    ],
)
def test_launch_subset_pipeline_single_clause_dsl_query(gen_pipeline_args):
    runner = CliRunner()
    with default_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command, args + ['--solid-selection', '*do_something+',],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert run.solid_selection == ['*do_something+']
            assert run.solids_to_execute == {'do_something', 'do_input'}


@pytest.mark.parametrize(
    'gen_pipeline_args',
    [
        python_bar_cli_args('foo'),
        pytest.param(grpc_server_bar_cli_args('foo'), marks=pytest.mark.deployed_grpc),
    ],
)
def test_launch_subset_pipeline_multiple_clauses(gen_pipeline_args):
    runner = CliRunner()
    with default_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command, args + ['--solid-selection', '*do_something+,do_input',],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert set(run.solid_selection) == set(['*do_something+', 'do_input'])
            assert run.solids_to_execute == {'do_something', 'do_input'}


@pytest.mark.parametrize(
    'gen_pipeline_args',
    [
        python_bar_cli_args('foo'),
        pytest.param(grpc_server_bar_cli_args('foo'), marks=pytest.mark.deployed_grpc),
    ],
)
def test_launch_subset_pipeline_invalid_value(gen_pipeline_args):
    runner = CliRunner()
    with default_instance() as _instance:
        with gen_pipeline_args as args:
            result = runner.invoke(pipeline_launch_command, args + ['--solid-selection', 'a, b',],)
            assert result.exit_code == 1
            assert 'No qualified solids to execute found for solid_selection' in str(
                result.exception
            )
