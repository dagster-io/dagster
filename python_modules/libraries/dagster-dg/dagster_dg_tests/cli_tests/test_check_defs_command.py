from pathlib import Path

import pytest
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, is_windows, pushd

ensure_dagster_dg_tests_import()
from dagster_components.test.test_cases import BASIC_INVALID_VALUE, BASIC_MISSING_VALUE

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_check_defs_workspace_context_success():
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, create_venv=True):
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "projects/project-1",
        )
        assert_runner_result(result)
        result = runner.invoke(
            "scaffold",
            "project",
            "--use-editable-dagster",
            dagster_git_repo_dir,
            "projects/project-2",
        )
        assert_runner_result(result)

        result = runner.invoke("check", "defs")
        assert_runner_result(result)

        (Path("projects") / "project-1" / "project_1" / "definitions.py").write_text("invalid")
        result = runner.invoke("check", "defs")
        assert result.exit_code == 1


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_check_defs_project_context_success():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("check", "defs")
        assert_runner_result(result)

        (Path("foo_bar") / "definitions.py").write_text("invalid")
        result = runner.invoke("check", "defs")
        assert result.exit_code == 1


def test_implicit_yaml_check_from_dg_check_defs() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke("check", "defs")
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.stdout))
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))


def test_implicit_yaml_check_from_dg_check_defs_workspace() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
        ) as tmpdir,
    ):
        with pushd(str(Path(tmpdir).parent)):
            result = runner.invoke("dev")
            assert result.exit_code != 0, str(result.stdout)

            assert BASIC_MISSING_VALUE.check_error_msg
            BASIC_MISSING_VALUE.check_error_msg(str(result.stdout))
