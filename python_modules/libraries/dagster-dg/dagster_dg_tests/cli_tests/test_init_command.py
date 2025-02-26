import os
from pathlib import Path

from dagster_dg.utils import discover_git_root, ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result


def test_dg_init_command_success(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("init", "--use-editable-dagster", input="\nhelloworld\n")
        assert_runner_result(result)
        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/pyproject.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert Path("dagster-workspace/libraries").exists()
        assert Path("dagster-workspace/projects/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/helloworld").exists()
        assert Path("dagster-workspace/projects/helloworld/pyproject.toml").exists()
        assert Path("dagster-workspace/projects/helloworld/helloworld_tests").exists()


def test_dg_init_command_no_project(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke("init", "--use-editable-dagster", input="\n\n")
        assert_runner_result(result)
        assert Path("dagster-workspace").exists()
        assert Path("dagster-workspace/pyproject.toml").exists()
        assert Path("dagster-workspace/projects").exists()
        assert Path("dagster-workspace/libraries").exists()


def test_dg_init_override_workspace_name(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        result = runner.invoke(
            "init", "--use-editable-dagster", input="my-workspace\ngoodbyeworld\n"
        )
        assert_runner_result(result)
        assert Path("my-workspace").exists()
        assert Path("my-workspace/pyproject.toml").exists()
        assert Path("my-workspace/projects").exists()
        assert Path("my-workspace/libraries").exists()
        assert Path("my-workspace/projects/goodbyeworld").exists()
        assert Path("my-workspace/projects/goodbyeworld/goodbyeworld").exists()
        assert Path("my-workspace/projects/goodbyeworld/pyproject.toml").exists()
        assert Path("my-workspace/projects/goodbyeworld/goodbyeworld_tests").exists()


def test_dg_init_workspace_already_exists_failure(monkeypatch) -> None:
    dagster_git_repo_dir = discover_git_root(Path(__file__))
    monkeypatch.setenv("DAGSTER_GIT_REPO_DIR", str(dagster_git_repo_dir))

    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        os.mkdir("dagster-workspace")
        result = runner.invoke("init", "--use-editable-dagster", input="\nhelloworld\n")
        assert_runner_result(result, exit_0=False)
        assert "already exists" in result.output
