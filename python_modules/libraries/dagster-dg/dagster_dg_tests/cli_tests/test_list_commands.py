import textwrap

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
    isolated_example_deployment_foo,
)


def test_list_code_locations_success():
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        runner.invoke("generate", "code-location", "foo")
        runner.invoke("generate", "code-location", "bar")
        result = runner.invoke("list", "code-locations")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            bar
            foo
        """).strip()
        )


def test_list_code_locations_outside_deployment_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("list", "code-locations")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster deployment directory" in result.output


def test_list_component_types_success():
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            dagster_components.test.all_metadata_empty_asset
            dagster_components.test.simple_asset
                A simple asset that returns a constant string value.
            dagster_components.test.simple_pipes_script_asset
                A simple asset that runs a Python script with the Pipes subprocess client.
        """).strip()
        )


def test_list_component_types_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("list", "component-types")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output


def test_list_components_succeeds():
    with ProxyRunner.test() as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke(
            "generate",
            "component",
            "dagster_components.test.all_metadata_empty_asset",
            "qux",
        )
        assert_runner_result(result)
        result = runner.invoke("list", "components")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
            qux
        """).strip()
        )


def test_list_components_command_outside_code_location_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("list", "components")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster code location directory" in result.output
