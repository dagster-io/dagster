from pathlib import Path

import pytest
from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import, is_windows

ensure_dagster_dg_tests_import()
from dagster_dg_tests.utils import (
    ProxyRunner,
    isolated_example_project_foo_bar,
    isolated_example_workspace,
)


# @pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
@pytest.mark.skip  # Weirdness with environment, temporarily skipping
def test_validate_command_deployment_context_success():
    dagster_git_repo_dir = str(discover_git_root(Path(__file__)))
    with ProxyRunner.test() as runner, isolated_example_workspace(runner, create_venv=True):
        runner.invoke(
            "scaffold", "project", "--use-editable-dagster", dagster_git_repo_dir, "project-1"
        )
        runner.invoke(
            "scaffold", "project", "--use-editable-dagster", dagster_git_repo_dir, "project-2"
        )

        result = runner.invoke("check", "definitions")
        assert result.exit_code == 0

        (Path("projects") / "project-1" / "project_1" / "definitions.py").write_text("invalid")
        result = runner.invoke("check", "definitions")
        assert result.exit_code == 1


@pytest.mark.skipif(is_windows(), reason="Temporarily skipping (signal issues in CLI)..")
def test_validate_command_code_location_context_success():
    with ProxyRunner.test() as runner, isolated_example_project_foo_bar(runner):
        result = runner.invoke("check", "defs")
        assert result.exit_code == 0

        (Path("foo_bar") / "definitions.py").write_text("invalid")
        result = runner.invoke("check", "defs")
        assert result.exit_code == 1
