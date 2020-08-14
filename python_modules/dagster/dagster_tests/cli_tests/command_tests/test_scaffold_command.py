from __future__ import print_function

import re

import pytest
from click.testing import CliRunner

from dagster.cli.pipeline import execute_scaffold_command, pipeline_scaffold_command

from .test_cli_commands import (
    valid_external_pipeline_target_args,
    valid_external_pipeline_target_cli_args,
)


def no_print(_):
    return None


@pytest.mark.parametrize('scaffold_args', valid_external_pipeline_target_args())
def test_scaffold_command(scaffold_args):
    cli_args, uses_legacy_repository_yaml_format = scaffold_args
    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            cli_args['print_only_required'] = True
            execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

            cli_args['print_only_required'] = False
            execute_scaffold_command(cli_args=cli_args, print_fn=no_print)
    else:
        cli_args['print_only_required'] = True
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

        cli_args['print_only_required'] = False
        execute_scaffold_command(cli_args=cli_args, print_fn=no_print)


@pytest.mark.parametrize('execute_cli_args', valid_external_pipeline_target_cli_args())
def test_scaffold_command_cli(execute_cli_args):
    cli_args, uses_legacy_repository_yaml_format = execute_cli_args

    runner = CliRunner()

    if uses_legacy_repository_yaml_format:
        with pytest.warns(
            UserWarning,
            match=re.escape(
                'You are using the legacy repository yaml format. Please update your file '
            ),
        ):
            result = runner.invoke(pipeline_scaffold_command, cli_args)
            assert result.exit_code == 0

            result = runner.invoke(pipeline_scaffold_command, ['--print-only-required'] + cli_args)
            assert result.exit_code == 0
    else:
        result = runner.invoke(pipeline_scaffold_command, cli_args)
        assert result.exit_code == 0

        result = runner.invoke(pipeline_scaffold_command, ['--print-only-required'] + cli_args)
        assert result.exit_code == 0
