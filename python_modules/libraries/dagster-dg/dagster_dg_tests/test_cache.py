import subprocess
from contextlib import nullcontext
from functools import partial
from pathlib import Path

import pytest
from dagster_dg.utils import pushd

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)

# For all cache tests, avoid setting up venv in example project so we do not prepopulate the
# cache (which is part of the venv setup routine).
example_project = partial(isolated_example_project_foo_bar, populate_cache=False)
cache_runner_args = {"verbose": True}


def test_load_from_cache():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_cache_invalidation_uv_lock():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        subprocess.run(["uv", "add", "dagster-components[dbt]", "dagster-dbt"], check=True)

        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_invalidation_modified_lib():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        result = runner.invoke("scaffold", "component-type", "my_component")
        assert_runner_result(result)

        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_no_invalidation_modified_pkg():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        Path("foo_bar/submodule.py").write_text("print('hello')")

        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


@pytest.mark.parametrize("clear_outside_project", [True, False])
def test_clear_cache(clear_outside_project: bool):
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        with pushd("..") if clear_outside_project else nullcontext():
            result = runner.invoke("--clear-cache")
            assert_runner_result(result)
            assert "CACHE [clear-all]" in result.output

        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_rebuild_component_registry_success():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("--rebuild-component-registry")
        assert_runner_result(result)

        # Run it again and ensure it clears the previous entry
        result = runner.invoke("--rebuild-component-registry")
        assert_runner_result(result)
        assert "CACHE [clear-key]" in result.output

        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_rebuild_component_registry_fails_with_subcommand():
    with (
        ProxyRunner.test(**cache_runner_args) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        result = runner.invoke("--rebuild-component-registry", "list", "component-type")
        assert_runner_result(result, exit_0=False)
        assert "Cannot specify --rebuild-component-registry with a subcommand." in result.output


def test_rebuild_component_registry_fails_with_clear_cache():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("--rebuild-component-registry", "--clear-cache")
        assert_runner_result(result, exit_0=False)
        assert "Cannot specify both --clear-cache and --rebuild-component-registry" in result.output


def test_rebuild_component_registry_fails_with_disabled_cache():
    with ProxyRunner.test(**cache_runner_args) as runner, example_project(runner):
        result = runner.invoke("--rebuild-component-registry", "--disable-cache")
        assert_runner_result(result, exit_0=False)
        assert "Cache is disabled" in result.output


def test_cache_disabled():
    with (
        ProxyRunner.test(**cache_runner_args, disable_cache=True) as runner,
        example_project(runner),
    ):
        result = runner.invoke("list", "component-type")
        assert_runner_result(result)
        assert "CACHE" not in result.output
