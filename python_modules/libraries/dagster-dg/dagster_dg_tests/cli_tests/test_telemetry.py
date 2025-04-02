from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dagster.components.test.test_cases import BASIC_INVALID_VALUE, BASIC_VALID_VALUE
from dagster_dg.utils import ensure_dagster_dg_tests_import, pushd

ensure_dagster_dg_tests_import()

import json
import os

from dagster_shared.telemetry import get_or_create_dir_from_dagster_home

from dagster_dg_tests.utils import (
    ProxyRunner,
    crawl_cli_commands,
    create_project_from_components,
    isolated_example_project_foo_bar,
    modify_environment_variable,
)

NO_TELEMETRY_COMMANDS = {
    ("utils", "inspect-component-type"),
    # Is actually instrumented, but since subcommands are dynamically generated we test manually
    ("scaffold",),
}


def test_telemetry_commands_properly_wrapped():
    commands = crawl_cli_commands()
    for command, command_defn in commands.items():
        if tuple(command[1:]) in NO_TELEMETRY_COMMANDS:
            continue

        fn = command_defn.callback
        while hasattr(fn, "__wrapped__"):
            if getattr(fn, "__has_cli_telemetry_wrapper", None) is True:
                break
            fn = getattr(fn, "__wrapped__")

        assert hasattr(fn, "__has_cli_telemetry_wrapper") is True, (
            f"Command {command} is not properly wrapped. Please wrap in the @cli_telemetry_wrapper decorator "
            "or add it to the NO_TELEMETRY_COMMANDS set."
        )


@pytest.mark.parametrize("success", [True, False])
def test_basic_logging_success_failure(caplog: pytest.LogCaptureFixture, success: bool) -> None:
    test_case = BASIC_VALID_VALUE if success else BASIC_INVALID_VALUE
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            test_case.component_path,
            local_component_defn_to_inject=test_case.component_type_filepath,
        ) as tmpdir,
        TemporaryDirectory() as dagster_home,
        modify_environment_variable("DAGSTER_HOME", dagster_home),
    ):
        caplog.clear()
        with pushd(tmpdir):
            result = runner.invoke("check", "yaml")
            assert result.exit_code == 0 if success else 1

        assert os.path.exists(
            os.path.join(get_or_create_dir_from_dagster_home("logs"), "event.log")
        )
        assert len(caplog.records) == 2, caplog.records

        first_message = json.loads(caplog.records[0].getMessage())
        second_message = json.loads(caplog.records[1].getMessage())

        assert first_message["action"] == "check_yaml_command_started"
        assert second_message["action"] == "check_yaml_command_ended"
        assert (
            second_message["metadata"]["command_success"] == "True" if success else "False"
        ), second_message["metadata"]


def test_telemetry_disabled_dagster_yaml(caplog: pytest.LogCaptureFixture) -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
        ) as tmpdir,
        TemporaryDirectory() as dagster_home,
        modify_environment_variable("DAGSTER_HOME", dagster_home),
    ):
        caplog.clear()

        dagster_yaml = Path(dagster_home) / "dagster.yaml"
        dagster_yaml.write_text(
            """
            telemetry:
                enabled: false
            """
        )
        with pushd(tmpdir):
            result = runner.invoke("check", "yaml")
            assert result.exit_code == 0

        assert not os.path.exists(
            os.path.join(get_or_create_dir_from_dagster_home("logs"), "event.log")
        )
        assert len(caplog.records) == 0


def test_telemetry_disabled_dg_config(caplog: pytest.LogCaptureFixture) -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_VALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_VALID_VALUE.component_type_filepath,
        ) as tmpdir,
        TemporaryDirectory() as dg_cli_config_folder,
        TemporaryDirectory() as dagster_cloud_config_folder,
        modify_environment_variable("DG_CLI_CONFIG", str(Path(dg_cli_config_folder) / "dg.toml")),
        modify_environment_variable(
            "DAGSTER_CLOUD_CLI_CONFIG", str(Path(dagster_cloud_config_folder) / "config.yaml")
        ),
    ):
        caplog.clear()
        dg_config_path = Path(dg_cli_config_folder) / "dg.toml"
        dg_config_path.write_text(
            """
            [cli.telemetry]
            enabled = false
            """
        )

        with pushd(tmpdir):
            result = runner.invoke("check", "yaml")
            assert result.exit_code == 0, str(result.exception)

        assert len(caplog.records) == 0


@pytest.mark.skip("temp")
def test_telemetry_scaffold_component(caplog: pytest.LogCaptureFixture) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
        TemporaryDirectory() as dagster_home,
        modify_environment_variable("DAGSTER_HOME", dagster_home),
    ):
        caplog.clear()
        result = runner.invoke(
            "scaffold", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert Path("foo_bar/defs/qux").exists()
        assert len(caplog.records) == 2
        first_message = json.loads(caplog.records[0].getMessage())
        second_message = json.loads(caplog.records[1].getMessage())
        assert first_message["action"] == "scaffold_component_command_started"
        assert second_message["action"] == "scaffold_component_command_ended"
        assert second_message["metadata"]["command_success"] == "True"
