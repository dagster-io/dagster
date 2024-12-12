import sys
from pathlib import Path

from click.testing import CliRunner
from dagster_dg import __file__ as dagster_dg_init_py
from dagster_dg.cli.generate import generate_code_location_command, generate_component_command
from dagster_dg.cli.list import (
    list_code_locations_command,
    list_component_types_command,
    list_components_command,
)


def ensure_dagster_dg_tests_import() -> None:
    dagster_dg_package_root = (Path(dagster_dg_init_py) / ".." / "..").resolve()
    assert (
        dagster_dg_package_root / "dagster_dg_tests"
    ).exists(), "Could not find dagster_dg_tests where expected"
    sys.path.append(dagster_dg_package_root.as_posix())


ensure_dagster_dg_tests_import()

from dagster_dg_tests.cli_tests.test_generate_commands import (
    isolated_example_code_location_bar,
    isolated_example_code_location_bar_with_component_type_baz,
    isolated_example_deployment_foo,
)


def test_list_code_locations_success():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        runner.invoke(generate_code_location_command, ["foo"])
        runner.invoke(generate_code_location_command, ["bar"])
        result = runner.invoke(list_code_locations_command)
        assert result.exit_code == 0
        assert result.output == "bar\nfoo\n"


def test_list_code_locations_outside_deployment_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(list_code_locations_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster deployment directory" in result.output


def test_list_component_types_success():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        result = runner.invoke(list_component_types_command)
        assert result.exit_code == 0
        assert (
            result.output
            == "\n".join(
                [
                    "dagster_components.pipes_subprocess_script_collection",
                ]
            )
            + "\n"
        )


def test_list_component_types_outside_code_location_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(list_component_types_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location directory" in result.output


def test_list_components_succeeds():
    runner = CliRunner()
    # with isolated_example_code_location_bar(runner):
    with isolated_example_code_location_bar_with_component_type_baz(runner):
        result = runner.invoke(list_components_command)
        runner.invoke(generate_component_command, ["bar.baz", "qux"])
        result = runner.invoke(list_components_command)
        assert result.output == "qux\n"


def test_list_components_command_outside_code_location_fails() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(list_components_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location directory" in result.output
