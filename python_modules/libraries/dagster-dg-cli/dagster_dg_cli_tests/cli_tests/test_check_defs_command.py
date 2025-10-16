from pathlib import Path

import pytest
from dagster_dg_core.utils import discover_git_root, is_windows, pushd
from dagster_shared.utils import environ
from dagster_test.components.test_utils.test_cases import BASIC_INVALID_VALUE, BASIC_MISSING_VALUE
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    create_project_from_components,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_check_defs_workspace_context_success():
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with (
        ProxyRunner.test() as runner,
        isolated_example_workspace(runner, create_venv=True),
        environ({"DAGSTER_GIT_REPO_DIR": dagster_git_repo_dir}),
    ):
        result = runner.invoke_create_dagster(
            "project",
            "--use-editable-dagster",
            "projects/project-1",
            "--uv-sync",
        )
        assert_runner_result(result)
        result = runner.invoke_create_dagster(
            "project",
            "--use-editable-dagster",
            "projects/project-2",
            "--uv-sync",
        )
        assert_runner_result(result)

        result = runner.invoke("check", "defs")
        assert_runner_result(result)

        (Path("projects") / "project-1" / "src" / "project_1" / "defs" / "__init__.py").write_text(
            "invalid"
        )
        result = runner.invoke("check", "defs")
        assert result.exit_code == 1


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_check_defs_project_context_success():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("check", "defs")
        assert_runner_result(result)


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_check_defs_project_context_failure():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        (Path("src") / "foo_bar" / "defs" / "__init__.py").write_text("invalid")
        result = runner.invoke("check", "defs")
        assert result.exit_code == 1


def test_implicit_yaml_check_from_dg_check_defs_in_project_context() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=False,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke("check", "defs", catch_exceptions=False)
            assert result.exit_code != 0, str(result.output)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.output))
            BASIC_MISSING_VALUE.check_error_msg(str(result.output))

            # didn't make it to defs check
            assert "Validation failed for code location foo-bar" not in str(result.output)


def test_implicit_yaml_check_disabled_in_project_context() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=False,
        ) as tmpdir,
    ):
        with pushd(str(tmpdir)):
            result = runner.invoke("check", "defs", "--no-check-yaml", catch_exceptions=False)
            assert result.exit_code != 0, str(result.output)

            # yaml check was skipped, defs check failed
            assert "Validation failed for code location foo-bar" in str(result.output)


def test_no_implicit_yaml_check_from_dg_check_defs_in_workspace_context() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=True,
        ) as tmpdir,
    ):
        with pushd(Path(tmpdir).parent):
            result = runner.invoke("check", "defs", catch_exceptions=False)
            assert result.exit_code != 0, str(result.output)

            # yaml check was skipped, defs check failed
            assert "Validation failed for code location foo-bar" in str(result.output)


def test_implicit_yaml_check_from_dg_check_defs_disallowed_in_workspace_context() -> None:
    with (
        ProxyRunner.test() as runner,
        create_project_from_components(
            runner,
            BASIC_MISSING_VALUE.component_path,
            BASIC_INVALID_VALUE.component_path,
            local_component_defn_to_inject=BASIC_MISSING_VALUE.component_type_filepath,
            in_workspace=True,
        ) as tmpdir,
    ):
        with pushd(Path(tmpdir).parent):
            result = runner.invoke("check", "defs", "--check-yaml", catch_exceptions=False)
            assert result.exit_code != 0, str(result.output)

            assert "--check-yaml is not currently supported in a workspace context" in str(
                result.output
            )

        # It is supported and is the default in a project context within a workspace
        with pushd(tmpdir):
            result = runner.invoke("check", "defs", "--check-yaml", catch_exceptions=False)
            assert result.exit_code != 0, str(result.output)

            assert BASIC_INVALID_VALUE.check_error_msg and BASIC_MISSING_VALUE.check_error_msg
            BASIC_INVALID_VALUE.check_error_msg(str(result.output))
            BASIC_MISSING_VALUE.check_error_msg(str(result.output))
