import re

import click
import mock
import pytest
from click.testing import CliRunner
from dagster.cli.sensor import (
    check_repo_and_scheduler,
    sensor_list_command,
    sensor_preview_command,
    sensor_start_command,
    sensor_stop_command,
)
from dagster.core.host_representation import ExternalRepository
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import environ

from .test_cli_commands import sensor_command_contexts


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensors_list(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(sensor_list_command, cli_args)

            assert result.exit_code == 0
            assert result.output == "Repository bar\n**************\nSensor: foo_sensor [STOPPED]\n"


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensors_start_and_stop(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            runner = CliRunner()

            result = runner.invoke(
                sensor_start_command,
                cli_args + ["foo_sensor"],
            )

            assert result.exit_code == 0
            assert "Started sensor foo_sensor\n" == result.output

            result = runner.invoke(
                sensor_stop_command,
                cli_args + ["foo_sensor"],
            )

            assert result.exit_code == 0
            assert "Stopped sensor foo_sensor\n" == result.output


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensors_start_empty(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance
            result = runner.invoke(
                sensor_start_command,
                cli_args,
            )

            assert result.exit_code == 2
            assert "Missing sensor name argument" in result.output


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensors_start_all(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                sensor_start_command,
                cli_args + ["--start-all"],
            )

            assert result.exit_code == 0
            assert result.output == "Started all sensors for repository bar\n"


def test_check_repo_and_sensorr_no_external_sensors():
    repository = mock.MagicMock(spec=ExternalRepository)
    repository.get_external_sensors.return_value = []
    instance = mock.MagicMock(spec=DagsterInstance)
    with pytest.raises(click.UsageError, match="There are no sensors defined for repository"):
        check_repo_and_scheduler(repository, instance)


def test_check_repo_and_scheduler_dagster_home_not_set():
    with environ({"DAGSTER_HOME": ""}):
        repository = mock.MagicMock(spec=ExternalRepository)
        repository.get_external_sensors.return_value = [mock.MagicMock()]
        instance = mock.MagicMock(spec=DagsterInstance)

        with pytest.raises(
            click.UsageError, match=re.escape("The environment variable $DAGSTER_HOME is not set.")
        ):
            check_repo_and_scheduler(repository, instance)


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensor_preview(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                sensor_preview_command,
                cli_args + ["foo_sensor"],
            )

            assert result.exit_code == 0
            assert result.output == "Sensor returning run requests for 1 run(s):\n\nfoo: FOO\n\n"


@pytest.mark.parametrize("gen_sensor_args", sensor_command_contexts())
def test_sensor_preview_since(gen_sensor_args):
    with gen_sensor_args as (cli_args, instance):
        runner = CliRunner()
        with mock.patch("dagster.core.instance.DagsterInstance.get") as _instance:
            _instance.return_value = instance

            result = runner.invoke(
                sensor_preview_command, cli_args + ["foo_sensor", "--since", 1.1]
            )

            assert result.exit_code == 0
            assert (
                result.output
                == "Sensor returning run requests for 1 run(s):\n\nfoo: FOO\nsince: 1.1\n\n"
            )
