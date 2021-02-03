import os

from click.testing import CliRunner
from dagster.cli import new_repo_cli


def test_new_repo_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(new_repo_cli, ["existing_dir"])
        assert isinstance(result.exception, FileExistsError)
        assert result.exit_code != 0


def test_new_repo_command_fails_when_file_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("existing_file", "a").close()
        result = runner.invoke(new_repo_cli, ["existing_file"])
        assert isinstance(result.exception, FileExistsError)
        assert result.exit_code != 0


def test_new_repo_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(new_repo_cli, ["my-repo"])
        assert result.exit_code == 0
