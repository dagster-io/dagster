import textwrap
from pathlib import Path

import pytest
import tomli
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, pushd

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    clear_module_from_cache,
    isolated_example_deployment_foo,
)

# ########################
# ##### SCAFFOLD
# ########################

# At this time all of our tests are against an editable install of dagster-components. The reason
# for this is that this package should always be tested against the corresponding version of
# dagster-copmonents (i.e. from the same commit), and the only way to achieve this right now is
# using the editable install variant of `dg code-location SCAFFOLD`.
#
# Ideally we would have a way to still use the matching dagster-components without using the
# editable install variant, but this will require somehow configuring uv to ensure that it builds
# and returns the local version of the package.


def test_code_location_scaffold_inside_deployment_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("code-location", "scaffold", "foo-bar", "--use-editable-dagster")
        assert_runner_result(result)
        assert Path("code_locations/foo-bar").exists()
        assert Path("code_locations/foo-bar/foo_bar").exists()
        assert Path("code_locations/foo-bar/foo_bar/lib").exists()
        assert Path("code_locations/foo-bar/foo_bar/components").exists()
        assert Path("code_locations/foo-bar/foo_bar_tests").exists()
        assert Path("code_locations/foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("code_locations/foo-bar/.venv").exists()
        assert Path("code_locations/foo-bar/uv.lock").exists()

        # Restore when we are able to test without editable install
        # with open("code_locations/bar/pyproject.toml") as f:
        #     toml = tomli.loads(f.read())
        #
        #     # No tool.uv.sources added without --use-editable-dagster
        #     assert "uv" not in toml["tool"]

        # Check cache was populated
        with pushd("code_locations/foo-bar"):
            result = runner.invoke("component-type", "list", "--verbose")
            assert_runner_result(result)
            assert "CACHE [hit]" in result.output


def test_code_location_scaffold_outside_deployment_success(monkeypatch) -> None:
    # Remove when we are able to test without editable install
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem(), clear_module_from_cache("bar"):
        result = runner.invoke("code-location", "scaffold", "foo-bar", "--use-editable-dagster")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv created
        assert Path("foo-bar/.venv").exists()
        assert Path("foo-bar/uv.lock").exists()


@pytest.mark.parametrize("mode", ["env_var", "arg"])
def test_code_location_scaffold_editable_dagster_success(mode: str, monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    if mode == "env_var":
        monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))
        editable_args = ["--use-editable-dagster", "--"]
    else:
        editable_args = ["--use-editable-dagster", str(dagster_git_repo_dir)]
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("code-location", "scaffold", *editable_args, "foo-bar")
        assert_runner_result(result)
        assert Path("code_locations/foo-bar").exists()
        assert Path("code_locations/foo-bar/pyproject.toml").exists()
        with open("code_locations/foo-bar/pyproject.toml") as f:
            toml = tomli.loads(f.read())
            assert toml["tool"]["uv"]["sources"]["dagster"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-pipes"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster-pipes",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-webserver"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/dagster-webserver",
                "editable": True,
            }
            assert toml["tool"]["uv"]["sources"]["dagster-components"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/libraries/dagster-components",
                "editable": True,
            }
            # Check for presence of one random package with no component to ensure we are
            # preemptively adding all packages
            assert toml["tool"]["uv"]["sources"]["dagstermill"] == {
                "path": f"{dagster_git_repo_dir}/python_modules/libraries/dagstermill",
                "editable": True,
            }


def test_code_location_scaffold_skip_venv_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("code-location", "scaffold", "--skip-venv", "foo-bar")
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_code_location_scaffold_no_use_dg_managed_environment_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "code-location", "scaffold", "--no-use-dg-managed-environment", "foo-bar"
        )
        assert_runner_result(result)
        assert Path("foo-bar").exists()
        assert Path("foo-bar/foo_bar").exists()
        assert Path("foo-bar/foo_bar/lib").exists()
        assert Path("foo-bar/foo_bar/components").exists()
        assert Path("foo-bar/foo_bar_tests").exists()
        assert Path("foo-bar/pyproject.toml").exists()

        # Check venv not created
        assert not Path("foo-bar/.venv").exists()
        assert not Path("foo-bar/uv.lock").exists()


def test_code_location_scaffold_editable_dagster_no_env_var_no_value_fails(monkeypatch) -> None:
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", "")
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("code-location", "scaffold", "--use-editable-dagster", "--", "bar")
        assert_runner_result(result, exit_0=False)
        assert "requires the `DAGSTER_GIT_REPO_DIR`" in result.output


def test_code_location_scaffold_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        result = runner.invoke("code-location", "scaffold", "bar", "--skip-venv")
        assert_runner_result(result)
        result = runner.invoke("code-location", "scaffold", "bar", "--skip-venv")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output


# ########################
# ##### LIST
# ########################


def test_code_location_list_success():
    with ProxyRunner.test() as runner, isolated_example_deployment_foo(runner):
        runner.invoke("code-location", "scaffold", "foo")
        runner.invoke("code-location", "scaffold", "bar")
        result = runner.invoke("code-location", "list")
        assert_runner_result(result)
        assert (
            result.output.strip()
            == textwrap.dedent("""
                bar
                foo
            """).strip()
        )


def test_code_location_list_outside_deployment_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("code-location", "list")
        assert_runner_result(result, exit_0=False)
        assert "must be run inside a Dagster deployment directory" in result.output
