import subprocess
from functools import partial
from pathlib import Path

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
)

# For all cache tests, avoid setting up venv in example code location so we do not prepopulate the
# cache (which is part of the venv setup routine).
example_code_location = partial(isolated_example_code_location_bar, skip_venv=True)


def test_load_from_cache():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_cache_invalidation_uv_lock():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)

        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_invalidation_modified_lib():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        result = runner.invoke("component-type", "scaffold", "my_component")
        assert_runner_result(result)

        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_no_invalidation_modified_pkg():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        Path("bar/submodule.py").write_text("print('hello')")

        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_clear_cache():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        result = runner.invoke("--clear-cache")
        assert_runner_result(result)
        assert "CACHE [clear-all]" in result.output
        result = runner.invoke("component-type", "list")

        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_rebuild_component_registry_success():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("--rebuild-component-registry")
        assert_runner_result(result)

        # Run it again and ensure it clears the previous entry
        result = runner.invoke("--rebuild-component-registry")
        assert_runner_result(result)
        assert "CACHE [clear-key]" in result.output

        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_rebuild_component_registry_fails_outside_code_location():
    with ProxyRunner.test(verbose=True) as runner, runner.isolated_filesystem():
        result = runner.invoke("--rebuild-component-registry")
        assert_runner_result(result, exit_0=False)
        assert "This command must be run inside a Dagster code location" in result.output


def test_rebuild_component_registry_fails_with_subcommand():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("--rebuild-component-registry", "component-type", "list")
        assert_runner_result(result, exit_0=False)
        assert "Cannot specify --rebuild-component-registry with a subcommand." in result.output


def test_rebuild_component_registry_fails_with_clear_cache():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("--rebuild-component-registry", "--clear-cache")
        assert_runner_result(result, exit_0=False)
        assert "Cannot specify both --clear-cache and --rebuild-component-registry" in result.output


def test_rebuild_component_registry_fails_with_disabled_cache():
    with ProxyRunner.test(verbose=True) as runner, example_code_location(runner):
        result = runner.invoke("--rebuild-component-registry", "--disable-cache")
        assert_runner_result(result, exit_0=False)
        assert "Cache is disabled" in result.output


def test_cache_disabled():
    with (
        ProxyRunner.test(verbose=True, disable_cache=True) as runner,
        example_code_location(runner),
    ):
        result = runner.invoke("component-type", "list")
        assert_runner_result(result)
        assert "CACHE" not in result.output
