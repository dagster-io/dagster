from click.testing import CliRunner
from dagster._components import ComponentRegistry
from dagster._components.cli.generate import (
    generate_code_location_command,
    generate_component_command,
    generate_component_type_command,
)
from dagster._components.cli.list import (
    list_code_locations_command,
    list_component_types_command,
    list_components_command,
)
from dagster_tests.components_tests.cli_tests.test_generate_commands import (
    isolated_example_code_location_bar,
    isolated_example_deployment_foo,
)


def test_list_code_locations_command():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        runner.invoke(generate_code_location_command, ["bar"])
        runner.invoke(generate_code_location_command, ["baz"])
        result = runner.invoke(list_code_locations_command)
        assert result.exit_code == 0
        assert result.output == "bar\nbaz\n"


def test_list_code_locations_outside_deployment_fails():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(list_code_locations_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster deployment project" in result.output


def test_list_component_types_command():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        runner.invoke(generate_component_type_command, ["alpha"])
        result = runner.invoke(list_component_types_command)
        assert result.exit_code == 0
        assert "alpha" in result.output  # local types
        for k in ComponentRegistry.get_global().keys():  # global types
            assert k in result.output


def test_list_component_types_outside_code_location_fails():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(list_component_types_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output


def test_list_components_command():
    runner = CliRunner()
    with isolated_example_code_location_bar(runner):
        runner.invoke(generate_component_command, ["simple_asset", "alpha"])
        runner.invoke(generate_component_command, ["simple_asset", "beta"])
        result = runner.invoke(list_components_command)
        assert result.exit_code == 0
        assert result.output == "alpha\nbeta\n"


def test_list_components_outside_code_location_fails():
    runner = CliRunner()
    with isolated_example_deployment_foo(runner):
        result = runner.invoke(list_components_command)
        assert result.exit_code != 0
        assert "must be run inside a Dagster code location project" in result.output
