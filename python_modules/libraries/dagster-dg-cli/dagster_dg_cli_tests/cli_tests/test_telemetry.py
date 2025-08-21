import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dagster_dg_core.utils import pushd
from dagster_shared.telemetry import (
    cleanup_telemetry_logger,
    get_or_create_dir_from_dagster_home,
    get_telemetry_logger,
)
from dagster_test.components.test_utils.test_cases import BASIC_INVALID_VALUE, BASIC_VALID_VALUE
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    crawl_cli_commands,
    create_project_from_components,
    isolated_example_project_foo_bar,
    modify_environment_variable,
)

NO_TELEMETRY_COMMANDS = {
    ("utils", "inspect-component"),
    # Is actually instrumented, but since subcommands are dynamically generated we test manually
    ("scaffold",),
}


@pytest.fixture
def telemetry_caplog(caplog):
    # telemetry logger doesn't propagate to the root logger, so need to attach the caplog handler
    get_telemetry_logger().addHandler(caplog.handler)
    yield caplog
    get_telemetry_logger().removeHandler(caplog.handler)
    # Needed to avoid file contention issues on windows with the telemetry log file
    cleanup_telemetry_logger()


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
def test_basic_logging_success_failure(
    telemetry_caplog: pytest.LogCaptureFixture, success: bool
) -> None:
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
        telemetry_caplog.clear()
        with pushd(tmpdir):
            result = runner.invoke("check", "yaml")
            assert result.exit_code == 0 if success else 1

        assert os.path.exists(
            os.path.join(get_or_create_dir_from_dagster_home("logs"), "event.log")
        )
        assert len(telemetry_caplog.records) == 2, telemetry_caplog.records

        first_message = json.loads(telemetry_caplog.records[0].getMessage())
        second_message = json.loads(telemetry_caplog.records[1].getMessage())

        assert first_message["action"] == "check_yaml_command_started"
        assert second_message["action"] == "check_yaml_command_ended"
        assert second_message["metadata"]["command_success"] == "True" if success else "False", (
            second_message["metadata"]
        )


def test_telemetry_disabled_dagster_yaml(telemetry_caplog: pytest.LogCaptureFixture) -> None:
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
        telemetry_caplog.clear()

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
        assert len(telemetry_caplog.records) == 0


def test_telemetry_disabled_dg_config(telemetry_caplog: pytest.LogCaptureFixture) -> None:
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
        telemetry_caplog.clear()
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

        assert len(telemetry_caplog.records) == 0


@pytest.mark.skip("temp")
def test_telemetry_scaffold_component(telemetry_caplog: pytest.LogCaptureFixture) -> None:
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
        TemporaryDirectory() as dagster_home,
        modify_environment_variable("DAGSTER_HOME", dagster_home),
    ):
        telemetry_caplog.clear()
        result = runner.invoke(
            "scaffold", "defs", "dagster_test.components.AllMetadataEmptyComponent", "qux"
        )
        assert result.exit_code == 0, result.output + " " + str(result.exception)
        assert Path("foo_bar/defs/qux").exists()
        assert len(telemetry_caplog.records) == 2
        first_message = json.loads(telemetry_caplog.records[0].getMessage())
        second_message = json.loads(telemetry_caplog.records[1].getMessage())
        assert first_message["action"] == "scaffold_component_command_started"
        assert second_message["action"] == "scaffold_component_command_ended"
        assert second_message["metadata"]["command_success"] == "True"
