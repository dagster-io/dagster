import re
from unittest import mock

import click
import pytest
from click.testing import CliRunner
from dagster._cli.schedule import (
    schedule_list_command,
    schedule_logs_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_wipe_command,
)
from dagster._cli.utils import validate_dagster_home_is_set, validate_repo_has_defined_schedules
from dagster._core.remote_representation import RemoteRepository
from dagster._core.test_utils import environ

from dagster_tests.cli_tests.command_tests.test_cli_commands import (
    schedule_command_contexts,
    scheduler_instance,
)


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_list(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_list_command, cli_args)

            if result.exception:
                raise result.exception

            assert result.exit_code == 0
            assert (
                result.output == "Repository bar\n"
                "**************\n"
                "Schedule: foo_schedule [STOPPED]\n"
                "Cron Schedule: * * * * *\n"
                "**********************************\n"
                "Schedule: union_schedule [STOPPED]\n"
                "Cron Schedule: ['* * * * *', '* * * * *']\n"
            )


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_start_and_stop(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["foo_schedule"],
            )

            assert result.exit_code == 0
            assert result.output == "Started schedule foo_schedule\n"

            result = runner.invoke(
                schedule_stop_command,
                cli_args + ["foo_schedule"],
            )

            assert result.exit_code == 0
            assert result.output == "Stopped schedule foo_schedule\n"


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_start_empty(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(
                schedule_start_command,
                cli_args,
            )

            assert result.exit_code == 0
            assert "Noop: dagster schedule start was called without any arguments" in result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_start_all(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["--start-all"],
            )

            assert result.exit_code == 0
            assert result.output == "Started all schedules for repository bar\n"


def test_schedules_wipe_correct_delete_message():
    runner = CliRunner()
    with (
        scheduler_instance() as instance,
        mock.patch("dagster._core.instance.DagsterInstance.get") as _instance,
    ):
        _instance.return_value = instance

        result = runner.invoke(
            schedule_wipe_command,
            input="DELETE\n",
        )

        if result.exception:
            raise result.exception

        assert result.exit_code == 0
        assert "Turned off all schedules and deleted all schedule history" in result.output


def test_schedules_wipe_incorrect_delete_message():
    runner = CliRunner()
    with (
        scheduler_instance() as instance,
        mock.patch("dagster._core.instance.DagsterInstance.get") as _instance,
    ):
        _instance.return_value = instance
        result = runner.invoke(
            schedule_wipe_command,
            input="WRONG\n",
        )

        assert result.exit_code == 0
        assert "Exiting without turning off schedules or deleting schedule history" in result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_restart(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["foo_schedule"],
            )
            assert result.exit_code == 0

            result = runner.invoke(
                schedule_restart_command,
                cli_args + ["foo_schedule"],
            )

            assert result.exit_code == 0
            assert "Restarted schedule foo_schedule" in result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_restart_all(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["foo_schedule"],
            )

            result = runner.invoke(
                schedule_restart_command,
                cli_args + ["foo_schedule", "--restart-all-running"],
            )
            assert result.exit_code == 0
            assert result.output == "Restarted all running schedules for repository bar\n"


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_logs(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        with mock.patch("dagster._core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(schedule_logs_command, cli_args + ["foo_schedule"])

            assert result.exit_code == 0
            assert "scheduler.log" in result.output


def test_validate_repo_schedules():
    repository = mock.MagicMock(spec=RemoteRepository)
    repository.get_schedules.return_value = []
    with pytest.raises(click.UsageError, match="There are no schedules defined for repository"):
        validate_repo_has_defined_schedules(repository)


def test_validate_no_dagster_home():
    with environ({"DAGSTER_HOME": ""}):
        with pytest.raises(
            click.UsageError, match=re.escape("The environment variable $DAGSTER_HOME is not set.")
        ):
            validate_dagster_home_is_set()
