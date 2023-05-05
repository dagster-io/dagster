import os
import re

from click.testing import CliRunner
from dagster import file_relative_path
from dagster._cli.project import (
    from_example_command,
    scaffold_code_location_command,
    scaffold_command,
    scaffold_repository_command,
)
from dagster._core.workspace.load_target import get_origins_from_toml
from dagster._generate.download import AVAILABLE_EXAMPLES, EXAMPLES_TO_IGNORE
from dagster._generate.generate import _should_skip_file


def test_project_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_command, ["--name", "existing_dir"])
        assert re.match(r"The directory .* already exists", result.output)
        assert result.exit_code != 0


def test_project_scaffold_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_command, ["--name", "my_dagster_project"])
        assert result.exit_code == 0
        assert os.path.exists("my_dagster_project")
        assert os.path.exists("my_dagster_project/my_dagster_project")
        assert os.path.exists("my_dagster_project/my_dagster_project_tests")
        assert os.path.exists("my_dagster_project/README.md")
        assert os.path.exists("my_dagster_project/pyproject.toml")

        # test target loadable
        origins = get_origins_from_toml("my_dagster_project/pyproject.toml")
        assert len(origins) == 1
        assert origins[0].loadable_target_origin.module_name == "my_dagster_project"


def test_scaffold_code_location_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_code_location_command, ["--name", "existing_dir"])
        assert re.match(r"The directory .* already exists", result.output)
        assert result.exit_code != 0


def test_scaffold_code_location_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_code_location_command, ["--name", "my_dagster_code"])
        assert result.exit_code == 0
        assert os.path.exists("my_dagster_code")
        assert os.path.exists("my_dagster_code/my_dagster_code")
        assert os.path.exists("my_dagster_code/my_dagster_code_tests")
        assert os.path.exists("my_dagster_code/pyproject.toml")

        # test target loadable
        origins = get_origins_from_toml("my_dagster_code/pyproject.toml")
        assert len(origins) == 1
        assert origins[0].loadable_target_origin.module_name == "my_dagster_code"


def test_from_example_command_fails_when_example_not_available():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command, ["--name", "my_dagster_project", "--example", "foo"]
        )
        assert re.match(r"Example .* not available", result.output)
        assert result.exit_code != 0


def test_from_example_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            from_example_command,
            ["--name", "my_dagster_project", "--example", "assets_dbt_python"],
        )
        assert result.exit_code == 0
        assert os.path.exists("my_dagster_project")
        assert os.path.exists("my_dagster_project/assets_dbt_python")
        assert os.path.exists("my_dagster_project/assets_dbt_python_tests")
        # ensure we filter out tox.ini because it's used in our own CI
        assert not os.path.exists("my_dagster_project/tox.ini")


def test_available_examples_in_sync_with_example_folder():
    # ensure the list of AVAILABLE_EXAMPLES is in sync with the example folder minus EXAMPLES_TO_IGNORE
    # run me
    example_folder = file_relative_path(__file__, "../../../../examples")
    available_examples_in_folder = [
        e
        for e in os.listdir(example_folder)
        if (e not in EXAMPLES_TO_IGNORE and not _should_skip_file(e))
    ]
    assert set(available_examples_in_folder) == set(AVAILABLE_EXAMPLES)


# `dagster project scaffold-repository` command is deprecated.
# We're keeping the tests below for backcompat.


def test_scaffold_repository_deprecation():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_repository_command, ["--name", "my_dagster_project"])
        assert re.match(
            (
                "WARNING: This command is deprecated. Use `dagster project scaffold-code-location`"
                " instead."
            ),
            result.output,
        )


def test_scaffold_repository_scaffold_command_fails_when_dir_path_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.mkdir("existing_dir")
        result = runner.invoke(scaffold_repository_command, ["--name", "existing_dir"])
        assert re.match(r"The directory .* already exists", result.output)
        assert result.exit_code != 0


def test_scaffold_repository_command_succeeds():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(scaffold_repository_command, ["--name", "my_dagster_repo"])
        assert result.exit_code == 0
        assert os.path.exists("my_dagster_repo")
        assert os.path.exists("my_dagster_repo/my_dagster_repo")
        assert os.path.exists("my_dagster_repo/my_dagster_repo_tests")
        assert not os.path.exists("my_dagster_repo/workspace.yaml")
