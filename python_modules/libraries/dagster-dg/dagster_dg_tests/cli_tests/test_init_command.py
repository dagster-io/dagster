import os
from pathlib import Path

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result


def test_dg_init_command_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("init", input="helloworld\n")
        assert_runner_result(result)
        assert Path("workspace").exists()
        assert Path("workspace/pyproject.toml").exists()
        assert Path("workspace/projects").exists()
        assert Path("workspace/libraries").exists()
        assert Path("workspace/projects/helloworld").exists()
        assert Path("workspace/projects/helloworld/helloworld").exists()
        assert Path("workspace/projects/helloworld/pyproject.toml").exists()
        assert Path("workspace/projects/helloworld/helloworld_tests").exists()


def test_dg_init_workspace_already_exists_failure() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("workspace")
        result = runner.invoke("init", input="helloworld\n")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output
