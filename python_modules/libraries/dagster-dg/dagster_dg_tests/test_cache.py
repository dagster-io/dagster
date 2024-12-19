import subprocess
from pathlib import Path

import pytest

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_code_location_bar,
)


def test_load_from_cache():
    with ProxyRunner.test(verbose=True) as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


def test_cache_invalidation_uv_lock():
    with ProxyRunner.test(verbose=True) as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        subprocess.run(["uv", "add", "dagster-components[dbt]"], check=True)

        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_invalidation_modified_lib():
    with ProxyRunner.test(verbose=True) as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        result = runner.invoke("generate", "component-type", "my_component")
        assert_runner_result(result)

        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_no_invalidation_modified_pkg():
    with ProxyRunner.test(verbose=True) as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        Path("bar/submodule.py").write_text("print('hello')")

        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [hit]" in result.output


@pytest.mark.parametrize("with_command", [True, False])
def test_cache_clear(with_command: bool):
    with ProxyRunner.test(verbose=True) as runner, isolated_example_code_location_bar(runner):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE [miss]" in result.output
        assert "CACHE [write]" in result.output

        if with_command:
            result = runner.invoke("--clear-cache", "list", "component-types")
        else:
            result = runner.invoke("--clear-cache")
            assert_runner_result(result)
            result = runner.invoke("list", "component-types")

        assert_runner_result(result)
        assert "CACHE [miss]" in result.output


def test_cache_disabled():
    with (
        ProxyRunner.test(verbose=True, disable_cache=True) as runner,
        isolated_example_code_location_bar(runner),
    ):
        result = runner.invoke("list", "component-types")
        assert_runner_result(result)
        assert "CACHE" not in result.output
