import os
from pathlib import Path

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result

# ########################
# ##### SCAFFOLD
# ########################


def test_scaffold_deployment_command_success() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("deployment", "scaffold", "foo")
        assert_runner_result(result)
        assert Path("foo").exists()
        assert Path("foo/.github").exists()
        assert Path("foo/.github/workflows").exists()
        assert Path("foo/.github/workflows/dagster-cloud-deploy.yaml").exists()
        assert Path("foo/dagster_cloud.yaml").exists()
        assert Path("foo/code_locations").exists()


def test_scaffold_deployment_command_already_exists_fails() -> None:
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("foo")
        result = runner.invoke("deployment", "scaffold", "foo")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output
