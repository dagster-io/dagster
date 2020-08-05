from __future__ import print_function

import mock
import pytest
from click.testing import CliRunner

from dagster.cli.schedule import (
    schedule_list_command,
    schedule_logs_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_up_command,
    schedule_wipe_command,
)

from .test_cli_commands import schedule_command_contexts


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_list(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_list_command, cli_args)

            if result.exception:
                raise result.exception

            assert result.exit_code == 0
            assert result.output == ('Repository bar\n' '**************\n')


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_up(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args,)
            assert result.exit_code == 0
            assert 'Changes:\n  + foo_schedule (add)' in result.output


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_up_and_list(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_list_command, cli_args)

            assert result.exit_code == 0
            assert (
                result.output == 'Repository bar\n'
                '**************\n'
                'Schedule: foo_schedule [STOPPED]\n'
                'Cron Schedule: * * * * *\n'
            )


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_start_and_stop(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(schedule_up_command, cli_args,)

            result = runner.invoke(schedule_start_command, cli_args + ['foo_schedule'],)

            assert result.exit_code == 0
            assert 'Started schedule foo_schedule\n' == result.output

            result = runner.invoke(schedule_stop_command, cli_args + ['foo_schedule'],)

            assert result.exit_code == 0
            assert 'Stopped schedule foo_schedule\n' == result.output


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_start_empty(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_start_command, cli_args,)

            assert result.exit_code == 0
            assert 'Noop: dagster schedule start was called without any arguments' in result.output


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_start_all(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_start_command, cli_args + ['--start-all'],)

            assert result.exit_code == 0
            assert result.output == 'Started all schedules for repository bar\n'


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_wipe_correct_delete_message(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_wipe_command, cli_args, input="DELETE\n",)

            if result.exception:
                raise result.exception

            assert result.exit_code == 0
            assert 'Wiped all schedules and schedule cron jobs' in result.output

            result = runner.invoke(schedule_up_command, cli_args + ['--preview'],)

            # Verify schedules were wiped
            assert result.exit_code == 0
            assert 'Planned Schedule Changes:\n  + foo_schedule (add)' in result.output


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_wipe_incorrect_delete_message(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_wipe_command, cli_args, input="WRONG\n",)

            assert result.exit_code == 0
            assert 'Exiting without deleting all schedules and schedule cron jobs' in result.output

            result = runner.invoke(schedule_up_command, cli_args + ['--preview'],)

            # Verify schedules were not wiped
            assert result.exit_code == 0
            assert (
                result.output
                == 'No planned changes to schedules.\n1 schedules will remain unchanged\n'
            )


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_restart(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_start_command, cli_args + ['foo_schedule'],)

            result = runner.invoke(schedule_restart_command, cli_args + ['foo_schedule'],)

            assert result.exit_code == 0
            assert 'Restarted schedule foo_schedule' in result.output


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_restart_all(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_start_command, cli_args + ['foo_schedule'],)

            result = runner.invoke(
                schedule_restart_command, cli_args + ['foo_schedule', '--restart-all-running'],
            )
            assert result.exit_code == 0
            assert result.output == 'Restarted all running schedules for repository bar\n'


@pytest.mark.parametrize('gen_schedule_args', schedule_command_contexts())
def test_schedules_logs(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        with mock.patch('dagster.core.instance.DagsterInstance.get') as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(schedule_logs_command, cli_args + ['foo_schedule'],)

            assert result.exit_code == 0
            assert result.output.endswith('scheduler.log\n')
