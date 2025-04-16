import os
from pathlib import Path
from dagster_dg_tests.utils import ProxyRunner, assert_runner_result, install_to_venv
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()


def test_init_project_and_list_defs():
    """Test that we can initialize a project with `dg init` and then run `dg list defs` without errors."""
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "init",
            "--project-name",
            "test-project",
        )
        assert_runner_result(result)

        assert Path("test-project").exists()

        os.chdir("test-project")

        result = runner.invoke("list", "defs")

        assert_runner_result(result)

        assert "Section" in result.output
        assert "Definitions" in result.output
