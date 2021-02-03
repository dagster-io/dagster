import re

import click
import mock
import pytest
from click.testing import CliRunner
from dagster.cli.schedule import (
    check_repo_and_scheduler,
    schedule_list_command,
    schedule_logs_command,
    schedule_restart_command,
    schedule_start_command,
    schedule_stop_command,
    schedule_up_command,
    schedule_wipe_command,
)
from dagster.core.host_representation import ExternalRepository
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import environ

from .test_cli_commands import schedule_command_contexts


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_list(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_list_command, cli_args)

            if result.exception:
                raise result.exception

            assert result.exit_code == 0
            assert result.output == ("Repository bar\n" "**************\n")


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_up(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(
                schedule_up_command,
                cli_args,
            )
            assert result.exit_code == 0
            assert "Changes:\n" in result.output
            assert "  + foo_schedule (add)" in result.output
            assert "  + partitioned_schedule (add)" in result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_up_and_list(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(schedule_list_command, cli_args)

            assert result.exit_code == 0
            assert (
                result.output == "Repository bar\n"
                "**************\n"
                "Schedule: foo_schedule [STOPPED]\n"
                "Cron Schedule: * * * * *\n"
                "****************************************\n"
                "Schedule: partitioned_schedule [STOPPED]\n"
                "Cron Schedule: * * * * *\n"
            )


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_start_and_stop(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(
                schedule_up_command,
                cli_args,
            )

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["foo_schedule"],
            )

            assert result.exit_code == 0
            assert "Started schedule foo_schedule\n" == result.output

            result = runner.invoke(
                schedule_stop_command,
                cli_args + ["foo_schedule"],
            )

            assert result.exit_code == 0
            assert "Stopped schedule foo_schedule\n" == result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_start_empty(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
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
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["--start-all"],
            )

            assert result.exit_code == 0
            assert result.output == "Started all schedules for repository bar\n"


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_wipe_correct_delete_message(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(
                schedule_wipe_command,
                cli_args,
                input="DELETE\n",
            )

            if result.exception:
                raise result.exception

            assert result.exit_code == 0
            assert "Turned off all schedules and deleted all schedule history" in result.output

            result = runner.invoke(
                schedule_up_command,
                cli_args + ["--preview"],
            )

            # Verify schedules were wiped
            assert result.exit_code == 0
            assert "Planned Schedule Changes:\n" in result.output
            assert "  + partitioned_schedule (add)" in result.output
            assert "  + foo_schedule (add)" in result.output


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_wipe_incorrect_delete_message(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(
                schedule_wipe_command,
                cli_args,
                input="WRONG\n",
            )

            assert result.exit_code == 0
            assert (
                "Exiting without turning off schedules or deleting schedule history"
                in result.output
            )

            result = runner.invoke(
                schedule_up_command,
                cli_args + ["--preview"],
            )

            # Verify schedules were not wiped
            assert result.exit_code == 0
            assert (
                result.output
                == "No planned changes to schedules.\n2 schedules will remain unchanged\n"
            )


@pytest.mark.parametrize("gen_schedule_args", schedule_command_contexts())
def test_schedules_restart(gen_schedule_args):
    with gen_schedule_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

            result = runner.invoke(
                schedule_start_command,
                cli_args + ["foo_schedule"],
            )

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
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(schedule_up_command, cli_args)

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
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(schedule_logs_command, cli_args + ["foo_schedule"])

            assert result.exit_code == 0
            assert "scheduler.log" in result.output


def test_check_repo_and_scheduler_no_external_schedules():
    repository = mock.MagicMock(spec=ExternalRepository)
    repository.get_external_schedules.return_value = []
    instance = mock.MagicMock(spec=DagsterInstance)
    with pytest.raises(click.UsageError, match="There are no schedules defined for repository"):
        check_repo_and_scheduler(repository, instance)


def test_check_repo_and_scheduler_dagster_home_not_set():
    with environ({"DAGSTER_HOME": ""}):
        repository = mock.MagicMock(spec=ExternalRepository)
        repository.get_external_schedules.return_value = [mock.MagicMock()]
        instance = mock.MagicMock(spec=DagsterInstance)

        with pytest.raises(
            click.UsageError, match=re.escape("The environment variable $DAGSTER_HOME is not set.")
        ):
            check_repo_and_scheduler(repository, instance)


def test_check_repo_and_scheduler_instance_scheduler_not_set():
    repository = mock.MagicMock(spec=ExternalRepository)
    repository.get_external_schedules.return_value = [mock.MagicMock()]
    instance = mock.MagicMock(spec=DagsterInstance)
    type(instance).scheduler = mock.PropertyMock(return_value=None)

    with environ({"DAGSTER_HOME": "~/dagster_home"}):
        with pytest.raises(
            click.UsageError,
            match=re.escape("A scheduler must be configured to run schedule commands."),
        ):
            check_repo_and_scheduler(repository, instance)
